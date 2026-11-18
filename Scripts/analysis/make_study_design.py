"""
Study-design figure (Figure 1) as an editable draw.io file, plus PDF/PNG rendered
from that same file, so the three never disagree.

    python Scripts/analysis/make_study_design.py            # write .drawio, then render
    python Scripts/analysis/make_study_design.py --render   # only render an edited .drawio

Output: paper/figures/study_design.drawio  (open in draw.io / diagrams.net)
        paper/figures/study_design.pdf, study_design.png

The renderer understands what this script writes (rounded boxes with HTML
labels, plain text cells, straight or way-pointed edges). After larger edits in
draw.io, export PDF/PNG from draw.io itself (File > Export as) instead.
"""

import html
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "paper", "figures")
DRAWIO = os.path.join(OUT, "study_design.drawio")

INK, INK2 = "#0b0b0b", "#52514e"
PREP, EVAL = "#eaf2fb", "#fdeee7"          # tints of palette blue / orange
W, H, H2, GAP, X0, Y1, Y2 = 180, 80, 96, 30, 20, 20, 160
Y3, H3 = Y2 + H2 + 44, 96            # third row: diagnostic variants (RQ5)
COL = [X0 + i * (W + GAP) for i in range(5)]
FONT = 14

BOXES = [  # id, column, row, fill, lines (first line bold)
    ("bb", 0, 1, PREP, ["BeetleBox dataset", "6 Java/Python projects", "4,995 bugs"]),
    ("fx", 1, 1, PREP, ["Fix commits", "files vs. first parent", "4,578 with counted files"]),
    ("cl", 2, 1, PREP, ["Classification", "3,594 primary-anchored:", "2,561 Mono / 985 Poly"]),
    ("sp", 3, 1, PREP, ["Chronological split", "2 folds, purged", "1,399 rankable test bugs"]),
    ("sn", 4, 1, PREP, ["Pre-fix snapshot", "every text file is", "a candidate"]),
    ("te", 4, 2, EVAL, ["Five techniques", "BM25, BLAZE: all text", "FLIM: parseable files",
                        "LocAgent, SweRank: .py"]),
    ("ev", 3, 2, EVAL, ["One evaluator", "parse status per file", "all-files / parseable"]),
    ("st", 2, 2, EVAL, ["Statistics", "AP, CFR@10, RR", "mixed models, S1\u2013S6"]),
    ("pr", 1, 2, PREP, ["Prevalence", "per grain and project", "984 no-primary aside"]),
    ("fe", 0, 2, PREP, ["Filter-excluded", "1,226 reports naming", "a fixed file: scored", "separately"]),
    ("dv", 4, 3, EVAL, ["Diagnostic variants", "SweRank on all text files", "hybrid with BM25", "co-change (history)"]),
]
EDGES = [("bb", "fx"), ("fx", "cl"), ("cl", "sp"), ("sp", "sn"), ("sn", "te"), ("te", "ev"), ("ev", "st"),
         ("cl", "pr"), ("bb", "fe"), ("te", "dv")]
LABELS = [("RQ1", "pr"), ("RQ2", "ev"), ("RQ3, RQ4", "st"), ("RQ5 (exploratory)", "dv")]


def geom(col, row):
    return COL[col], {1: Y1, 2: Y2, 3: Y3}[row], W, {1: H, 2: H2, 3: H3}[row]


def write_drawio():
    mx = ET.Element("mxfile", host="app.diagrams.net")
    dg = ET.SubElement(mx, "diagram", name="Study design", id="study-design")
    gm = ET.SubElement(dg, "mxGraphModel", dx="1100", dy="320", grid="1", gridSize="10", guides="1",
                       tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1",
                       pageWidth=str(COL[-1] + W + X0), pageHeight=str(Y3 + H3 + 34), math="0", shadow="0")
    root = ET.SubElement(gm, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")
    pos = {}
    for bid, c, r, fill, lines in BOXES:
        x, y, w, h = geom(c, r)
        pos[bid] = (x, y, w, h)
        val = "<b>" + html.escape(lines[0]) + "</b><br>" + "<br>".join(html.escape(l) for l in lines[1:])
        cell = ET.SubElement(root, "mxCell", id=bid, value=val, vertex="1", parent="1",
                             style=f"rounded=1;whiteSpace=wrap;html=1;arcSize=8;fillColor={fill};"
                                   f"strokeColor={INK2};fontColor={INK};fontFamily=Helvetica;fontSize={FONT};")
        ET.SubElement(cell, "mxGeometry", x=str(x), y=str(y), width=str(w), height=str(h), **{"as": "geometry"})
    for i, (s, t) in enumerate(EDGES):
        style = (f"edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;endSize=6;"
                 f"strokeColor={INK2};strokeWidth=1.5;")
        sx, sy, sw, sh = pos[s]
        tx, ty, tw, th = pos[t]
        pts = []
        if (s, t) == ("cl", "pr"):          # down from Classification, left, down into Prevalence
            style += "exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;"
            ymid = (sy + sh + ty) // 2
            pts = [(sx + sw // 2, ymid), (tx + tw // 2, ymid)]
        if (s, t) == ("dv", "ev"):          # left out of the variants box, up into the evaluator
            style += "exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=0.5;entryY=1;entryDx=0;entryDy=0;"
            pts = [(tx + tw // 2, sy + sh // 2)]
        cell = ET.SubElement(root, "mxCell", id=f"e{i}", style=style, edge="1", parent="1", source=s, target=t)
        g = ET.SubElement(cell, "mxGeometry", relative="1", **{"as": "geometry"})
        if pts:
            arr = ET.SubElement(g, "Array", **{"as": "points"})
            for px, py in pts:
                ET.SubElement(arr, "mxPoint", x=str(px), y=str(py))
    for i, (txt, under) in enumerate(LABELS):
        x, y, w, h = pos[under]
        cell = ET.SubElement(root, "mxCell", id=f"rq{i}", value=f"<b>{txt}</b>", vertex="1", parent="1",
                             style=f"text=1;html=1;align=center;verticalAlign=middle;strokeColor=none;"
                                   f"fillColor=none;fontColor={INK2};fontFamily=Helvetica;fontSize={FONT};")
        ET.SubElement(cell, "mxGeometry", x=str(x), y=str(y + h + 4), width=str(w), height="24",
                      **{"as": "geometry"})
    ET.indent(mx)
    os.makedirs(OUT, exist_ok=True)
    ET.ElementTree(mx).write(DRAWIO, encoding="utf-8", xml_declaration=False)
    print("wrote", DRAWIO)


# ------------------------------------------------------------------ renderer
def style_of(s):
    return dict(kv.split("=", 1) for kv in (s or "").strip(";").split(";") if "=" in kv)


def render():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager as fm
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
    for f in ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
        if os.path.exists(f):
            fm.fontManager.addfont(f)
    plt.rcParams.update({"font.family": "Liberation Sans", "pdf.fonttype": 42})
    tree = ET.parse(DRAWIO)
    gm = tree.find(".//mxGraphModel")
    pw, ph = float(gm.get("pageWidth")), float(gm.get("pageHeight"))
    width_in = 17.6 / 2.54
    k = width_in * 72 / pw                       # points per drawio px
    fig = plt.figure(figsize=(width_in, width_in * ph / pw))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, pw)
    ax.set_ylim(ph, 0)
    ax.axis("off")
    cells = {c.get("id"): c for c in tree.iter("mxCell")}
    boxes = {}
    for c in cells.values():
        if c.get("vertex") != "1":
            continue
        g = c.find("mxGeometry")
        x, y, w, h = (float(g.get(a, 0)) for a in ("x", "y", "width", "height"))
        st = style_of(c.get("style"))
        fs = float(st.get("fontSize", 12)) * k
        if st.get("text") != "1":
            boxes[c.get("id")] = (x, y, w, h)
            ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={0.08 * min(w, h)}",
                                        fc=st.get("fillColor", "white"), ec=st.get("strokeColor", INK2), lw=0.8))
        lines = [l for l in re.split(r"<br\s*/?>", html.unescape(c.get("value") or "")) if l.strip()]
        n = len(lines)
        for i, l in enumerate(lines):
            bold = "<b>" in l
            ax.text(x + w / 2, y + h / 2 + (i - (n - 1) / 2) * fs / k * 1.25, re.sub(r"<[^>]+>", "", l),
                    ha="center", va="center", fontsize=fs, color=st.get("fontColor", INK),
                    fontweight="bold" if bold else "normal")
    for c in cells.values():
        if c.get("edge") != "1":
            continue
        s, t = boxes[c.get("source")], boxes[c.get("target")]
        pts = [(float(p.get("x")), float(p.get("y"))) for p in c.iter("mxPoint")]
        st = style_of(c.get("style"))
        col = st.get("strokeColor", INK2)
        if pts and st.get("exitX") == "0":                          # left side out, into the bottom
            path = [(s[0], s[1] + s[3] / 2)] + pts + [(t[0] + t[2] / 2, t[1] + t[3])]
        elif pts:
            path = [(s[0] + s[2] / 2, s[1] + s[3])] + pts + [(t[0] + t[2] / 2, t[1])]
        elif abs((s[1] + s[3] / 2) - (t[1] + t[3] / 2)) < 1:        # same row
            yy = s[1] + s[3] / 2
            path = [(s[0] + s[2], yy), (t[0], yy)] if t[0] > s[0] else [(s[0], yy), (t[0] + t[2], yy)]
        else:                                                       # same column
            xx = s[0] + s[2] / 2
            path = [(xx, s[1] + s[3]), (xx, t[1])] if t[1] > s[1] else [(xx, s[1]), (xx, t[1] + t[3])]
        for a, b in zip(path[:-2], path[1:-1]):
            ax.plot([a[0], b[0]], [a[1], b[1]], color=col, lw=1.0, solid_capstyle="butt")
        ax.add_patch(FancyArrowPatch(path[-2], path[-1], arrowstyle="-|>,head_length=4,head_width=2.4",
                                     color=col, lw=1.0, shrinkA=0, shrinkB=0.5))
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, f"study_design.{ext}"), dpi=300, bbox_inches="tight", pad_inches=0.01)
    print("rendered", os.path.join(OUT, "study_design.pdf"), "and .png")


if __name__ == "__main__":
    if "--render" not in sys.argv:
        write_drawio()
    render()
