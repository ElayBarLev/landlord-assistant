#!/usr/bin/env python3
"""Check and total landlord ledgers. Standard library only; never changes files."""
import argparse
import csv
import re
import sys
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation

FIELDS = ["date", "building", "unit", "type", "category", "amount", "currency", "period", "note"]
CATEGORIES = {"rent", "deposit", "repair", "insurance", "tax", "utilities", "fees", "other"}
MONTH = re.compile(r"\d{4}-(0[1-9]|1[0-2])")


def load(paths):
    rows, problems = [], []
    for path in paths:
        with open(path, newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != FIELDS:
                problems.append(f"{path}: header must be {','.join(FIELDS)}")
                continue
            for row in reader:
                where = f"{path} line {reader.line_num}"
                bad = len(problems)
                if None in row or None in row.values():
                    problems.append(f"{where}: wrong number of columns")
                    continue
                row = {key: value.strip() for key, value in row.items()}
                try:
                    if len(row["date"]) != 10:
                        raise ValueError
                    date.fromisoformat(row["date"])
                except ValueError:
                    problems.append(f"{where}: bad date {row['date']!r}")
                try:
                    row["amount"] = Decimal(row["amount"])
                    if not row["amount"].is_finite() or row["amount"] <= 0:
                        raise InvalidOperation
                except InvalidOperation:
                    problems.append(f"{where}: amount must be a plain positive number")
                if row["type"] not in ("income", "expense"):
                    problems.append(f"{where}: type must be income or expense")
                if row["category"] not in CATEGORIES:
                    problems.append(f"{where}: unknown category {row['category']!r}")
                if not row["building"] or not row["currency"]:
                    problems.append(f"{where}: building and currency are required")
                if row["period"] and not MONTH.fullmatch(row["period"]):
                    problems.append(f"{where}: period must be YYYY-MM")
                if row["category"] == "rent" and not (row["period"] and row["unit"]):
                    problems.append(f"{where}: rent needs a unit and a period")
                if len(problems) == bad:
                    rows.append(row)
    return rows, problems


def duplicates(rows):
    seen, found = set(), []
    for r in rows:
        key = (r["date"], r["building"], r["unit"], r["type"], r["category"],
               r["amount"], r["currency"], r["period"])
        if key in seen:
            found.append(f"possible duplicate: {r['date']} {r['building']} {r['unit']} {r['amount']}")
        seen.add(key)
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["check", "summary", "rent"])
    parser.add_argument("ledgers", nargs="+")
    parser.add_argument("--month")
    parser.add_argument("--building")
    args = parser.parse_intermixed_args()
    if args.month and not MONTH.fullmatch(args.month):
        parser.error("--month must be YYYY-MM")
    if args.command == "rent" and not args.month:
        parser.error("rent needs --month")

    try:
        rows, problems = load(args.ledgers)
    except (OSError, UnicodeDecodeError) as error:
        sys.exit(f"Cannot read ledger: {error}")
    if problems:
        print("PROBLEMS (fix before trusting totals)")
        print("\n".join(problems))
        sys.exit(1)
    for line in duplicates(rows):
        print(line)
    if args.command == "check":
        print(f"OK: {len(rows)} lines")
        return
    if args.building:
        rows = [r for r in rows if r["building"] == args.building]

    if args.command == "rent":
        totals = defaultdict(Decimal)
        for r in rows:
            if r["category"] == "rent" and r["period"] == args.month:
                sign = 1 if r["type"] == "income" else -1
                totals[(r["building"], r["unit"], r["currency"])] += sign * r["amount"]
        print(f"Rent recorded for {args.month}")
        for (building, unit, currency), total in sorted(totals.items()):
            print(f"{building} / {unit}: {total:.2f} {currency}")
        if not totals:
            print("none")
        return

    if args.month:
        rows = [r for r in rows if r["date"].startswith(args.month)]
    if not rows:
        print("No lines match.")
        return
    sums = defaultdict(lambda: {"income": Decimal(0), "expense": Decimal(0),
                                "in": Decimal(0), "out": Decimal(0)})
    for r in rows:
        if r["category"] == "deposit":
            column = "in" if r["type"] == "income" else "out"
        else:
            column = r["type"]
        for name in (r["building"], "~TOTAL"):
            sums[(r["currency"], name)][column] += r["amount"]
    for (currency, name), s in sorted(sums.items()):
        print(f"{name.lstrip('~')} [{currency}]: income {s['income']:.2f}, "
              f"expenses {s['expense']:.2f}, net {s['income'] - s['expense']:.2f}, "
              f"deposits received {s['in']:.2f}, deposits returned {s['out']:.2f}")


if __name__ == "__main__":
    main()
