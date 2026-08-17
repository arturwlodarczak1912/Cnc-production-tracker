# CNC Production Tracker

A lightweight desktop application for logging CNC machine production runs
on the shop floor and reviewing basic output statistics in real time —
built with Python's standard library only (`tkinter` + `sqlite3`).

## Why this project

After 12 years operating CNC machines (Heidenhain-controlled Hedelius mills)
in agricultural machinery manufacturing, I know first-hand that production
counts are often still tracked on paper or in spreadsheets that nobody
looks at until the end of the shift. This project is a small, practical
step toward Industry 4.0 on the shop floor: a simple tool an operator can
use to log each finished batch in seconds, with live totals and an export
to CSV for further analysis (e.g. in pandas, Excel, or a reporting
dashboard).

It intentionally uses only the Python standard library (no external
dependencies, no internet connection, no cloud account) because that is
the reality of many production PCs on the shop floor — locked down,
offline, and running whatever Python ships with Windows.

## 🎯 Features

- Log a production batch: operator, part number, cycle time (seconds),
  quantity produced
- Press **Enter** in any field to log the entry (no need to reach for the
  mouse), or click **Log entry**
- Live daily statistics: total pieces produced today, number of batches,
  and average cycle time per piece
- Table view of today's entries (`ttk.Treeview`), newest first
- Delete a wrongly logged entry
- Export today's log to a CSV file for further analysis
- All data persisted locally in a SQLite database (`production_log.db`),
  so history is kept between sessions

## Tech stack

- Python 3 standard library only: `tkinter`, `ttk`, `sqlite3`, `csv`,
  `datetime`, `pathlib`
- No external dependencies — runs anywhere Python 3 is installed

## How to run

```bash
python3 cnc_production_tracker.py
```

A window opens with an entry form at the top, live statistics below it,
and a table of today's logged batches. Data is stored in
`production_log.db` in the same folder, created automatically on first run.

## Project structure

```
cnc-production-tracker/
├── cnc_production_tracker.py   # application (GUI + SQLite data layer)
├── README.md
└── .gitignore
```

## Possible next steps

- Add a `pandas`-based analysis script to summarize `production_log.db`
  across multiple days/weeks (OEE-style metrics: pieces/hour, downtime
  between batches, etc.)
- Add a per-part target cycle time and flag batches that ran slower than
  expected
- Package as a standalone `.exe` with PyInstaller for shop-floor PCs

## Author

Artur Wlodarczak — CNC machinist transitioning into data analytics and
Python development, with a focus on Industry 4.0 / manufacturing
analytics roles.
