"""Descarga los woff2 de Google Fonts (subset latin/latin-ext) y genera un
CSS local para auto-hospedar Inter + JetBrains Mono.

Ejecutar una sola vez:  python scripts/fetch_fonts.py
Los archivos van a app/static/fonts/ y se genera app/static/css/fonts.css.
"""
import re
import urllib.request
from pathlib import Path

CSS_URL = (
    "https://fonts.googleapis.com/css2"
    "?family=Inter:wght@400;500;600;700"
    "&family=JetBrains+Mono:wght@400;500"
    "&display=swap"
)
# UA de Chrome moderno -> Google devuelve woff2 (no ttf).
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = ROOT / "app" / "static" / "fonts"
CSS_OUT = ROOT / "app" / "static" / "css" / "fonts.css"

# Subsets que cubren español + inglés. Descartamos cyrillic/greek/vietnamese.
KEEP_SUBSETS = {"latin", "latin-ext"}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req) as r:
        return r.read()


def main() -> None:
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    css = fetch(CSS_URL).decode("utf-8")

    # Cada @font-face va precedido por un comentario /* subset */
    blocks = re.split(r"/\*\s*([\w-]+)\s*\*/", css)
    # blocks = ['', subset1, face1, subset2, face2, ...]
    out_faces = []
    downloaded = {}
    for i in range(1, len(blocks) - 1, 2):
        subset = blocks[i].strip()
        face = blocks[i + 1]
        if subset not in KEEP_SUBSETS:
            continue
        fam = re.search(r"font-family:\s*'([^']+)'", face).group(1)
        weight = re.search(r"font-weight:\s*(\d+)", face).group(1)
        url = re.search(r"url\(([^)]+)\)", face).group(1)
        slug = fam.lower().replace(" ", "-")
        fname = f"{slug}-{weight}-{subset}.woff2"
        if fname not in downloaded:
            (FONTS_DIR / fname).write_bytes(fetch(url))
            downloaded[fname] = True
            print("descargado", fname)
        # Reescribe el bloque para apuntar al archivo local
        local_face = re.sub(r"url\([^)]+\)",
                            f"url('../fonts/{fname}')", face)
        out_faces.append(local_face.strip())

    CSS_OUT.write_text(
        "/* Fuentes auto-hospedadas (generado por scripts/fetch_fonts.py) */\n"
        + "\n".join(out_faces) + "\n",
        encoding="utf-8",
    )
    print(f"\n{len(downloaded)} archivos woff2, CSS -> {CSS_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
