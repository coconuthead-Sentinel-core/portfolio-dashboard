"""Tests for FastAPI endpoints (using TestClient)."""
import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient   # noqa: E402

from portfolio_dashboard.api import create_app   # noqa: E402


@pytest.fixture
def client():
    app = create_app(db_path=":memory:")
    return TestClient(app)


class TestSnapshot:
    def test_snapshot_returns_three_sections(self, client):
        r = client.get("/api/snapshot")
        assert r.status_code == 200
        body = r.json()
        assert "canon" in body
        assert "media" in body
        assert "disciplines" in body


class TestCanonEndpoint:
    def test_returns_total_field(self, client):
        r = client.get("/api/canon")
        assert r.status_code == 200
        body = r.json()
        assert "total" in body
        assert "entries" in body


class TestMediaEndpoint:
    def test_returns_inventory_shape(self, client):
        r = client.get("/api/media")
        assert r.status_code == 200
        body = r.json()
        assert "total_artifacts" in body
        assert "diagram_grade" in body


class TestDisciplinesEndpoint:
    def test_returns_list_field(self, client):
        r = client.get("/api/disciplines")
        assert r.status_code == 200
        body = r.json()
        assert "list" in body


class TestDiagramsForKeyword:
    def test_returns_keyword_field(self, client):
        r = client.get("/api/diagrams/forge?limit=3")
        assert r.status_code == 200
        body = r.json()
        assert body["keyword"] == "forge"
        assert "results" in body


class TestCodexCRUD:
    def test_artifact_round_trip(self, client):
        r = client.post("/api/codex/artifacts", json={
            "label": "img-1", "kind": "image", "source_path": "/tmp/a"})
        assert r.status_code == 200
        assert r.json()["artifact_id"] >= 1
        listed = client.get("/api/codex/artifacts").json()
        assert len(listed) == 1
        assert listed[0]["label"] == "img-1"

    def test_memory_round_trip(self, client):
        client.post("/api/codex/memories", json={
            "topic": "t1", "memory_value": "v1", "confidence": 0.9})
        listed = client.get("/api/codex/memories").json()
        assert len(listed) == 1
        assert listed[0]["topic"] == "t1"

    def test_action_filter_by_status(self, client):
        client.post("/api/codex/actions", json={
            "sequence_no": 1, "action_text": "A", "status": "open"})
        client.post("/api/codex/actions", json={
            "sequence_no": 2, "action_text": "B", "status": "closed"})
        open_acts = client.get("/api/codex/actions?status=open").json()
        assert len(open_acts) == 1
        assert open_acts[0]["sequence_no"] == 1

    def test_skill_round_trip(self, client):
        client.post("/api/codex/skills", json={
            "skill_name": "x", "purpose": "do x"})
        listed = client.get("/api/codex/skills").json()
        assert len(listed) == 1


class TestCodexIngest:
    def test_ingest_concept_board_returns_ids(self, client):
        r = client.post("/api/codex/ingest", json={
            "label": "board-1",
            "source_path": "/tmp/img.png",
            "title": "test board",
            "usefulness": "concept ref",
            "legend": ["item 1", "item 2"],
        })
        assert r.status_code == 200
        body = r.json()
        assert "ingested" in body
        assert "stats" in body
        assert body["stats"]["artifacts"] >= 1
        assert body["stats"]["memories"] >= 2

    def test_ingest_validates_required(self, client):
        r = client.post("/api/codex/ingest", json={
            "label": "", "source_path": "", "title": "",
            "usefulness": "", "legend": [],
        })
        assert r.status_code == 400


class TestCodexStats:
    def test_stats_starts_zero(self, client):
        r = client.get("/api/codex/stats")
        assert r.status_code == 200
        s = r.json()
        assert s["artifacts"] == 0
        assert s["memories"] == 0
