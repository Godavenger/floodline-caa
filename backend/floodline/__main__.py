from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import Settings


def main():
    parser = argparse.ArgumentParser(description="Run and verify the synthetic Floodline prototype.")
    sub = parser.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--host", choices=["127.0.0.1", "localhost", "0.0.0.0"], default="127.0.0.1")
    sub.add_parser("migrate")
    evaluation = sub.add_parser("evaluate")
    evaluation.add_argument("--csv", type=Path)
    backup = sub.add_parser("backup")
    backup.add_argument("destination", type=Path)
    args = parser.parse_args()
    settings = Settings()
    if args.command == "serve":
        import uvicorn
        from .main import create_app
        settings.allowed_origins = (*settings.allowed_origins, f"http://127.0.0.1:{args.port}", f"http://localhost:{args.port}")
        uvicorn.run(create_app(settings), host=args.host, port=args.port, log_level="warning")
    elif args.command == "evaluate":
        from .evaluation import evaluate
        result = evaluate(settings, args.csv)
        print(json.dumps({key: result[key] for key in ["status", "mode", "independent_events", "usable_rows", "historical_accuracy_established", "candidate_promoted"]}, indent=2))
    else:
        from .database import Database
        db = Database(settings.database_url)
        if args.command == "migrate":
            db.migrate()
            print("Database migrations complete.")
        elif args.command == "backup":
            args.destination.parent.mkdir(parents=True, exist_ok=True)
            db.backup(args.destination)
            print(f"Backup written to {args.destination}.")


if __name__ == "__main__":
    main()
