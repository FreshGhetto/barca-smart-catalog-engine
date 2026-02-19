
import io
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

import barca_catalog_generator as bcg

def _load_font(size: int):
    # Use the same strategy as bcg if available, else fallback
    for name in ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf"]:
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            continue
    return ImageFont.load_default()

def draw_card(
    code: str,
    product: str,
    supplier: str,
    perc_vendita: Optional[float],
    consegnate: Optional[int],
    vendute: Optional[int],
    giacenza: Optional[int],
    tacco_mm: Optional[float],
    rank: int,
    image_bytes: Optional[bytes],
    image_err: Optional[str] = None,
) -> bytes:
    """
    Layout A6: foto sopra + box info sotto (stile catalog generator).
    """
    W, H = getattr(bcg, "CANVAS_W", 1240), getattr(bcg, "CANVAS_H", 1748)
    M = getattr(bcg, "MARGIN", 40)
    PHOTO_H = getattr(bcg, "PHOTO_H", 1120)
    BORDER_W = 6

    canvas = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(canvas)

    # Outer border
    d.rectangle([0, 0, W-1, H-1], outline="black", width=BORDER_W)

    # Photo box
    photo_box = (M, M, W-M, PHOTO_H)
    d.rectangle(photo_box, outline="black", width=BORDER_W)

    def paste_no_upscale(img: Image.Image, box):
        x0,y0,x1,y1=box
        bw, bh = x1-x0, y1-y0
        iw, ih = img.size
        scale = min(bw/iw, bh/ih, 1.0)
        nw, nh = int(iw*scale), int(ih*scale)
        img2 = img.resize((nw, nh), Image.LANCZOS)
        px = x0 + (bw-nw)//2
        py = y0 + (bh-nh)//2
        canvas.paste(img2, (px,py))

    if image_bytes:
        try:
            im = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            paste_no_upscale(im, photo_box)
        except Exception:
            image_bytes = None
            image_err = image_err or "bad_image_bytes"

    if not image_bytes:
        msg = "IMMAGINE NON TROVATA"
        if image_err:
            msg += f"\n({image_err})"
        d.multiline_text((M+30, M+40), msg, fill="black", font=_load_font(36), spacing=10)

    # Info box
    info_y0 = PHOTO_H + M
    info_box = (M, info_y0, W-M, H-M)
    d.rectangle(info_box, outline="black", width=8)

    font_big = _load_font(56)
    font_med = _load_font(40)
    font_small = _load_font(34)

    x = M + 30
    y = info_y0 + 22

    # Header
    d.text((x, y), f"#{rank:03d}   {code}", fill="black", font=font_big)
    y += 72

    # Product wrap (use bcg.wrap_text signature: (draw, text, font, max_width))
    maxw = (W - 2*M - 60)
    prod_lines = bcg.wrap_text(d, product or "", font_med, maxw)[:2]
    for ln in prod_lines:
        d.text((x, y), ln, fill="black", font=font_med)
        y += 48
    y += 6

    # Requested fields
    def fmt(v):
        return "" if v is None else str(v)

    if perc_vendita is not None:
        pv = f"{perc_vendita:.1f}%"
    else:
        pv = ""

    lines_left = [
        f"FORNITORE: {supplier}",
        f"% VENDITA: {pv}",
        f"CONSEGNATE: {fmt(consegnate)}",
        f"VENDUTE: {fmt(vendute)}",
        f"GIACENZA: {fmt(giacenza)}",
    ]
    if tacco_mm is not None:
        lines_left.append(f"TACCO (mm): {int(tacco_mm) if float(tacco_mm).is_integer() else tacco_mm}")

    yy = y
    for ln in lines_left:
        d.text((x, yy), ln, fill="black", font=font_small)
        yy += 44

    out = io.BytesIO()
    canvas.save(out, format="JPEG", quality=95, subsampling=0, optimize=True)
    return out.getvalue()
