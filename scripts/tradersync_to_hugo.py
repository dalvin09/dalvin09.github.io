#!/usr/bin/env python3
"""
TraderSync CSV → Hugo Markdown generator.

Usage:
    python3 scripts/tradersync_to_hugo.py trades.csv

Reads a TraderSync CSV export and generates a Hugo .md file for each trade
in the correct section (forex/ or options/) based on the asset type.

Expected TraderSync CSV columns (adjust COLUMN_MAP below if yours differ):
    Date, Symbol, Side, Quantity, Entry Price, Exit Price, P&L, Notes
"""

import csv
import sys
import os
import re
from datetime import datetime

# --- Adjust these to match your TraderSync export column headers ---
COLUMN_MAP = {
    "date":        "Date",
    "symbol":      "Symbol",
    "side":        "Side",
    "quantity":    "Qty",
    "entry":       "Entry",
    "exit":        "Exit",
    "pnl":         "P&L ($)",
    "notes":       "Notes",
}

FOREX_PAIRS = {"GBPUSD", "EURUSD", "USDJPY", "GBPJPY", "AUDUSD",
               "USDCAD", "NZDUSD", "EURGBP", "EURJPY", "GBPAUD"}

CONTENT_DIR = os.path.join(os.path.dirname(__file__), "..", "content")


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text


def detect_section(symbol):
    sym = symbol.upper().replace("/", "").replace("=X", "")
    if sym in FOREX_PAIRS:
        return "forex"
    return "options"


def next_trade_number(section):
    section_dir = os.path.join(CONTENT_DIR, section)
    os.makedirs(section_dir, exist_ok=True)
    existing = [f for f in os.listdir(section_dir)
                if re.match(r"^\d{3}-", f) and f.endswith(".md")]
    if not existing:
        return 1
    nums = [int(f[:3]) for f in existing]
    return max(nums) + 1


def generate_md(row, trade_num, section):
    date_raw = row.get(COLUMN_MAP["date"], "").strip()
    symbol   = row.get(COLUMN_MAP["symbol"], "").strip().upper()
    side     = row.get(COLUMN_MAP["side"], "").strip().capitalize()
    qty      = row.get(COLUMN_MAP["quantity"], "").strip()
    entry    = row.get(COLUMN_MAP["entry"], "").strip()
    exit_    = row.get(COLUMN_MAP["exit"], "").strip()
    pnl      = row.get(COLUMN_MAP["pnl"], "").strip()
    notes    = row.get(COLUMN_MAP["notes"], "").strip()

    try:
        date_obj = datetime.strptime(date_raw, "%Y-%m-%d")
    except ValueError:
        try:
            date_obj = datetime.strptime(date_raw, "%m/%d/%Y")
        except ValueError:
            date_obj = datetime.today()

    date_fmt = date_obj.strftime("%Y-%m-%d")
    title    = f"{trade_num:03d} — {symbol} {side}"
    slug     = f"{trade_num:03d}-{slugify(symbol)}-{slugify(side)}"
    filename = f"{slug}.md"

    content = f"""---
title: "{title}"
date: {date_fmt}
tags: ["{symbol}", "{side.lower()}", "{section}"]
categories: ["{section}"]
summary: "TraderSync import — {symbol} {side}. P&L: {pnl}"
draft: false
---

## Setup Overview

| Field       | Detail       |
|------------|--------------|
| Symbol      | {symbol}     |
| Direction   | {side}       |
| Quantity    | {qty}        |
| Entry       | {entry}      |
| Exit        | {exit_}      |
| P&L         | {pnl}        |

---

## Rationale

{notes if notes else "*(Add your trade rationale here)*"}

---

## Chart

*(Paste your TraderSync chart screenshot here)*

![Trade Chart](/images/{slug}-chart.png)

---

## TraderSync Verified P&L

*(Embed TraderSync shared trade link here)*

---

## Review

**What went well:**
**What to improve:**
**Grade:**
"""
    return filename, content


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/tradersync_to_hugo.py trades.csv")
        sys.exit(1)

    csv_path = sys.argv[1]
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        sys.exit(1)

    created = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol  = row.get(COLUMN_MAP["symbol"], "").strip()
            if not symbol:
                continue
            section    = detect_section(symbol)
            trade_num  = next_trade_number(section)
            filename, content = generate_md(row, trade_num, section)
            out_path = os.path.join(CONTENT_DIR, section, filename)
            with open(out_path, "w") as out:
                out.write(content)
            created.append(out_path)
            print(f"Created: {out_path}")

    print(f"\nDone — {len(created)} file(s) generated.")


if __name__ == "__main__":
    main()
