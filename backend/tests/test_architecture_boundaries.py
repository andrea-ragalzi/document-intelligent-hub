"""Lightweight dependency-direction regression tests."""

import ast
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1] / "app"


def _imports(module_path: Path) -> set[str]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_services_do_not_import_routers() -> None:
    offenders = {
        path.name: sorted(name for name in _imports(path) if name.startswith("app.routers"))
        for path in (APP_ROOT / "services").glob("*.py")
        if any(name.startswith("app.routers") for name in _imports(path))
    }
    assert offenders == {}


def test_ports_do_not_import_framework_or_infrastructure_modules() -> None:
    forbidden_prefixes = (
        "app.infrastructure",
        "fastapi",
        "firebase_admin",
        "google.cloud",
        "openai",
        "langchain_openai",
        "chromadb",
    )
    offenders = {
        path.name: sorted(
            name for name in _imports(path) if name.startswith(forbidden_prefixes)
        )
        for path in (APP_ROOT / "ports").glob("*.py")
        if any(name.startswith(forbidden_prefixes) for name in _imports(path))
    }
    assert offenders == {}


def test_migrated_llm_services_do_not_construct_provider_clients() -> None:
    migrated_services = (
        "query_expansion_service.py",
        "query_parser_service.py",
        "translation_service.py",
    )
    forbidden_calls = {"ChatOpenAI", "OpenAI"}
    offenders: dict[str, list[str]] = {}
    for filename in migrated_services:
        tree = ast.parse((APP_ROOT / "services" / filename).read_text(encoding="utf-8"))
        calls = sorted(
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in forbidden_calls
        )
        if calls:
            offenders[filename] = calls
    assert offenders == {}
