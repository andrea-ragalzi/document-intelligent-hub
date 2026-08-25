"""Export exact main-dependency constraints from a Poetry lock file."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path


def export_constraints(lock_path: Path, output_path: Path) -> None:
    """Write one exact pip constraint per package in Poetry's main group."""
    lock_data = tomllib.loads(lock_path.read_text(encoding="utf-8"))
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

    constraints = "".join(
        f"{name}=={version}\n" for name, version in sorted(versions.items())
    )
    output_path.write_text(constraints, encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: export_lock_constraints.py POETRY_LOCK OUTPUT_CONSTRAINTS"
        )
    export_constraints(Path(sys.argv[1]), Path(sys.argv[2]))
