import subprocess, sys, tempfile, unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "plugins/landlord/skills/money/scripts/ledger.py"
HEAD = "date,building,unit,type,category,amount,currency,period,note\n"


def run(command, *bodies, extra=()):
    with tempfile.TemporaryDirectory() as d:
        paths = []
        for i, body in enumerate(bodies):
            p = Path(d) / f"{i}.csv"
            p.write_text(HEAD + body, encoding="utf-8")
            paths.append(str(p))
        r = subprocess.run([sys.executable, str(SCRIPT), command, *paths, *extra], capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr


class Ledger(unittest.TestCase):
    def test_totals_keep_deposits_and_currencies_apart(self):
        code, out = run("summary",
            "2026-11-01,a,1,income,rent,950.10,EUR,2026-11,\n2026-11-02,a,,expense,repair,50.20,EUR,,\"tap, sink\"\n"
            "2026-11-03,a,1,income,deposit,900,EUR,,\n2026-11-03,b,1,income,rent,10,USD,2026-11,\n")
        self.assertEqual(code, 0)
        self.assertIn("a [EUR]: income 950.10, expenses 50.20, net 899.90, deposits received 900.00", out)
        self.assertIn("TOTAL [USD]: income 10.00", out)

    def test_rent_paid_across_year_end(self):
        code, out = run("rent", "2026-12-30,a,1,income,rent,400,EUR,2027-01,\n",
                        "2027-01-02,a,1,income,rent,100,EUR,2027-01,\n", extra=("--month", "2027-01"))
        self.assertEqual(code, 0)
        self.assertIn("a / 1: 500.00 EUR", out)

    def test_bad_lines_stop_totals(self):
        for line in ("2026-13-01,a,1,income,rent,1,EUR,2026-11,\n", "2026-11-01,a,1,income,rent,-1,EUR,2026-11,\n",
                     "2026-11-01,a,1,income,rent,\"1,000\",EUR,2026-11,\n", "2026-11-01,a,1,income,rent,1,EUR,,\n",
                     "2026-11-01,a,1,income,rent,1\n", "2026-11-01,a,1,income,rent,1,EUR,2026-11,x,y\n"):
            code, out = run("summary", line)
            self.assertEqual(code, 1, line)
            self.assertIn("PROBLEMS", out)

    def test_duplicate_is_flagged(self):
        line = "2026-11-01,a,1,income,rent,1,EUR,2026-11,\n"
        self.assertIn("possible duplicate", run("check", line + line)[1])


unittest.main()
