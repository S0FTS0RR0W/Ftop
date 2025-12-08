# a btop clone with slight customizations written in python with a random hex dump for looks

import os
import signal
import sys
import time
import threading
import random
import curses
from collections import deque
from datetime import datetime
import platform
import hex  # Import the hex module
import re
import psutil

def signal_handler(sig, frame):
    # curses will handle terminal cleanup
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def setup_colors():
    """Initializes color pairs for curses."""
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)  # Headers / Titles
    curses.init_pair(2, curses.COLOR_GREEN, -1) # Bars
    curses.init_pair(3, 242, -1)              # Dim text (borders)
    return {
        'title': curses.color_pair(1),
        'bar': curses.color_pair(2),
        'border': curses.color_pair(3),
    }

def get_bar(percent, width, color_map):
    """Creates a simple text-based progress bar."""
    filled_width = int(percent / 100 * width)
    bar = "┃" * filled_width + " " * (width - filled_width)
    return bar, color_map['bar']

def format_bytes(n):
    """Formats bytes into a human-readable string (KB, MB, GB)."""
    if n is None: return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"

def draw_sparkline(win, y, x, data, width, title, max_val=100.0):
    """Draws a simple sparkline graph, ensuring it fits."""
    win_height, win_width = win.getmaxyx()
    win.addstr(y, x, f"{title}: [") # Title can be of variable length

    # Calculate available space for the graph itself
    graph_start_x = x + len(title) + 3
    closing_bracket_x = graph_start_x + width

    # Check if the entire sparkline (including title and brackets) fits
    if closing_bracket_x >= win_width -1:
        # If it doesn't fit, don't draw the graph part to avoid crashing
        return

    if not data:
        win.addstr(y, graph_start_x, " " * width)
        win.addstr(y, closing_bracket_x, "]")
        return

    if max_val == 0: max_val = 100.0

    # Braille-based sparkline
    braille_dots = [[0, 0] for _ in range(width)]
    data_points = list(data) # Create a list for index access
    num_data_points = len(data_points)

    for i in range(width):
        # Map the data point to the current graph column
        data_idx = int(i * num_data_points / width)
        if data_idx >= num_data_points: continue

        val = data_points[data_idx]
        
        # Map the value to the 4 vertical dots in a braille character
        dot_level = int((val / max_val) * 4)
        
        # Set the braille dots from the bottom up
        if dot_level > 0: braille_dots[i][0] |= 0x40  # Dot 7
        if dot_level > 1: braille_dots[i][0] |= 0x04  # Dot 3
        if dot_level > 2: braille_dots[i][0] |= 0x02  # Dot 2
        if dot_level > 3: braille_dots[i][0] |= 0x01  # Dot 1

    graph_str = ''.join([chr(0x2800 + d[0] + d[1]) for d in braille_dots])
    
    win.addstr(y, graph_start_x, graph_str)
    win.addstr(y, closing_bracket_x, "]")

def hex_renderer(hex_win, stop_event, draw_lock):
    """A thread that rapidly generates and draws hex lines to its own window."""
    # Keep a list of the last N lines to fill the window
    win_height, win_width = hex_win.getmaxyx()
    hex_lines = deque(maxlen=win_height - 2)
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    slow_mode_lines_left = 0

    while not stop_event.is_set():
        raw_hex_line = hex.generate_hex_line()
        # Use regex to efficiently strip all ANSI escape codes
        clean_hex_line = ansi_escape.sub('', raw_hex_line)
        
        hex_lines.append(clean_hex_line)

        with draw_lock:
            hex_win.erase() # Clear just this window
            for i, line in enumerate(list(hex_lines)):
                hex_win.addstr(i + 1, 2, line[:win_width-3])
            hex_win.box()
            hex_win.addstr(0, 2, " Hex Dump ")
            hex_win.refresh()
        
        # --- Restore random sleep behavior ---
        # 1 in 100 chance of a long pause
        if random.randint(1, 100) == 1:
            time.sleep(random.uniform(0.5, 1.5))

        # Check if we should enter "slow mode"
        if slow_mode_lines_left == 0 and random.randint(1, 250) == 1:
            slow_mode_lines_left = random.randint(10, 30)

        if slow_mode_lines_left > 0:
            time.sleep(random.uniform(0.08, 0.25))  # Slower "thinking" speed
            slow_mode_lines_left -= 1
        else:
            time.sleep(random.uniform(0.001, 0.01)) # Regular fast speed

def get_logo():
    """Returns an ASCII logo based on the operating system."""
    system = platform.system()
    logos = {
        "Linux": [
            "    .--.    ",
            "   |o_o |   ",
            "   |:_/ |   ",
            "  //   \\ \\  ",
            " (|     | ) ",
            "/'\\_   _/'\\ ",
            "\\___)=(___/"
        ],
        # Add other OS logos here if you like
    }
    # Return the logo for the current system, or a default if not found
    return logos.get(system, logos.get("Linux", []))


def draw_fastfetch(win, colors):
    """Draws system information, like fastfetch."""
    win.erase()
    win.box()
    win.addstr(0, 2, " System ", colors['title'])
    
    uname = platform.uname()
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    
    # Format uptime string
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    uptime_str = f"{days}d {hours}h {minutes}m"

    logo = get_logo()
    logo_width = max(len(line) for line in logo) if logo else 0
    
    for i, line in enumerate(logo):
        win.addstr(i + 1, 2, line, colors['title'])

    win.addstr(2, logo_width + 4, f"OS:      {uname.system} {uname.release}")
    win.addstr(3, logo_width + 4, f"Kernel:  {uname.version.split(' ')[0]}")
    win.addstr(4, logo_width + 4, f"Uptime:  {uptime_str}")
    win.addstr(5, logo_width + 4, f"CPU:     {platform.processor()}")

def draw_ui(stdscr):
    """Main drawing function managed by curses."""
    curses.curs_set(0)
    stdscr.nodelay(True)
    colors = setup_colors()
    draw_lock = threading.Lock()
    stop_event = threading.Event()

    # --- Window Layout ---
    lines, cols = stdscr.getmaxyx()
    left_width = cols // 2
    right_width = cols - left_width

    fastfetch_height = 8
    hex_height = (lines * 3) // 10
    metrics_height = lines - hex_height - fastfetch_height

    fastfetch_win = curses.newwin(fastfetch_height, left_width, 0, 0)
    metrics_win = curses.newwin(metrics_height, left_width, fastfetch_height, 0)
    proc_win = curses.newwin(lines, right_width, 0, left_width)
    hex_win = curses.newwin(hex_height, left_width, fastfetch_height + metrics_height, 0)

    # --- Start Hex Thread ---
    hex_thread = threading.Thread(target=hex_renderer, args=(hex_win, stop_event, draw_lock), daemon=True)
    hex_thread.start()

    # --- Network Usage Tracking ---
    last_net_io = psutil.net_io_counters()
    last_time = time.time()

    # --- History Tracking ---
    cpu_history = deque(maxlen=left_width - 18)
    mem_history = deque(maxlen=left_width - 18)
    net_up_history = deque(maxlen=left_width - 18)
    net_down_history = deque(maxlen=left_width - 18)

    try:
        while True:
            # --- Main Thread: Update Metrics and Processes (slowly) ---
            with draw_lock:
                # Check for resize
                if stdscr.getch() == curses.KEY_RESIZE:
                    lines, cols = stdscr.getmaxyx()
                    stdscr.clear()
                    
                    left_width = cols // 2
                    right_width = cols - left_width
                    fastfetch_height = 8
                    hex_height = (lines * 3) // 10
                    metrics_height = lines - hex_height - fastfetch_height

                    fastfetch_win.resize(fastfetch_height, left_width)
                    metrics_win.resize(metrics_height, left_width)
                    hex_win.resize(hex_height, left_width)
                    proc_win.resize(lines, right_width)

                    metrics_win.mvwin(fastfetch_height, 0)
                    hex_win.mvwin(fastfetch_height + metrics_height, 0)
                    proc_win.mvwin(0, left_width)
                    
                    # --- Reset History on Resize ---
                    cpu_history = deque(maxlen=left_width - 18)
                    mem_history = deque(maxlen=left_width - 18)
                    net_up_history = deque(maxlen=left_width - 18)
                    net_down_history = deque(maxlen=left_width - 18)
                    stdscr.refresh()

                # --- Fastfetch Info ---
                draw_fastfetch(fastfetch_win, colors)

                # --- System Metrics ---
                metrics_win.erase()
                metrics_win.box()
                header_text = f" Ftop - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
                metrics_win.addstr(0, (left_width - len(header_text)) // 2, header_text, colors['title'])

                per_cpu_percent = psutil.cpu_percent(interval=None, percpu=True)
                cpu_percent = sum(per_cpu_percent) / len(per_cpu_percent)
                mem_info = psutil.virtual_memory()
                swap_info = psutil.swap_memory()
                load_avg = psutil.getloadavg()
                disk_info = psutil.disk_usage('/')
                cpu_history.append(cpu_percent)
                mem_history.append(mem_info.percent)

                # --- Network Calculation ---
                current_net_io = psutil.net_io_counters()
                current_time = time.time()
                elapsed_time = current_time - last_time
                bytes_sent_per_sec = (current_net_io.bytes_sent - last_net_io.bytes_sent) / elapsed_time if elapsed_time > 0 else 0
                bytes_recv_per_sec = (current_net_io.bytes_recv - last_net_io.bytes_recv) / elapsed_time if elapsed_time > 0 else 0
                net_up_history.append(bytes_sent_per_sec)
                net_down_history.append(bytes_recv_per_sec)
                last_net_io = current_net_io
                last_time = current_time
                
                bar_width = left_width - 18
                cpu_bar, bar_color = get_bar(cpu_percent, bar_width, colors)
                mem_bar, _ = get_bar(mem_info.percent, bar_width, colors)
                swap_bar, _ = get_bar(swap_info.percent, bar_width, colors)
                disk_bar, _ = get_bar(disk_info.percent, bar_width, colors)
                
                y = 1
                metrics_win.addstr(y, 2, f"CPU [{cpu_percent:5.1f}%] ["); y += 1
                metrics_win.addstr(y-1, 17, cpu_bar, bar_color)
                metrics_win.addstr(y-1, left_width - 2, "]")

                # Per-CPU Bars
                for i, core_percent in enumerate(per_cpu_percent):
                    if y >= metrics_height - 8: break # Stop if we run out of space
                    core_bar, core_color = get_bar(core_percent, bar_width, colors)
                    metrics_win.addstr(y, 2, f"  {i:<2} [{core_percent:5.1f}%] [")
                    metrics_win.addstr(y, 17, core_bar, core_color)
                    metrics_win.addstr(y, left_width - 2, "]")
                    y += 1

                if y < metrics_height - 7:
                    mem_text = f"MEM [{mem_info.percent:5.1f}%] [{format_bytes(mem_info.used)}/{format_bytes(mem_info.total)}]"
                    metrics_win.addstr(y, 2, mem_text); y += 1
                    metrics_win.addstr(y-1, 17, mem_bar, bar_color)
                    metrics_win.addstr(y-1, left_width - 2, "]")

                if y < metrics_height - 6:
                    swap_text = f"SWP [{swap_info.percent:5.1f}%] [{format_bytes(swap_info.used)}/{format_bytes(swap_info.total)}]"
                    metrics_win.addstr(y, 2, swap_text); y += 1
                    metrics_win.addstr(y-1, 17, swap_bar, bar_color)
                    metrics_win.addstr(y-1, left_width - 2, "]")

                if y < metrics_height - 5:
                    disk_text = f"DSK [{disk_info.percent:5.1f}%] [{format_bytes(disk_info.used)}/{format_bytes(disk_info.total)}]"
                    metrics_win.addstr(y, 2, disk_text); y += 1
                    metrics_win.addstr(y-1, 17, disk_bar, bar_color)
                    metrics_win.addstr(y-1, left_width - 2, "]")

                if y < metrics_height - 4:
                    draw_sparkline(metrics_win, y, 2, cpu_history, bar_width, "CPU Hist")
                    y += 1

                if y < metrics_height - 3:
                    draw_sparkline(metrics_win, y, 2, mem_history, bar_width, "MEM Hist")
                    y += 1

                if y < metrics_height - 2:
                    net_max_up = max(max(net_up_history, default=1), 1024)
                    draw_sparkline(metrics_win, y, 2, net_up_history, bar_width, f"NET Up {format_bytes(net_max_up):>7}/s", max_val=net_max_up)
                    y += 1

                if y < metrics_height - 2:
                    net_max_down = max(max(net_down_history, default=1), 1024)
                    draw_sparkline(metrics_win, y, 2, net_down_history, bar_width, f"NET Dn {format_bytes(net_max_down):>7}/s", max_val=net_max_down)
                    y += 1

                if y < metrics_height - 1:
                    metrics_win.addstr(y, 2, f"Load Avg: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}")

                # --- Process Box ---
                proc_win.erase()
                proc_win.box()
                proc_win.addstr(0, 2, " Processes ", colors['title'])
                proc_header = f"{'PID':>6} {'USER':<12} {'CPU%':>6} {'MEM%':>6} {'COMMAND'}"
                proc_win.addstr(1, 2, proc_header[:right_width-3])
                proc_win.addstr(2, 1, "─" * (right_width - 2))

                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                    try:
                        processes.append(proc.info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
                top_processes = sorted(processes, key=lambda p: p.get('cpu_percent', 0), reverse=True)

                for i in range(lines - 4):
                    if i >= len(top_processes): break
                    p = top_processes[i]
                    user = str(p.get('username', 'N/A'))
                    command = p.get('name', 'N/A')
                    line_str = f"{p.get('pid', ''):>6} {user:<12.12} {p.get('cpu_percent', 0):>6.1f} {p.get('memory_percent', 0):>6.1f} {command}"
                    proc_win.addstr(i + 3, 2, line_str[:right_width-3])

                # Refresh windows
                fastfetch_win.refresh()
                metrics_win.refresh()
                proc_win.refresh()

            time.sleep(1) # Main loop refresh rate

    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        stop_event.set()

def main():
    curses.wrapper(draw_ui)

if __name__ == "__main__":
    main()