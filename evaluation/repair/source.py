#!/usr/bin/env python3
"""Original synthetic report source for a layout-repair forward test."""
import argparse
from pathlib import Path
from reportlab.graphics.shapes import Drawing, Line, String
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether


def chart():
    drawing = Drawing(430, 210)
    drawing.add(Line(45, 35, 400, 35))
    drawing.add(Line(45, 35, 45, 190))
    for x, label in [(45, "0"), (130, "1"), (215, "2"), (300, "3"), (385, "4")]:
        drawing.add(String(x - 3, 19, label, fontSize=10))
    for y, label in [(35, "0"), (85, "1"), (135, "2"), (185, "3")]:
        drawing.add(String(25, y - 3, label, fontSize=10))
    drawing.add(String(165, 2, "Observation time (s)", fontSize=10))
    drawing.add(String(48, 198, "Response (a.u.)", fontSize=10))
    series = [
        (colors.HexColor("#176e87"), [(45, 60), (130, 90), (215, 120), (300, 145), (385, 155)]),
        (colors.HexColor("#9c3d35"), [(45, 60), (130, 80), (215, 90), (300, 100), (385, 105)]),
    ]
    for color, points in series:
        for start, end in zip(points, points[1:]):
            drawing.add(Line(*start, *end, strokeColor=color, strokeWidth=2))
    drawing.add(String(260, 182, "Treatment", fontSize=10, fillColor=series[0][0]))
    drawing.add(String(260, 168, "Control", fontSize=10, fillColor=series[1][0]))
    return drawing


def build(output):
    styles = getSampleStyleSheet()
    styles["BodyText"].fontSize = 11
    styles["BodyText"].leading = 15
    story = [
        Paragraph("Controlled response comparison", styles["Title"]),
        Paragraph("Synthetic layout test; the observations below are fictional.", styles["BodyText"]),
        Spacer(1, 16),
        Paragraph("Results", styles["Heading1"]),
        Paragraph(
            "Figure 1 shows the treatment and control responses at 0, 1, 2, 3, and 4 seconds. "
            "The curves begin at the same level and diverge after 1 second. "
            "Under the tested conditions, the treatment response reaches 2.4 a.u.; "
            "the control reaches 1.4 a.u. These observations describe this sample only.",
            styles["BodyText"]),
        Spacer(1, 12),
        KeepTogether([
            chart(),
            Spacer(1, 10),
            Paragraph(
                "Figure 1. Treatment and control response over 4 seconds. "
                "Lines connect the five observed values in each series.",
                styles["BodyText"])
        ]),
        Spacer(1, 12),
        Paragraph("Acquisition and interpretation", styles["Heading1"]),
        Paragraph(
            "Both groups use the same acquisition protocol. Time is measured in seconds and "
            "response in arbitrary units. The chart preserves every supplied observation. "
            "The connecting segments are visual guides and do not add measurements.",
            styles["BodyText"]),
        Spacer(1, 12),
        Paragraph(
            "The study design does not establish causality. The limited sample and controlled "
            "conditions restrict generalization. Layout changes must retain these qualifications.",
            styles["BodyText"]),
    ]
    SimpleDocTemplate(str(output), pagesize=(612, 792),
                      leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54).build(story)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    build(args.out)
