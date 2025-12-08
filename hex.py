# simple python program that lists random hex dumps in a loop for looks in the terminal

import os
import random
import time
import string
import sys
import shutil
import signal

class Colors:
    GREEN = '\033[92m'
    LIGHT_GREEN = '\033[32m'
    DARK_GREEN = '\033[38;5;22m'
    ENDC = '\033[0m'

def generate_hex_line(bytes_per_line=16):
    """Generates a single line of a hex dump."""
    address = f"{random.randint(0, 0xFFFFFFFF):08X}"
    byte_values = [random.randint(0, 255) for _ in range(bytes_per_line)]
    hex_bytes = ' '.join(f"{byte:02X}" for byte in byte_values)

    ascii_chars = []
    for byte in byte_values:
        if 32 <= byte <= 126:
            ascii_chars.append(chr(byte))
        else:
            ascii_chars.append('.')
    ascii_representation = ''.join(ascii_chars)
    return f"{Colors.GREEN}{address}{Colors.ENDC}  {Colors.LIGHT_GREEN}{hex_bytes}{Colors.ENDC}  |{Colors.DARK_GREEN}{ascii_representation}{Colors.ENDC}|"

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')
def signal_handler(sig, frame):
    clear_terminal()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# take random breaks for looks and change speed of hex dump randomly

def get_random_sleep_duration():
    return random.uniform(0.001, 0.01)

# slow down at random intervals to simulate thinking or data processing
def slow_down_randomly():
    if random.randint(1, 100) == 1:
        time.sleep(random.uniform(0.5, 2.0))

def main():
    clear_terminal()
    slow_mode_lines_left = 0
    while True:
        # This is the very long pause you already have.
        slow_down_randomly()

        # Check if we should enter "slow mode" to simulate thinking.
        if slow_mode_lines_left == 0 and random.randint(1, 250) == 1:
            slow_mode_lines_left = random.randint(10, 30)  # It will be slow for 10-30 lines.

        hex_line = generate_hex_line()
        print(hex_line)

        if slow_mode_lines_left > 0:
            time.sleep(random.uniform(0.08, 0.25))  # Slower "thinking" speed.
            slow_mode_lines_left -= 1
        else:
            time.sleep(get_random_sleep_duration())  # Regular fast speed.

if __name__ == "__main__":
    main()