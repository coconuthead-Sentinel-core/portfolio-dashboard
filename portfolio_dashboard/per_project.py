"""Per-project dashboard generator.

Clones the #23 dashboard pattern for any individual canon entry. Reads
canon + diagrams + always_on disciplines through the same aggregator
contract used by the main dashboard, then renders a self-contained
single-file HTML report — no server required, no build chain.

Usage:
    from portfolio_dashboard.per_project import (
        generate_dashboard_html, write_dashboard_for_canon_id,
        write_dashboards_for_all,
    )

    html = generate_dashboard_html(canon_entry, aggregator)

CLI:
    python -m portfolio_dashboard.per_project --canon-id 5 --out ./out
    python -m portfolio_dashboard.per_project --all --out ./out
"""
from __future__ import annotations

import html as _html
import json
from pathlib import Path
from typing import Any, Iterable

from .aggregator import PortfolioAggregator


def _esc(s: Any) -> str:
    return _html.escape(str(s if s is not None else ""))


def _slugify(name: str) -> str:
    out = []
    for ch in name.lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in (" ", "-", "_"):
            out.append("-")
    s = "".join(out)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-") or "project"


_CSS = """
:root {
  --bg: #0c1c35; --panel: #162c4c; --line: #4873a8; --accent: #58beff;
  --text: #eef4fc; --muted: #b7cae2; --warn: #ffb86c; --good: #7dd87d;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font: 14px/1.5 system-ui, "Segoe UI", sans-serif;
  min-height: 100vh;
}
header {
  padding: 18px 28px; border-bottom: 2px solid var(--accent);
  background: linear-gradient(180deg, var(--panel), var(--bg));
}
header h1 { margin: 0; font-size: 24px; }
.subtitle { color: var(--muted); font-size: 13px; margin-top: 4px; }
.canon-badge {
  background: var(--accent); color: var(--bg);
  padding: 2px 10px; border-radius: 12px; font-weight: 600;
  font-size: 12px; margin-right: 8px;
}
main { padding: 24px 28px 80px; max-width: 1200px; margin: 0 auto; }
section { margin-bottom: 32px; }
section h2 { color: var(--accent); margin-top: 0; }
.stats-grid {
  display: grid; gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
}
.stat-card {
  background: var(--panel); border-left: 3px solid var(--accent);
  padding: 12px 14px; border-radius: 4px;
}
.stat-card .label { color: var(--muted); font-size: 11px;
  text-transform: uppercase; letter-spacing: .8px; }
.stat-card .value { font-size: 28px; font-weight: 600; margin-top: 4px; }
table {
  width: 100%; border-collapse: collapse; background: var(--panel);
  border-radius: 4px; overflow: hidden; font-size: 13px;
}
th, td { padding: 8px 12px; text-align: left;
  border-bottom: 1px solid var(--line); }
th { background: rgba(0,0,0,.2); color: var(--accent); }
tr:last-child td { border-bottom: none; }
a { color: var(--accent); }
.gap-banner {
  background: rgba(255,184,108,.15); border-left: 3px solid var(--warn);
  padding: 10px 14px; border-radius: 4px; color: var(--warn);
}
.ok-banner {
  background: rgba(125,216,125,.10); border-left: 3px solid var(--good);
  padding: 10px 14px; border-radius: 4px; color: var(--good);
}
ol { background: var(--panel); padding: 12px 28px;
  border-radius: 4px; line-height: 1.8; }
ol li::marker { color: var(--accent); font-weight: 600; }
footer {
  position: fixed; bottom: 0; left: 0; right: 0;
  background: var(--panel); color: var(--muted);
  padding: 6px 28px; font-size: 11px; text-align: center;
  border-top: 1px solid var(--line);
}
pre { background: var(--panel); padding: 12px; border-radius: 4px;
  overflow-x: auto; font-size: 12px; border-left: 3px solid var(--line); }
"""


def _diagram_audit_keywords(name: str) -> list[str]:
    """Pull short tokens from the project name to use as audit keywords."""
    import re
    seen: list[str] = []
    for tok in re.findall(r"[A-Za-z]{4,}", name):
        t = tok.lower()
        if t not in seen:
            seen.append(t)
    return seen[:3]


def generate_dashboard_html(
    canon_entry: dict,
    aggregator: PortfolioAggregator,
    *,
    diagram_limit: int = 10,
) -> str:
    """Render a single-file HTML dashboard for one canon entry."""
    cid    = canon_entry.get("id", "?")
    name   = canon_entry.get("name", "Untitled")
    tier   = canon_entry.get("tier", "")
    tests  = canon_entry.get("tests", "—")
    url    = canon_entry.get("url", "")

    # Per-project diagram audit — try every keyword from the name
    diagram_hits: list[dict] = []
    for kw in _diagram_audit_keywords(name):
        for hit in aggregator.diagram_audit_for(kw, limit=diagram_limit):
            if hit not in diagram_hits:
                diagram_hits.append(hit)
        if len(diagram_hits) >= diagram_limit:
            break
    diagram_hits = diagram_hits[:diagram_limit]

    disc = aggregator.discipline_summary()

    rows = []
    rows.append("<!DOCTYPE html><html lang='en'><head>"
                "<meta charset='UTF-8'>"
                "<meta name='viewport' content='width=device-width, initial-scale=1.0'>"
                f"<title>Canon #{cid} — {_esc(name)}</title>"
                f"<style>{_CSS}</style></head><body>")

    rows.append("<header>"
                f"<h1><span class='canon-badge'>#{cid}</span>{_esc(name)}</h1>"
                f"<div class='subtitle'>{_esc(tier)} &middot; tests: {_esc(tests)} "
                + (f"&middot; <a href='{_esc(url)}' target='_blank'>repo</a>"
                   if str(url).startswith("https://") else "")
                + "</div></header>")

    rows.append("<main>")

    # Section: identity card
    parts_passing = 0
    if isinstance(tests, str) and "/" in tests:
        try:
            parts_passing = int(tests.split("/")[0])
        except ValueError:
            parts_passing = 0
    rows.append("<section><h2>Identity</h2><div class='stats-grid'>")
    rows.append(f"<div class='stat-card'><div class='label'>Canon ID</div>"
                f"<div class='value'>#{cid}</div></div>")
    rows.append(f"<div class='stat-card'><div class='label'>Tests passing</div>"
                f"<div class='value'>{parts_passing}</div></div>")
    rows.append(f"<div class='stat-card'><div class='label'>Tier</div>"
                f"<div class='value' style='font-size:15px'>{_esc(tier)}</div></div>")
    rows.append(f"<div class='stat-card'><div class='label'>GitHub</div>"
                f"<div class='value' style='font-size:13px'>"
                + (f"<a href='{_esc(url)}'>open</a>"
                   if str(url).startswith("https://") else "(local)")
                + "</div></div>")
    rows.append("</div></section>")

    # Section: diagram audit
    rows.append("<section><h2>Workbench Diagram Audit</h2>")
    if diagram_hits:
        rows.append(f"<div class='ok-banner'>{len(diagram_hits)} diagram-grade "
                    "hit(s) found in the unified media catalog.</div>")
        rows.append("<table><thead><tr>"
                    "<th>Filename</th><th>Kind</th><th>Categories</th>"
                    "<th>Glyphs</th></tr></thead><tbody>")
        for h in diagram_hits:
            rows.append(
                f"<tr><td>{_esc(h.get('filename'))}</td>"
                f"<td>{_esc(h.get('kind'))}</td>"
                f"<td>{_esc(', '.join(h.get('categories', [])))}</td>"
                f"<td>{_esc(h.get('glyph_tags', ''))}</td></tr>")
        rows.append("</tbody></table>")
    else:
        rows.append("<div class='gap-banner'>No diagram-grade hits found. "
                    "Capture and tag a visual spec for this project, then "
                    "re-run the audit.</div>")
    rows.append("</section>")

    # Section: disciplines (the always-on set this entry inherits)
    if not disc.error and disc.disciplines:
        rows.append("<section><h2>Inherited Always-On Disciplines</h2>")
        rows.append("<ol>")
        for d in disc.disciplines:
            rows.append(f"<li>{_esc(d)}</li>")
        rows.append("</ol></section>")

    # Section: machine-readable JSON for downstream tools
    rows.append("<section><h2>Machine-readable snapshot</h2>")
    snap = {
        "canon": canon_entry,
        "diagram_hits": diagram_hits,
        "disciplines": disc.disciplines if not disc.error else [],
    }
    rows.append("<pre>" + _esc(json.dumps(snap, indent=2)) + "</pre></section>")

    rows.append("</main>")
    rows.append("<footer>Per-project dashboard &middot; cloned from canon #23 "
                "&middot; Archivist of Wisdom co-creator role &middot; MIT</footer>")
    rows.append("</body></html>")
    return "\n".join(rows)


def write_dashboard_for_canon_id(canon_id: int, *,
                                 aggregator: PortfolioAggregator,
                                 out_dir: str | Path) -> Path:
    """Write one canon entry's dashboard. Returns the output path."""
    summary = aggregator.canon_summary()
    if summary.error:
        raise RuntimeError(f"canon module error: {summary.error}")
    entry = next((e for e in summary.entries if e.get("id") == canon_id), None)
    if entry is None:
        raise KeyError(f"canon entry id={canon_id} not found")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    fname = f"canon_{canon_id:02d}_{_slugify(entry.get('name',''))}_dashboard.html"
    path = out / fname
    path.write_text(generate_dashboard_html(entry, aggregator),
                    encoding="utf-8")
    return path


def write_dashboards_for_all(*, aggregator: PortfolioAggregator,
                             out_dir: str | Path,
                             only_ids: Iterable[int] | None = None
                             ) -> list[Path]:
    """Write one dashboard per canon entry. Returns the list of output paths."""
    summary = aggregator.canon_summary()
    if summary.error:
        raise RuntimeError(f"canon module error: {summary.error}")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    selected_ids = set(only_ids) if only_ids is not None else None
    paths: list[Path] = []
    for entry in summary.entries:
        if selected_ids is not None and entry.get("id") not in selected_ids:
            continue
        fname = f"canon_{entry.get('id', 0):02d}_{_slugify(entry.get('name',''))}_dashboard.html"
        p = out / fname
        p.write_text(generate_dashboard_html(entry, aggregator),
                     encoding="utf-8")
        paths.append(p)
    return paths


def _build_default_aggregator() -> PortfolioAggregator:
    """Best-effort: load cstm_skills modules from the standard portfolio root."""
    import importlib
    import sys
    cstm_root = Path(r"E:\AI_Memory_Core_Portfolio_Backup_2026-05-02")
    if cstm_root.exists() and str(cstm_root) not in sys.path:
        sys.path.insert(0, str(cstm_root))
    mods: dict[str, Any] = {}
    for name in ("canon", "diagrams", "always_on"):
        try:
            mods[name] = importlib.import_module(f"cstm_skills.{name}")
        except Exception:
            mods[name] = None
    return PortfolioAggregator(
        canon_module=mods["canon"],
        diagrams_module=mods["diagrams"],
        always_on_module=mods["always_on"],
    )


def _cli() -> None:
    import argparse
    p = argparse.ArgumentParser(prog="portfolio_dashboard.per_project",
                                description="Per-project canon dashboard generator")
    p.add_argument("--out", default="./_per_project_dashboards",
                   help="output directory (default: ./_per_project_dashboards)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--canon-id", type=int, help="single canon entry id")
    g.add_argument("--all", action="store_true",
                   help="generate one dashboard per canon entry")
    args = p.parse_args()

    aggregator = _build_default_aggregator()
    if args.all:
        paths = write_dashboards_for_all(aggregator=aggregator, out_dir=args.out)
        print(f"Wrote {len(paths)} dashboards to {args.out}")
        for p_ in paths:
            print(f"  - {p_}")
    else:
        path = write_dashboard_for_canon_id(args.canon_id,
                                            aggregator=aggregator,
                                            out_dir=args.out)
        print(f"Wrote: {path}")


if __name__ == "__main__":
    _cli()
