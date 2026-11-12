"""Prepare presentation backgrounds and crops from the recorded application."""
from pathlib import Path
import json
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[3]
ASSETS = Path(__file__).resolve().parent / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)


def background(name, glows, contours=True):
    w, h = 1920, 1080
    yy, xx = np.mgrid[0:h, 0:w]
    u, v = xx / w, yy / h
    base = np.zeros((h, w, 3), dtype=np.float64)
    base[:] = (6, 20, 25)
    base += (0.65 * u + 0.2 * v)[..., None] * np.array([3, 8, 10])
    for cx, cy, rx, ry, color, strength in glows:
        g = np.exp(-(((u-cx)/rx)**2 + ((v-cy)/ry)**2) * 2.0)
        base += g[..., None] * np.array(color) * strength
    noise = np.random.default_rng(20261112).normal(0, 0.38, (h,w,1))
    base = np.clip(base + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(base, "RGB").convert("RGBA")
    if contours:
        lines = Image.new("RGBA", (w,h))
        d = ImageDraw.Draw(lines)
        # A single, quiet water-contour motif. Never crosses the title area.
        for j in range(15):
            points=[]
            for k in range(220):
                x=1060+k*4.5
                y=605+j*19 + 70*math.sin(k/55+j/19)
                points.append((x,y))
            d.line(points, fill=(117,218,198,8), width=1)
        img = Image.alpha_composite(img,lines.filter(ImageFilter.GaussianBlur(0.45)))
    img.convert("RGB").save(ASSETS / f"{name}.jpg", quality=96, subsampling=0)


background("background",[(.88,.27,.52,.65,(13,86,76),.37),(.42,.99,.70,.55,(9,43,50),.4)])
background("hero",[(.78,.46,.50,.64,(18,116,93),.56),(.99,.93,.45,.45,(25,52,56),.3)])
background("data",[(.88,.26,.50,.64,(15,95,84),.46),(.29,.96,.70,.57,(13,38,49),.35)])
background("warning",[(.84,.36,.53,.62,(20,89,81),.37),(.96,.88,.39,.40,(107,46,36),.2)])

crops = {
    "dashboard":("desktop-dark.png",(224,48,1434,820)),
    "dashboard_map":("desktop-dark.png",(249,281,1051,809)),
    "area_evidence":("desktop-dark.png",(1067,281,1407,809)),
    "evidence_focus":("desktop-dark.png",(1084,332,1395,574)),
    "report_form":("report-form-dark.png",(248,174,830,884)),
    "moderation":("moderation-dark.png",(249,164,1406,944)),
    "alerts":("alerts-active-dark.png",(248,182,1407,1020)),
    "outage_map":("feed-outage-dark.png",(249,281,1051,809)),
    "phone":("mobile-dark.png",(0,0,390,938)),
}
manifest={}
for name,(source,bounds) in crops.items():
    path=ROOT / ".impeccable" / "review" / source
    img=Image.open(path).convert("RGBA").crop(bounds)
    mask=Image.new("L",img.size,0)
    d=ImageDraw.Draw(mask)
    d.rounded_rectangle((0,0,img.width-1,img.height-1),radius=16,fill=255)
    img.putalpha(mask)
    img.save(ASSETS / f"{name}.png")
    manifest[name]={"source":str(path.relative_to(ROOT)),"crop":bounds,"size":img.size}
(ASSETS / "source_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print(f"Prepared {len(crops)} screenshot crops and 4 backgrounds in {ASSETS}")
