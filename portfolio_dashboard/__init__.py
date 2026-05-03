"""
portfolio_dashboard — Codex Concept Intake & Portfolio Dashboard

Canon entry #23. Aggregates EVERY data source in the architect's
portfolio into a single live dashboard:

  - 22 canon entries with test counts + GitHub URLs
  - 638 media artifacts + per-project diagram audit
  - 20 always-on disciplines
  - Codex Concept-Board Intake (4-table SQLite schema lifted from
    populate_codex_image_assets.ps1)

Layers:
  - SQLite store (codex.db)            -> store.py
  - Schema model + ingest functions    -> schema.py + ingest.py
  - Canon / media / discipline aggregator -> aggregator.py
  - FastAPI REST API                   -> api.py
  - Static HTML / CSS / vanilla-JS UI  -> static/
"""
from __future__ import annotations

__version__ = "1.0.0"

from .store import CodexStore
from .schema import (
    ArtifactRecord,
    WorkingMemoryRecord,
    NextActionRecord,
    SkillSeedRecord,
    SCHEMA_SQL,
)
from .ingest import ingest_concept_board
from .aggregator import (
    PortfolioAggregator,
    CanonSummary,
    MediaSummary,
    DisciplineSummary,
)
from .lattice_bridge import CodexLatticeBridge, LatticeEnvelope
from .per_project import (
    generate_dashboard_html,
    write_dashboard_for_canon_id,
    write_dashboards_for_all,
)

__all__ = [
    "CodexStore",
    "ArtifactRecord",
    "WorkingMemoryRecord",
    "NextActionRecord",
    "SkillSeedRecord",
    "SCHEMA_SQL",
    "ingest_concept_board",
    "PortfolioAggregator",
    "CanonSummary",
    "MediaSummary",
    "DisciplineSummary",
    "CodexLatticeBridge",
    "LatticeEnvelope",
    "generate_dashboard_html",
    "write_dashboard_for_canon_id",
    "write_dashboards_for_all",
]
