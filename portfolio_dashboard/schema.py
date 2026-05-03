"""SQLite schema lifted from populate_codex_image_assets.ps1.

The PowerShell original wrote to MS Access. This module re-expresses
the same four tables in portable SQLite + dataclasses.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS ArtifactIndex (
    artifact_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    label           TEXT    NOT NULL UNIQUE,
    kind            TEXT    NOT NULL,
    source_path     TEXT    NOT NULL,
    location_group  TEXT,
    status          TEXT    DEFAULT 'active',
    practical_role  TEXT,
    notes           TEXT,
    last_checked    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS WorkingMemory (
    memory_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    topic           TEXT    NOT NULL UNIQUE,
    memory_value    TEXT    NOT NULL,
    source_artifact TEXT,
    confidence      REAL    DEFAULT 1.0,
    updated_at      TEXT    NOT NULL,
    next_use        TEXT
);

CREATE TABLE IF NOT EXISTS NextActions (
    action_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    sequence_no     INTEGER NOT NULL UNIQUE,
    action_text     TEXT    NOT NULL,
    source_artifact TEXT,
    status          TEXT    DEFAULT 'open',
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS SkillSeeds (
    seed_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name      TEXT    NOT NULL UNIQUE,
    purpose         TEXT    NOT NULL,
    source_artifact TEXT,
    status          TEXT    DEFAULT 'active',
    notes           TEXT
);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ArtifactRecord:
    label:          str
    kind:           str
    source_path:    str
    location_group: str = "workspace"
    status:         str = "active"
    practical_role: str = ""
    notes:          str = ""
    last_checked:   str = field(default_factory=_now_iso)


@dataclass
class WorkingMemoryRecord:
    topic:           str
    memory_value:    str
    source_artifact: str = ""
    confidence:      float = 1.0
    next_use:        str = ""
    updated_at:      str = field(default_factory=_now_iso)


@dataclass
class NextActionRecord:
    sequence_no:     int
    action_text:     str
    source_artifact: str = ""
    status:          str = "open"
    notes:           str = ""


@dataclass
class SkillSeedRecord:
    skill_name:      str
    purpose:         str
    source_artifact: str = ""
    status:          str = "active"
    notes:           str = ""
