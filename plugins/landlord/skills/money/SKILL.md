---
name: money
description: Record and report rent, deposits and expenses. Use for "X paid", "who hasn't paid", receipts, bills, repair costs, monthly or yearly totals, income per building, or numbers for an accountant.
---

# Money

The ledger is `money/<year>.csv`, one line per payment, by the year in which money moved:

`date,building,unit,type,category,amount,currency,period,note`

- `date`: YYYY-MM-DD. `type`: `income` or `expense`. `amount`: a plain positive number such as `950.00`.
- `building` and `unit`: exactly the folder and file names in memory. Empty unit means the whole building.
- `category`: `rent`, `deposit`, `repair`, `insurance`, `tax`, `utilities`, `fees`, `other`.
- `period`: YYYY-MM the payment is for. Required for rent.
- Put text containing a comma inside double quotes.

**Record:** read the rent from the unit file. Before adding, look for the same date, unit and amount; if found, ask whether it is a second payment. If the paid amount differs from the rent, record what was paid and say the difference. Only append. Fix a mistake by correcting that line and logging the change.

**Report:** do not add numbers yourself. Run the script beside this file. If the folder is not reachable from the shell, copy the CSV into the workspace first.

```
python3 scripts/ledger.py check   <ledger.csv> [...]
python3 scripts/ledger.py summary <ledger.csv> [...] [--month YYYY-MM] [--building NAME]
python3 scripts/ledger.py rent    <ledger.csv> [...] --month YYYY-MM
```

Run `check` first and fix problems with the user. `summary` totals by date paid. `rent` totals by the month the rent is for: pass last year's and this year's ledgers together, since rent can be paid early or late.

**Who hasn't paid:** run `rent`, compare with the rent in each occupied unit (use the `portfolio-checker` agent for several buildings), and list unpaid and partly paid units. "Not recorded" does not prove "not paid": say so, and ask before drafting reminders.

Deposits are held money and are reported apart from income. Never add different currencies together. Do not give tax advice: prepare the numbers for the accountant.
