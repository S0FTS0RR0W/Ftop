# Ftop

Because apparently btop wasn’t dramatic enough, here’s Ftop: a Python system monitor with a retro hex dump aesthetic that screams “I’m watching you, CPU”. It’s like Task Manager, but with more attitude and fewer excuses.

(Screenshot placeholder, because screenshots are for people who don’t trust words.)

## Features

Live System Metrics: Watch your CPU and RAM cry in real time, complete with bars that pretend they’re graphs.

Process List: A parade of processes sorted by CPU usage, so you can finally see which Chrome tab is ruining your life.

Independent Hex Dump: A pointless but beautiful animated hex dump running in its own thread. It does nothing useful, but it looks like your terminal is thinking deep thoughts.

Dynamic "Thinking" Animation: Sometimes the hex dump slows down, pauses, or speeds up—because even your monitor deserves mood swings.

Flicker-Free UI: Built with Python’s curses library, so you can stare at boxes without feeling like you’re in a strobe-lit nightmare.

Responsive Layout: Resize your terminal and watch the UI gracefully adapt, unlike your last relationship.

## Requirements
Python 3 (because Python 2 is basically a fossil)

The psutil library (aka the only reason this thing knows what your CPU is doing)

## Installation
Clone the repo (or download the files if you’re allergic to git).

Install the required Python package:

bash
pip install psutil

## Usage
Run the script like you mean it:
```bash
python3 Ftop.py
```

Press `Ctrl+C` to exit.
