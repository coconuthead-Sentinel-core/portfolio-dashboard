"""Portfolio Aggregator — pulls canon, media, and disciplines into one view.

All data sources are optional. If a source is unavailable the aggregator
degrades gracefully and reports the gap.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CanonSummary:
    total:             int = 0
    github_published:  int = 0
    with_tests:        int = 0
    aggregate_tests_passing: int = 0
    entries:           list[dict] = field(default_factory=list)
    error:             str = ""


@dataclass
class MediaSummary:
    total_artifacts:   int = 0
    diagram_grade:     int = 0
    by_kind:           dict[str, int] = field(default_factory=dict)
    error:             str = ""


@dataclass
class DisciplineSummary:
    total:             int = 0
    disciplines:       list[str] = field(default_factory=list)
    error:             str = ""


def _parse_test_count(s: str) -> int:
    """'46/47' -> 46.  '378/378' -> 378.  '—' -> 0."""
    if not s or s == "—":
        return 0
    if "/" in s:
        try:
            return int(s.split("/")[0])
        except ValueError:
            return 0
    try:
        return int(s)
    except ValueError:
        return 0


class PortfolioAggregator:
    """Aggregates canon + media + disciplines into one snapshot.

    Pass any callable / module that exposes the documented contracts:

      canon_module      .CANON (list[dict]), .stats() -> dict
      diagrams_module   .total_media_inventory() -> dict,
                        .workbench_audit(keyword) -> str,
                        .find_diagrams(keyword, limit) -> list[dict]
      always_on_module  .list_active_disciplines() -> list[str]

    Any module left None simply skips its section.
    """

    def __init__(
        self,
        canon_module: Any = None,
        diagrams_module: Any = None,
        always_on_module: Any = None,
    ):
        self.canon = canon_module
        self.diagrams = diagrams_module
        self.always_on = always_on_module

    # ── Canon ─────────────────────────────────────────────────────
    def canon_summary(self) -> CanonSummary:
        if self.canon is None:
            return CanonSummary(error="no canon module configured")
        try:
            stats = self.canon.stats()
            entries = list(self.canon.CANON)
            agg = sum(_parse_test_count(e.get("tests", "")) for e in entries)
            return CanonSummary(
                total=stats.get("total", 0),
                github_published=stats.get("github_published", 0),
                with_tests=stats.get("with_tests", 0),
                aggregate_tests_passing=agg,
                entries=entries,
            )
        except Exception as e:
            return CanonSummary(error=str(e))

    # ── Media ─────────────────────────────────────────────────────
    def media_summary(self) -> MediaSummary:
        if self.diagrams is None:
            return MediaSummary(error="no diagrams module configured")
        try:
            inv = self.diagrams.total_media_inventory()
            return MediaSummary(
                total_artifacts=inv.get("total_artifacts", 0),
                diagram_grade=inv.get("estimated_diagrams", 0),
                by_kind=inv.get("by_kind", {}),
            )
        except Exception as e:
            return MediaSummary(error=str(e))

    # ── Per-project diagram audit ────────────────────────────────
    def diagram_audit_for(self, keyword: str, limit: int = 5
                          ) -> list[dict]:
        if self.diagrams is None:
            return []
        try:
            return self.diagrams.find_diagrams(keyword, limit=limit)
        except Exception:
            return []

    # ── Disciplines ──────────────────────────────────────────────
    def discipline_summary(self) -> DisciplineSummary:
        if self.always_on is None:
            return DisciplineSummary(error="no always_on module configured")
        try:
            disciplines = list(self.always_on.list_active_disciplines())
            return DisciplineSummary(
                total=len(disciplines), disciplines=disciplines)
        except Exception as e:
            return DisciplineSummary(error=str(e))

    # ── Snapshot ────────────────────────────────────────────────
    def snapshot(self) -> dict[str, Any]:
        c = self.canon_summary()
        m = self.media_summary()
        d = self.discipline_summary()
        return {
            "canon":       {
                "total":             c.total,
                "github_published":  c.github_published,
                "with_tests":        c.with_tests,
                "aggregate_tests_passing": c.aggregate_tests_passing,
                "entries":           c.entries,
                "error":             c.error,
            },
            "media": {
                "total_artifacts":   m.total_artifacts,
                "diagram_grade":     m.diagram_grade,
                "by_kind":           m.by_kind,
                "error":             m.error,
            },
            "disciplines": {
                "total":             d.total,
                "list":              d.disciplines,
                "error":             d.error,
            },
        }
