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
import hex  # Import the hex module
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

def hex_renderer(hex_win, stop_event, draw_lock):
    """A thread that rapidly generates and draws hex lines to its own window."""
    # Keep a list of the last N lines to fill the window
    win_height, win_width = hex_win.getmaxyx()
    hex_lines = deque(maxlen=win_height - 2)
    slow_mode_lines_left = 0

    while not stop_event.is_set():
        # The hex module returns strings with ANSI color codes, which curses can't handle.
        # We need a version that returns raw text.
        # For now, let's strip them out. A better fix would be to modify hex.py.
        raw_hex_line = hex.generate_hex_line()
        # A simple way to strip ANSI codes
        clean_hex_line = ''.join(filter(lambda x: 31 < ord(x) < 127, raw_hex_line.replace('\033[92m', '').replace('\033[32m', '').replace('\033[38;5;22m', '').replace('\033[0m', '')))
        
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

def draw_ui(stdscr):
    """Main drawing function managed by curses."""
    curses.curs_set(0)
    stdscr.nodelay(True)
    colors = setup_colors()
    draw_lock = threading.Lock()
    stop_event = threading.Event()

    # --- Window Layout ---
    lines, cols = stdscr.getmaxyx()
    proc_height = (lines - 5) // 2
    hex_height = lines - 5 - proc_height

    proc_win = curses.newwin(proc_height, cols, 5, 0)
    hex_win = curses.newwin(hex_height, cols, 5 + proc_height, 0)

    # --- Start Hex Thread ---
    hex_thread = threading.Thread(target=hex_renderer, args=(hex_win, stop_event, draw_lock), daemon=True)
    hex_thread.start()

    try:
        while True:
            # --- Main Thread: Update Metrics and Processes (slowly) ---
            with draw_lock:
                # Check for resize
                if stdscr.getch() == curses.KEY_RESIZE:
                    lines, cols = stdscr.getmaxyx()
                    stdscr.clear()
                    proc_height = (lines - 5) // 2
                    hex_height = lines - 5 - proc_height
                    proc_win.resize(proc_height, cols)
                    hex_win.resize(hex_height, cols)
                    hex_win.mvwin(5 + proc_height, 0)

                # --- Header ---
                header_text = f"Ftop - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                stdscr.addstr(0, (cols - len(header_text)) // 2, header_text, colors['title'])

                # --- System Metrics ---
                cpu_percent = psutil.cpu_percent(interval=None)
                mem_info = psutil.virtual_memory()
                bar_width = cols - 15
                cpu_bar, bar_color = get_bar(cpu_percent, bar_width, colors)
                mem_bar, _ = get_bar(mem_info.percent, bar_width, colors)
                
                stdscr.addstr(2, 0, f"CPU [{cpu_percent:5.1f}%] [")
                stdscr.addstr(2, 14, cpu_bar, bar_color)
                stdscr.addstr(2, cols - 1, "]")

                stdscr.addstr(3, 0, f"MEM [{mem_info.percent:5.1f}%] [")
                stdscr.addstr(3, 14, mem_bar, bar_color)
                stdscr.addstr(3, cols - 1, "]")

                # --- Process Box ---
                proc_win.erase()
                proc_win.box()
                proc_win.addstr(0, 2, " Processes ", colors['title'])
                proc_header = f"{'PID':>6} {'USER':<12} {'CPU%':>6} {'MEM%':>6} {'COMMAND'}"
                proc_win.addstr(1, 2, proc_header[:cols-3])
                proc_win.addstr(2, 1, "─" * (cols - 2))

                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                    try:
                        processes.append(proc.info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
                top_processes = sorted(processes, key=lambda p: p.get('cpu_percent', 0), reverse=True)

                for i in range(proc_height - 4):
                    if i >= len(top_processes): break
                    p = top_processes[i]
                    user = str(p.get('username', 'N/A'))
                    command = p.get('name', 'N/A')
                    line_str = f"{p.get('pid', ''):>6} {user:<12.12} {p.get('cpu_percent', 0):>6.1f} {p.get('memory_percent', 0):>6.1f} {command}"
                    proc_win.addstr(i + 3, 2, line_str[:cols-3])

                # Refresh main screen and process window
                stdscr.refresh()
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