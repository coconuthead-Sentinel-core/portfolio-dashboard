"""FastAPI REST API + static dashboard mount."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .aggregator import PortfolioAggregator
from .ingest import ConceptBoard, ingest_concept_board
from .schema import (
    ArtifactRecord,
    NextActionRecord,
    SkillSeedRecord,
    WorkingMemoryRecord,
)
from .store import CodexStore


# ── Optional CSTM portfolio modules (loaded best-effort) ──────────
def _load_portfolio_modules() -> dict[str, Any]:
    """Try to import canon / diagrams / always_on from cstm_skills."""
    out: dict[str, Any] = {"canon": None, "diagrams": None, "always_on": None}
    cstm_root = Path(r"E:\AI_Memory_Core_Portfolio_Backup_2026-05-02")
    if cstm_root.exists() and str(cstm_root) not in sys.path:
        sys.path.insert(0, str(cstm_root))
    for name in ("canon", "diagrams", "always_on"):
        try:
            out[name] = importlib.import_module(f"cstm_skills.{name}")
        except Exception:
            out[name] = None
    return out


# ── Pydantic schemas (request bodies) ──────────────────────────────
class ConceptBoardIn(BaseModel):
    label:            str
    source_path:      str
    title:            str
    usefulness:       str
    legend:           list[str] = Field(default_factory=list)
    summary_md_path:  str = ""
    next_action_seed: int = 100


class ArtifactIn(BaseModel):
    label:          str
    kind:           str
    source_path:    str
    location_group: str = "workspace"
    status:         str = "active"
    practical_role: str = ""
    notes:          str = ""


class MemoryIn(BaseModel):
    topic:           str
    memory_value:    str
    source_artifact: str = ""
    confidence:      float = 1.0
    next_use:        str = ""


class ActionIn(BaseModel):
    sequence_no:     int
    action_text:     str
    source_artifact: str = ""
    status:          str = "open"
    notes:           str = ""


class SkillIn(BaseModel):
    skill_name:      str
    purpose:         str
    source_artifact: str = ""
    status:          str = "active"
    notes:           str = ""


# ── App factory ────────────────────────────────────────────────────
def create_app(*, db_path: str = ":memory:") -> FastAPI:
    """Build the FastAPI app, wired to a CodexStore + portfolio modules."""
    app = FastAPI(
        title="Codex Concept Intake & Portfolio Dashboard",
        version="1.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
    )

    store = CodexStore(db_path=db_path)
    modules = _load_portfolio_modules()
    aggregator = PortfolioAggregator(
        canon_module=modules["canon"],
        diagrams_module=modules["diagrams"],
        always_on_module=modules["always_on"],
    )
    app.state.store = store
    app.state.aggregator = aggregator

    # ── Portfolio endpoints ─────────────────────────────────────
    @app.get("/api/snapshot")
    def snapshot() -> dict:
        return aggregator.snapshot()

    @app.get("/api/canon")
    def canon_list() -> dict:
        s = aggregator.canon_summary()
        return {
            "total": s.total,
            "github_published": s.github_published,
            "with_tests": s.with_tests,
            "aggregate_tests_passing": s.aggregate_tests_passing,
            "entries": s.entries,
            "error": s.error,
        }

    @app.get("/api/media")
    def media_summary() -> dict:
        m = aggregator.media_summary()
        return {
            "total_artifacts": m.total_artifacts,
            "diagram_grade":   m.diagram_grade,
            "by_kind":         m.by_kind,
            "error":           m.error,
        }

    @app.get("/api/disciplines")
    def disciplines() -> dict:
        d = aggregator.discipline_summary()
        return {"total": d.total, "list": d.disciplines, "error": d.error}

    @app.get("/api/diagrams/{keyword}")
    def diagrams_for(keyword: str, limit: int = 10) -> dict:
        return {
            "keyword": keyword,
            "results": aggregator.diagram_audit_for(keyword, limit=limit),
        }

    # ── Codex CRUD endpoints ───────────────────────────────────
    @app.get("/api/codex/stats")
    def codex_stats() -> dict:
        return store.stats()

    @app.get("/api/codex/artifacts")
    def list_artifacts() -> list[dict]:
        return store.list_artifacts()

    @app.post("/api/codex/artifacts")
    def add_artifact(rec: ArtifactIn) -> dict:
        rid = store.upsert_artifact(ArtifactRecord(**rec.model_dump()))
        return {"artifact_id": rid}

    @app.get("/api/codex/memories")
    def list_memories() -> list[dict]:
        return store.list_memories()

    @app.post("/api/codex/memories")
    def add_memory(rec: MemoryIn) -> dict:
        rid = store.upsert_memory(WorkingMemoryRecord(**rec.model_dump()))
        return {"memory_id": rid}

    @app.get("/api/codex/actions")
    def list_actions(status: str | None = None) -> list[dict]:
        return store.list_actions(status=status)

    @app.post("/api/codex/actions")
    def add_action(rec: ActionIn) -> dict:
        rid = store.upsert_action(NextActionRecord(**rec.model_dump()))
        return {"action_id": rid}

    @app.get("/api/codex/skills")
    def list_skills() -> list[dict]:
        return store.list_skills()

    @app.post("/api/codex/skills")
    def add_skill(rec: SkillIn) -> dict:
        rid = store.upsert_skill(SkillSeedRecord(**rec.model_dump()))
        return {"seed_id": rid}

    # ── Concept-board ingest ──────────────────────────────────
    @app.post("/api/codex/ingest")
    def ingest(board: ConceptBoardIn) -> dict:
        if not board.label or not board.source_path:
            raise HTTPException(400, "label and source_path are required")
        result = ingest_concept_board(store, ConceptBoard(**board.model_dump()))
        return {"ingested": result, "stats": store.stats()}

    # ── Static dashboard ─────────────────────────────────────
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True),
                  name="static")

    return app
