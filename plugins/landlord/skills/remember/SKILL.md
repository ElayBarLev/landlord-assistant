---
name: remember
description: Save a lasting fact to the landlord's folder memory. Use whenever the user says remember, save, note or update, or when a conversation reveals a new tenant, rent, date, agreement, contact, preference or building fact that should be kept.
---

# Remember

Memory stays small so each task costs little. One fact lives in one place.

| What | Where |
|---|---|
| Preference, or a rule for all buildings | `HOME.md` |
| Building fact or contact | `properties/<building>/building.md` |
| Tenant, rent, lease, agreement | `properties/<building>/units/<unit>.md` |
| Something that happened | one line in `properties/<building>/log-<year>.md`: `YYYY-MM-DD, unit, what` |
| Something to do by a date | `TODO.md` |
| Money in or out | the `money` skill |
| A document | the `repairs` skill, section Documents |

Steps:

1. Read the target file and change only the lines concerned. If nobody saved it yet, create it from the `start` skill's templates.
2. Replace outdated facts. Put the old value in the log with the date: `rent 900 -> 950`.
3. Tenant, rent and lease end also appear in the Units table of `building.md`. Update both together.
4. When a tenant leaves, move a copy of the unit file to `archive/`, then clear the unit and mark it empty.
5. Store dates as YYYY-MM-DD. Turn "next Friday" into a date.
6. Save only what the user said or a document shows. Write `unknown` rather than a guess.
7. Re-read the changed lines to confirm they were saved. If saving failed, say so plainly.

Limits: `HOME.md` 80 lines, `building.md` 60, unit file 60. When one gets longer, move old detail to the log or `archive/`, never drop it.

Do not save passwords, full bank or card numbers, or ID numbers. Do not save opinions about a tenant's religion, origin, health, family or similar.
