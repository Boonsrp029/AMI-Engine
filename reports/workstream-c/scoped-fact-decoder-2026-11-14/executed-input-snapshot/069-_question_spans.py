"""Private question-offset wire. Membership is structural, not gap semantics."""
import hashlib
import re
from typing import Literal, Union

from pydantic import Field, create_model, field_validator, model_validator
from ..schemas import StrictModel
from .._source_selection import SourceSelection, WIRE_VERSION as SOURCE_WIRE_VERSION


QUESTION_WIRE_VERSION = "cq-question-span-v1"
MAX_HINTS = 32


def check_question(question):
    if not isinstance(question,str) or not question.strip() or len(question)>1200:
        raise ValueError("Question spans require nonempty text of at most 1200 Unicode code points")


def question_span_context(question):
    """Sparse hints never restrict the full representable character-offset range."""
    check_question(question)
    words=list(re.finditer(r"\S+",question))
    if len(words)>MAX_HINTS:
        indexes=[round(i*(len(words)-1)/(MAX_HINTS-1)) for i in range(MAX_HINTS)]
    else:indexes=list(range(len(words)))
    return {"offset_unit":"Python Unicode code point; start inclusive, end exclusive",
        "length":len(question),"hints":[[words[i].start(),words[i].end(),words[i].group()] for i in indexes],
        "hints_sampled":len(words)>MAX_HINTS,"valid_offsets":"all positions; hints are optional aids"}


class QuestionSpan(StrictModel):
    start: int = Field(strict=True,ge=0)
    end: int = Field(strict=True,ge=1)

    @model_validator(mode="after")
    def ordered(self):
        if self.end<=self.start:
            raise ValueError("Question span must be nonempty and ordered")
        return self


class QuestionComponent(StrictModel):
    component_id: str
    status: Literal["supported","partial","missing","conflicting"]
    evidence: list[str]
    gap: QuestionSpan | None
    measure: Literal[""] = ""
    scenario: Literal[""] = ""
    kind: Literal["unknown"] = "unknown"

    @field_validator("evidence")
    @classmethod
    def unique(cls,value):
        if len(value)!=len(set(value)):
            raise ValueError("Selected evidence span IDs must be distinct")
        return value


def question_selection_schema(catalog,question,requests,geography_type):
    check_question(question)
    if not 1<=len(requests)<=5 or len({r["component_id"] for r in requests})!=len(requests):
        raise ValueError("Question selection needs one to five distinct canonical requests")
    span=create_model("BoundedQuestionSpan",__base__=QuestionSpan,
        start=(int,Field(strict=True,ge=0,le=len(question)-1)),
        end=(int,Field(strict=True,ge=1,le=len(question))))
    evidence_type=list[Literal[tuple(catalog)]] if catalog else list[str]
    slots=[]
    for index,request in enumerate(requests):
        if not request.get("question_anchor") or request["question_anchor"] not in question:
            raise ValueError("Canonical request anchor must occur verbatim in question")
        fields={"component_id":(Literal[request["component_id"]],...)}
        missing=create_model(f"MissingRequestSlot{index}",__base__=QuestionComponent,**fields,
            status=(Literal["missing"],...),evidence=(list[str],Field(...,max_length=0)),gap=(Literal[None],...))
        variants=[]
        if catalog:
            nonempty=(evidence_type,Field(...,min_length=1,max_length=5,json_schema_extra={"uniqueItems":True}))
            variants.extend([
                create_model(f"SupportedRequestSlot{index}",__base__=QuestionComponent,**fields,
                    status=(Literal["supported"],...),evidence=nonempty,gap=(Literal[None],...)),
                create_model(f"PartialRequestSlot{index}",__base__=QuestionComponent,**fields,
                    status=(Literal["partial"],...),evidence=nonempty,gap=(span,...))])
            if len(catalog)>=2:
                variants.append(create_model(f"ConflictingRequestSlot{index}",__base__=QuestionComponent,**fields,
                    status=(Literal["conflicting"],...),
                    evidence=(evidence_type,Field(...,min_length=2,max_length=5,json_schema_extra={"uniqueItems":True})),
                    gap=(span|None,...)))
        variants.append(missing)
        slots.append(Union[tuple(variants)] if len(variants)>1 else variants[0])
    return create_model("ConcurrentQuestionSelection",__base__=StrictModel,
        wire_version=(Literal[QUESTION_WIRE_VERSION],...),components=(tuple[tuple(slots)],...),
        geography=(geography_type,...),period=(Literal[""],""))


def resolve_question_selection(schema,value,question,requests):
    """Resolve explicit positions only; never infer missing spans or repair IDs."""
    parsed=schema.model_validate(value).model_dump()
    known={r["component_id"]:r["question_anchor"] for r in requests}
    resolved={**parsed,"wire_version":SOURCE_WIRE_VERSION,"components":[]}
    trace=[]
    for component in parsed["components"]:
        gap=component["gap"]
        if component["status"]=="missing":
            anchor=known[component["component_id"]]
            basis="canonical_missing_request"
        elif gap is None:
            anchor="";basis="explicit_null"
        else:
            anchor=question[gap["start"]:gap["end"]]
            if not anchor.strip():
                raise ValueError("Question span cannot contain only whitespace")
            basis="explicit_question_offsets"
        resolved["components"].append({**{k:v for k,v in component.items() if k!="gap"},"gap_anchor":anchor})
        trace.append({"component_id":component["component_id"],"status":component["status"],
            "selected_gap":gap,"resolved_gap_anchor":anchor,"basis":basis,
            "question_sha256":hashlib.sha256(question.encode("utf-8")).hexdigest(),
            "membership_proven":True,"semantic_missingness_proven":False})
    # Retain all existing state/identity checks before quotation/source resolution.
    return SourceSelection.model_validate(resolved).model_dump(),trace
