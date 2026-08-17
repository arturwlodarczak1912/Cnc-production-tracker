"""
CNC Production Tracker
=======================
A lightweight desktop tool for logging CNC machine production runs on the
shop floor and reviewing basic output statistics in real time.

Built with Python's standard library only (tkinter + sqlite3), so it runs
on any machine with Python installed -- no extra dependencies, no network,
no cloud account. That matters on a shop floor where PCs are often locked
down and offline.

Author: Artur Wlodarczak
"""

import csv
import sqlite3
import tkinter as tk
from datetime import datetime, date
from pathlib import Path
from tkinter import ttk, messagebox, filedialog

DB_PATH = Path(__file__).parent / "production_log.db"

FONT_LABEL = ("Arial", 13, "bold")
FONT_ENTRY = ("Consolas", 13)
FONT_TITLE = ("Arial", 20, "bold")
FONT_STAT = ("Arial", 14, "bold")


# --------------------------------------------------------------------------
# Data layer
# --------------------------------------------------------------------------
class ProductionDB:
    """Thin wrapper around a local SQLite database that stores one row per
    completed production batch (operator, part, cycle time, quantity)."""

    def __init__(self, db_path: Path):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS production_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                operator TEXT NOT NULL,
                part_number TEXT NOT NULL,
                cycle_time_sec REAL NOT NULL,
                quantity INTEGER NOT NULL,
                notes TEXT
            )
            """
        )
        self.conn.commit()

    def add_entry(self, operator, part_number, cycle_time_sec, quantity, notes=""):
        self.conn.execute(
            """INSERT INTO production_log
               (timestamp, operator, part_number, cycle_time_sec, quantity, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                datetime.now().isoformat(timespec="seconds"),
                operator,
                part_number,
                cycle_time_sec,
                quantity,
                notes,
            ),
        )
        self.conn.commit()

    def entries_for_today(self):
        today = date.today().isoformat()
        cur = self.conn.execute(
            """SELECT id, timestamp, operator, part_number, cycle_time_sec, quantity, notes
               FROM production_log
               WHERE timestamp LIKE ?
               ORDER BY id DESC""",
            (f"{today}%",),
        )
        return cur.fetchall()

    def all_entries(self):
        cur = self.conn.execute(
            """SELECT id, timestamp, operator, part_number, cycle_time_sec, quantity, notes
               FROM production_log
               ORDER BY id DESC"""
        )
        return cur.fetchall()

    def delete_entry(self, entry_id):
        self.conn.execute("DELETE FROM production_log WHERE id = ?", (entry_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()


# --------------------------------------------------------------------------
# GUI layer
# --------------------------------------------------------------------------
class CNCTrackerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.db = ProductionDB(DB_PATH)

        self.root.title("CNC Production Tracker")
        self.root.geometry("900x650")
        self.root.minsize(760, 560)

        self._build_form()
        self._build_stats()
        self._build_table()
        self._build_actions()

        self.refresh()

    # ---- UI construction -------------------------------------------------
    def _build_form(self):
        frame = tk.Frame(self.root, padx=16, pady=12)
        frame.pack(fill="x")

        tk.Label(frame, text="CNC Production Tracker", font=FONT_TITLE).grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 12)
        )

        tk.Label(frame, text="Operator", font=FONT_LABEL).grid(row=1, column=0, sticky="w")
        self.entry_operator = tk.Entry(frame, font=FONT_ENTRY, width=18)
        self.entry_operator.grid(row=2, column=0, padx=(0, 12), sticky="w")

        tk.Label(frame, text="Part number", font=FONT_LABEL).grid(row=1, column=1, sticky="w")
        self.entry_part = tk.Entry(frame, font=FONT_ENTRY, width=16)
        self.entry_part.grid(row=2, column=1, padx=(0, 12), sticky="w")

        tk.Label(frame, text="Cycle time (sec)", font=FONT_LABEL).grid(row=1, column=2, sticky="w")
        self.entry_cycle = tk.Entry(frame, font=FONT_ENTRY, width=10)
        self.entry_cycle.grid(row=2, column=2, padx=(0, 12), sticky="w")

        tk.Label(frame, text="Quantity", font=FONT_LABEL).grid(row=1, column=3, sticky="w")
        self.entry_qty = tk.Entry(frame, font=FONT_ENTRY, width=8)
        self.entry_qty.grid(row=2, column=3, padx=(0, 12), sticky="w")

        add_btn = tk.Button(
            frame, text="Log entry (Enter)", font=("Arial", 12, "bold"),
            bg="#1F4E79", fg="white", command=self.log_entry,
        )
        add_btn.grid(row=2, column=4, sticky="w")

        # Enter key in any field triggers logging, like in the exercises this
        # is based on (poleTekstowe.bind('<Return>', akcja)).
        for entry in (self.entry_operator, self.entry_part, self.entry_cycle, self.entry_qty):
            entry.bind("<Return>", self.log_entry)

        self.status_label = tk.Label(frame, text="", fg="#B00000", font=("Arial", 11))
        self.status_label.grid(row=3, column=0, columnspan=5, sticky="w", pady=(6, 0))

    def _build_stats(self):
        frame = tk.Frame(self.root, padx=16, pady=4)
        frame.pack(fill="x")

        self.stat_pieces = tk.Label(frame, text="Pieces today: 0", font=FONT_STAT, fg="#1F4E79")
        self.stat_pieces.pack(side="left", padx=(0, 24))

        self.stat_entries = tk.Label(frame, text="Batches today: 0", font=FONT_STAT, fg="#1F4E79")
        self.stat_entries.pack(side="left", padx=(0, 24))

        self.stat_avg_cycle = tk.Label(frame, text="Avg cycle time: -", font=FONT_STAT, fg="#1F4E79")
        self.stat_avg_cycle.pack(side="left")

    def _build_table(self):
        frame = tk.Frame(self.root, padx=16, pady=8)
        frame.pack(fill="both", expand=True)

        columns = ("time", "operator", "part", "cycle", "qty", "notes")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=14)

        headings = {
            "time": "Time",
            "operator": "Operator",
            "part": "Part number",
            "cycle": "Cycle (s)",
            "qty": "Qty",
            "notes": "Notes",
        }
        widths = {"time": 130, "operator": 120, "part": 120, "cycle": 80, "qty": 60, "notes": 220}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="left", fill="y")

    def _build_actions(self):
        frame = tk.Frame(self.root, padx=16, pady=8)
        frame.pack(fill="x")

        tk.Button(frame, text="Delete selected", command=self.delete_selected).pack(side="left")
        tk.Button(frame, text="Export today to CSV", command=self.export_csv).pack(side="left", padx=8)
        tk.Button(frame, text="Refresh", command=self.refresh).pack(side="left")

    # ---- Actions -----------------------------------------------------------
    def log_entry(self, event=None):
        operator = self.entry_operator.get().strip()
        part = self.entry_part.get().strip()
        cycle_raw = self.entry_cycle.get().strip()
        qty_raw = self.entry_qty.get().strip()

        if not operator or not part or not cycle_raw or not qty_raw:
            self.status_label.configure(text="Please fill in all fields before logging an entry.")
            return

        try:
            cycle_time = float(cycle_raw)
            quantity = int(qty_raw)
            if cycle_time <= 0 or quantity <= 0:
                raise ValueError
        except ValueError:
            self.status_label.configure(text="Cycle time must be a number and quantity a whole number > 0.")
            return

        self.db.add_entry(operator, part, cycle_time, quantity)
        self.status_label.configure(text="")
        self.entry_part.delete(0, tk.END)
        self.entry_cycle.delete(0, tk.END)
        self.entry_qty.delete(0, tk.END)
        self.entry_part.focus_set()

        self.refresh()

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        if not messagebox.askyesno("Confirm", "Delete selected entry?"):
            return
        for item in selected:
            entry_id = self.tree.item(item, "tags")[0]
            self.db.delete_entry(int(entry_id))
        self.refresh()

    def export_csv(self):
        rows = self.db.entries_for_today()
        if not rows:
            messagebox.showinfo("Export", "No entries logged today yet.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"production_{date.today().isoformat()}.csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "timestamp", "operator", "part_number", "cycle_time_sec", "quantity", "notes"])
            writer.writerows(rows)

        messagebox.showinfo("Export", f"Exported {len(rows)} entries to:\n{path}")

    def refresh(self):
        rows = self.db.entries_for_today()

        for item in self.tree.get_children():
            self.tree.delete(item)

        total_pieces = 0
        total_cycle = 0.0
        for row in rows:
            entry_id, timestamp, operator, part, cycle_time, qty, notes = row
            time_only = timestamp.split("T")[1] if "T" in timestamp else timestamp
            self.tree.insert(
                "", "end",
                values=(time_only, operator, part, f"{cycle_time:.1f}", qty, notes or ""),
                tags=(str(entry_id),),
            )
            total_pieces += qty
            total_cycle += cycle_time * qty

        entry_count = len(rows)
        avg_cycle = (total_cycle / total_pieces) if total_pieces else 0

        self.stat_pieces.configure(text=f"Pieces today: {total_pieces}")
        self.stat_entries.configure(text=f"Batches today: {entry_count}")
        self.stat_avg_cycle.configure(
            text=f"Avg cycle time: {avg_cycle:.1f}s" if total_pieces else "Avg cycle time: -"
        )

    def on_close(self):
        self.db.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = CNCTrackerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
