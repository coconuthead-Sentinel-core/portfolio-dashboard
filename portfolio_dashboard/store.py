"""SQLite-backed Codex store with upsert semantics."""
from __future__ import annotations

import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .schema import (
    ArtifactRecord,
    NextActionRecord,
    SCHEMA_SQL,
    SkillSeedRecord,
    WorkingMemoryRecord,
    _now_iso,
)


class CodexStore:
    """Thin SQLite wrapper. All upserts are idempotent on natural keys.

    Natural keys:
      - ArtifactIndex.label
      - WorkingMemory.topic
      - NextActions.sequence_no
      - SkillSeeds.skill_name
    """

    def __init__(self, db_path: str | Path = ":memory:"):
        self.db_path = str(db_path)
        # check_same_thread=False allows the FastAPI TestClient and any
        # framework that hands requests to a worker thread to reuse the
        # connection. We serialize all writes through commit() boundaries
        # in the upsert helpers so single-writer semantics still hold.
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()

    # ── lifecycle ────────────────────────────────────────────────
    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "CodexStore":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ── ArtifactIndex ────────────────────────────────────────────
    def upsert_artifact(self, rec: ArtifactRecord) -> int:
        cur = self._conn.execute(
            "SELECT artifact_id FROM ArtifactIndex WHERE label = ?",
            (rec.label,),
        )
        row = cur.fetchone()
        if row is None:
            cur = self._conn.execute(
                """INSERT INTO ArtifactIndex
                   (label, kind, source_path, location_group, status,
                    practical_role, notes, last_checked)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (rec.label, rec.kind, rec.source_path, rec.location_group,
                 rec.status, rec.practical_role, rec.notes, rec.last_checked),
            )
            self._conn.commit()
            return cur.lastrowid
        else:
            self._conn.execute(
                """UPDATE ArtifactIndex
                   SET kind = ?, source_path = ?, location_group = ?,
                       status = ?, practical_role = ?, notes = ?,
                       last_checked = ?
                   WHERE label = ?""",
                (rec.kind, rec.source_path, rec.location_group, rec.status,
                 rec.practical_role, rec.notes, _now_iso(), rec.label),
            )
            self._conn.commit()
            return int(row["artifact_id"])

    def list_artifacts(self) -> list[dict]:
        return [dict(r) for r in self._conn.execute(
            "SELECT * FROM ArtifactIndex ORDER BY artifact_id")]

    # ── WorkingMemory ───────────────────────────────────────────
    def upsert_memory(self, rec: WorkingMemoryRecord) -> int:
        cur = self._conn.execute(
            "SELECT memory_id FROM WorkingMemory WHERE topic = ?",
            (rec.topic,),
        )
        row = cur.fetchone()
        if row is None:
            cur = self._conn.execute(
                """INSERT INTO WorkingMemory
                   (topic, memory_value, source_artifact, confidence,
                    updated_at, next_use)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (rec.topic, rec.memory_value, rec.source_artifact,
                 rec.confidence, rec.updated_at, rec.next_use),
            )
            self._conn.commit()
            return cur.lastrowid
        else:
            self._conn.execute(
                """UPDATE WorkingMemory
                   SET memory_value = ?, source_artifact = ?,
                       confidence = ?, updated_at = ?, next_use = ?
                   WHERE topic = ?""",
                (rec.memory_value, rec.source_artifact, rec.confidence,
                 _now_iso(), rec.next_use, rec.topic),
            )
            self._conn.commit()
            return int(row["memory_id"])

    def list_memories(self) -> list[dict]:
        return [dict(r) for r in self._conn.execute(
            "SELECT * FROM WorkingMemory ORDER BY memory_id")]

    # ── NextActions ─────────────────────────────────────────────
    def upsert_action(self, rec: NextActionRecord) -> int:
        cur = self._conn.execute(
            "SELECT action_id FROM NextActions WHERE sequence_no = ?",
            (rec.sequence_no,),
        )
        row = cur.fetchone()
        if row is None:
            cur = self._conn.execute(
                """INSERT INTO NextActions
                   (sequence_no, action_text, source_artifact, status, notes)
                   VALUES (?, ?, ?, ?, ?)""",
                (rec.sequence_no, rec.action_text, rec.source_artifact,
                 rec.status, rec.notes),
            )
            self._conn.commit()
            return cur.lastrowid
        else:
            self._conn.execute(
                """UPDATE NextActions
                   SET action_text = ?, source_artifact = ?, status = ?,
                       notes = ?
                   WHERE sequence_no = ?""",
                (rec.action_text, rec.source_artifact, rec.status,
                 rec.notes, rec.sequence_no),
            )
            self._conn.commit()
            return int(row["action_id"])

    def list_actions(self, *, status: str | None = None) -> list[dict]:
        if status:
            return [dict(r) for r in self._conn.execute(
                "SELECT * FROM NextActions WHERE status = ? "
                "ORDER BY sequence_no", (status,))]
        return [dict(r) for r in self._conn.execute(
            "SELECT * FROM NextActions ORDER BY sequence_no")]

    # ── SkillSeeds ──────────────────────────────────────────────
    def upsert_skill(self, rec: SkillSeedRecord) -> int:
        cur = self._conn.execute(
            "SELECT seed_id FROM SkillSeeds WHERE skill_name = ?",
            (rec.skill_name,),
        )
        row = cur.fetchone()
        if row is None:
            cur = self._conn.execute(
                """INSERT INTO SkillSeeds
                   (skill_name, purpose, source_artifact, status, notes)
                   VALUES (?, ?, ?, ?, ?)""",
                (rec.skill_name, rec.purpose, rec.source_artifact,
                 rec.status, rec.notes),
            )
            self._conn.commit()
            return cur.lastrowid
        else:
            self._conn.execute(
                """UPDATE SkillSeeds
                   SET purpose = ?, source_artifact = ?, status = ?,
                       notes = ?
                   WHERE skill_name = ?""",
                (rec.purpose, rec.source_artifact, rec.status, rec.notes,
                 rec.skill_name),
            )
            self._conn.commit()
            return int(row["seed_id"])

    def list_skills(self) -> list[dict]:
        return [dict(r) for r in self._conn.execute(
            "SELECT * FROM SkillSeeds ORDER BY seed_id")]

    # ── stats ───────────────────────────────────────────────────
    def stats(self) -> dict:
        return {
            "artifacts":      self._count("ArtifactIndex"),
            "memories":       self._count("WorkingMemory"),
            "actions_open":   self._count_where("NextActions", "status = 'open'"),
            "actions_closed": self._count_where("NextActions", "status = 'closed'"),
            "skills":         self._count("SkillSeeds"),
        }

    def _count(self, table: str) -> int:
        return int(self._conn.execute(
            f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"])

    def _count_where(self, table: str, where: str) -> int:
        return int(self._conn.execute(
            f"SELECT COUNT(*) AS n FROM {table} WHERE {where}").fetchone()["n"])
