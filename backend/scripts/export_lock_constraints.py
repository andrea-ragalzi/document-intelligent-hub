"""Export exact main-dependency constraints from a Poetry lock file."""

from __future__ import annotations

import tomllib
from pathlib import Path

LOCK_PATH = Path(__file__).resolve().parents[1] / "poetry.lock"


def export_constraints() -> str:
    """Return one exact pip constraint per package in Poetry's main group."""
    lock_data = tomllib.loads(LOCK_PATH.read_text(encoding="utf-8"))
    versions: dict[str, str] = {}

    for package in lock_data.get("package", []):
        if "main" not in package.get("groups", []):
            continue

        name = str(package["name"])
        version = str(package["version"])
        previous = versions.setdefault(name, version)
        if previous != version:
            raise ValueError(
                f"Cannot export conflicting locked versions for {name}: "
                f"{previous} and {version}"
            )

    return "".join(
        f"{name}=={version}\n" for name, version in sorted(versions.items())
    )


if __name__ == "__main__":
    print(export_constraints(), end="")
