from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv

from dataset.models import EtymologyExtract, GlossReview, RankSuggestion, SenseFlag

load_dotenv()


def llm_enabled() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY")) and os.environ.get("DATASET_NO_LLM") != "1"


def _model(name: str = "claude-sonnet-4-5"):
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(model=name, temperature=0)


def extract_etymology_llm(word: str, wiki_quote: str, ety_quote: str) -> Optional[EtymologyExtract]:
    if not llm_enabled():
        return None
    llm = _model().with_structured_output(EtymologyExtract)
    return llm.invoke(
        [
            (
                "system",
                "Extract an oldest-to-English etymology trail. Use ONLY forms, languages, "
                "and years that appear in the quoted sources. If a year is not in a quote, "
                "omit it. year_grounded is true only if every year is in the quotes. "
                "Fail closed: empty from_steps is better than invention.",
            ),
            (
                "human",
                f"Word: {word}\n\nWiktionary:\n{wiki_quote}\n\nEtymonline:\n{ety_quote}",
            ),
        ]
    )


def sense_flag_llm(word: str, family_hub: str, gloss: str, quotes: str) -> Optional[SenseFlag]:
    if not llm_enabled():
        return None
    llm = _model().with_structured_output(SenseFlag)
    return llm.invoke(
        [
            (
                "system",
                "Flag whether Google Books / ngram counts for this surface form are polluted "
                "by a dominant other sense (homograph or older meaning). pollutes_curve is "
                "true only if the other sense would dominate historical counts. Do not flag "
                "ordinary etymology. usageNote should be one plain sentence for a reader, "
                "or null.",
            ),
            (
                "human",
                f"Word: {word}\nFamily: {family_hub}\nLesson gloss: {gloss}\n\nSources:\n{quotes}",
            ),
        ]
    )


def gloss_review_llm(family_payload: str) -> Optional[GlossReview]:
    if not llm_enabled():
        return None
    llm = _model().with_structured_output(GlossReview)
    return llm.invoke(
        [
            (
                "system",
                "Swap test: if two glosses could be swapped and both still sound true, both "
                "are too weak. List those pairs in swap_failures. Propose contrastive "
                "replacements only for failures. Do not invent new family members.",
            ),
            ("human", family_payload),
        ]
    )


def rank_llm(family_payload: str, axes: str) -> Optional[list[RankSuggestion]]:
    if not llm_enabled():
        return None
    from pydantic import BaseModel

    class RankBundle(BaseModel):
        ranks: list[RankSuggestion]

    llm = _model().with_structured_output(RankBundle)
    out = llm.invoke(
        [
            (
                "system",
                "Rank the words relative to each other on the named axes. "
                "suggested_xyz is optional and MUST NOT be treated as ground truth. "
                "Walk intensity is body effort, not speed. "
                "Return one RankSuggestion per axis that actually separates the family.",
            ),
            ("human", f"Axes in play: {axes}\n\n{family_payload}"),
        ]
    )
    return out.ranks
