"""CSTM_Lattice bridge — route every Codex ingest through the
8-node CSTM lattice so each persisted board carries:

  - N-05 METADATA_GENERATE  ->  10-field YAML metadata header
  - N-08 PERSIST_OUTPUT      ->  decision audit recorded in WorkingMemory

Bridge is OPTIONAL. If `cstm_lattice` is not installed, the bridge
returns a stub envelope and the dashboard continues to function.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LatticeEnvelope:
    """Result of running an ingest through the CSTM lattice."""
    available:        bool = False
    session_id:       str = ""
    zone:             str = ""
    qa_pass:          bool = False
    yaml_frontmatter: str = ""
    persisted_path:   str = ""
    error:            str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "available":        self.available,
            "session_id":       self.session_id,
            "zone":             self.zone,
            "qa_pass":          self.qa_pass,
            "yaml_frontmatter": self.yaml_frontmatter,
            "persisted_path":   self.persisted_path,
            "error":            self.error,
        }


def _import_lattice() -> Any | None:
    """Best-effort import; returns None if the package is unavailable."""
    try:
        import cstm_lattice
        return cstm_lattice.Lattice
    except Exception:
        return None


class CodexLatticeBridge:
    """Bridges CodexStore ingest events into CSTM_Lattice runs.

    Usage:
        bridge = CodexLatticeBridge(persist_dir="./_lattice_runs")
        env = bridge.run("Ingest neuromorphic-humanoid board",
                         cognitive_load=7)
        print(env.to_dict())
    """

    def __init__(self, *, persist_dir: str = "./_lattice_runs"):
        Lattice = _import_lattice()
        self._lattice_cls = Lattice
        self._persist_dir = persist_dir
        self._instance: Any = None
        if Lattice is not None:
            try:
                self._instance = Lattice(persist_dir=persist_dir)
            except Exception:
                self._instance = None

    @property
    def available(self) -> bool:
        return self._instance is not None

    def run(self, task_text: str, cognitive_load: int = 5) -> LatticeEnvelope:
        if self._instance is None:
            return LatticeEnvelope(
                available=False,
                error="cstm_lattice not installed — bridge disabled",
            )
        try:
            result = self._instance.run(task_text, cognitive_load=cognitive_load)
            return LatticeEnvelope(
                available=True,
                session_id=getattr(result, "session_id", ""),
                zone=getattr(getattr(result, "zone", None), "value", ""),
                qa_pass=bool(getattr(result, "qa_pass", False)),
                yaml_frontmatter=str(getattr(result, "yaml_frontmatter", "")),
                persisted_path=str(getattr(result, "persisted_path", "")),
            )
        except Exception as e:
            return LatticeEnvelope(available=True, error=f"lattice error: {e}")
