---
name: archive
description: Catalog, search and summarize old files going back decades. Use when the user adds old files or scans, asks about the past ("when did we replace the roof", "who lived in 2A in 1998", "find the deed"), mentions paper boxes, or wants old documents organized.
---

# Old files

Old files are in `old-files/`. Originals are evidence: never edit, rename, move or delete them. `catalog.csv` lists every file. It can have thousands of lines, so **never read it whole**: use the script beside this file. `ROOT` is the My Properties folder.

```
python3 scripts/catalog.py scan  ROOT                         find new, moved, changed and missing files
python3 scripts/catalog.py stats ROOT                         counts only
python3 scripts/catalog.py find  ROOT WORDS... [--building B] search names and summaries
python3 scripts/catalog.py next  ROOT [--under old-files/X] [--limit 10]
python3 scripts/catalog.py set   ROOT PATH --status read|skip|unreadable [--building B] [--unit U] [--type T] [--date D] [--summary S]
python3 scripts/catalog.py paper ROOT --place "Box 3" --summary S [--building B] [--type T] [--date D]
```

If the shell cannot reach the folder, say so and work on one subfolder at a time with the file tools. Do not build a second catalog.

## Adding files

1. Files are copied, not moved, into `old-files/`, any structure. Originals stay where they were until a backup exists.
2. Run `scan`, then `stats`. Report in one short paragraph: how many files, which years and types, how many duplicates.
3. Ask which of these matter first, and read only those: deeds and purchase papers, loans, renovations, permits, insurance, leases of current tenants, disputes.

## Reading in batches

Reading is expensive: a scanned page costs about as much as several pages of text. Do not read the whole archive.

1. First batch: 5 files, then ask if the result is useful. Later batches: 10 files at most, then stop and say what is left.
2. Use the `document-reader` agent, one document per call. Over 30 pages: first and last pages, then only what is needed.
3. `set` each file right after reading: status, building, type, date, a one-line summary. That makes the work resumable in any new task. Use `skip` for what the user says is unimportant, `unreadable` for a failed scan.
4. Types: `deed`, `purchase`, `loan`, `improvement`, `permit`, `insurance`, `lease`, `tax`, `dispute`, `letter`, `invoice`, `photo`, `other`. Date: YYYY, YYYY-MM or YYYY-MM-DD. Leave it empty if unknown; never use the file's own date as the document's date.
5. Add lasting events to `properties/<building>/history.md`, oldest first, one line each: `1998-05 | roof replaced, 12,400 | old-files/.../roof.pdf p.2`. Limit 150 lines; merge small ones.

**Old facts never change current memory.** A 1998 lease goes in history only. Change a building or unit page only if the document is the one in force and the user confirms.

## Answering about the past

1. Read that building's `history.md`, then `find`. Try the words in every language the papers may use.
2. Read only the best one or two documents, and give the answer with file name, page and date.
3. Nothing found: say how many files are still unread and offer to read the likely ones. Never say a thing did not happen because it was not found.

## Paper

- Scan to searchable PDF, one document per file, 300 dpi, with building and year in the name. Start with deeds, purchase, renovations and current leases.
- Record unscanned boxes with `paper`, so Claude can say which box.
- Keep the physical originals of deeds, wills, stamped or notarized papers.
- Keep ID copies, bank logins and full bank statements out of the folder.
- Never advise destroying a record. How long to keep it depends on the country: check an official source and suggest the accountant.
