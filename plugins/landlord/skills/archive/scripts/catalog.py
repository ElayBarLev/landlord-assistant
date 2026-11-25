#!/usr/bin/env python3
"""Catalog old files in catalog.csv. Standard library only; never changes the files themselves."""
import argparse
import csv
import hashlib
import os
import shutil
import sys
import unicodedata
from collections import Counter
from pathlib import Path

FIELDS = ["path", "status", "building", "unit", "type", "date", "summary", "size", "modified", "sha256"]
FOLDERS = ["old-files", "documents"]
JUNK = {"thumbs.db", "desktop.ini"}


def catalog_path(root):
    return root / "catalog.csv"


def load(root):
    path = catalog_path(root)
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            sys.exit("catalog.csv has an unexpected header. Nothing was changed.")
        rows = list(reader)
    if any(None in row or None in row.values() for row in rows):
        sys.exit("catalog.csv has a damaged line. Nothing was changed.")
    return rows


def save(root, rows):
    path = catalog_path(root)
    temp = root / "catalog.csv.tmp"
    with open(temp, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda row: row["path"]))
    if path.exists():
        shutil.copyfile(path, root / "catalog.bak.csv")
    os.replace(temp, path)


def digest(path):
    value = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            value.update(block)
    return value.hexdigest()


def is_paper(row):
    return row["path"].startswith("paper:")


def walk(root, problems, known):
    def failed(error):
        problems.append(str(error))
    for folder in FOLDERS:
        # A folder that was never used is fine; one that vanished may just be disconnected.
        if not (root / folder).is_dir() and not any(name.startswith(folder + "/") for name in known):
            continue
        for where, dirs, names in os.walk(root / folder, onerror=failed):
            dirs[:] = sorted(d for d in dirs if not d.startswith(".") and not os.path.islink(os.path.join(where, d)))
            for name in sorted(names):
                path = Path(where) / name
                if name.startswith((".", "~$")) or name.lower() in JUNK or path.is_symlink():
                    continue
                yield path


def scan(root):
    rows, problems = load(root), []
    if not any((root / folder).is_dir() for folder in FOLDERS):
        sys.exit("No old-files or documents folder here. Nothing was changed.")
    known = {row["path"]: row for row in rows if not is_paper(row)}
    found, fresh, changed, moved = set(), [], 0, 0
    for path in walk(root, problems, known):
        name = path.relative_to(root).as_posix()
        found.add(name)
        row = known.get(name)
        try:
            info = path.stat()
            size, modified = str(info.st_size), str(int(info.st_mtime))
            if row and (row["size"], row["modified"]) == (size, modified):
                if row["status"] == "missing":
                    row["status"] = "read" if row["summary"] else "new"
                continue
            value = digest(path)
        except OSError as error:
            problems.append(f"{name}: {error.strerror}")
            continue
        if row:
            if row["sha256"] != value:
                row["status"] = "new"
                changed += 1
            elif row["status"] == "missing":
                row["status"] = "read" if row["summary"] else "new"
            row.update(size=size, modified=modified, sha256=value)
        else:
            fresh.append(dict.fromkeys(FIELDS, "") | {"path": name, "status": "new", "size": size,
                                                      "modified": modified, "sha256": value})
    # A folder that could not be listed must not make its files look missing.
    gone = [] if problems else [row for name, row in known.items() if name not in found]
    by_hash = {}
    for row in gone:
        by_hash.setdefault(row["sha256"], []).append(row)
    added = 0
    for new in fresh:
        old = by_hash.get(new["sha256"])
        if old:
            row = old.pop(0)
            if row["status"] == "missing":
                row["status"] = "read" if row["summary"] else "new"
            row.update(path=new["path"], modified=new["modified"])
            gone = [other for other in gone if other is not row]
            moved += 1
        else:
            rows.append(new)
            added += 1
    for row in gone:
        row["status"] = "missing"
    save(root, rows)
    print(f"added {added}, moved {moved}, changed {changed}, missing {len(gone)}, total {len(rows)}")
    for line in problems[:20]:
        print(f"could not read: {line}")
    if problems:
        print(f"{len(problems)} problems; missing files were not marked this time")


def show(row):
    details = " | ".join(row[key] for key in ("date", "type", "building", "unit", "summary") if row[key])
    print(f"{row['path']} [{row['status']}]" + (f" {details}" if details else ""))


def fold(text):
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).casefold()


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    parts = {name: commands.add_parser(name) for name in ("scan", "stats", "find", "next", "set", "paper")}
    for part in parts.values():
        part.add_argument("root", type=Path)
    parts["find"].add_argument("words", nargs="+")
    parts["find"].add_argument("--building", dest="only")
    parts["next"].add_argument("--under", default="")
    for name in ("find", "next"):
        parts[name].add_argument("--limit", type=int, default=20 if name == "find" else 10)
    parts["set"].add_argument("path")
    parts["set"].add_argument("--status", required=True, choices=["read", "skip", "unreadable"])
    parts["paper"].add_argument("--place", required=True)
    for name in ("set", "paper"):
        for key in ("building", "unit", "type", "date"):
            parts[name].add_argument(f"--{key}")
        parts[name].add_argument("--summary", required=name == "paper")
    args = parser.parse_args()
    root = args.root
    if not root.is_dir():
        sys.exit("Folder not found.")
    if args.command == "scan":
        return scan(root)
    rows = load(root)

    if args.command in ("set", "paper"):
        values = {key: " ".join(getattr(args, key).split()) for key in ("building", "unit", "type", "date", "summary")
                  if getattr(args, key) is not None}
        if args.command == "paper":
            number = sum(map(is_paper, rows)) + 1
            row = dict.fromkeys(FIELDS, "") | {"path": f"paper:{args.place} #{number}", "status": "paper"}
            rows.append(row)
        else:
            match = [row for row in rows if row["path"] == args.path]
            if not match:
                sys.exit("That path is not in the catalog. Run scan first.")
            row = match[0]
            row["status"] = args.status
        row.update(values)
        save(root, rows)
        return show(row)

    if args.command == "find":
        words = [fold(word) for word in args.words]
        ranked = []
        for row in rows:
            if args.only and row["building"] != args.only:
                continue
            text = fold(" ".join(row[key] for key in FIELDS[:7]))
            score = sum(word in text for word in words)
            if score:
                ranked.append((-score, row["path"], row))
        ranked.sort(key=lambda item: item[:2])
        for _, _, row in ranked[:args.limit]:
            show(row)
        print(f"{len(ranked)} matches, {min(len(ranked), args.limit)} shown")
        return

    done = {row["sha256"] for row in rows if row["status"] in ("read", "skip", "unreadable")}
    waiting, seen = [], set()
    for row in sorted(rows, key=lambda row: row["path"]):
        if row["status"] == "new" and row["sha256"] not in done and row["sha256"] not in seen:
            seen.add(row["sha256"])
            waiting.append(row)
    if args.command == "next":
        waiting = [row for row in waiting if row["path"].startswith(args.under)]
        for row in waiting[:args.limit]:
            show(row)
        print(f"{len(waiting)} unread")
        return
    present = [row for row in rows if not is_paper(row) and row["status"] != "missing"]
    print("status: " + ", ".join(f"{k} {v}" for k, v in sorted(Counter(r["status"] for r in rows).items())))
    print("kinds: " + ", ".join(f"{k or 'none'} {v}" for k, v in
          Counter(Path(r["path"]).suffix.lower() for r in present).most_common(12)))
    print("folders: " + ", ".join(f"{k} {v}" for k, v in
          Counter("/".join(r["path"].split("/")[:-1][:2]) for r in present).most_common(20)))
    print(f"exact duplicates: {len(present) - len({r['sha256'] for r in present})}, unread: {len(waiting)}, "
          f"size: {sum(int(r['size']) for r in present) / 1e6:.0f} MB")


if __name__ == "__main__":
    main()
