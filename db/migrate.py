from __future__ import annotations

from pathlib import Path

from db.connection import init_db


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    db_path = root / "data" / "finance.db"
    init_db(db_path)
    print(f"Initialized database at {db_path}")


if __name__ == "__main__":
    main()
