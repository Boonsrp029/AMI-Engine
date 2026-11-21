"""Public contracts for the local pilot (version 1)."""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.pilot._presentation import without_bullet_glyphs
from src.pilot.subtasks.contracts import Plan, Subtask


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


class SubtaskResearchRequest(ResearchRequest):
    """Explicit, bounded plan for the opt-in workflow; no automatic planner."""

    subtasks: tuple[Subtask, ...] = Field(min_length=1, max_length=5)
    retrieval_concurrency: int = Field(default=2, ge=1, le=2)
    deadline_seconds: float = Field(default=180.0, gt=0, le=180, allow_inf_nan=False)

    @field_validator("subtasks", mode="before")
    @classmethod
    def json_sequences(cls, value):
        # The internal contract is strict and immutable; adapt JSON arrays to
        # tuples at this HTTP boundary before validating each Subtask.
        if not isinstance(value, (list, tuple)):
            return value
        normalized = []
        for raw in value:
            if not isinstance(raw, dict):
                normalized.append(raw)
                continue
            task = dict(raw)
            for field in ("source_ids", "dependencies"):
                if isinstance(task.get(field), list):
                    task[field] = tuple(task[field])
            normalized.append(task)
        return tuple(normalized)

    def make_plan(self, corpus_sha256: str) -> Plan:
        return Plan(query=self.query, corpus_sha256=corpus_sha256,
                    subtasks=self.subtasks, retrieval_concurrency=self.retrieval_concurrency,
                    deadline_seconds=self.deadline_seconds)


class Claim(StrictModel):
    text: str = Field(min_length=1, max_length=800)
    source_ids: list[str] = Field(min_length=1, max_length=5)

    @field_validator("text")
    @classmethod
    def prose_without_source_bullets(cls, value):
        value = without_bullet_glyphs(value)
        if not value.strip():
            raise ValueError("Claim must contain prose, not only bullet characters")
        return value


class Draft(StrictModel):
    title: str = Field(min_length=1, max_length=160)
    claims: list[Claim] = Field(default_factory=list, max_length=5)
    warnings: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("title")
    @classmethod
    def title_without_source_bullets(cls, value):
        value = without_bullet_glyphs(value)
        if not value.strip():
            raise ValueError("Brief title must contain text")
        return value

    @field_validator("warnings")
    @classmethod
    def warnings_without_source_bullets(cls, values):
        return [cleaned for value in values if (cleaned := without_bullet_glyphs(value)).strip()]


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
