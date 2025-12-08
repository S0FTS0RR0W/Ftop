# Ftop

A customizable, `btop`-inspired system monitor written in Python, featuring a retro hex dump aesthetic. It provides a live look at system metrics and processes within a clean, boxed terminal interface.

*(Screenshot placeholder)*

## Features

-   **Live System Metrics:** Real-time display of CPU and Memory utilization with graphical bars.
-   **Process List:** A view of running processes, sorted by CPU usage, showing PID, User, CPU%, and Memory%.
-   **Independent Hex Dump:** A decorative, animated hex dump runs in a separate thread, providing a dynamic background without impacting the performance of metric updates.
-   **Dynamic "Thinking" Animation:** The hex dump randomly slows down, pauses, and speeds up to create a "thinking" or "processing" effect.
-   **Flicker-Free UI:** Built with Python's `curses` library for a smooth, flicker-free terminal interface with distinct boxes for different components.
-   **Responsive Layout:** The UI components resize gracefully with the terminal window.

## Requirements

-   Python 3
-   The `psutil` library

## Installation

1.  Clone the repository (or download the files).
2.  Install the required Python package:
    ```bash
    pip install psutil
    ```

## Usage

To run the application, simply execute the `Ftop.py` script from your terminal:

```bash
python3 Ftop.py
```

Press `Ctrl+C` to exit.
