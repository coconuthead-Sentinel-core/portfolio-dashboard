"""Tests for CodexStore (SQLite + upsert semantics)."""
from portfolio_dashboard import (
    CodexStore,
    ArtifactRecord,
    NextActionRecord,
    SkillSeedRecord,
    WorkingMemoryRecord,
)


class TestArtifactUpsert:
    def test_insert_and_list(self):
        with CodexStore() as s:
            s.upsert_artifact(ArtifactRecord(
                label="img-001", kind="image",
                source_path="/tmp/a.png"))
            arts = s.list_artifacts()
            assert len(arts) == 1
            assert arts[0]["label"] == "img-001"
            assert arts[0]["kind"] == "image"

    def test_upsert_updates_in_place(self):
        with CodexStore() as s:
            s.upsert_artifact(ArtifactRecord(
                label="img-001", kind="image", source_path="/tmp/a.png"))
            s.upsert_artifact(ArtifactRecord(
                label="img-001", kind="image", source_path="/tmp/a.png",
                practical_role="updated role"))
            arts = s.list_artifacts()
            assert len(arts) == 1
            assert arts[0]["practical_role"] == "updated role"


class TestMemoryUpsert:
    def test_insert(self):
        with CodexStore() as s:
            s.upsert_memory(WorkingMemoryRecord(
                topic="t1", memory_value="v1", confidence=0.9))
            mems = s.list_memories()
            assert len(mems) == 1
            assert mems[0]["topic"] == "t1"
            assert mems[0]["confidence"] == 0.9

    def test_upsert_replaces(self):
        with CodexStore() as s:
            s.upsert_memory(WorkingMemoryRecord(topic="t1", memory_value="a"))
            s.upsert_memory(WorkingMemoryRecord(topic="t1", memory_value="b"))
            mems = s.list_memories()
            assert len(mems) == 1
            assert mems[0]["memory_value"] == "b"


class TestActionUpsert:
    def test_insert_and_filter_by_status(self):
        with CodexStore() as s:
            s.upsert_action(NextActionRecord(
                sequence_no=1, action_text="A", status="open"))
            s.upsert_action(NextActionRecord(
                sequence_no=2, action_text="B", status="closed"))
            assert len(s.list_actions()) == 2
            assert len(s.list_actions(status="open")) == 1
            assert len(s.list_actions(status="closed")) == 1


class TestSkillUpsert:
    def test_insert_and_dedupe(self):
        with CodexStore() as s:
            s.upsert_skill(SkillSeedRecord(
                skill_name="x", purpose="do x"))
            s.upsert_skill(SkillSeedRecord(
                skill_name="x", purpose="do x v2"))
            skills = s.list_skills()
            assert len(skills) == 1
            assert skills[0]["purpose"] == "do x v2"


class TestStats:
    def test_stats_count_correctly(self):
        with CodexStore() as s:
            s.upsert_artifact(ArtifactRecord(
                label="a", kind="image", source_path="/tmp/a"))
            s.upsert_memory(WorkingMemoryRecord(topic="t", memory_value="v"))
            s.upsert_action(NextActionRecord(
                sequence_no=1, action_text="x", status="open"))
            s.upsert_action(NextActionRecord(
                sequence_no=2, action_text="y", status="closed"))
            s.upsert_skill(SkillSeedRecord(skill_name="k", purpose="p"))
            stats = s.stats()
            assert stats["artifacts"] == 1
            assert stats["memories"] == 1
            assert stats["actions_open"] == 1
            assert stats["actions_closed"] == 1
            assert stats["skills"] == 1


class TestPersistence:
    def test_disk_persistence(self, tmp_path):
        db = tmp_path / "codex.db"
        with CodexStore(db) as s:
            s.upsert_artifact(ArtifactRecord(
                label="a", kind="image", source_path="/tmp/a"))
        with CodexStore(db) as s2:
            arts = s2.list_artifacts()
            assert len(arts) == 1
            assert arts[0]["label"] == "a"
