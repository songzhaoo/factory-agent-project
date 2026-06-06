from __future__ import annotations

from app.core import configure_logging
from app.db.database import Database


def main() -> None:
    configure_logging()
    Database(seed_demo=False)


if __name__ == "__main__":
    main()
