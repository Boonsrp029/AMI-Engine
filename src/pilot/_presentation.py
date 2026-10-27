"""Reader-facing labels; source indexes stay zero-based."""

import re


def without_bullet_glyphs(value):
    """Remove decorative source bullets from prose, preserving words and units."""
    if not re.search(r"[•▪▫‣⁃●○◦]", value):
        return value
    return re.sub(r"\s*[•▪▫‣⁃●○◦]+\s*", " ", value).strip()


def pdf_page_label(index):
    return f"PDF page {index + 1}" if type(index) is int and index >= 0 else "PDF page unavailable"
