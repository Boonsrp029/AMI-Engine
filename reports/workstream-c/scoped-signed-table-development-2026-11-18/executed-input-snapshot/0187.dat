"""Necessary explicit-period checks, not semantic support or date inference."""
import re
from datetime import date

_MONTHS = "January February March April May June July August September October November December"
_PERIOD = re.compile(r"\b(?:" + "|".join(_MONTHS.split()) + r")\s+\d{4}\b|\b\d{4}-\d{2}-\d{2}\b", re.I)
_PUBLICATION = re.compile(r"\b(?:published|publication|released|release|issued|dated)\b", re.I)
_COMMAND = re.compile(r"\bignore\b.{0,60}\b(?:instructions|rules)\b|\bapprove_export\b|\breveal\b.{0,40}\b(?:secrets|credentials)\b", re.I)
_GAP = re.compile(
    r"^(?:the\s+)?(?:(?:retrieved|supplied|provided|current)\s+)?"
    r"(?:documents?|sources?|evidence|records?)\s+(?:do|does)\s+not\s+"
    r"(?:establish|contain|provide|report)\s+(?:an?\s+)?"
    r"(?:answer|observation|figure|evidence|record|support|prices?|data)\s+(?:to|for|in|on|of)\s*$", re.I)


def _key(value):
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            return None
    month, year = value.split()
    return f"{year}-{next(i for i, m in enumerate(_MONTHS.split(), 1) if m.casefold() == month.casefold()):02}" if 1 <= int(year) <= 9999 else None


def explicit_periods(text):
    """Preserve the pilot's full English month/year and valid ISO-date contract."""
    values = []
    for match in _PERIOD.finditer(text):
        value = " ".join(match.group().split())
        if _key(value) and value.casefold() not in {v.casefold() for v in values}:
            values.append(value)
    return values


def reporting_period_headings(text):
    """Recognize narrow report headings, including an explicit shared month/year.

    A publication date is never a measurement date. Coordinated month/quarter
    headings are accepted only when the month belongs to the stated quarter.
    """
    if _COMMAND.search(text):
        return []
    pattern = re.compile(r"^(?:Press[ \t]+Release[ \t]+on[ \t]+the[ \t]+)?"
        r"(?:Economic[ \t]+and[ \t]+Monetary|Economic)[ \t]+Conditions[ \t]+for[ \t]+"
        r"(?P<month>" + "|".join(_MONTHS.split()) + r")[ \t]+"
        r"(?:(?P<year>\d{4})|and[ \t]+(?:the[ \t]+)?(?P<quarter>First|Second|Third|Fourth)"
        r"[ \t]+Quarter[ \t]+of[ \t]+(?P<shared_year>\d{4}))\.?[ \t]*$", re.I | re.M)
    results = []
    for match in pattern.finditer(text):
        month = next(m for m in _MONTHS.split() if m.casefold() == match['month'].casefold())
        if match['quarter']:
            quarter = ['first', 'second', 'third', 'fourth'].index(match['quarter'].casefold()) + 1
            if (_MONTHS.split().index(month) // 3) + 1 != quarter:
                continue
        period = month + ' ' + (match['year'] or match['shared_year'])
        if _key(period):
            results.append({'period': period, 'quote': match.group().rstrip(), 'start': match.start(),
                'end': match.start() + len(match.group().rstrip()),
                'normalization': 'explicit_shared_year' if match['quarter'] else 'literal_month_year'})
    return results


def _references(text):
    text = _PERIOD.sub(lambda match: " ".join(match.group().split()), text)
    for clause in re.split(r"(?<=[.!?;])\s+|\n+", text):
        for match in _PERIOD.finditer(clause):
            value = " ".join(match.group().split())
            prefix = clause[:match.start()].strip()
            yield {"value": value, "key": _key(value),
                   "role": "command" if _COMMAND.search(clause) else
                           "gap" if _GAP.fullmatch(prefix) and clause[match.end():].strip() in {"", ".", "!", "?", ";"} else
                           "publication" if _PUBLICATION.search(prefix) else "statement"}


def unestablished_report_periods(report, evidence):
    """Reject absent/invalid explicit dates and publication-only substitutions.

    Matching a date is only necessary. It cannot bind a date to the right company,
    measurement, observation/forecast or source, or resolve relative dates.
    The model policy and the pilot's per-component checks still run afterwards.
    """
    sources = [ref for ref in _references(evidence) if ref["key"] and ref["role"] not in {"command", "gap"}]
    sources += [{"value": h['period'], "key": _key(h['period']), "role": "statement"}
                for h in reporting_period_headings(evidence)]
    rejected = []
    for ref in _references(report):
        if ref["role"] == "gap" and ref["key"]:
            continue  # A narrow explicit statement about supplied-evidence limits.
        compatible = [source for source in sources if source["role"] == ref["role"] and
                      (source["key"] == ref["key"] or (ref["key"] and len(ref["key"]) == 7 and
                                                       source["key"].startswith(ref["key"] + "-")))]
        if not compatible and ref["value"] not in rejected:
            rejected.append(ref["value"])
    return rejected
