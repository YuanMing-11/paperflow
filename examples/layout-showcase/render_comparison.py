"""Compose a README figure from the actual showcase PDFs (no invented page content)."""
from pathlib import Path
import base64
import html
import json
import fitz

BASE = Path(__file__).resolve().parent
OUT = Path(__file__).resolve().parents[2] / "assets"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1600, 1510
parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
    '<rect width="1600" height="1510" rx="26" fill="#f4f6fa"/>',
]

def rect(x, y, w, h, fill, stroke="none", radius=0, sw=1):
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

def text(x, y, value, size=24, color="#18263b", weight="normal", anchor="start"):
    parts.append(f'<text x="{x}" y="{y}" font-family="sans-serif" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{html.escape(value)}</text>')

def pill(x, y, label, color, fill, width):
    rect(x, y, width, 38, fill, radius=19)
    text(x+width/2, y+26, label, 21, color, "bold", "middle")

def pdf_image(doc, page, x, y, w, h, bbox=None):
    p = doc[page]
    clip = fitz.Rect(bbox) if bbox else p.rect
    scale = min(w / clip.width, h / clip.height)
    iw, ih = clip.width * scale, clip.height * scale
    ix, iy = x + (w-iw)/2, y+(h-ih)/2
    pix = p.get_pixmap(matrix=fitz.Matrix(max(scale*2, 1.4), max(scale*2, 1.4)), clip=clip, alpha=False)
    data = base64.b64encode(pix.tobytes("png")).decode()
    parts.append(f'<image x="{ix}" y="{iy}" width="{iw}" height="{ih}" xlink:href="data:image/png;base64,{data}"/>')
    return ix, iy, scale

def arrow(x1, y1, x2, y2, color="#7e8da4"):
    parts.append(f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round"/>')
    parts.append(f'<path d="M{x2-7},{y2-7} L{x2},{y2} L{x2-7},{y2+7}" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round"/>')

def highlight(transform, bbox, color, number):
    x, y, s = transform
    a,b,c,d = bbox
    rect(x+a*s-3, y+b*s-3, (c-a)*s+6, (d-b)*s+6, "none", color, 4, 2)
    cx,cy=x+a*s-7,y+b*s-7
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="13" fill="{color}"/>')
    text(cx,cy+5,str(number),16,"#ffffff","bold","middle")

before = fitz.open(BASE / "before.pdf")
after = fitz.open(BASE / "after.pdf")
meta = json.loads((BASE / "comparison-regions.json").read_text())

text(56, 56, "PaperFlow", 25, "#3059d6", "bold")
text(56, 116, "一篇论文，七类排版优化", 48, "#14243c", "bold")
text(56, 163, "图文位置 · 分页读序 · 图表 · 表格 · 公式 · 图注 · 引用", 24, "#607087")
pill(1322, 35, "可复现示例", "#52657f", "#e7ecf3", 220)

for x, label, detail, tint, accent in [
    (40, "优化前", "图文分离，阅读频繁中断", "#fff1ec", "#bc6047"),
    (840, "优化后", "解释、图表与细节顺畅衔接", "#e8f5ef", "#218563"),
]:
    rect(x, 200, 720, 565, "#ffffff", "#e1e7ef", 18)
    pill(x+28, 225, label, accent, tint, 116)
    text(x+163, 253, detail, 24, "#263951")

transforms = {}
for key, doc, panel_x in [("before", before, 40), ("after", after, 840)]:
    for page in range(2):
        px = panel_x + 48 + page*320
        py = 290
        rect(px-1, py-1, 278, 360, "#ffffff", "#d4dce7", 2)
        transforms[(key,page)] = pdf_image(doc,page,px,py,276,358)
        text(px+138, 679, f"第 {page+1} 页", 18, "#76859a", anchor="middle")
    for item in meta.get("overview",{}).get(key,[]):
        if item["bbox"][2] - item["bbox"][0] < 100:
            continue
        highlight(transforms[(key,item["page"])],item["bbox"],"#bc6047" if key=="before" else "#218563",item["number"])

text(76, 727, "① 图文距离    ② 标题分页    ③ 图注与引用", 23, "#9b513f")
text(876, 727, "图随解释 · 标题跟随正文 · 图注与编号对应", 23, "#1d7558")
parts.append('<circle cx="800" cy="480" r="26" fill="#e6ecf7"/>')
arrow(787,480,813,480,"#5071ba")

text(56, 825, "放大看细节", 29, "#14243c", "bold")
text(298, 825, "同一组数据，同一段内容", 23, "#607087")

cards = [
    ("chart", "图表可读性", "字号清晰，颜色与点型共同区分"),
    ("table", "表格对齐", "列宽、数值与表头更易扫读"),
    ("equation", "公式折行", "长公式分行，编号右对齐"),
]
for i,(key,title,caption) in enumerate(cards):
    x = 40+i*520
    rect(x, 855, 480, 555, "#ffffff", "#e1e7ef", 16)
    text(x+24, 897, title, 27, "#20344f", "bold")
    text(x+24, 934, caption, 20, "#607087")
    pill(x+24, 957, "优化前", "#a05d4c", "#fff1ec", 88)
    pill(x+24, 1177, "优化后", "#218563", "#e8f5ef", 88)
    for side,doc,dy in [("before",before,0),("after",after,220)]:
        region=meta["details"][key][side]
        bbox = list(region["bbox"])
        # Magnify the labels/series and numeric columns instead of shrinking
        # an entire chart or table into a detail card.
        if key == "chart":
            bbox = [310, bbox[1], 563, bbox[1]+112]
        elif key == "table":
            bbox = [270, bbox[1], 500, bbox[3]]
        pdf_image(doc,region["page"],x+24,1003+dy,432,165,bbox)
    parts.append(f'<path d="M{x+24},1170 H{x+456}" stroke="#e8edf4" stroke-width="1"/>')

text(56, 1470, "保留文字、数据与必要限定，把调整落到最终页面。", 27, "#263951", "bold")
text(1544, 1470, "示例 PDF 实际渲染", 19, "#7c8a9d", anchor="end")
parts.append("</svg>")
svg = "\n".join(parts).encode()
(OUT/"layout-before-after.svg").write_bytes(svg)
d=fitz.open(stream=svg,filetype="svg")
d[0].get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(OUT/"layout-before-after.png")
print(OUT/"layout-before-after.png")
