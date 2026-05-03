"""Tests for PortfolioAggregator."""
from types import SimpleNamespace

from portfolio_dashboard import PortfolioAggregator


def _fake_canon():
    CANON = [
        {"id": 1, "name": "A", "tier": "x", "tests": "10/10",
         "url": "https://github.com/x/a"},
        {"id": 2, "name": "B", "tier": "y", "tests": "—",
         "url": "(local-only)"},
        {"id": 3, "name": "C", "tier": "z", "tests": "5/5",
         "url": "https://github.com/x/c"},
    ]
    return SimpleNamespace(
        CANON=CANON,
        stats=lambda: {"total": 3, "github_published": 2, "with_tests": 2},
    )


def _fake_diagrams():
    return SimpleNamespace(
        total_media_inventory=lambda: {
            "total_artifacts": 100,
            "estimated_diagrams": 50,
            "by_kind": {"image": 80, "video": 20},
        },
        find_diagrams=lambda kw, limit=10: [
            {"filename": f"{kw}-1.png", "kind": "image",
             "categories": ["architecture"], "glyph_tags": "🔷"},
        ],
    )


def _fake_always_on():
    return SimpleNamespace(
        list_active_disciplines=lambda: ["d1", "d2", "d3"]
    )


class TestCanonSummary:
    def test_aggregate_test_count(self):
        a = PortfolioAggregator(canon_module=_fake_canon())
        c = a.canon_summary()
        assert c.total == 3
        assert c.github_published == 2
        assert c.aggregate_tests_passing == 15  # 10 + 5
        assert len(c.entries) == 3

    def test_no_canon_module_returns_error(self):
        a = PortfolioAggregator()
        c = a.canon_summary()
        assert c.error


class TestMediaSummary:
    def test_returns_inventory(self):
        a = PortfolioAggregator(diagrams_module=_fake_diagrams())
        m = a.media_summary()
        assert m.total_artifacts == 100
        assert m.diagram_grade == 50
        assert m.by_kind == {"image": 80, "video": 20}

    def test_no_diagrams_module_returns_error(self):
        a = PortfolioAggregator()
        m = a.media_summary()
        assert m.error


class TestDiagramAuditFor:
    def test_returns_results(self):
        a = PortfolioAggregator(diagrams_module=_fake_diagrams())
        r = a.diagram_audit_for("forge")
        assert len(r) == 1
        assert r[0]["filename"] == "forge-1.png"

    def test_no_diagrams_module_returns_empty(self):
        a = PortfolioAggregator()
        assert a.diagram_audit_for("forge") == []


class TestDisciplineSummary:
    def test_returns_list(self):
        a = PortfolioAggregator(always_on_module=_fake_always_on())
        d = a.discipline_summary()
        assert d.total == 3
        assert d.disciplines == ["d1", "d2", "d3"]

    def test_no_always_on_module_returns_error(self):
        a = PortfolioAggregator()
        d = a.discipline_summary()
        assert d.error


class TestSnapshot:
    def test_full_snapshot_structure(self):
        a = PortfolioAggregator(
            canon_module=_fake_canon(),
            diagrams_module=_fake_diagrams(),
            always_on_module=_fake_always_on(),
        )
        snap = a.snapshot()
        assert snap["canon"]["total"] == 3
        assert snap["canon"]["aggregate_tests_passing"] == 15
        assert snap["media"]["total_artifacts"] == 100
        assert snap["disciplines"]["total"] == 3

    def test_snapshot_with_no_modules(self):
        a = PortfolioAggregator()
        snap = a.snapshot()
        assert "canon" in snap and snap["canon"]["error"]
        assert "media" in snap and snap["media"]["error"]
        assert "disciplines" in snap and snap["disciplines"]["error"]
