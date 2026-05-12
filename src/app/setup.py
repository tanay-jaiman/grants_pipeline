#!/usr/bin/env python3

from pathlib import Path


ENV_TEMPLATE = """OPENROUTESERVICE_API_KEY=
GOOGLE_MAPS_API_KEY=
"""


def ensure_prerequisites():
    Path("input").mkdir(exist_ok=True)
    Path("output").mkdir(exist_ok=True)
    Path("data/cache").mkdir(parents=True, exist_ok=True)

    env_path = Path(".env")

    if not env_path.exists():
        env_path.write_text(ENV_TEMPLATE)


if __name__ == "__main__":
    ensure_prerequisites()
