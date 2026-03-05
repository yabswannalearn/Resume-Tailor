import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    HRFlowable, Table, TableStyle
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER


# ─── Constants ────────────────────────────────────────────
OUTPUT_PATH = "output/tailored_resume.pdf"
MARGIN = 15 * mm
DARK = colors.HexColor("#1a1a1a")
BLUE = colors.HexColor("#1a0dab")  # link color


# ─── Styles ───────────────────────────────────────────────
def get_styles():
    return {
        "name": ParagraphStyle(
            "name",
            fontName="Times-Bold",
            fontSize=28,
            textColor=DARK,
            spaceAfter=2,
        ),
        "contact": ParagraphStyle(
            "contact",
            fontName="Times-Roman",
            fontSize=9,
            textColor=DARK,
            spaceAfter=4,
        ),
        "summary": ParagraphStyle(
            "summary",
            fontName="Times-Roman",
            fontSize=9.5,
            textColor=DARK,
            spaceAfter=4,
            leading=14,
        ),
        "portfolio": ParagraphStyle(
            "portfolio",
            fontName="Times-Bold",
            fontSize=9.5,
            textColor=DARK,
            spaceAfter=6,
        ),
        "section_title": ParagraphStyle(
            "section_title",
            fontName="Times-Bold",
            fontSize=16,
            textColor=DARK,
            spaceBefore=8,
            spaceAfter=2,
        ),
        "company": ParagraphStyle(
            "company",
            fontName="Times-Bold",
            fontSize=9.5,
            textColor=DARK,
            spaceAfter=0,
        ),
        "role": ParagraphStyle(
            "role",
            fontName="Times-BoldItalic",
            fontSize=9.5,
            textColor=DARK,
            spaceAfter=2,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName="Times-Roman",
            fontSize=9.5,
            textColor=DARK,
            leftIndent=12,
            spaceAfter=2,
            leading=13,
        ),
        "project_title": ParagraphStyle(
            "project_title",
            fontName="Times-Bold",
            fontSize=9.5,
            textColor=DARK,
            spaceAfter=1,
        ),
        "normal": ParagraphStyle(
            "normal",
            fontName="Times-Roman",
            fontSize=9.5,
            textColor=DARK,
            spaceAfter=2,
            leading=13,
        ),
        "cert": ParagraphStyle(
            "cert",
            fontName="Times-Roman",
            fontSize=9.5,
            textColor=DARK,
            spaceAfter=1,
        ),
    }

# ─── Helpers ──────────────────────────────────────────────
def divider():
    """A full-width horizontal line, just like in your CV."""
    return HRFlowable(
        width="100%",
        thickness=0.8,
        color=DARK,
        spaceAfter=4,
        spaceBefore=2,
    )


def two_col(left_text, right_text, styles, left_style="company", right_style="company"):
    """
    Renders two items side by side — left aligned and right aligned.
    Used for company/location and role/date rows.
    """
    left = Paragraph(left_text, styles[left_style])
    right = Paragraph(right_text, styles[right_style])

    table = Table(
        [[left, right]],
        colWidths=["70%", "30%"]
    )
    table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return table


# ─── Section Builders ─────────────────────────────────────
def build_header(resume: dict, styles: dict) -> list:
    elements = []

    personal = resume.get("personal", {})

    # Big name
    elements.append(Paragraph(personal.get("name", ""), styles["name"]))

    # Contact line
    contact_line = (
        f'{personal.get("email", "")} | '
        f'{personal.get("phone", "")} | '
        f'<a href="{personal.get("linkedin", "")}" color="#1a0dab">'
        f'{personal.get("linkedin", "").replace("https://", "")}</a>'
    )
    elements.append(Paragraph(contact_line, styles["contact"]))

    # Summary
    elements.append(Paragraph(resume.get("summary", ""), styles["summary"]))

    # Portfolio
    portfolio_url = personal.get("portfolio", "")
    elements.append(Paragraph(
        f'<b>DIGITAL PORTFOLIO:</b> '
        f'<a href="{portfolio_url}" color="#1a0dab">{portfolio_url}</a>',
        styles["portfolio"]
    ))

    return elements


def build_experience(resume: dict, styles: dict) -> list:
    elements = []

    elements.append(Paragraph("Experience", styles["section_title"]))
    elements.append(divider())

    for job in resume.get("experience", []):
        # Company name | Location
        elements.append(two_col(
            job.get("company", ""),
            job.get("location", ""),
            styles
        ))
        # Role | Duration
        elements.append(two_col(
            job.get("role", ""),
            job.get("duration", ""),
            styles,
            left_style="role",
            right_style="normal"
        ))

        for bullet in job.get("bullets", []):
            elements.append(Paragraph(f"• {bullet}", styles["bullet"]))

        elements.append(Spacer(1, 4))

    return elements


def build_skills(resume: dict, styles: dict) -> list:
    elements = []

    elements.append(Paragraph("Technical Skills", styles["section_title"]))
    elements.append(divider())

    # Group skills into categories of ~5 each
    all_skills = resume.get("skills", [])
    chunk_size = 6
    chunks = [all_skills[i:i+chunk_size] for i in range(0, len(all_skills), chunk_size)]

    for chunk in chunks:
        line = ", ".join(chunk)
        elements.append(Paragraph(f"• {line}", styles["bullet"]))

    return elements


def build_projects(resume: dict, styles: dict) -> list:
    elements = []

    elements.append(Paragraph("Projects", styles["section_title"]))
    elements.append(divider())

    for project in resume.get("projects", []):
        elements.append(Paragraph(
            f'<b>{project.get("name", "")}</b>',
            styles["project_title"]
        ))
        elements.append(Paragraph(
            f'• {project.get("description", "")}',
            styles["bullet"]
        ))
        elements.append(Spacer(1, 3))

    return elements


def build_education(resume: dict, styles: dict) -> list:
    elements = []

    elements.append(Paragraph("Education", styles["section_title"]))
    elements.append(divider())

    for edu in resume.get("education", []):
        elements.append(two_col(
            f'<b>{edu.get("institution", "")}</b>',
            edu.get("location", edu.get("duration", "")),
            styles
        ))
        elements.append(Paragraph(
            f'<i>{edu.get("degree", "")}</i>',
            styles["normal"]
        ))
        if edu.get("achievements"):
            elements.append(Paragraph(
                edu.get("achievements", ""),
                styles["normal"]
            ))
        elements.append(Spacer(1, 4))

    return elements


def build_certifications(resume: dict, styles: dict) -> list:
    elements = []

    elements.append(Paragraph("Certifications", styles["section_title"]))
    elements.append(divider())

    certs = resume.get("certifications", [])

    # Split into 3 columns just like your original CV
    col_size = (len(certs) + 2) // 3
    cols = [certs[i:i+col_size] for i in range(0, len(certs), col_size)]

    # Pad columns to same length
    max_len = max(len(c) for c in cols)
    for col in cols:
        while len(col) < max_len:
            col.append("")

    rows = []
    for i in range(max_len):
        row = [Paragraph(f"• {cols[j][i]}" if i < len(cols[j]) else "", styles["cert"])
               for j in range(len(cols))]
        rows.append(row)

    table = Table(rows, colWidths=["33%", "33%", "34%"])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    elements.append(table)

    return elements


# ─── Main Function ────────────────────────────────────────
def generate(resume: dict) -> str:
    """
    Main function.
    Takes the tailored resume dict and generates a PDF.
    Returns the output file path.
    """
    os.makedirs("output", exist_ok=True)

    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )

    styles = get_styles()
    story = []

    # Build each section in order
    story += build_header(resume, styles)
    story += build_experience(resume, styles)
    story += build_skills(resume, styles)
    story += build_projects(resume, styles)
    story += build_education(resume, styles)
    story += build_certifications(resume, styles)

    doc.build(story)

    return OUTPUT_PATH