from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from dataset import SCHEMA_VERSION, USAGE_YEARS


class FromStep(BaseModel):
    lang: str
    form: Optional[str] = None
    year: Optional[int] = None


class Root(BaseModel):
    id: str
    form: str
    gloss: str = ""


class Word(BaseModel):
    w: str
    x: float
    y: float
    z: float
    band: float
    gloss: str
    ex: str
    from_: list[FromStep] = Field(default_factory=list, alias="from")
    root: Optional[Root] = None
    usage: list[float] = Field(default_factory=list)
    usageNote: Optional[str] = None
    usageMix: Optional[list[bool]] = None
    usageMixTag: Optional[str] = None
    sense: Optional[str] = None

    model_config = {"populate_by_name": True}

    @field_validator("usage")
    @classmethod
    def six_samples(cls, v: list[float]) -> list[float]:
        if v and len(v) != len(USAGE_YEARS):
            raise ValueError(f"usage must have {len(USAGE_YEARS)} samples")
        return v


class Family(BaseModel):
    hub: str
    answer: list[str]
    prompt: str
    insight: str
    words: list[Word]


class Dataset(BaseModel):
    schema_version: str = SCHEMA_VERSION
    usage_years: tuple[int, ...] = USAGE_YEARS
    families: list[Family]


class Evidence(BaseModel):
    source: str
    url: str = ""
    quote: str = ""


class EtymologyExtract(BaseModel):
    from_steps: list[FromStep] = Field(default_factory=list)
    root: Optional[Root] = None
    quotes: list[str] = Field(default_factory=list)
    year_grounded: bool = False
    notes: str = ""


class SenseFlag(BaseModel):
    pollutes_curve: bool
    other_senses: list[str] = Field(default_factory=list)
    usageNote: Optional[str] = None
    reason: str = ""


class GlossCandidate(BaseModel):
    gloss: str
    why: str = ""


class GlossReview(BaseModel):
    swap_failures: list[str] = Field(default_factory=list)
    candidates: dict[str, list[GlossCandidate]] = Field(default_factory=dict)


class RankSuggestion(BaseModel):
    axis: Literal["connotation", "intensity", "formality"]
    low_label: str
    high_label: str
    order_low_to_high: list[str]
    note: str = ""
    suggested_xyz: dict[str, dict[str, float]] = Field(default_factory=dict)


class WordProposal(BaseModel):
    word: str
    hub: str
    status: Literal["pending", "accepted", "rejected"] = "pending"
    evidence: list[Evidence] = Field(default_factory=list)
    proposed_from: Optional[list[FromStep]] = None
    proposed_root: Optional[Root] = None
    proposed_usage: Optional[list[float]] = None
    proposed_usageNote: Optional[str] = None
    proposed_gloss: Optional[str] = None
    proposed_ex: Optional[str] = None
    rank_suggestions: list[RankSuggestion] = Field(default_factory=list)
    gloss_candidates: list[GlossCandidate] = Field(default_factory=list)
    diffs: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    wiki_roots: list[str] = Field(default_factory=list)


class RootLink(BaseModel):
    proposed_id: str
    form: str
    gloss: str = ""
    words: list[str]
    hubs: list[str]
    evidence: list[Evidence] = Field(default_factory=list)
    reason: str = ""


class RootLinkProposal(BaseModel):
    status: Literal["pending", "accepted", "rejected"] = "pending"
    note: str = ""
    links: list[RootLink] = Field(default_factory=list)
