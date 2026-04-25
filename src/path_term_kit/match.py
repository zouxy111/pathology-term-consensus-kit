from __future__ import annotations

import re
from dataclasses import dataclass

from .config import ProjectConfig
from .term_catalog import TermFamily


@dataclass(frozen=True)
class Segment:
    text: str
    accepted: bool
    reason: str


@dataclass(frozen=True)
class TermMatch:
    family: TermFamily
    variant: str
    segment: str


def split_segments(text: str, config: ProjectConfig) -> list[Segment]:
    raw_segments = re.split(config.target_filter.text_split_pattern, text or "")
    segments: list[Segment] = []
    for raw in raw_segments:
        segment = " ".join(raw.split()).strip()
        if not segment:
            continue
        include_hit = (
            config.target_filter.allow_empty_include_terms
            or not config.target_filter.include_terms
            or any(term in segment for term in config.target_filter.include_terms)
        )
        exclude_hit = any(term in segment for term in config.target_filter.exclude_terms)
        if not include_hit:
            segments.append(Segment(segment, False, "no_include_term"))
        elif exclude_hit:
            segments.append(Segment(segment, False, "excluded_term"))
        else:
            segments.append(Segment(segment, True, "accepted"))
    return segments


def match_segment(segment: str, families: list[TermFamily]) -> list[TermMatch]:
    matches: list[TermMatch] = []
    for family in families:
        for pattern in family.patterns:
            if pattern.regex.search(segment):
                matches.append(TermMatch(family=family, variant=pattern.label, segment=segment))
                break
    return matches

