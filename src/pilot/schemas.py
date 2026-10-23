"""Public contracts for the local pilot (version 1)."""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ResearchRequest(StrictModel):
    query: str = Field(min_length=3, max_length=1200)
    request_key: str = Field(min_length=8, max_length=100, pattern=r"^[\w-]+$")

    @field_validator("query")
    @classmethod
    def public_material_only(cls, value):
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Enter a research question")
        if re.search(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b|\b\d{13,19}\b", value):
            raise ValueError("This public-data pilot does not accept email addresses or account/identity numbers")
        return value


class Claim(StrictModel):
    text: str = Field(min_length=1, max_length=800)
    source_ids: list[str] = Field(min_length=1, max_length=5)


class Draft(StrictModel):
    title: str = Field(min_length=1, max_length=160)
    claims: list[Claim] = Field(default_factory=list, max_length=5)
    warnings: list[str] = Field(default_factory=list, max_length=10)


class EditRequest(StrictModel):
    revision: int = Field(ge=1)
    draft: Draft


class ReviewRequest(StrictModel):
    revision: int = Field(ge=1)
    decision: Literal["approve", "reject"]
    reviewer: str = Field(min_length=1, max_length=80)
    support_confirmed: bool = False
    note: str = Field(default="", max_length=2000)
    task_seconds: float | None = Field(default=None, ge=0)
    manual_seconds: float | None = Field(default=None, ge=0)
    usefulness: int | None = Field(default=None, ge=1, le=5)


class SearchArguments(StrictModel):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=5, ge=1, le=5)


class InspectArguments(StrictModel):
    source_id: str = Field(min_length=1, max_length=200)


def validate_citations(draft: dict, sources: dict) -> dict:
    value = Draft.model_validate(draft).model_dump()
    for claim in value["claims"]:
        if any(source_id not in sources for source_id in claim["source_ids"]):
            raise ValueError("Draft contains a citation that was not retrieved")
    return value
