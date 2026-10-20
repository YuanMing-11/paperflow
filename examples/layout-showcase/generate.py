#!/usr/bin/env python3
"""Generate a wholly fictional, content-preserving PaperFlow layout showcase.

All observations and numbers are synthetic. This is a source-authored product
demonstration, not a benchmark result or a claim of automatic repair.
"""
from pathlib import Path
import json
import re
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor, Color, white
import fitz
from matplotlib.textpath import TextPath
from matplotlib.path import Path as MplPath
from matplotlib.font_manager import FontProperties

ROOT = Path(__file__).resolve().parent
W, H = 612, 792
L, R = 54, 558
INK = HexColor("#202b38")
MUTED = HexColor("#586576")
BLUE = HexColor("#245a81")
TEAL = HexColor("#14867e")
GRID = HexColor("#dce3e8")
BODY = ParagraphStyle("body", fontName="Times-Roman", fontSize=10.6,
                      leading=14.2, textColor=INK, spaceAfter=0)
CAPTION = ParagraphStyle("caption", fontName="Helvetica", fontSize=8.7,
                         leading=11.7, textColor=MUTED)
SMALL_CAPTION = ParagraphStyle("smallcap", fontName="Helvetica", fontSize=7,
                               leading=9.3, textColor=MUTED)

TEXT = {
    "abstract": (
        "Longer retrieval contexts can improve coverage while increasing the work "
        "required to find useful evidence. We compare a dense retriever with a "
        "reranked pipeline at three context budgets on a synthetic evaluation "
        "set. The reranked pipeline achieves higher answer accuracy at every "
        "tested budget, with a smaller gain between 4k and 8k tokens. These "
        "observations describe this controlled example; they do not establish "
        "that more context improves every retrieval task."
    ),
    "setup": (
        "We evaluate 1,200 questions using the same corpus, generator, and prompt "
        "for both pipelines. Context budgets are 2k, 4k, and 8k tokens. Each "
        "configuration is repeated with five random seeds. Accuracy is the "
        "fraction of answers matching the reference response; latency is measured "
        "on the same hardware. The training objective combines a task loss, a "
        "consistency term, and weight regularization:"
    ),
    "equation_note": (
        "Here N is the number of training examples; alpha, beta, and lambda are "
        "fixed across all configurations."
    ),
    "results": (
        "Figure {ref} compares accuracy across the three context budgets. The "
        "reranked pipeline rises from 68.4% at 2k to 76.1% at 8k, while the dense "
        "retriever rises from 64.2% to 70.0%. The largest observed gain occurs "
        "between 2k and 4k tokens for both pipelines. Error bars show one standard "
        "deviation across five seeds. These differences summarize the tested "
        "configurations and should not be interpreted as a causal effect of "
        "context length alone."
    ),
    "robustness": (
        "Table 1 reports the complete measurements at the 4k budget. Reranking "
        "improves accuracy by 6.2 percentage points and increases median latency "
        "by 24 ms in this setup. Removing the consistency term reduces accuracy "
        "to 72.9%, while latency remains within 1 ms of the full pipeline. This "
        "ablation is consistent with a contribution from the training objective, "
        "although it does not isolate every possible interaction."
    ),
    "discussion": (
        "The comparison suggests that a moderate context budget can retain much "
        "of the observed accuracy benefit while limiting latency. The 4k "
        "configuration reaches 74.8% accuracy with a median latency of 118 ms. "
        "The 8k configuration reaches 76.1%, but its additional context may "
        "contain redundant evidence. We therefore interpret the results as a "
        "trade-off within the evaluated setting, rather than as a universal "
        "choice of budget. Application requirements may favor a different point "
        "on this trade-off."
    ),
    "limitations": (
        "The corpus, questions, and measurements in this document are "
        "fictional and were created to demonstrate document layout. The "
        "evaluation design represents one language and one hardware setting. "
        "A real study would need independent datasets, uncertainty analysis, "
        "and measurements under deployment conditions before supporting "
        "broader claims. Layout changes in this example preserve the numerical "
        "values, methodological conditions, and interpretive limits of the text."
    ),
}
FIG_CAP = (
    "<b>Figure 1.</b> Answer accuracy by context budget. Points show the mean "
    "of five seeds; error bars show one standard deviation."
)
TABLE_CAP = (
    "<b>Table 1.</b> Measurements at 4k tokens. Accuracy is mean +/- standard "
    "deviation over five seeds; latency is the median."
)
EQUATION = (
    "J(theta) = (1/N) sum_i [alpha L_task(y_i, f_theta(x_i)) "
    "+ beta L_cons(f_theta(x_i), f_theta(x'_i))] + lambda ||theta||_2^2"
)
EQ_LINES = [
    "J(theta) = (1/N) sum_i [alpha L_task(y_i, f_theta(x_i))",
    "                         + beta L_cons(f_theta(x_i), f_theta(x'_i))]",
    "                         + lambda ||theta||_2^2",
]
MATH_FULL = (r"$\mathcal{J}(\theta)=\frac{1}{N}\sum_{i=1}^{N}"
             r"\left[\alpha\mathcal{L}_{\mathrm{task}}(y_i,f_\theta(x_i))"
             r"+\beta\mathcal{L}_{\mathrm{cons}}(f_\theta(x_i),f_\theta(x_i^{\prime}))\right]"
             r"+\lambda\Vert\theta\Vert_2^2$")
MATH_LINES = [
    (r"$\mathcal{J}(\theta)=\frac{1}{N}\sum_{i=1}^{N}"
     r"\left[\alpha\mathcal{L}_{\mathrm{task}}(y_i,f_\theta(x_i))\right.$"),
    (r"$\left.\qquad+\beta\mathcal{L}_{\mathrm{cons}}(f_\theta(x_i),"
     r"f_\theta(x_i^{\prime}))\right]+\lambda\Vert\theta\Vert_2^2$"),
]
TABLE = [
    ["Configuration", "Accuracy (%)", "Latency (ms)", "Context"],
    ["Dense", "68.6 +/- 0.8", "94", "4k"],
    ["Reranked", "74.8 +/- 0.7", "118", "4k"],
    ["No consistency term", "72.9 +/- 0.9", "117", "4k"],
]
REGIONS = {"before": {}, "after": {}}


def rect(c, x, top, w, h, fill, stroke=None, radius=0):
    c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke)
    if radius:
        c.roundRect(x, H-top-h, w, h, radius, fill=1, stroke=bool(stroke))
    else:
        c.rect(x, H-top-h, w, h, fill=1, stroke=bool(stroke))


def line(c, x1, y1, x2, y2, color=GRID, width=0.6):
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.line(x1, H-y1, x2, H-y2)


def text(c, x, y, s, font="Helvetica", size=10, color=INK, align="left"):
    c.setFillColor(color)
    c.setFont(font, size)
    method = {"left":c.drawString, "right":c.drawRightString,
              "center":c.drawCentredString}[align]
    method(x, H-y, s)


def para(c, value, top, width=R-L, x=L, style=BODY):
    p = Paragraph(value, style)
    _, height = p.wrap(width, 1000)
    p.drawOn(c, x, H-top-height)
    return height


def section(c, title, top, after):
    text(c, L, top+13, title, "Helvetica-Bold" if after else "Times-Bold",
         11.4 if after else 11.2, BLUE if after else INK)


def furniture(c, page, after):
    c.setTitle("Retrieval Quality Across Context Lengths")
    c.setAuthor("PaperFlow synthetic example")
    c.setSubject("Fictional, content-preserving document layout demonstration")
    text(c, L, 29, "RETRIEVAL STUDY  /  SYNTHETIC EXAMPLE", size=7.2, color=MUTED)
    text(c, R, 29, "RESEARCH NOTE", size=7.2, color=MUTED, align="right")
    if after:
        line(c, L, 36, R, 36)
    line(c, L, 755, R, 755)
    text(c, L, 771, "PaperFlow demonstration  |  All data are fictional", size=7.2, color=MUTED)
    text(c, R, 771, str(page), size=8, color=MUTED, align="right")


def title(c, after):
    text(c, L, 73, "Retrieval Quality Across", "Times-Bold", 23 if after else 21)
    text(c, L, 101, "Context Lengths", "Times-Bold", 23 if after else 21)
    text(c, L, 119, "A controlled comparison of dense and reranked pipelines",
         "Helvetica", 9.1, MUTED)


def equation(c, top, after):
    def mathpath(formula, x, baseline, size):
        tp=TextPath((0,0),formula,size=size,
                    prop=FontProperties(math_fontfamily="stix"))
        p=c.beginPath()
        current=(0,0)
        def xy(a,b):
            return x+a,H-baseline+b
        for values,code in tp.iter_segments(curves=True,simplify=False):
            if code==MplPath.MOVETO:
                current=(values[0],values[1]); p.moveTo(*xy(*current))
            elif code==MplPath.LINETO:
                current=(values[0],values[1]); p.lineTo(*xy(*current))
            elif code==MplPath.CURVE3:
                control=(values[0],values[1]); end=(values[2],values[3])
                c1=tuple(current[k]+2/3*(control[k]-current[k]) for k in (0,1))
                c2=tuple(end[k]+2/3*(control[k]-end[k]) for k in (0,1))
                p.curveTo(*xy(*c1),*xy(*c2),*xy(*end));current=end
            elif code==MplPath.CURVE4:
                p.curveTo(*xy(values[0],values[1]),*xy(values[2],values[3]),
                          *xy(values[4],values[5]))
                current=(values[4],values[5])
            elif code==MplPath.CLOSEPOLY:
                p.close()
        c.setFillColor(INK);c.drawPath(p,fill=1,stroke=0,fillMode=1)
    if after:
        mathpath(MATH_LINES[0],L+53,top,14)
        mathpath(MATH_LINES[1],L+87,top+29,14)
        text(c, R, top+15, "(1)", "Times-Roman", 10, align="right")
        REGIONS["after"]["equation"]={"page":1,"bbox":[45,top-24,568,top+43]}
    else:
        # Dense, small mathematics with its number stranded on a separate line.
        mathpath(MATH_FULL,L+12,top,12)
        text(c, R+22, top+18, "(1)", "Times-Roman", 10, align="right")
        REGIONS["before"]["equation"]={"page":1,"bbox":[45,top-24,608,top+28]}


def chart(c, top, after):
    height = 188 if after else 185
    x0, x1 = L+49, R-24
    y0, y1 = top+28, top+height-34
    fontsize = 9.4 if after else 6.3
    # Good version has a stronger print-safe distinction as well as color.
    series = [
        ("Dense", [64.2,68.6,70.0],[0.9,0.8,0.8], BLUE, "circle"),
        ("Reranked",[68.4,74.8,76.1],[0.8,0.7,0.7], TEAL, "square"),
    ]
    for val in [60,65,70,75,80]:
        y = y1-(val-60)/20*(y1-y0)
        line(c,x0,y,x1,y,GRID,0.55)
        text(c,x0-11,y+3,str(val),size=fontsize,color=MUTED,align="right")
    for j, label in enumerate(["2k","4k","8k"]):
        x = x0+25+j*(x1-x0-50)/2
        text(c,x,y1+16,label,size=fontsize,color=MUTED,align="center")
    line(c,x0,y0,x0,y1,HexColor("#a8b4bd"),0.7)
    line(c,x0,y1,x1,y1,HexColor("#a8b4bd"),0.7)
    text(c,x0,top+12,"Accuracy (%)",size=fontsize,color=MUTED)
    text(c,(x0+x1)/2,top+height-2,"Context budget (tokens)",size=fontsize,color=MUTED,align="center")
    for k,(name,values,errors,color,marker) in enumerate(series):
        coords = [(x0+25+j*(x1-x0-50)/2,
                   y1-(value-60)/20*(y1-y0)) for j,value in enumerate(values)]
        c.setStrokeColor(color)
        c.setLineWidth(1.7 if after else 1)
        if after and marker == "square":
            c.setDash(4,2.5)
        path=c.beginPath()
        for j,(x,y) in enumerate(coords):
            (path.moveTo if not j else path.lineTo)(x,H-y)
        c.drawPath(path)
        c.setDash()
        for (x,y),err in zip(coords,errors):
            d=err/20*(y1-y0)
            line(c,x,y-d,x,y+d,color,0.8)
            line(c,x-3,y-d,x+3,y-d,color,0.8)
            line(c,x-3,y+d,x+3,y+d,color,0.8)
            c.setFillColor(color)
            if after and marker == "square":
                c.rect(x-3,H-y-3,6,6,fill=1,stroke=0)
            else:
                c.circle(x,H-y,3 if after else 1.9,fill=1,stroke=0)
        lx=L+300+k*98
        ly=top+9
        line(c,lx,ly,lx+16,ly,color,1.4 if after else 1)
        if after and marker=="square":
            rect(c,lx+6,ly-2.6,5.2,5.2,color)
        else:
            c.setFillColor(color); c.circle(lx+8,H-ly,2.6 if after else 1.5,fill=1,stroke=0)
        text(c,lx+22,ly+3,name,size=fontsize,color=INK)
    return height


def table(c, top, after):
    rh=27 if after else 24
    width=R-L
    bounds=[L,L+216,L+338,L+446,R]
    if after:
        rect(c,L,top,width,rh,HexColor("#edf3f5"))
        line(c,L,top,R,top,BLUE,1.0)
        for row in range(1,4):
            if row==2:
                rect(c,L,top+rh*row,width,rh,HexColor("#f5f8fa"))
            line(c,L,top+rh*(row+1),R,top+rh*(row+1),GRID,0.65)
        for i,row in enumerate(TABLE):
            y=top+i*rh+17.5
            for j,val in enumerate(row):
                if j==0:
                    x=L+8; align="left"
                elif i==0:
                    x=(bounds[j]+bounds[j+1])/2;align="center"
                else:
                    x=bounds[j+1]-14;align="right"
                text(c,x,y,val,"Helvetica-Bold" if i==0 else "Helvetica",
                     8.7 if i==0 else 9.2, INK,align)
        line(c,L,top+rh*4,R,top+rh*4,BLUE,0.9)
    else:
        for i in range(5):
            line(c,L,top+rh*i,R,top+rh*i,HexColor("#6e7885"),0.65)
        for x in bounds:
            line(c,x,top,x,top+rh*4,HexColor("#6e7885"),0.65)
        for i,row in enumerate(TABLE):
            y=top+i*rh+15.5
            for j,val in enumerate(row):
                # All columns are left aligned; small header and dense box rules.
                text(c,bounds[j]+7,y,val,"Times-Roman",8.1,INK)
    return rh*4


def create(version):
    after=version=="after"
    c=canvas.Canvas(str(ROOT/f"{version}.pdf"),pagesize=(W,H),pageCompression=1)
    furniture(c,1,after); title(c,after)
    if after:
        section(c,"Abstract",137,after); para(c,TEXT["abstract"],159)
        section(c,"1. Evaluation setup",239,after); para(c,TEXT["setup"],261)
        equation(c,342,after)
        para(c,TEXT["equation_note"],388,style=ParagraphStyle(
            "note",parent=BODY,fontSize=9.3,leading=12))
        section(c,"2. Results",415,after)
        resulttop=437; para(c,TEXT["results"].format(ref="1"),resulttop)
        figtop=522; chart(c,figtop,True)
        para(c,FIG_CAP,719,style=CAPTION)
        REGIONS[version].update({
            "results":{"page":1,"bbox":[48,412,564,515]},
            "chart":{"page":1,"bbox":[47,516,565,715]},
            "caption":{"page":1,"bbox":[48,715,564,747]},
            "figure_group":{"page":1,"bbox":[47,516,565,747]},
        })
    else:
        section(c,"Abstract",145,after);para(c,TEXT["abstract"],168)
        section(c,"1. Evaluation setup",269,after);para(c,TEXT["setup"],294)
        equation(c,390,after)
        para(c,TEXT["equation_note"],425)
        section(c,"2. Results",480,after)
        para(c,TEXT["results"].format(ref="??"),506)
        section(c,"2.1. A closer look at 4k",606,after)
        para(c,TEXT["robustness"],632)
        section(c,"3. Discussion",730,after)
        REGIONS[version].update({
            "results":{"page":1,"bbox":[48,476,564,595]},
            "orphan_heading":{"page":1,"bbox":[48,719,564,750]},
            "reference":{"page":1,"bbox":[48,500,564,528]},
        })
    c.showPage()
    furniture(c,2,after)
    if after:
        para(c,TABLE_CAP,59,style=CAPTION)
        tabtop=92; tabheight=table(c,tabtop,True)
        section(c,"2.1. A closer look at 4k",235,after)
        para(c,TEXT["robustness"],260)
        section(c,"3. Discussion",368,after)
        para(c,TEXT["discussion"],393)
        section(c,"4. Scope and limitations",515,after)
        para(c,TEXT["limitations"],540)
        REGIONS[version].update({
            "table":{"page":2,"bbox":[48,85,564,208]},
            "table_group":{"page":2,"bbox":[48,52,564,208]},
            "discussion_heading":{"page":2,"bbox":[48,360,564,490]},
            "limitations":{"page":2,"bbox":[48,510,564,639]},
            "reference":{"page":1,"bbox":[48,434,564,459]},
        })
    else:
        figtop=61;chart(c,figtop,False)
        para(c,FIG_CAP,293,style=SMALL_CAPTION)
        tabtop=364;tabheight=table(c,tabtop,False)
        para(c,TABLE_CAP,489,style=SMALL_CAPTION)
        para(c,TEXT["discussion"],540)
        section(c,"4. Scope and limitations",659,False)
        para(c,TEXT["limitations"],682)
        REGIONS[version].update({
            "chart":{"page":2,"bbox":[47,54,565,251]},
            "caption":{"page":2,"bbox":[48,285,564,321]},
            "figure_group":{"page":2,"bbox":[47,54,565,321]},
            "table":{"page":2,"bbox":[48,356,564,467]},
            "table_group":{"page":2,"bbox":[48,356,564,515]},
            "discussion_body":{"page":2,"bbox":[48,534,564,645]},
            "limitations":{"page":2,"bbox":[48,653,564,751]},
        })
    c.save()
    doc=fitz.open(ROOT/f"{version}.pdf")
    for n,page in enumerate(doc):
        page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(
            ROOT/f"{version}-page-{n+1}.png")
    return doc


def main():
    docs={key:create(key) for key in ("before","after")}
    metadata={
        "provenance":"Wholly fictional, original source-authored product illustration.",
        "claim_boundary":"Demonstrates repair targets; does not claim automatic detection or repair.",
        "coordinate_system":"PDF points, top-left origin, 612 x 792; page numbers are 1-based.",
        "render_scale":1.5,
        "pages":{"before":2,"after":2},
        "regions":REGIONS,
        "preserved":{
            "paragraphs":TEXT,
            "table":TABLE,
            "figure":{
                "context_tokens":[2000,4000,8000],
                "dense_accuracy":[64.2,68.6,70.0],
                "dense_standard_deviation":[0.9,0.8,0.8],
                "reranked_accuracy":[68.4,74.8,76.1],
                "reranked_standard_deviation":[0.8,0.7,0.7],
                "seeds":5
            },
            "equation":EQUATION,
            "figure_caption":FIG_CAP,
            "table_caption":TABLE_CAP,
        },
        "intentional_changes":[
            "Figure moves from page 2 to page 1, next to the results paragraph.",
            "Chart labels increase from 6.3pt to 9.4pt; square markers and dashed line distinguish reranked data.",
            "Figure caption moves from 47pt below the chart to 9pt below; caption type increases from 7pt to 8.7pt.",
            "Table uses an emphasized header, restrained horizontal rules, row shading and right-aligned numeric columns.",
            "Table caption moves above its table and stays grouped with it.",
            "Dense single-line equation becomes larger, two-line mathematics with the equation number aligned; math tokens are retained.",
            "Discussion heading moves from the bottom of page 1 to accompany its paragraph on page 2.",
            "Unresolved Figure ?? becomes Figure 1.",
            "Section typography, inter-block spacing and page hierarchy are made consistent."
        ],
    }
    (ROOT/"regions.json").write_text(json.dumps(metadata,indent=2)+"\n")
    comparison={
        "overview":{
            "before":[
                {"page":0,"bbox":[48,476,564,595],"number":1},
                {"page":1,"bbox":[47,54,565,251],"number":1},
                {"page":0,"bbox":[48,719,564,750],"number":2},
                {"page":1,"bbox":[48,285,564,321],"number":3},
                {"page":0,"bbox":[48,500,115,528],"number":3},
            ],
            "after":[
                {"page":0,"bbox":[48,412,564,515],"number":1},
                {"page":0,"bbox":[47,516,565,715],"number":1},
                {"page":1,"bbox":[48,360,564,490],"number":2},
                {"page":0,"bbox":[48,715,564,747],"number":3},
                {"page":0,"bbox":[48,434,112,459],"number":3},
            ],
        },
        "details":{},
    }
    for kind in ["chart","table","equation"]:
        comparison["details"][kind]={}
        for v in ["before","after"]:
            entry=REGIONS[v][kind]
            comparison["details"][kind][v]={"page":entry["page"]-1,"bbox":entry["bbox"]}
    (ROOT/"comparison-regions.json").write_text(json.dumps(comparison,indent=2)+"\n")
    for version,doc in docs.items():
        extracted="\n".join(p.get_text() for p in doc)
        (ROOT/f"{version}-extracted.txt").write_text(extracted)
        # Highlight any incidental off-page text in the generator output.
        for n,page in enumerate(doc):
            for b in page.get_text("blocks"):
                if b[0] < 0 or b[1] < 0 or b[2] > W+.1 or b[3]>H+.1:
                    print("OUTSIDE",version,n+1,b[:4],repr(b[4][:70]))
        print(version,len(doc),"pages")
    print(ROOT/"regions.json")


if __name__=="__main__":
    main()
