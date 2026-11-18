#!/usr/bin/env python3
"""Render the 17 November 2026 news front page (1024x1024) for make.fun
news-image-20261117. Flat editorial infographic, newspaper style:
warm paper, black ink, one red accent. No photos, no gradients.

Run from the repo root:  python3 tools/draw.py [out.png]
Fonts are vendored under assets/fonts/ and loaded by path only.
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets" / "fonts"

W = H = 1024
M = 28                      # outer margin
CW = W - 2 * M              # content width = 968

PAPER = (246, 241, 231)
INK = (22, 21, 19)
RED = (179, 39, 30)
MUTED = (107, 101, 90)
PANEL = (255, 253, 248)
GOLD = (176, 134, 22)
BLUE = (31, 68, 140)


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


SANS = "DejaVuSans.ttf"
SANS_B = "DejaVuSans-Bold.ttf"
SERIF = "DejaVuSerif.ttf"
SERIF_B = "DejaVuSerif-Bold.ttf"


def wrap(d, text, f, max_w):
    """Greedy word wrap; returns list of lines. Raises if a word is too wide."""
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if d.textlength(trial, font=f) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            if d.textlength(word, font=f) > max_w:
                raise SystemExit(f"WORD TOO WIDE: {word!r} at {f.size}px")
            cur = word
    if cur:
        lines.append(cur)
    return lines


def block(d, x, y, text, f, fill, max_w, leading, limit_y, tag=""):
    """Draw wrapped text; return bottom y. Fail loudly on overflow."""
    lines = wrap(d, text, f, max_w)
    for ln in lines:
        d.text((x, y), ln, font=f, fill=fill)
        y += leading
    bottom = y - (leading - f.size)
    if bottom > limit_y:
        raise SystemExit(f"OVERFLOW {tag}: bottom {bottom} > limit {limit_y} "
                         f"({len(lines)} lines)")
    return bottom


def centered_segments(d, y, segments, gap=0):
    """segments: [(text, font, fill)]. Draw one line centered on the page."""
    total = sum(d.textlength(t, font=f) for t, f, _ in segments) + gap * (len(segments) - 1)
    x = (W - total) / 2
    for i, (t, f, fill) in enumerate(segments):
        d.text((x, y), t, font=f, fill=fill)
        x += d.textlength(t, font=f) + gap
    return total


def fit_font(d, text, name, start, max_w):
    size = start
    while size > 10:
        f = font(name, size)
        if d.textlength(text, font=f) <= max_w:
            return f
        size -= 2
    raise SystemExit(f"cannot fit {text!r} in {max_w}px")


# ---------------------------------------------------------------- motifs
def motif_eye(d, ox, oy, s=56):
    d.ellipse([ox + 4, oy + s * 0.32, ox + s - 4, oy + s * 0.68],
              outline=INK, width=3)
    d.ellipse([ox + s / 2 - 10, oy + s / 2 - 10, ox + s / 2 + 10, oy + s / 2 + 10],
              outline=RED, width=3)
    d.ellipse([ox + s / 2 - 4, oy + s / 2 - 4, ox + s / 2 + 4, oy + s / 2 + 4],
              fill=INK)


def motif_globe(d, ox, oy, s=56):
    cx, cy, r = ox + s / 2, oy + s / 2, 21
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK, width=3)
    d.arc([cx - r, cy - r + 9, cx + r, cy + r - 9], 200, 340, fill=INK, width=2)
    d.arc([cx - r, cy - r + 9, cx + r, cy + r - 9], 20, 160, fill=INK, width=2)
    d.line([cx - 13, cy + 13, cx + 13, cy - 13], fill=INK, width=2)
    # tilt axis
    d.line([cx - 6, cy - 27, cx + 6, cy + 27], fill=RED, width=3)


def motif_bars(d, ox, oy, s=56):
    bw, gap = 12, 7
    heights = [42, 30, 17]
    x = ox + 5
    base = oy + s - 6
    for i, h in enumerate(heights):
        fill = GOLD if i == 2 else (214, 196, 150)
        d.rectangle([x, base - h, x + bw, base], fill=fill, outline=INK, width=2)
        x += bw + gap
    d.line([ox + 2, base, ox + s - 2, base], fill=INK, width=2)


def motif_chair(d, ox, oy, s=56):
    # empty chair: back, seat, legs, one red cushion outline left empty
    d.line([ox + 12, oy + 6, ox + 12, oy + 34], fill=INK, width=3)
    d.line([ox + 12, oy + 6, ox + 38, oy + 6], fill=INK, width=3)
    d.line([ox + 38, oy + 6, ox + 38, oy + 34], fill=INK, width=3)
    d.line([ox + 8, oy + 34, ox + 46, oy + 34], fill=INK, width=3)
    d.line([ox + 12, oy + 34, ox + 8, oy + 50], fill=INK, width=3)
    d.line([ox + 42, oy + 34, ox + 48, oy + 50], fill=INK, width=3)
    d.rectangle([ox + 16, oy + 20, ox + 34, oy + 30], outline=RED, width=2)


def motif_gavel(d, ox, oy, s=56):
    def rot(px, py, cx, cy, deg):
        a = math.radians(deg)
        dx, dy = px - cx, py - cy
        return (cx + dx * math.cos(a) - dy * math.sin(a),
                cy + dx * math.sin(a) + dy * math.cos(a))

    cx, cy = ox + s / 2, oy + s / 2
    head = [(ox + 8, oy + 12), (ox + 48, oy + 12), (ox + 48, oy + 26),
            (ox + 8, oy + 26)]
    d.polygon([rot(x, y, cx, cy, 28) for x, y in head], fill=INK)
    hx1, hy1 = rot(ox + 28, oy + 26, cx, cy, 28)
    hx2, hy2 = rot(ox + 28, oy + 48, cx, cy, 28)
    d.line([hx1, hy1, hx2, hy2], fill=INK, width=5)
    bx1, by1 = rot(ox + 8, oy + 50, cx, cy, 28)
    bx2, by2 = rot(ox + 48, oy + 50, cx, cy, 28)
    d.line([bx1, by1, bx2, by2], fill=RED, width=3)


def motif_flags_podium(d, x0, y0, x1, y1):
    """Three flags above a podium. Zone: x0..x1, y0..y1."""
    poles = [x0 + 52, x0 + 152, x0 + 252]
    top, base = y0 + 8, y1 - 64
    for px in poles:
        d.line([px, top, px, base], fill=INK, width=4)
        d.ellipse([px - 3, top - 4, px + 3, top + 2], fill=RED)
    fw, fh = 62, 40
    # Indonesia: red over white
    d.rectangle([poles[0], top, poles[0] + fw, top + fh], outline=INK, width=2)
    d.rectangle([poles[0] + 1, top + 1, poles[0] + fw - 1, top + fh // 2], fill=RED)
    # United States: stripes + canton
    d.rectangle([poles[1], top, poles[1] + fw, top + fh], fill=(255, 255, 255),
                outline=INK, width=2)
    for i in range(0, 7, 2):
        d.rectangle([poles[1] + 1, top + 1 + i * (fh // 7),
                     poles[1] + fw - 1, top + 1 + (i + 1) * (fh // 7)], fill=RED)
    d.rectangle([poles[1] + 1, top + 1, poles[1] + 26, top + fh // 2 + 2],
                fill=BLUE)
    for dx in (6, 14, 22):
        for dy in (5, 12):
            d.ellipse([poles[1] + dx - 1, top + dy - 1,
                       poles[1] + dx + 1, top + dy + 1], fill=(255, 255, 255))
    # ASEAN: blue field, white ring of ten dots
    d.rectangle([poles[2], top, poles[2] + fw, top + fh], fill=BLUE,
                outline=INK, width=2)
    ccx, ccy = poles[2] + fw // 2, top + fh // 2
    for k in range(10):
        a = math.radians(k * 36 - 90)
        d.ellipse([ccx + 11 * math.cos(a) - 2, ccy + 9 * math.sin(a) - 2,
                   ccx + 11 * math.cos(a) + 2, ccy + 9 * math.sin(a) + 2],
                  fill=(255, 255, 255))
    # lectern spanning all three poles, so none dangles
    d.polygon([(x0 + 40, base), (x1 - 40, base), (x1 - 24, y1 - 2),
               (x0 + 24, y1 - 2)], fill=INK)
    d.rectangle([x0 + 40, base - 6, x1 - 40, base], fill=RED)


# ---------------------------------------------------------------- page
def render():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # ---- masthead ----
    d.line([M, 20, W - M, 20], fill=INK, width=2)
    f_day = font(SANS_B, 24)
    d.text(((W - d.textlength("TUESDAY", font=f_day)) / 2, 30), "TUESDAY",
           font=f_day, fill=RED)
    f_date = fit_font(d, "17 NOVEMBER 2026", SERIF_B, 88, CW - 20)
    d.text(((W - d.textlength("17 NOVEMBER 2026", font=f_date)) / 2, 62),
           "17 NOVEMBER 2026", font=f_date, fill=INK)
    d.rectangle([M, 156, W - M, 161], fill=INK)
    d.line([M, 168, W - M, 168], fill=INK, width=2)
    f_stand = font(SERIF, 19)
    stand = ("ASEAN summit in Manila, a surveillance investigation, and gold's "
             "slide: the day in six stories.")
    block(d, M, 182, stand, f_stand, INK, CW, 26, 210,
          tag="standfirst")

    # ---- hero: ASEAN summit ----
    hx0, hy0, hx1, hy1 = M, 222, W - M, 572
    d.rectangle([hx0, hy0, hx1, hy1], fill=PANEL, outline=INK, width=3)
    tx = hx0 + 24
    tw = 580
    f_kick = font(SANS_B, 19)
    d.text((tx, hy0 + 16), "MANILA  ·  ASEAN SUMMIT", font=f_kick, fill=RED)
    f_head = font(SANS_B, 38)
    block(d, tx, hy0 + 46, "PRABOWO BACKS PALESTINE AT ASEAN SUMMIT",
          f_head, INK, tw, 48, hy0 + 192, tag="hero headline")
    f_deck = font(SANS, 17)
    bullets = [
        "At the East Asia Summit, Prabowo reaffirmed support for Palestinian "
        "independence and a two-state solution.",
        "Trump, at the ASEAN\u2013US summit, called him \u201ca great leader\u201d.",
        "Also: pharma and disaster cooperation with India; Sabang and the "
        "Andaman Islands to be developed together.",
    ]
    y = hy0 + 198
    for b in bullets:
        d.rectangle([tx, y + 7, tx + 8, y + 15], fill=RED)
        y = block(d, tx + 20, y, b, f_deck, INK, tw - 20, 23, hy1 - 14,
                  tag="hero bullet")
        y += 6
    motif_flags_podium(d, hx0 + 640, hy0 + 10, hx1 - 12, hy1 - 10)

    # ---- grid of five panels ----
    gap = 12
    gx0, gy0 = M, 588
    row1_h, row2_h = 200, 172
    w3 = (CW - 2 * gap) // 3          # 314
    w2 = (CW - gap) // 2              # 477

    def panel(x0, y0, w, h, kicker, headline, deck, motif, big=None,
              head_size=20, deck_size=15):
        d.rectangle([x0, y0, x0 + w, y0 + h], fill=PANEL, outline=INK, width=2)
        px, py = x0 + 14, y0 + 12
        f_k = font(SANS_B, 14)
        d.text((px, py), kicker, font=f_k, fill=RED)
        if motif:
            motif(d, x0 + w - 14 - 56, y0 + 8)
        f_h = font(SANS_B, head_size)
        y = block(d, px, py + 58, headline, f_h, INK, w - 28,
                  head_size + 6, y0 + h - 70, tag=f"headline {kicker}")
        if big:
            f_b = font(SANS_B, 28)
            d.text((px, y + 2), big, font=f_b, fill=GOLD)
            y += 30
        f_d = font(SANS, deck_size)
        block(d, px, y + 6, deck, f_d, INK, w - 28, deck_size + 5,
              y0 + h - 12, tag=f"deck {kicker}")

    # row 1
    panel(gx0, gy0, w3, row1_h, "SURVEILLANCE",
          "ISRAELI ARMY FED 3.5M PHOTOS TO AMAZON",
          "Dragnet over Palestinians; data reached Amazon servers in early "
          "2024. Unit: \u201cRolling Stone\u201d.", motif_eye)
    panel(gx0 + w3 + gap, gy0, w3, row1_h, "SCIENCE",
          "EARTH'S POLE SHIFTED 78.48 CM",
          "Groundwater pumping moved the rotation pole in 1993\u20132010, a "
          "Seoul National University study found.", motif_globe)
    panel(gx0 + 2 * (w3 + gap), gy0, w3, row1_h, "MARKETS",
          "GOLD'S ONE-YEAR LOW",
          "Down 31.5% from its early-year high of $5,594.82, pressured by "
          "high US yields and a stronger dollar.",
          motif_bars, big="$3,830.74")

    # row 2
    y2 = gy0 + row1_h + gap
    panel(gx0, y2, w2, row2_h, "JAKARTA",
          "GIBRAN RESIGNS; VP SEAT VACANT",
          "Prabowo picks the successor; Gerindra says wait until he returns, "
          "around 24 Nov. Police general Eko Hadi Santoso sacked over "
          "wiretapping of the president.", motif_chair,
          head_size=22, deck_size=16)
    panel(gx0 + w2 + gap, y2, w2, row2_h, "GRAFT",
          "DISASTER-FUND GRAFT AT BNPB",
          "KPK revealed procurement graft using disaster ready-to-use funds: "
          "\u201cborrowed company flags\u201d and fees paid to officials for "
          "direct appointments.", motif_gavel,
          head_size=22, deck_size=16)

    # ---- ticker strip ----
    ty0 = 972
    d.rectangle([0, ty0, W, H], fill=INK)
    f_t = font(SANS_B, 17)
    f_tr = font(SANS, 17)
    centered_segments(d, ty0 + 6, [
        ("IHSG +0.39% TO 5,341", f_t, (255, 255, 255)),
        ("  ·  ", f_tr, (255, 255, 255)),
        ("NIKKEI -0.57%", f_tr, (255, 255, 255)),
        ("  ·  ", f_tr, (255, 255, 255)),
        ("S&P/ASX 200 -0.15%", f_tr, (255, 255, 255)),
    ])
    centered_segments(d, ty0 + 28, [
        ("COFFEE -21% YTD, ARABICA 274.43 US CENTS/LB", f_tr, (255, 255, 255)),
        ("  ·  ", f_tr, (255, 255, 255)),
        ("RUPIAH Rp18,206 PER US$", f_t, (255, 255, 255)),
    ])
    return img


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "entry.png"
    img = render()
    img.save(out, format="PNG", optimize=True)
    print(f"wrote {out} {img.size} {out.stat().st_size} bytes")


if __name__ == "__main__":
    main()
