"""Canonical verbatim request slots, without inferring entities or evidence."""
import re


def requested_components(question):
    text = question.strip()
    if not text:
        raise ValueError("A nonempty question is required")
    compound = re.search(r"^How did\s+(?P<subjects>.+?)\s+change\b.+?\bwhich activities supported them\??$", text, re.I)
    if compound and not any(c in compound["subjects"] for c in "\"'()"):
        subjects = re.split(r"\s+and\s+", compound["subjects"], flags=re.I)
        if len(subjects) == 2:
            return [{"component_id": f"r{i}", "question_anchor": subject,
                "instruction": "Answer both the change and all requested supporting activities for this subject, using the original question's scope."}
                for i, subject in enumerate(subjects, 1)]
    # Split only explicit new question clauses. A comma before the first question
    # belongs to its introductory scope, not an independent answer component.
    interrogative = r"(?:what|which|how|why|when|where|who|did|does|do|is|are|was|were|has|have|can|could)\b"
    separator = re.compile(r",?\s+\b(?:and|but)\s+(?=" + interrogative + r")"
        r"|(?<=\?)\s+(?=" + interrogative + r")|,\s+(?=" + interrogative + r")", re.I)
    protected = [m.span() for m in re.finditer(r'"[^"\n]*"|(?<!\w)\'[^\'\n]*\'(?!\w)|\([^()]*\)', text)]
    parts, start = [], 0
    for match in separator.finditer(text):
        if any(left <= match.start() < right for left, right in protected):
            continue
        left = text[start:match.start()].strip(" ,")
        if not re.search(r"\b" + interrogative, left, re.I):
            continue
        parts.append(left)
        start = match.end()
    parts.append(text[start:].strip(" ,"))
    if len(parts) > 5:
        parts = [text]  # Keep the whole request rather than silently dropping clauses.
    return [{"component_id": f"r{index}", "question_anchor": part} for index, part in enumerate(parts, 1)]
