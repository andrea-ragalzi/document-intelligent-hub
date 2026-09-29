"""Deterministic production-source size gate; no application imports or writes."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = {
    "backend": ("backend/app",),
    "frontend": (
        "frontend/app",
        "frontend/components",
        "frontend/hooks",
        "frontend/lib",
        "frontend/contexts",
        "frontend/stores",
        "frontend/providers",
    ),
}
EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".mts", ".css"}
EXCLUDED_DIRS = {"__pycache__", "node_modules", "migrations", "generated"}


def source_files(root: Path, area: str) -> list[Path]:
    """Include new/untracked source, but not generated declarations or migrations."""
    paths = {
        path
        for directory in SOURCE_DIRS[area]
        for path in (root / directory).rglob("*")
        if path.is_file()
        and path.suffix in EXTENSIONS
        and not path.name.endswith(".d.ts")
        and not EXCLUDED_DIRS.intersection(path.relative_to(root).parts)
    }
    if area == "backend" and (root / "backend/main.py").exists():
        paths.add(root / "backend/main.py")
    return sorted(paths)


def check(root: Path, area: str, exceptions: dict) -> list[str]:
    """Return failures; every file over 400 physical lines remains visible."""
    errors = []
    seen = set()
    for path in source_files(root, area):
        name = path.relative_to(root).as_posix()
        seen.add(name)
        lines = len(path.read_text(encoding="utf-8").splitlines())
        entry = exceptions.get(name)
        limit = 600
        if entry is not None:
            if (
                not isinstance(entry.get("max_lines"), int)
                or not entry.get("reason", "").strip()
            ):
                errors.append(
                    f"{name}: exception needs max_lines and a concrete reason"
                )
                continue
            limit = entry["max_lines"]
            if limit <= 600 or lines <= 600:
                errors.append(f"{name}: remove obsolete size exception")
        if lines > limit:
            errors.append(
                f"{name}: {lines} lines exceeds {limit}; review responsibilities"
            )
        elif lines > 400:
            print(
                f"REVIEW {name}: {lines} lines"
                + (f"; ceiling {limit}" if entry else "")
            )
    for name in exceptions:
        if name.startswith(area + "/") and name not in seen:
            errors.append(f"{name}: stale or excluded size exception")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("area", choices=SOURCE_DIRS)
    args = parser.parse_args()
    exceptions = json.loads((ROOT / "quality/size-exceptions.json").read_text())
    errors = check(ROOT, args.area, exceptions)
    for error in errors:
        print(f"ERROR {error}")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
