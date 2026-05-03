"""Tests for the per-project dashboard generator."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from portfolio_dashboard import (
    PortfolioAggregator,
    generate_dashboard_html,
    write_dashboard_for_canon_id,
    write_dashboards_for_all,
)
from portfolio_dashboard.per_project import _slugify, _diagram_audit_keywords


def _aggregator():
    canon_module = SimpleNamespace(
        CANON=[
            {"id": 1, "name": "Sentinel Forge",   "tier": "full-stack",
             "tests": "20/20", "url": "https://github.com/x/sf"},
            {"id": 2, "name": "Quantum Nexus",    "tier": "backend",
             "tests": "15/15", "url": "https://github.com/x/qn"},
            {"id": 7, "name": "Local Only Kernel","tier": "kernel",
             "tests": "—",     "url": "(local-only)"},
        ],
        stats=lambda: {"total": 3, "github_published": 2, "with_tests": 2},
    )
    diag_module = SimpleNamespace(
        total_media_inventory=lambda: {"total_artifacts": 100,
                                       "estimated_diagrams": 50,
                                       "by_kind": {"image": 100}},
        find_diagrams=lambda kw, limit=5: [
            {"filename": f"{kw}-01.png", "kind": "image",
             "categories": ["architecture", "data_flow"],
             "glyph_tags": "🔷"},
        ],
    )
    always_on = SimpleNamespace(
        list_active_disciplines=lambda: ["A", "B", "C"]
    )
    return PortfolioAggregator(
        canon_module=canon_module,
        diagrams_module=diag_module,
        always_on_module=always_on,
    )


class TestHelpers:
    def test_slugify_basic(self):
        assert _slugify("Sentinel Forge") == "sentinel-forge"
        assert _slugify("AI_Memory_Core") == "ai-memory-core"
        assert _slugify("Hub & Spoke!") == "hub-spoke"

    def test_slugify_collapses_dashes(self):
        assert _slugify("a   b   c") == "a-b-c"

    def test_slugify_strips_edges(self):
        assert _slugify("---x---") == "x"

    def test_slugify_handles_empty(self):
        assert _slugify("---") == "project"

    def test_diagram_keywords_dedupes_and_caps(self):
        assert _diagram_audit_keywords("Library-First Decision Agent") == [
            "library", "first", "decision"]

    def test_diagram_keywords_skips_short(self):
        assert _diagram_audit_keywords("AI to do") == []


class TestGenerateDashboardHtml:
    def test_renders_canon_id_and_name(self):
        agg = _aggregator()
        entry = agg.canon_summary().entries[0]
        html = generate_dashboard_html(entry, agg)
        assert "Canon #1" in html or ">#1<" in html
        assert "Sentinel Forge" in html
        assert "https://github.com/x/sf" in html

    def test_includes_diagram_hits(self):
        agg = _aggregator()
        entry = agg.canon_summary().entries[0]   # "Sentinel Forge"
        html = generate_dashboard_html(entry, agg)
        # diagram audit keyword "sentinel" -> filename sentinel-01.png
        assert "sentinel-01.png" in html

    def test_includes_disciplines_when_present(self):
        agg = _aggregator()
        entry = agg.canon_summary().entries[0]
        html = generate_dashboard_html(entry, agg)
        for d in ["A", "B", "C"]:
            assert f">{d}<" in html or f">{d}</li>" in html

    def test_local_only_entry_renders(self):
        agg = _aggregator()
        entry = agg.canon_summary().entries[2]   # local-only
        html = generate_dashboard_html(entry, agg)
        assert "Local Only Kernel" in html
        assert "(local)" in html  # GitHub badge falls back

    def test_html_is_well_formed_basics(self):
        agg = _aggregator()
        entry = agg.canon_summary().entries[0]
        html = generate_dashboard_html(entry, agg)
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html
        assert "<title>" in html


class TestWriteDashboardForCanonId:
    def test_writes_file(self, tmp_path: Path):
        agg = _aggregator()
        path = write_dashboard_for_canon_id(1, aggregator=agg,
                                            out_dir=tmp_path)
        assert path.exists()
        assert path.suffix == ".html"
        assert "sentinel-forge" in path.name.lower()

    def test_unknown_id_raises(self, tmp_path: Path):
        agg = _aggregator()
        with pytest.raises(KeyError):
            write_dashboard_for_canon_id(999, aggregator=agg, out_dir=tmp_path)


class TestWriteDashboardsForAll:
    def test_writes_one_per_entry(self, tmp_path: Path):
        agg = _aggregator()
        paths = write_dashboards_for_all(aggregator=agg, out_dir=tmp_path)
        assert len(paths) == 3
        for p in paths:
            assert p.exists()

    def test_only_ids_filter(self, tmp_path: Path):
        agg = _aggregator()
        paths = write_dashboards_for_all(aggregator=agg, out_dir=tmp_path,
                                         only_ids=[1, 7])
        assert len(paths) == 2
        names = {p.name for p in paths}
        assert any("sentinel" in n for n in names)
        assert any("local-only" in n for n in names)
