"""Genera el set completo de favicons + la imagen Open Graph (1200x630) a
partir del trazo del logo (mismas coordenadas que static/img/favicon.svg),
con el degradado violeta -> verde de la marca. Sin dependencias nativas de
SVG: todo se dibuja con Pillow.

Ejecutar:  python scripts/generate_favicons.py
Salida en app/static/  (favicons, site.webmanifest) y app/static/img/ (OG).
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "app" / "static"
IMG = STATIC / "img"

# Paleta de la marca (idéntica al SVG del logo)
VIOLET = (147, 51, 234)     # #9333EA
GREEN = (16, 185, 129)      # #10B981
BG_DARK = (13, 13, 20)      # #0d0d14  (--bg-base)
TEXT = (238, 238, 245)      # #eeeef5
MUTED = (150, 150, 165)

# Trazos del logo en coordenadas SVG (viewBox 0 0 100 100)
PATHS = [
    [(22, 85), (50, 15), (78, 85)],
    [(50, 15), (50, 55), (12, 70)],
    [(50, 55), (70, 65)],
]
SVG_STROKE = 7
SS = 4  # supersampling para bordes suaves


def _lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _diagonal_gradient(size):
    """RGBA con degradado diagonal violeta(sup-izq) -> verde(inf-der)."""
    w = h = size
    grad = Image.new("RGB", (w, h))
    px = grad.load()
    for y in range(h):
        for x in range(w):
            t = ((x / w) + (y / h)) / 2
            px[x, y] = _lerp(VIOLET, GREEN, t)
    return grad


def draw_mark(size, pad_ratio=0.14, bg=None):
    """Devuelve un RGBA `size`x`size` con el trazo del logo en degradado.
    Si `bg` es un color RGB, pinta un cuadrado redondeado de fondo.
    """
    S = size * SS
    pad = S * pad_ratio
    scale = (S - 2 * pad) / 100.0

    def tf(p):
        return (pad + p[0] * scale, pad + p[1] * scale)

    sw = max(1, round(SVG_STROKE * scale))

    # Máscara con los trazos (blanco sobre negro)
    mask = Image.new("L", (S, S), 0)
    md = ImageDraw.Draw(mask)
    for path in PATHS:
        pts = [tf(p) for p in path]
        md.line(pts, fill=255, width=sw, joint="curve")
        for p in pts:  # tapas/uniones redondeadas
            r = sw / 2
            md.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=255)

    grad = _diagonal_gradient(S).convert("RGBA")
    grad.putalpha(mask)

    if bg is not None:
        base = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        bd = ImageDraw.Draw(base)
        radius = S * 0.20
        bd.rounded_rectangle([0, 0, S - 1, S - 1], radius=radius, fill=bg + (255,))
        base.alpha_composite(grad)
        out = base
    else:
        out = grad

    return out.resize((size, size), Image.LANCZOS)


def _font(size, bold=True):
    """Fuente para la OG. Usa Inter si está, si no Segoe UI (Win) / default."""
    candidates = [
        ROOT / "app/static/fonts/Inter-Bold.ttf",   # si existiera un ttf local
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for c in candidates:
        if c.exists():
            return ImageFont.truetype(str(c), size)
    return ImageFont.load_default()


def build_og():
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), BG_DARK)
    draw = ImageDraw.Draw(img)

    # Glows sutiles de marca (violeta arriba-izq, verde abajo-der)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-200, -260, 480, 360], fill=VIOLET + (46,))
    gd.ellipse([760, 320, 1500, 900], fill=GREEN + (40,))
    from PIL import ImageFilter
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Marca
    mark = draw_mark(300, pad_ratio=0.06)
    img.paste(mark, (110, 165), mark)

    # Textos
    x = 470
    f_brand = _font(96, bold=True)
    f_sub = _font(40, bold=False)
    f_tag = _font(30, bold=False)

    draw.text((x, 205), "AS Vertex", font=f_brand, fill=TEXT)
    draw.text((x, 320), "Desarrollo Web Profesional", font=f_sub, fill=(200, 200, 215))
    draw.text((x, 388), "Python · Flask · JavaScript · HTML · CSS", font=f_tag, fill=MUTED)

    # Barra de acento con degradado abajo
    bar = _diagonal_gradient(1).resize((W, 8))
    grad_line = Image.new("RGB", (W, 8))
    for i in range(W):
        grad_line.paste(_lerp(VIOLET, GREEN, i / W), [i, 0, i + 1, 8])
    img.paste(grad_line, (0, H - 8))

    IMG.mkdir(parents=True, exist_ok=True)
    img.save(IMG / "og-image.png", "PNG", optimize=True)
    print("OG ->", (IMG / "og-image.png").relative_to(ROOT))


def build_favicons():
    STATIC.mkdir(parents=True, exist_ok=True)

    # PNGs transparentes
    draw_mark(16).save(STATIC / "favicon-16x16.png")
    draw_mark(32).save(STATIC / "favicon-32x32.png")
    # Apple / Android con fondo oscuro (mejor en iOS/instalado)
    draw_mark(180, pad_ratio=0.16, bg=BG_DARK).save(STATIC / "apple-touch-icon.png")
    draw_mark(192, pad_ratio=0.18, bg=BG_DARK).save(STATIC / "android-chrome-192x192.png")
    draw_mark(512, pad_ratio=0.18, bg=BG_DARK).save(STATIC / "android-chrome-512x512.png")

    # .ico multi-resolución
    ico = draw_mark(64)
    ico.save(STATIC / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    print("favicons -> app/static/  (ico, 16, 32, apple-touch, android 192/512)")


def build_manifest():
    manifest = """{
  "name": "AS Vertex",
  "short_name": "AS Vertex",
  "description": "Desarrollo web profesional con Python, Flask, JavaScript, HTML y CSS.",
  "icons": [
    { "src": "/static/android-chrome-192x192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/static/android-chrome-512x512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable" }
  ],
  "theme_color": "#0d0d14",
  "background_color": "#0d0d14",
  "display": "standalone",
  "start_url": "/"
}
"""
    (STATIC / "site.webmanifest").write_text(manifest, encoding="utf-8")
    print("manifest -> app/static/site.webmanifest")


if __name__ == "__main__":
    build_favicons()
    build_og()
    build_manifest()
