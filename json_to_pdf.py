#!/usr/bin/env python3
"""
KSL AI Model Control Review → PDF Generator
-Generator
- Fixed title: "KSL AI Model Control Review"
- Shows original risk scores (1/2/3/4)
- Shows Total Risk Score per artifact
- 100% syntax-error-free
"""

import json
import sys
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)


def load_json(filepath: str) -> dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_styles():
    styles = getSampleStyleSheet()

    # Main title
    styles.add(ParagraphStyle(
        name='DocTitle',
        parent=styles['Title'],
        fontSize=22,
        spaceAfter=30,
        textColor=HexColor('#1a365d'),
        alignment=1,
        fontName='Helvetica-Bold'
    ))

    # Section headers
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading1'],
        fontSize=16,
        spaceBefore=20,
        spaceAfter=12,
        textColor=HexColor('#2c5282'),
        keepWithNext=True
    ))

    # Per-item header (e.g., "1. pytorch-2.9.1-ngc")
    styles.add(ParagraphStyle(
        name='ItemHeader',
        parent=styles['Heading2'],        # ← Fixed: was missing closing parenthesis!
        fontSize=13,
        spaceBefore=18,
        spaceAfter=8,
        textColor=HexColor('#3182ce'),
        keepWithNext=True
    ))

    # Table text
    styles.add(ParagraphStyle(
        name='TableText',
        parent=styles['Normal'],
        fontSize=10,
        leading=12
    ))

    # Total risk highlight
    styles.add(ParagraphStyle(
        name='TotalRisk',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica-Bold',
        textColor=HexColor('#b91c1c'),   # red-700
        spaceBefore=10,
        spaceAfter=15,
        leftIndent=5
    ))

    return styles


def calculate_total_risk(checks: list) -> int:
    total = 0
    for check in checks:
        score = check.get("score")
        if isinstance(score, (int, float)):
            total += int(score)
    return total


def create_check_table(checks: list, styles) -> Table:
    data = [["Check", "Risk Score", "Notes"]]

    for check in checks:
        name = check.get("name", "—")
        score = check.get("score", "—")
        notes = (check.get("notes") or "").strip().replace('\n', '<br/>')

        score_display = f"<b>{score}</b>" if score != "—" else "—"

        data.append([
            Paragraph(name, styles['TableText']),
            Paragraph(score_display, styles['TableText']),
            Paragraph(notes if notes else "—", styles['TableText'])
        ])

    table = Table(data, colWidths=[2.3*inch, 0.8*inch, 3.9*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c5282')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f8fafc')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (1, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (1, 1), (-1, -1), 6),
    ]))
    return table


# (rest of the functions unchanged – metadata table, add_component_section, etc.)

# ... [same as previous working version] ...

# Full script continues below (only showing the corrected part above + rest unchanged)

# I'll paste the complete corrected script to avoid any confusion:

# COMPLETE FIXED SCRIPT (copy
#!/usr/bin/env python3
"""
KSL AI Model Control Review → PDF Generator
- Fixed title
- Original risk scores
- Total Risk Score per artifact
- No syntax errors
"""

import json
import sys
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)


def load_json(filepath: str) -> dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='DocTitle',
        parent=styles['Title'],
        fontSize=22,
        spaceAfter=30,
        textColor=HexColor('#1a365d'),
        alignment=1,
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading1'],
        fontSize=16,
        spaceBefore=20,
        spaceAfter=12,
        textColor=HexColor('#2c5282'),
        keepWithNext=True
    ))

    # FIXED LINE
    styles.add(ParagraphStyle(
        name='ItemHeader',
        parent=styles['Heading2'],
        fontSize=13,
        spaceBefore=18,
        spaceAfter=8,
        textColor=HexColor('#3182ce'),
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        name='TableText',
        parent=styles['Normal'],
        fontSize=10,
        leading=12
    ))

    styles.add(ParagraphStyle(
        name='TotalRisk',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica-Bold',
        textColor=HexColor('#b91c1c'),
        spaceBefore=10,
        spaceAfter=15,
        leftIndent=5
    ))

    return styles


def calculate_total_risk(checks: list) -> int:
    total = 0
    for check in checks:
        score = check.get("score")
        if isinstance(score, (int, float)):
            total += int(score)
    return total


def create_check_table(checks: list, styles) -> Table:
    data = [["Check", "Risk Score", "Notes"]]

    for check in checks:
        name = check.get("name", "—")
        score = check.get("score", "—")
        notes = (check.get("notes") or "").strip().replace('\n', '<br/>')
        score_display = f"<b>{score}</b>" if score != "—" else "—"

        data.append([
            Paragraph(name, styles['TableText']),
            Paragraph(score_display, styles['TableText']),
            Paragraph(notes if notes else "—", styles['TableText'])
        ])

    table = Table(data, colWidths=[2.3*inch, 0.8*inch, 3.9*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c5282')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f8fafc')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (1, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (1, 1), (-1, -1), 6),
    ]))
    return table


def create_metadata_table(metadata: dict, styles) -> Table:
    fields = {
        'proposal_title': 'Proposal Title',
        'principal_investigator': 'Principal Investigator',
        'proposal_date': 'Proposal Date',
        'reviewer_name': 'Reviewer Name',
        'reviewer_id': 'Reviewer ID',
        'aimcr_date': 'AIMCR Date',
        'project_id': 'Project ID'
    }

    data = []
    for key, label in fields.items():
        value = metadata.get(key, 'N/A')
        data.append([
            Paragraph(f"<b>{label}:</b>", styles['TableText']),
            Paragraph(str(value), styles['TableText'])
        ])

    table = Table(data, colWidths=[2.4*inch, 4.3*inch])
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cbd5e0')),
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#edf2f7')),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return table


def add_component_section(story, title: str, items: list, styles):
    story.append(Paragraph(title, styles['SectionHeader']))

    if not items:
        story.append(Paragraph("No items in this category.", styles['TableText']))
        story.append(Spacer(1, 20))
        return

    for idx, item in enumerate(items, 1):
        name = item.get("name", "").strip() or "(Unnamed component)"
        story.append(Paragraph(f"{idx}. {name}", styles['ItemHeader']))

        checks = item.get("checks", [])
        if checks:
            story.append(KeepTogether(create_check_table(checks, styles)))
            total = calculate_total_risk(checks)
            story.append(Paragraph(f"Total Risk Score: {total}", styles['TotalRisk']))
        else:
            story.append(Paragraph("No checks recorded.", styles['TableText']))

        story.append(Spacer(1, 25))


def json_to_pdf(json_filepath: str, output_filepath: str = None) -> str:
    data = load_json(json_filepath)
    output_filepath = output_filepath or json_filepath.rsplit('.', 1)[0] + ".pdf"

    doc = SimpleDocTemplate(
        output_filepath,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.8*inch,
        bottomMargin=0.8*inch
    )

    styles = create_styles()
    story = []

    story.append(Paragraph("KSL AI Model Control Review", styles['DocTitle']))
    story.append(HRFlowable(width="100%", thickness=4, color=HexColor('#2c5282'), spaceAfter=30))

    story.append(Paragraph("Review Information", styles['SectionHeader']))
    story.append(create_metadata_table(data.get("metadata", {}), styles))
    story.append(Spacer(1, 30))

    add_component_section(story, "Third-Party Software", data.get("third_party_software", []), styles)
    story.append(PageBreak())

    add_component_section(story, "Source Code", data.get("source_code", []), styles)
    story.append(PageBreak())

    add_component_section(story, "Datasets / User Files", data.get("datasets_user_files", []), styles)
    story.append(PageBreak())

    add_component_section(story, "AI Models", data.get("models", []), styles)

    story.append(Paragraph("General Observations", styles['SectionHeader']))
    story.append(Paragraph(data.get("observations", "").strip() or "None recorded.", styles['TableText']))
    story.append(Spacer(1, 20))

    story.append(Paragraph("Final Recommendation", styles['SectionHeader']))
    story.append(Paragraph(data.get("recommendation", "").strip() or "Not provided.", styles['TableText']))

    story.append(Spacer(1, 40))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#cbd5e0')))
    story.append(Paragraph(
        f"Report generated on {datetime.now():%Y-%m-%d %H:%M:%S}",
        ParagraphStyle(name='Footer', alignment=1, fontSize=9, textColor=HexColor('#718096'))
    ))

    doc.build(story)
    return output_filepath


def main():
    if len(sys.argv) < 2:
        print("Usage: python json_to_pdf.py <input.json> [output.pdf]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        result = json_to_pdf(input_file, output_file)
        print(f"PDF created: {result}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()