"""Tests for the CSTM_Lattice bridge."""
import pytest

from portfolio_dashboard import CodexLatticeBridge, LatticeEnvelope


class TestLatticeEnvelope:
    def test_to_dict_keys(self):
        env = LatticeEnvelope(available=True, session_id="abc", zone="GREEN",
                              qa_pass=True, yaml_frontmatter="---\n",
                              persisted_path="/tmp/x.md")
        d = env.to_dict()
        for k in ("available", "session_id", "zone", "qa_pass",
                  "yaml_frontmatter", "persisted_path", "error"):
            assert k in d
        assert d["available"] is True
        assert d["zone"] == "GREEN"


class TestBridgeWithoutLattice:
    """Whatever the host machine has installed, the bridge must NOT crash."""

    def test_bridge_constructs(self, tmp_path):
        bridge = CodexLatticeBridge(persist_dir=str(tmp_path))
        assert isinstance(bridge.available, bool)

    def test_run_returns_envelope_either_way(self, tmp_path):
        bridge = CodexLatticeBridge(persist_dir=str(tmp_path))
        env = bridge.run("test task", cognitive_load=5)
        assert isinstance(env, LatticeEnvelope)
        if not bridge.available:
            assert "not installed" in env.error
        else:
            # If lattice is present we expect either a real run or an error
            assert env.session_id != "" or env.error != ""


class TestBridgeWithLatticeIfAvailable:
    """Real-run smoke test — only runs when cstm_lattice is importable."""

    def test_real_run_persists(self, tmp_path):
        try:
            import cstm_lattice  # noqa: F401
        except ImportError:
            pytest.skip("cstm_lattice not installed")

        bridge = CodexLatticeBridge(persist_dir=str(tmp_path))
        if not bridge.available:
            pytest.skip("bridge could not initialize lattice")

        env = bridge.run("Codex ingest test", cognitive_load=8)
        assert env.available is True
        assert env.session_id  # non-empty
        assert env.zone in ("GREEN", "YELLOW", "RED")
