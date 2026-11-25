"""Run with a Python that has landlord-library installed."""
import hashlib, io, json, os, subprocess, sys, tempfile, unittest, zipfile
from pathlib import Path
from PIL import Image, ImageDraw


def snapshot(folder):
    return {str(p): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns, p.stat().st_mode)
            for p in folder.rglob("*") if p.is_file() and not p.is_symlink()} | {
            str(p): (p.stat().st_mtime_ns,) for p in folder.rglob("*") if p.is_dir()}


class Library(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        self.base = Path(t.name).resolve(); self.docs = self.base / "Documents"; self.vault = self.docs / "My Properties"
        self.vault.mkdir(parents=True); self.out = self.base / "outside"; self.out.mkdir()
        self.env = dict(os.environ, LANDLORD_LIBRARY_HOME=str(self.base / "app"), HOME=str(self.base))

    def cli(self, *args, ok=True):
        r = subprocess.run([sys.executable, "-m", "landlord_library.main", *args], env=self.env, capture_output=True, text=True)
        self.assertEqual(r.returncode == 0, ok, r.stdout + r.stderr); return r.stdout + r.stderr

    def put(self, name, data):
        p = self.docs / name; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data if isinstance(data, bytes) else data.encode()); return p

    def setup_lib(self): return self.cli("setup", "--vault", str(self.vault), "--root", str(self.docs), "--no-schedule")

    def choose(self, *lines): (self.vault / "library/folders.txt").write_text("\n".join(lines))

    def cards(self): return sorted((self.vault / "library/cards").rglob("*.md"))

    def card(self, text): return next(c for c in self.cards() if text in c.read_text())

    def scan(self, lines):
        im = Image.new("RGB", (1240, 900), "white"); d = ImageDraw.Draw(im)
        d.text((80, 120), lines, fill="black", font_size=48); b = io.BytesIO(); im.save(b, "PDF", resolution=150); return b.getvalue()

    def test_nothing_is_read_until_chosen_and_originals_never_change(self):
        self.put("Houses/Main St/lease 1998.txt", "Lease of unit 2A, rent 450")
        self.put("Houses/Main St/scan.pdf", self.scan("INSURANCE POLICY 2004"))
        z = io.BytesIO()
        with zipfile.ZipFile(z, "w") as a: a.writestr("word/document.xml", "<w:p>Roof contract 1999</w:p>")
        self.put("Houses/roof.docx", z.getvalue())
        im = Image.new("RGB", (900, 600), "blue"); ex = im.getexif(); ex[306] = "2011:05:06 10:00:00"
        b = io.BytesIO(); im.save(b, "JPEG", exif=ex); self.put("Houses/photo.jpg", b.getvalue())
        self.put("Private/diary.txt", "secret diary"); before = {k: v for k, v in snapshot(self.docs).items() if "My Properties" not in k and k != str(self.vault)}
        self.setup_lib(); self.assertEqual(self.cards(), [])
        m = (self.vault / "library/MAP.md").read_text(); self.assertIn("Main St", m); self.assertNotIn("rent 450", m)
        self.choose(f"+ {self.docs / 'Houses'}"); self.cli("run"); self.assertEqual(len(self.cards()), 4)
        self.assertIn('taken: "2011-05-06"', self.card("photo.jpg").read_text())
        self.assertIn("Roof contract 1999", self.card("roof.docx").read_text())
        self.assertIn("library/previews/", self.card("scan.pdf").read_text())
        everything = "".join(p.read_text(errors="replace") for p in (self.vault / "library").rglob("*") if p.is_file())
        self.assertNotIn("secret diary", everything)
        self.cli("run"); after = {k: v for k, v in snapshot(self.docs).items() if "My Properties" not in k and k != str(self.vault)}
        self.assertEqual(before, after)

    def test_descriptions_survive_moves_and_reruns(self):
        p = self.put("H/a.txt", "lease text here"); self.setup_lib(); self.choose(f"+ {self.docs}"); self.cli("run")
        c = self.cards()[0]; t = c.read_text().replace('status: "new"', "status: described").replace('summary: ""', "summary: Lease of 2A\ntags:\n  - x")
        c.write_text(t + "\nmy note\n"); (self.docs / "New").mkdir(); p.rename(self.docs / "New/b.txt"); self.cli("run")
        t = self.cards()[0].read_text(); self.assertEqual(len(self.cards()), 1)
        for part in ("summary: Lease of 2A", "my note", "  - x", "New/b.txt", 'state: "present"'): self.assertIn(part, t)
        self.assertIn("Lease of 2A", (self.vault / "library/index/general.md").read_text())

    def test_duplicates_share_a_card_and_deleted_is_marked(self):
        a = self.put("a.txt", "same"); self.put("b.txt", "same"); self.setup_lib(); self.choose(f"+ {self.docs}"); self.cli("run")
        self.assertEqual(len(self.cards()), 1); self.assertIn("b.txt", self.cards()[0].read_text())
        a.unlink(); (self.docs / "b.txt").unlink(); self.put("c.txt", "c"); self.cli("run")
        self.assertIn('state: "not found', self.card('"a.txt"').read_text())

    def test_unavailable_drive_does_not_mark_everything_missing(self):
        self.put("a.txt", "x"); self.setup_lib(); self.choose(f"+ {self.docs}"); self.cli("run")
        cfg = json.loads((self.base / "app/config.json").read_text()); cfg["roots"].append(str(self.base / "gone"))
        (self.base / "app/config.json").write_text(json.dumps(cfg)); (self.docs / "a.txt").rename(self.out / "a.txt"); self.cli("run")
        self.assertIn('state: "present"', self.cards()[0].read_text())

    def test_cannot_escape_roots(self):
        (self.out / "x.txt").write_text("outside secret"); self.put("ok.txt", "fine"); os.symlink(self.out, self.docs / "link")
        self.setup_lib(); self.choose(f"+ {self.out}", f"+ {self.docs}/../outside", f"+ {self.docs}"); self.cli("run")
        self.assertEqual(len(self.cards()), 1)

    def test_refuses_to_write_through_links(self):
        self.put("ok.txt", "fine"); self.setup_lib(); self.choose(f"+ {self.docs}")
        os.symlink(self.out, self.vault / "library/cards"); self.cli("run", ok=False); self.assertEqual(list(self.out.iterdir()), [])

    def test_private_names_and_numbers(self):
        self.put("passport scan.txt", "P1234567"); self.put("pay.txt", "card 4111 1111 1111 1111 iban PT50 0002 0123 1234 5678 9015 4 tel 912345678")
        self.setup_lib(); self.choose(f"+ {self.docs}"); self.cli("run"); self.assertEqual(len(self.cards()), 1)
        t = self.cards()[0].read_text(); self.assertNotIn("4111", t); self.assertNotIn("0002 0123", t); self.assertIn("912345678", t)
        self.assertNotIn("passport", (self.vault / "library/MAP.md").read_text())

    def test_bad_files_do_not_stop_it(self):
        self.put("bad.pdf", b"%PDF-1.4 garbage"); self.put("bad.jpg", b"nope"); self.put("bad.docx", b"PK"); self.put("ok.txt", "fine")
        self.setup_lib(); self.choose(f"+ {self.docs}"); self.assertIn("4 new", self.cli("run"))

    def test_folder_with_odd_names(self):
        self.put("חוזים [ישן] & co/חוזה 1995.txt", "שכירות"); self.setup_lib()
        f = self.docs / "חוזים [ישן] & co"; self.assertIn(str(f), (self.vault / "library/MAP.md").read_text())
        self.choose(f"+ {f}"); self.cli("run"); self.assertIn("שכירות", self.cards()[0].read_text())

    def test_windows_folder_of_a_landlord_is_not_system(self):
        self.put("Windows/quote.txt", "new windows"); self.setup_lib(); self.choose(f"+ {self.docs}"); self.cli("run"); self.assertEqual(len(self.cards()), 1)

    def test_exclude_wins_inside_include_and_limit_resumes(self):
        for i in range(5): self.put(f"H/{i}.txt", f"t{i}")
        self.put("H/no/x.txt", "x"); self.setup_lib(); self.choose(f"+ {self.docs}/H", f"- {self.docs}/H/no")
        self.assertIn("3 waiting", self.cli("run", "--limit", "2")); self.cli("run"); self.assertEqual(len(self.cards()), 5)


unittest.main()
