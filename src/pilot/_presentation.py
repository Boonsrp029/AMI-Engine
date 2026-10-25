"""Reader-facing labels; source indexes stay zero-based."""


def pdf_page_label(index):
    return f"PDF page {index + 1}" if type(index) is int and index >= 0 else "PDF page unavailable"
