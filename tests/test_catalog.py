import csv, os, subprocess, sys, tempfile, unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "plugins/landlord/skills/archive/scripts/catalog.py"


class Catalog(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        self.root = Path(t.name); (self.root / "old-files/1998").mkdir(parents=True)

    def write(self, name, text):
        p = self.root / "old-files" / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text); return p

    def run_it(self, command, *args, ok=True):
        r = subprocess.run([sys.executable, str(SCRIPT), command, str(self.root), *args], capture_output=True, text=True)
        self.assertEqual(r.returncode == 0, ok, r.stdout + r.stderr)
        return r.stdout + r.stderr

    def rows(self):
        with open(self.root / "catalog.csv", newline="", encoding="utf-8") as f:
            return {r["path"]: r for r in csv.DictReader(f)}

    def test_summary_survives_move_and_files_untouched(self):
        p = self.write("1998/roof.txt", "roof"); self.run_it("scan")
        self.run_it("set", "old-files/1998/roof.txt", "--status", "read", "--summary", "Roof, \"new\"\nslates")
        p.rename(self.root / "old-files/roof-1998.txt")
        self.assertIn("moved 1", self.run_it("scan"))
        row = self.rows()["old-files/roof-1998.txt"]
        self.assertEqual((row["status"], row["summary"]), ("read", 'Roof, "new" slates'))
        self.assertEqual((self.root / "old-files/roof-1998.txt").read_text(), "roof")

    def test_missing_and_return_keep_summary(self):
        p = self.write("a.txt", "a"); self.run_it("scan")
        self.run_it("set", "old-files/a.txt", "--status", "read", "--summary", "kept")
        p.unlink(); self.assertIn("missing 1", self.run_it("scan"))
        self.write("a.txt", "a"); self.run_it("scan")
        self.assertEqual((self.rows()["old-files/a.txt"]["status"], self.rows()["old-files/a.txt"]["summary"]), ("read", "kept"))

    def test_disconnected_folder_does_not_mark_files_missing(self):
        (self.root / "documents").mkdir(); self.write("a.txt", "a"); self.run_it("scan")
        (self.root / "old-files").rename(self.root / "elsewhere")
        self.assertIn("not marked", self.run_it("scan")); self.assertEqual(self.rows()["old-files/a.txt"]["status"], "new")

    def test_changed_file_is_unread_again(self):
        p = self.write("a.txt", "a"); self.run_it("scan"); self.run_it("set", "old-files/a.txt", "--status", "read")
        p.write_text("bb"); os.utime(p, (1, 1)); self.assertIn("changed 1", self.run_it("scan"))
        self.assertEqual(self.rows()["old-files/a.txt"]["status"], "new")

    def test_duplicates_read_once(self):
        self.write("a.txt", "same"); self.write("b.txt", "same"); self.run_it("scan")
        self.assertIn("1 unread", self.run_it("next")); self.assertIn("exact duplicates: 1", self.run_it("stats"))

    def test_paper_survives_scan_and_accents_match(self):
        self.write("a.txt", "a"); self.run_it("scan")
        self.run_it("paper", "--place", "Box 3", "--summary", "Escritura João 1987"); self.run_it("scan")
        out = self.run_it("find", "joao"); self.assertIn("paper:Box 3", out)

    def test_hebrew_and_symlink_and_junk(self):
        self.write("חוזה 1995.txt", "x"); self.write("Thumbs.db", "x"); self.write("~$a.docx", "x")
        os.symlink("/etc/hostname", self.root / "old-files/link.txt"); self.run_it("scan")
        self.assertEqual(list(self.rows()), ["old-files/חוזה 1995.txt"])
        self.assertIn("1 matches", self.run_it("find", "חוזה"))

    def test_damaged_catalog_is_left_alone(self):
        self.write("a.txt", "a"); (self.root / "catalog.csv").write_text("x,y\n1,2\n")
        self.run_it("scan", ok=False); self.assertEqual((self.root / "catalog.csv").read_text(), "x,y\n1,2\n")

    def test_large_archive(self):
        for i in range(3000): self.write(f"{i % 30}/f{i}.txt", str(i))
        self.assertIn("added 3000", self.run_it("scan"))
        self.assertLess(len(self.run_it("stats")), 2500); self.assertLess(len(self.run_it("find", "f1")), 2500)


unittest.main()
