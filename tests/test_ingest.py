"""Tests for concept-board ingest."""
from portfolio_dashboard import CodexStore, ingest_concept_board
from portfolio_dashboard.ingest import ConceptBoard, bulk_ingest


def _board():
    return ConceptBoard(
        label="neuromorphic-humanoid-2026-04-29",
        source_path="Codex thread image",
        title="Neuromorphic Humanoid Prototype",
        usefulness="Useful as concept art; not a manufacturing blueprint.",
        legend=[
            "Tetrahedron: foundation, recursive logic.",
            "Cube: stabilization, structure, memory grounding.",
            "Hexagon: cellular synthesis, structured cognition.",
        ],
        summary_md_path="/tmp/summary.md",
    )


class TestIngestConceptBoard:
    def test_creates_artifacts_memories_actions_skills(self):
        with CodexStore() as s:
            result = ingest_concept_board(s, _board())
            assert len(result["artifacts"]) == 2  # image + summary md
            assert len(result["memories"]) == 3   # title + usefulness + legend
            assert len(result["actions"]) == 2
            assert len(result["skills"]) == 1

    def test_stats_after_ingest(self):
        with CodexStore() as s:
            ingest_concept_board(s, _board())
            stats = s.stats()
            assert stats["artifacts"] == 2
            assert stats["memories"] == 3
            assert stats["actions_open"] == 2
            assert stats["skills"] == 1

    def test_re_ingest_is_idempotent(self):
        with CodexStore() as s:
            ingest_concept_board(s, _board())
            ingest_concept_board(s, _board())
            stats = s.stats()
            # All natural keys are stable so counts shouldn't grow
            assert stats["artifacts"] == 2
            assert stats["memories"] == 3
            assert stats["actions_open"] == 2
            assert stats["skills"] == 1

    def test_no_legend_skips_legend_memory(self):
        with CodexStore() as s:
            board = _board()
            board.legend = []
            result = ingest_concept_board(s, board)
            assert len(result["memories"]) == 2  # only title + usefulness

    def test_no_summary_path_skips_summary_artifact(self):
        with CodexStore() as s:
            board = _board()
            board.summary_md_path = ""
            result = ingest_concept_board(s, board)
            assert len(result["artifacts"]) == 1


class TestBulkIngest:
    def test_handles_multiple_boards(self):
        with CodexStore() as s:
            b1 = _board()
            b2 = ConceptBoard(
                label="another-board",
                source_path="/tmp/b.png",
                title="Another",
                usefulness="x",
                next_action_seed=200,
            )
            results = bulk_ingest(s, [b1, b2])
            assert len(results) == 2
            # b1 has summary_md_path -> 2 artifacts; b2 has none -> 1 artifact
            assert s.stats()["artifacts"] == 3
