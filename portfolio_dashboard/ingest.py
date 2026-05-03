"""Concept-board intake — convert a visually rich concept image plus
its summary into structured Codex records.

Mirrors the workflow encoded in populate_codex_image_assets.ps1.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .schema import (
    ArtifactRecord,
    NextActionRecord,
    SkillSeedRecord,
    WorkingMemoryRecord,
)
from .store import CodexStore


@dataclass
class ConceptBoard:
    """User-supplied concept board to ingest."""
    label:       str
    source_path: str
    title:       str
    usefulness:  str
    legend:      list[str] = field(default_factory=list)
    summary_md_path: str = ""
    next_action_seed: int = 100   # NextActions.sequence_no starting point


def ingest_concept_board(store: CodexStore, board: ConceptBoard,
                         *, skill_name: str = "concept-board-intake"
                         ) -> dict[str, list[int]]:
    """Persist a ConceptBoard into all four Codex tables.

    Returns the new/updated row IDs by table.
    """
    out: dict[str, list[int]] = {
        "artifacts": [],
        "memories":  [],
        "actions":   [],
        "skills":    [],
    }

    # 1. Artifacts: the source image + summary note
    out["artifacts"].append(store.upsert_artifact(ArtifactRecord(
        label=board.label,
        kind="concept-image",
        source_path=board.source_path,
        location_group="thread",
        status="reviewed",
        practical_role="User-provided source concept board",
        notes="Used as the basis for derived artifacts and intake records.",
    )))
    if board.summary_md_path:
        out["artifacts"].append(store.upsert_artifact(ArtifactRecord(
            label=f"{board.label} — summary.md",
            kind="markdown-note",
            source_path=board.summary_md_path,
            location_group="workspace",
            status="active",
            practical_role="Text mirror of the concept image's useful contents",
            notes="Summarizes the image and flags unreliable annotations.",
        )))

    # 2. Working memories — title, usefulness, legend
    out["memories"].append(store.upsert_memory(WorkingMemoryRecord(
        topic=f"{board.label}_title",
        memory_value=board.title,
        source_artifact=board.label,
        confidence=0.96,
        next_use="Use as the working label for cross-file references.",
    )))
    out["memories"].append(store.upsert_memory(WorkingMemoryRecord(
        topic=f"{board.label}_usefulness",
        memory_value=board.usefulness,
        source_artifact=board.label,
        confidence=0.98,
        next_use="Treat as concept reference, not engineering truth.",
    )))
    if board.legend:
        out["memories"].append(store.upsert_memory(WorkingMemoryRecord(
            topic=f"{board.label}_symbol_legend",
            memory_value=" | ".join(board.legend),
            source_artifact=board.label,
            confidence=0.87,
            next_use="Reuse as prompt/taxonomy material.",
        )))

    # 3. Next actions — preservation + reliability flag
    out["actions"].append(store.upsert_action(NextActionRecord(
        sequence_no=board.next_action_seed,
        action_text=("If the exact original uploaded image is later saved "
                     "to disk, replace any derived rendering while keeping "
                     "the same structured summary and assessment."),
        source_artifact=board.label,
        status="open",
        notes="Derived assets are not byte-for-byte copies.",
    )))
    out["actions"].append(store.upsert_action(NextActionRecord(
        sequence_no=board.next_action_seed + 1,
        action_text=("Do not treat upper blueprint callouts as fabrication "
                     "guidance unless a human-authored specification is "
                     "produced."),
        source_artifact=board.label,
        status="open",
        notes="The image is visually rich but technically unreliable.",
    )))

    # 4. Skill seed — the intake capability itself
    out["skills"].append(store.upsert_skill(SkillSeedRecord(
        skill_name=skill_name,
        purpose=("Convert visually rich concept images into structured "
                 "notes while separating inspiration from engineering truth."),
        source_artifact=board.label,
        status="active",
        notes="Useful for future image-to-memory ingestion work.",
    )))

    return out


def bulk_ingest(store: CodexStore, boards: Iterable[ConceptBoard]
                ) -> list[dict[str, list[int]]]:
    """Ingest many boards in sequence."""
    return [ingest_concept_board(store, b) for b in boards]
