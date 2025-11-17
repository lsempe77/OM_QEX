"""
Stage 2: Build 'evidence spans' from TEI + OM outcomes.

Given:
    - A TEI XML file (GROBID output)
    - A list of OM outcomes for a study

Produce:
    - A dict with study_id and a list of spans that likely contain
      effect-size information for those outcomes.

Each span is a small chunk of text (paragraph, figure caption, or table)
with:
    - om_outcome_id
    - span_type ("paragraph" | "figure_caption" | "table")
    - section_path
    - raw_text
    - span_confidence
    - tei_pointer
    - om_hints
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    # If this lives inside a package (e.g., om_qex_extraction.src)
    from .tei_parser import TEIParser  # type: ignore
except ImportError:
    # Fallback for running as a standalone script
    from tei_parser import TEIParser  # type: ignore


XML_ID_ATTR = "{http://www.w3.org/XML/1998/namespace}id"


# ---------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------


@dataclass
class ParagraphEntry:
    text: str
    xml_id: Optional[str]
    section_path: List[str]
    index_in_body: int


@dataclass
class FigureCaptionEntry:
    text: str
    xml_id: Optional[str]
    figure_id: Optional[str]
    section_path: List[str]


@dataclass
class TableEntry:
    text: str
    xml_id: Optional[str]
    section_path: List[str]
    index_in_body: int


@dataclass
class TEIIndex:
    study_id: str
    paragraphs: List[ParagraphEntry]
    figure_captions: List[FigureCaptionEntry]
    tables: List[TableEntry]


# ---------------------------------------------------------------------
# Helpers to read TEI and build an index
# ---------------------------------------------------------------------


def _get_section_path(elem, ns: Dict[str, str]) -> List[str]:
    """
    Walk up ancestors from elem and collect heading texts to form a section_path.
    E.g. ["Results", "Income"].
    """
    path: List[str] = []
    parent = elem.getparent()
    body_tag = f"{{{ns['tei']}}}body"

    while parent is not None and parent.tag != body_tag:
        # For each ancestor div, prepend its head text (if any)
        if parent.tag == f"{{{ns['tei']}}}div":
            head = parent.find("./tei:head", ns)
            if head is not None:
                head_text = " ".join(head.itertext()).strip()
                if head_text:
                    path.insert(0, head_text)
        parent = parent.getparent()

    return path


def index_tei_structure(tei_file: Path) -> TEIIndex:
    """
    Parse the TEI file and build a simple index of:
        - paragraphs (with section_path)
        - figure captions (with section_path)
        - tables (flattened text, with section_path)

    This is intentionally minimal and geared toward Stage 2.
    """
    parser = TEIParser(tei_file)
    root = parser.root
    ns = parser.NS

    body = root.find(".//tei:body", ns)
    if body is None:
        return TEIIndex(
            study_id=tei_file.stem,
            paragraphs=[],
            figure_captions=[],
            tables=[],
        )

    paragraphs: List[ParagraphEntry] = []
    figure_captions: List[FigureCaptionEntry] = []
    tables: List[TableEntry] = []

    # Collect paragraphs
    para_idx = 0
    for elem in body.iter():
        if elem.tag == f"{{{ns['tei']}}}p":
            text = " ".join(elem.itertext()).strip()
            if not text:
                continue
            xml_id = elem.get(XML_ID_ATTR)
            section_path = _get_section_path(elem, ns)
            paragraphs.append(
                ParagraphEntry(
                    text=text,
                    xml_id=xml_id,
                    section_path=section_path,
                    index_in_body=para_idx,
                )
            )
            para_idx += 1

    # Collect figure captions (heads inside figure elements or similar patterns)
    for fig in body.findall(".//tei:figure", ns):
        figure_id = fig.get(XML_ID_ATTR)

        # Caption typically in <head> or <figDesc>
        caption_elem = fig.find("./tei:head", ns)
        if caption_elem is None:
            caption_elem = fig.find("./tei:figDesc", ns)

        if caption_elem is None:
            continue

        caption_text = " ".join(caption_elem.itertext()).strip()
        if not caption_text:
            continue

        xml_id = caption_elem.get(XML_ID_ATTR)
        section_path = _get_section_path(fig, ns)
        figure_captions.append(
            FigureCaptionEntry(
                text=caption_text,
                xml_id=xml_id,
                figure_id=figure_id,
                section_path=section_path,
            )
        )

    # Collect tables (flatten cell text)
    table_idx = 0
    for table in body.findall(".//tei:table", ns):
        table_text = " ".join(table.itertext()).strip()
        if not table_text:
            continue
        xml_id = table.get(XML_ID_ATTR)
        section_path = _get_section_path(table, ns)
        tables.append(
            TableEntry(
                text=table_text,
                xml_id=xml_id,
                section_path=section_path,
                index_in_body=table_idx,
            )
        )
        table_idx += 1

    return TEIIndex(
        study_id=tei_file.stem,
        paragraphs=paragraphs,
        figure_captions=figure_captions,
        tables=tables,
    )


# ---------------------------------------------------------------------
# Scoring logic
# ---------------------------------------------------------------------


def _score_span_text(text: str, section_path: List[str], om_outcome: Dict[str, Any]) -> float:
    """
    Heuristic scoring of how likely a span is to contain effect-size
    information relevant to a specific OM outcome.
    Scores between 0 and 1.
    """
    text_lower = text.lower()
    section_lower = " ".join(section_path).lower()

    score = 0.0

    cat = (om_outcome.get("outcome_category") or "").lower()
    name = (om_outcome.get("outcome_name") or "").lower()
    literal = (om_outcome.get("literal_text") or "").lower()
    location = (om_outcome.get("location") or "").lower()

    # Outcome category / name in span text
    if cat and cat in text_lower:
        score += 0.4
    if name:
        # crude word overlap
        for w in name.split():
            if len(w) > 3 and w.lower() in text_lower:
                score += 0.05

    # Literal OM snippet overlap
    if literal and literal[:20] in text_lower:
        score += 0.2

    # Location hint in section_path or text
    if location:
        loc_tokens = [tok for tok in re.split(r"[\s;,]+", location) if tok]
        if any(tok.lower() in section_lower for tok in loc_tokens):
            score += 0.1
        if any(tok.lower() in text_lower for tok in loc_tokens):
            score += 0.05

    # Numbers & units (income, ppp, %, USD, index, etc.)
    if any(ch.isdigit() for ch in text):
        score += 0.1
    if any(u in text_lower for u in ["usd", "ppp", "percent", "%", "index", "score", "sd", "se"]):
        score += 0.1

    # Effect language
    if any(w in text_lower for w in ["effect", "impact", "increase", "decrease", "improve", "change", "difference"]):
        score += 0.1

    # Section names themselves: if category/name overlaps with section head text
    if cat and cat in section_lower:
        score += 0.1
    if name and any(w in section_lower for w in name.split()):
        score += 0.05

    # Cap at 1.0
    return min(score, 1.0)


# ---------------------------------------------------------------------
# Evidence span builders
# ---------------------------------------------------------------------


def build_evidence_spans_for_outcome(
    tei_index: TEIIndex,
    om_outcome: Dict[str, Any],
    max_spans: int = 7,
    min_score: float = 0.3,
) -> List[Dict[str, Any]]:
    """
    For a single OM outcome, score all paragraphs, figure captions, and tables,
    and return the top spans above min_score (up to max_spans).
    """
    spans_with_scores: List[Tuple[float, Dict[str, Any]]] = []

    outcome_id = om_outcome.get("om_outcome_id") or om_outcome.get("id") or "unknown_outcome"

    # Paragraphs
    for p in tei_index.paragraphs:
        s = _score_span_text(p.text, p.section_path, om_outcome)
        if s < min_score:
            continue

        span_id = f"{outcome_id}_p_{p.index_in_body}"
        span_obj: Dict[str, Any] = {
            "span_id": span_id,
            "om_outcome_id": outcome_id,
            "span_type": "paragraph",
            "section_path": p.section_path,
            "raw_text": p.text,
            "span_confidence": round(float(s), 3),
            "tei_pointer": {
                "element_type": "p",
                "xml_id": p.xml_id,
                "index_in_body": p.index_in_body,
            },
            "om_hints": {
                "literal_text_overlap": bool(
                    (om_outcome.get("literal_text") or "").lower()[:20] in p.text.lower()
                ),
                "location_hint": om_outcome.get("location", ""),
            },
        }
        spans_with_scores.append((s, span_obj))

    # Figure captions
    for cap in tei_index.figure_captions:
        s = _score_span_text(cap.text, cap.section_path, om_outcome)
        if s < min_score:
            continue

        fig_id = cap.figure_id or "fig"
        span_id = f"{outcome_id}_fig_{fig_id}"
        span_obj = {
            "span_id": span_id,
            "om_outcome_id": outcome_id,
            "span_type": "figure_caption",
            "section_path": cap.section_path,
            "raw_text": cap.text,
            "span_confidence": round(float(s), 3),
            "tei_pointer": {
                "element_type": "figure_caption",
                "xml_id": cap.xml_id,
                "figure_id": cap.figure_id,
            },
            "om_hints": {
                "literal_text_overlap": bool(
                    (om_outcome.get("literal_text") or "").lower()[:20] in cap.text.lower()
                ),
                "location_hint": om_outcome.get("location", ""),
            },
        }
        spans_with_scores.append((s, span_obj))

    # Tables
    for t in tei_index.tables:
        s = _score_span_text(t.text, t.section_path, om_outcome)
        if s < min_score:
            continue

        span_id = f"{outcome_id}_table_{t.index_in_body}"
        span_obj = {
            "span_id": span_id,
            "om_outcome_id": outcome_id,
            "span_type": "table",
            "section_path": t.section_path,
            "raw_text": t.text,
            "span_confidence": round(float(s), 3),
            "tei_pointer": {
                "element_type": "table",
                "xml_id": t.xml_id,
                "index_in_body": t.index_in_body,
            },
            "om_hints": {
                "literal_text_overlap": bool(
                    (om_outcome.get("literal_text") or "").lower()[:20] in t.text.lower()
                ),
                "location_hint": om_outcome.get("location", ""),
            },
        }
        spans_with_scores.append((s, span_obj))

    # Sort by score descending, keep top max_spans
    spans_with_scores.sort(key=lambda t: t[0], reverse=True)
    top_spans = [s[1] for s in spans_with_scores[:max_spans]]

    return top_spans


def build_evidence_spans_for_study(
    tei_file: Path,
    om_outcomes: List[Dict[str, Any]],
    max_spans_per_outcome: int = 7,
    min_score: float = 0.3,
) -> Dict[str, Any]:
    """
    Full Stage 2 builder for a single study.

    Returns:
        {
          "study_id": "<TEI filename stem>",
          "evidence_spans": [ ... span dicts ... ]
        }
    """
    tei_index = index_tei_structure(tei_file)

    all_spans: List[Dict[str, Any]] = []
    for om_outcome in om_outcomes:
        spans = build_evidence_spans_for_outcome(
            tei_index=tei_index,
            om_outcome=om_outcome,
            max_spans=max_spans_per_outcome,
            min_score=min_score,
        )
        all_spans.extend(spans)

    return {
        "study_id": tei_index.study_id,
        "evidence_spans": all_spans,
    }


# ---------------------------------------------------------------------
# CLI / debugging harness
# ---------------------------------------------------------------------


def _load_om_outcomes_from_json(path: Path) -> List[Dict[str, Any]]:
    """
    Tiny helper to load OM outcomes from a JSON file.
    The JSON is expected to look like:
        { "study_id": "...", "outcomes": [ { ... }, ... ] }
    or:
        [ { ... }, ... ]
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "outcomes" in data:
        return data["outcomes"]
    if isinstance(data, list):
        return data
    raise ValueError(f"Unrecognized OM JSON structure in {path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build evidence spans for a study from TEI + OM outcomes.")
    parser.add_argument("tei_file", type=str, help="Path to TEI XML file (GROBID output).")
    parser.add_argument(
        "om_json",
        type=str,
        help="Path to OM JSON file for this study (with an 'outcomes' list).",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Output JSON path (default: <tei_stem>.evidence_spans.json in current dir).",
    )
    parser.add_argument(
        "--max_spans_per_outcome",
        type=int,
        default=7,
        help="Maximum spans to keep per outcome.",
    )
    parser.add_argument(
        "--min_score",
        type=float,
        default=0.3,
        help="Minimum score threshold for including a span.",
    )

    args = parser.parse_args()

    tei_path = Path(args.tei_file)
    om_path = Path(args.om_json)

    om_outcomes = _load_om_outcomes_from_json(om_path)

    result = build_evidence_spans_for_study(
        tei_file=tei_path,
        om_outcomes=om_outcomes,
        max_spans_per_outcome=args.max_spans_per_outcome,
        min_score=args.min_score,
    )

    if args.out is not None:
        out_path = Path(args.out)
    else:
        out_path = Path(f"{tei_path.stem}.evidence_spans.json")

    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote evidence spans to {out_path}")
