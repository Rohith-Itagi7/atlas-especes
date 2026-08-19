#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fabrique une PLANCHE-CONTACT numérotée (grille d'images) pour annoter vite.
Usage : python3 montage.py <sortie.png> <img1> <img2> ...
Sort <sortie.png> et imprime le mapping « n° -> nom de fichier ».
"""
import sys, os, base64, subprocess, tempfile

out = sys.argv[1]
paths = sys.argv[2:]
COLS = 4; IMGSZ = 200; LBL = 26; CELL = IMGSZ + 12
rows = (len(paths) + COLS - 1) // COLS
W = COLS * CELL
H = rows * (IMGSZ + LBL) + 6
SQ = max(W, H)  # canevas carré : qlmanage recadre en carré, donc on évite qu'il rogne

def thumb(p):
    tmp = tempfile.mktemp(suffix=".jpg")
    subprocess.run(["sips", "-Z", "220", "-s", "format", "jpeg", "-s", "formatOptions", "78", p, "--out", tmp],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    src = tmp if os.path.exists(tmp) else p
    b = base64.b64encode(open(src, "rb").read()).decode()
    if os.path.exists(tmp):
        os.remove(tmp)
    return "data:image/jpeg;base64," + b

cells = []
for i, p in enumerate(paths):
    c = i % COLS; r = i // COLS
    x = c * CELL; y = r * (IMGSZ + LBL)
    cells.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#f0f0f0"/>' % (x + 6, y + LBL, IMGSZ, IMGSZ))
    cells.append('<image x="%d" y="%d" width="%d" height="%d" href="%s" preserveAspectRatio="xMidYMid slice"/>'
                 % (x + 6, y + LBL, IMGSZ, IMGSZ, thumb(p)))
    cells.append('<text x="%d" y="%d" text-anchor="middle" font-size="17" font-weight="700" font-family="Arial" fill="#111">%d</text>'
                 % (x + CELL / 2, y + 18, i + 1))
svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d"><rect width="%d" height="%d" fill="#fff"/>%s</svg>'
       % (SQ, SQ, SQ, SQ, "".join(cells)))
svgf = out + ".svg"
open(svgf, "w").write(svg)
outdir = os.path.dirname(out) or "."
subprocess.run(["qlmanage", "-t", "-s", str(min(2000, SQ * 2)), "-o", outdir, svgf],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
rendered = os.path.join(outdir, os.path.basename(svgf) + ".png")
if os.path.exists(rendered):
    os.replace(rendered, out)
os.remove(svgf)
for i, p in enumerate(paths):
    print("%2d -> %s" % (i + 1, os.path.basename(p)))
print("PLANCHE:", out, "(%d images)" % len(paths))
