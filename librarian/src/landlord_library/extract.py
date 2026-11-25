"""Read one file and return its text, a small preview and basic facts. Opens originals read-only."""
import html
import io
import multiprocessing
import re
import shutil
import subprocess
import zipfile
from email import message_from_binary_file, policy
from pathlib import Path

PDF = {".pdf"}
IMAGE = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp", ".heic", ".heif"}
OFFICE = {".docx": r"word/document\.xml", ".xlsx": r"xl/sharedStrings\.xml", ".pptx": r"ppt/slides/slide\d+\.xml",
          ".odt": r"content\.xml", ".ods": r"content\.xml"}
TEXT = {".txt", ".csv", ".md", ".htm", ".html", ".rtf"}
NAME_ONLY = {".doc", ".xls", ".ppt", ".msg", ".dwg", ".pages", ".numbers", ".wpd", ".wps", ".mdb", ".accdb"}
MAIL = {".eml"}
KNOWN = PDF | IMAGE | set(OFFICE) | TEXT | NAME_ONLY | MAIL
MAX_TEXT, MAX_BYTES, PREVIEW = 200_000, 200_000_000, 1100
MAX_XML = 50_000_000


def kind(path):
    ext = Path(path).suffix.lower()
    if ext in PDF:
        return "pdf"
    if ext in IMAGE:
        return "image"
    return "document"


def jpeg(image):
    image = image.convert("RGB")
    image.thumbnail((PREVIEW, PREVIEW))
    out = io.BytesIO()
    image.save(out, "JPEG", quality=72)
    return out.getvalue()


def ocr(data, languages):
    program = shutil.which("tesseract")
    if not program:
        return ""
    try:
        result = subprocess.run([program, "stdin", "stdout", "-l", languages], input=data, capture_output=True, timeout=90)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.decode("utf-8", "replace") if result.returncode == 0 else ""


def strip_tags(text):
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", text)
    return html.unescape(re.sub(r"<[^>]+>", " ", text))


def read_pdf(path, languages):
    import pypdfium2
    out = {"text": "", "previews": [], "pages": 0}
    with open(path, "rb") as handle:
        document = pypdfium2.PdfDocument(handle)
        out["pages"] = len(document)
        for number in range(len(document)):
            if len(out["text"]) > MAX_TEXT:
                break
            page = document[number].get_textpage().get_text_bounded()
            if page.strip():
                out["text"] += f"\n[page {number + 1}]\n{page}"
        if len(re.sub(r"\[page \d+\]|\s", "", out["text"])) < 40 * min(out["pages"], 3):
            for number in range(min(out["pages"], 3)):
                page = document[number]
                image = page.render(scale=min(2.5, 2400 / max(page.get_size()))).to_pil()
                out["previews"].append(jpeg(image.copy()))
                buffer = io.BytesIO()
                image.convert("L").save(buffer, "PNG")
                words = ocr(buffer.getvalue(), languages)
                if words.strip():
                    out["text"] += f"\n[page {number + 1}, read by OCR]\n{words}"
    return out


def read_image(path, languages):
    from PIL import Image, ImageOps
    if Path(path).suffix.lower() in (".heic", ".heif"):
        import pillow_heif
        pillow_heif.register_heif_opener()
    out = {"text": "", "previews": []}
    with Image.open(path) as image:
        exif = image.getexif()
        taken = exif.get_ifd(0x8769).get(36867) or exif.get(306)
        if taken:
            match = re.match(r"(\d{4}):(\d\d):(\d\d)", str(taken))
            out["taken"] = "-".join(match.groups()) if match else ""
        try:
            gps = exif.get_ifd(0x8825)
            if gps:
                def degrees(value, ref):
                    d, m, s = (float(x) for x in value)
                    return round((d + m / 60 + s / 3600) * (-1 if ref in ("S", "W") else 1), 5)
                out["place"] = f"{degrees(gps[2], gps[1])}, {degrees(gps[4], gps[3])}"
        except (KeyError, ValueError, TypeError, ZeroDivisionError):
            pass
        image = ImageOps.exif_transpose(image)
        out["previews"].append(jpeg(image.copy()))
        image.thumbnail((2400, 2400))
        buffer = io.BytesIO()
        image.convert("L").save(buffer, "PNG")
    out["text"] = ocr(buffer.getvalue(), languages)
    return out


def read_office(path):
    text, size = [], 0
    with zipfile.ZipFile(path) as archive:
        for item in archive.infolist():
            if re.fullmatch(OFFICE[Path(path).suffix.lower()], item.filename):
                size += item.file_size
                if size > MAX_XML:
                    break
                text.append(strip_tags(re.sub(r"</(w:p|a:p|si|text:p)>", "\n", archive.read(item).decode("utf-8", "replace"))))
    return {"text": "\n".join(text)}


def read_text(path):
    with open(path, "rb") as handle:
        raw = handle.read(MAX_TEXT * 2)
    for encoding in ("utf-8-sig", "utf-16" if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    ext = Path(path).suffix.lower()
    if ext in (".htm", ".html"):
        text = strip_tags(text)
    elif ext == ".rtf":
        text = re.sub(r"\\'[0-9a-f]{2}|\\[a-z]+-?\d* ?|[{}]", "", text)
    return {"text": text}


def read_mail(path):
    with open(path, "rb") as handle:
        message = message_from_binary_file(handle, policy=policy.default)
    body = message.get_body(preferencelist=("plain", "html"))
    text = body.get_content() if body else ""
    if body and body.get_content_type() == "text/html":
        text = strip_tags(text)
    head = "\n".join(f"{name}: {message[name]}" for name in ("From", "To", "Date", "Subject") if message[name])
    return {"text": f"{head}\n\n{text}"}


def extract(path, languages):
    ext = Path(path).suffix.lower()
    if ext in PDF:
        return read_pdf(path, languages)
    if ext in IMAGE:
        return read_image(path, languages)
    if ext in OFFICE:
        return read_office(path)
    if ext in TEXT:
        return read_text(path)
    if ext in MAIL:
        return read_mail(path)
    return {"note": "this file type is listed by name only"}


def _serve(pipe, languages):
    while (path := pipe.recv()) is not None:
        try:
            pipe.send(extract(path, languages))
        except Exception as error:  # a bad file must not stop the run
            pipe.send({"error": f"{type(error).__name__}: {error}"[:200]})


class Reader:
    """Reads files in a helper process, so a damaged file can be skipped instead of stopping everything."""

    def __init__(self, languages="eng", timeout=300):
        self.languages, self.timeout, self.process = languages, timeout, None

    def read(self, path):
        if self.process is None or not self.process.is_alive():
            context = multiprocessing.get_context("spawn")
            self.pipe, child = context.Pipe()
            self.process = context.Process(target=_serve, args=(child, self.languages), daemon=True)
            self.process.start()
            child.close()
        try:
            self.pipe.send(str(path))
            if self.pipe.poll(self.timeout):
                return self.pipe.recv()
            problem = "took too long"
        except (EOFError, OSError):
            problem = "damaged file"
        self.close()
        return {"error": problem}

    def close(self):
        if self.process:
            self.process.kill()
            self.process.join()
            self.pipe.close()
            self.process = None
