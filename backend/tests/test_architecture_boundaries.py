"""Lightweight dependency-direction regression tests."""

import ast
from importlib.util import resolve_name
from pathlib import Path

import pytest

APP_ROOT = Path(__file__).resolve().parents[1] / "app"

# Freeze known debt by import edge, not by exempting entire service files.
SERVICE_EXCEPTIONS = {
    "translation_service.py": ("app.infrastructure.openai_translation_adapter",),
    "email_service.py": ("app.infrastructure.resend_email_adapter",),
    "document_file_storage.py": ("app.infrastructure.local_file_storage",),
    "usage_tracking_service.py": ("app.infrastructure.firestore_usage_tracker",),
    "tier_limit_service.py": (
        "firebase_admin.auth",
        "app.infrastructure.firebase_config.load_app_config",
    ),
    "demo_document_state_service.py": ("firebase_admin.firestore",),
    "shared_demo_corpus_service.py": ("app.core.auth.DEMO_WORKSPACE_ID",),
}
PROVIDERS = (
    "firebase_admin",
    "google.cloud",
    "openai",
    "langchain_openai",
    "chromadb",
    "langchain_chroma",
    "cohere",
    "resend",
)
OUTER_LAYERS = (
    "app.routers",
    "app.dependencies",
    "app.infrastructure",
    "app.repositories",
    "app.db",
    "app.core.auth",
    "app.core.firebase",
    "fastapi",
    "starlette",
)


def _matches(name: str, prefixes: tuple[str, ...]) -> bool:
    return any(name == prefix or name.startswith(prefix + ".") for prefix in prefixes)


def _imports(module_path: Path, app_root: Path = APP_ROOT) -> set[str]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    package = ".".join(("app", *module_path.relative_to(app_root).parts[:-1]))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                module = resolve_name("." * node.level + module, package)
            imports.update(f"{module}.{alias.name}" for alias in node.names)
    return imports


@pytest.mark.parametrize(
    "layer,forbidden",
    [
        ("services", OUTER_LAYERS + PROVIDERS),
        ("ports", OUTER_LAYERS + PROVIDERS + ("app.services",)),
        ("schemas", OUTER_LAYERS + PROVIDERS + ("app.services",)),
        ("routers", ("app.db", "app.repositories", "chromadb", "langchain_chroma")),
    ],
)
def test_dependency_direction(layer: str, forbidden: tuple[str, ...]) -> None:
    offenders = {}
    for path in (APP_ROOT / layer).rglob("*.py"):
        relative = path.relative_to(APP_ROOT / layer).as_posix()
        allowed = SERVICE_EXCEPTIONS.get(relative, ()) if layer == "services" else ()
        violations = sorted(
            name
            for name in _imports(path)
            if _matches(name, forbidden) and not _matches(name, allowed)
        )
        if violations:
            offenders[relative] = violations
    assert offenders == {}


def test_service_exceptions_still_exist() -> None:
    for filename, allowed in SERVICE_EXCEPTIONS.items():
        imports = _imports(APP_ROOT / "services" / filename)
        for prefix in allowed:
            assert any(_matches(name, (prefix,)) for name in imports), (
                f"Remove obsolete architecture exception: {filename}: {prefix}"
            )


@pytest.mark.parametrize(
    "statement,expected",
    [
        ("from .. import routers", "app.routers"),
        ("from ..routers import query_router as router", "app.routers.query_router"),
        ("import app.routers.query_router as router", "app.routers.query_router"),
        ("from fastapi import Depends", "fastapi.Depends"),
    ],
)
def test_import_check_resolves_relative_and_aliased_imports(
    tmp_path: Path,
    statement: str,
    expected: str,
) -> None:
    path = tmp_path / "services" / "example.py"
    path.parent.mkdir()
    path.write_text(statement, encoding="utf-8")
    assert expected in _imports(path, tmp_path)
    assert _matches(expected, OUTER_LAYERS)


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
