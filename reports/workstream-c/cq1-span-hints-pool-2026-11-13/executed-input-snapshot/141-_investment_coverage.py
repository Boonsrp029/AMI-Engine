"""Conservative literal category retention, not semantic completeness scoring."""
import re

from src.pilot._scope import explicit_periods
from src.pilot._topics import _primary_subject
from src.utils._periods import _COMMAND


_REQUEST = re.compile(r'\b(?:which|what)\s+(?:investment\s+)?categories\b', re.I)
_CATEGORY = re.compile(
    r'\binvestment in\s+[^.!?;\n]{1,100}?\s+'
    r'(?:(?:also|slightly|strongly|notably)\s+)*'
    r'(?:increased|decreased|rose|fell|grew|expanded|declined|contracted|remained stable)\b'
    r'[^.!?;\n]*', re.I)
_STOP = {'the', 'a', 'an', 'in', 'and', 'or', 'of', 'to', 'by', 'as', 'with', 'was', 'were'}


def _terms(text):
    # Strict lexical retention can fall back on harmless paraphrases. It cannot
    # prove entailment, category identity, negation, or causal correctness.
    return {word for word in re.findall(r'[^\W\d_]+', text.casefold()) if word not in _STOP}


def missing_investment_categories(text, component, question, period=''):
    """Check only explicit clauses within a uniquely qualified investment quote.

    Use selected evidence only. Mixed subjects, ambiguous antecedents and periods
    outside the established literal period stay outside this bounded grammar.
    Existing upstream and final scope checks remain required.
    """
    if not _REQUEST.search(question):
        return False
    wanted = _primary_subject(component.question_anchor) or _primary_subject(question)
    if wanted not in {'private_investment', 'public_investment'}:
        return False
    actual = _terms(text)
    for evidence in component.evidence:
        quote = evidence.quote
        if _primary_subject(quote) != wanted:
            continue
        periods = explicit_periods(quote)
        if periods and (not period or period.casefold() not in {p.casefold() for p in periods}):
            continue
        if _COMMAND.search(quote):
            raise ValueError('Selected investment evidence contains instruction-like source content')
        for match in _CATEGORY.finditer(quote):
            if not _terms(match.group()).issubset(actual):
                return True
    return False
