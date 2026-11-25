---
name: repairs
description: Track repairs and file documents. Use when something is broken, for contractor quotes or visits, repair status, or when the user adds a lease, contract, invoice, inspection report or photo, or mentions the inbox.
---

# Repairs

1. If there is danger (gas smell, fire, flooding, exposed wiring, no heat in freezing weather), first say: get people safe and call the local emergency or utility line. Paperwork comes after.
2. Load the unit and the building contacts. Ask only what is missing: what, where, since when, who reported it.
3. Add a line under Open issues in the unit file (or `building.md` for shared areas): `YYYY-MM-DD | problem | status | who | next step`. Add the next step to `TODO.md`.
4. Offer drafts for the tenant and the contractor with the `messages` skill.
5. Compare quotes in a small table. Who pays depends on the lease and local law: check before saying.
6. When fixed: remove it from Open issues, close the TODO, add one log line, record the cost with the `money` skill, note any warranty end date.

# Documents

1. Use the `document-reader` agent so a long document stays out of this conversation.
2. Show the key facts with page numbers and ask for confirmation before changing tenant, rent, lease or deposit facts in memory.
3. Save the confirmed facts with `remember`. Put lease ends, notice deadlines, insurance ends and inspections in `TODO.md`.
4. Move the original, unedited, from `inbox/` to `documents/<building>/` as `YYYY-MM-DD-type-unit.ext`. If that name exists, add `-2`. Link it in the unit file. Old files elsewhere on the computer: use the `library` skill instead.
