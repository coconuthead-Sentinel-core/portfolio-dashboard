"""CLI entrypoint: `python -m portfolio_dashboard --port 8000`"""
from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="portfolio_dashboard",
        description="Codex Concept Intake & Portfolio Dashboard")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db", default="codex.db",
                        help="SQLite path (default: codex.db; ':memory:' OK)")
    args = parser.parse_args()

    import uvicorn
    from .api import create_app
    app = create_app(db_path=args.db)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
