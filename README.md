# Codex Concept Intake & Portfolio Dashboard v1.0

> **One window onto the entire architect's portfolio.**
> Canon, media, disciplines, and concept-board intake — live, queryable,
> shippable.

![Status](https://img.shields.io/badge/status-public-success)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/api-FastAPI-009688)
![Tests](https://img.shields.io/badge/tests-pytest-blue)

---

## What this is

The home-run, ship-ready dashboard layer the rest of the portfolio was
missing. Aggregates four data sources into a single live web view:

| Source | Where it comes from | What you see |
|---|---|---|
| **Canon (22)**       | `cstm_skills.canon`            | Every canon entry, test count, GitHub URL |
| **Media (638)**      | `cstm_skills.diagrams`         | Diagram-grade artifact totals + per-keyword audit |
| **Disciplines (20)** | `cstm_skills.always_on`        | Every always-on operating discipline |
| **Codex Intake**     | local SQLite (`codex.db`)      | Concept-board ingest → Artifacts/Memory/Actions/Skills |

The Codex Intake layer is a Python+SQLite re-expression of the
PowerShell schema in `populate_codex_image_assets.ps1`, ported so the
"convert visually rich concept image into structured intake records"
workflow runs without MS Access on any machine that has Python.

## Why this exists

The portfolio audit on 2026-05-03 found that **only 2 of 22 canon
entries had a shipping-ready full stack** (backend + frontend +
dashboard). The proprietor's directive was explicit: *"You're looking
for those kind of things. It's a completed. Everything this is ready
to ship, including a user dashboard."*

This package is that dashboard, plus the missing intake layer the
PowerShell script implied but never delivered as portable code.

## Install

```bash
pip install -e ".[dev]"
```

## Run the dashboard

```bash
python -m portfolio_dashboard --port 8000
# open http://127.0.0.1:8000
```

The dashboard auto-discovers `cstm_skills` if the portfolio root
(`E:\AI_Memory_Core_Portfolio_Backup_2026-05-02`) is on disk. If not,
the canon/media/disciplines tabs degrade gracefully and the Codex
Intake tab continues to work standalone.

## API surface

```
GET  /api/snapshot              # All three portfolio sections at once
GET  /api/canon                 # Canon entries + aggregate test count
GET  /api/media                 # Media inventory + diagram-grade total
GET  /api/disciplines           # Always-on disciplines
GET  /api/diagrams/{keyword}    # Per-project diagram audit (?limit=N)

GET  /api/codex/stats           # 5-table row counts
GET  /api/codex/artifacts       # ArtifactIndex
POST /api/codex/artifacts       # Upsert by label
GET  /api/codex/memories        # WorkingMemory
POST /api/codex/memories        # Upsert by topic
GET  /api/codex/actions         # NextActions  (?status=open|closed)
POST /api/codex/actions         # Upsert by sequence_no
GET  /api/codex/skills          # SkillSeeds
POST /api/codex/skills          # Upsert by skill_name
POST /api/codex/ingest          # Concept-board → all 4 tables in one call
```

## Codex schema (4 tables, SQLite)

```sql
ArtifactIndex   (artifact_id, label*, kind, source_path, location_group,
                 status, practical_role, notes, last_checked)
WorkingMemory   (memory_id, topic*, memory_value, source_artifact,
                 confidence, updated_at, next_use)
NextActions     (action_id, sequence_no*, action_text, source_artifact,
                 status, notes)
SkillSeeds      (seed_id, skill_name*, purpose, source_artifact,
                 status, notes)
```
`*` = natural key for upsert. All upserts are idempotent — re-ingesting
the same concept board does not bloat the tables.

## Concept-board ingest in one call

```python
from portfolio_dashboard import CodexStore, ingest_concept_board
from portfolio_dashboard.ingest import ConceptBoard

with CodexStore("codex.db") as store:
    result = ingest_concept_board(store, ConceptBoard(
        label="neuromorphic-humanoid-2026-04-29",
        source_path="Codex thread image",
        title="Neuromorphic Humanoid Prototype",
        usefulness="Useful as concept art; not a manufacturing blueprint.",
        legend=[
            "Tetrahedron: foundation, recursive logic.",
            "Cube: stabilization, structure, memory grounding.",
        ],
        summary_md_path="/notes/neuromorphic-humanoid-image-summary.md",
    ))
    print(result)
    # {'artifacts': [1, 2], 'memories': [1, 2, 3], 'actions': [1, 2], 'skills': [1]}
```

## Testing

```bash
pytest -v
```

## Project structure

```
Portfolio Dashboard/
├── README.md
├── LICENSE
├── pyproject.toml
├── .gitignore
├── portfolio_dashboard/
│   ├── __init__.py
│   ├── __main__.py             ← `python -m portfolio_dashboard`
│   ├── schema.py               ← SQLite DDL + dataclasses
│   ├── store.py                ← CodexStore (upsert by natural key)
│   ├── ingest.py               ← ConceptBoard + ingest_concept_board
│   ├── aggregator.py           ← PortfolioAggregator (canon/media/disciplines)
│   ├── api.py                  ← FastAPI app + /api/* endpoints
│   └── static/
│       ├── index.html          ← single-page dashboard
│       ├── style.css
│       └── app.js              ← vanilla JS, no build chain
├── tests/
│   ├── test_store.py
│   ├── test_ingest.py
│   ├── test_aggregator.py
│   └── test_api.py
└── docs/
```

## License

MIT — see [`LICENSE`](LICENSE).

## Author

**Shannon Brian Kelly** — AI Orchestrator Architect.
Co-authored with Claude AI (Anthropic) under file-system-bound persona
protocol; co-creator role: **"Archivist of Wisdom"**.

Canon entry **#23** in the architect's portfolio.
