"""DEV-only gate and runner entrypoint for the adaptive RAG benchmark.

The runner deliberately refuses to make an LLM call unless a non-secret PROD
configuration snapshot proves that the DEV process is comparable.  It never
opens a production Chroma directory and always creates a new temporary local
directory for its index.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any

from dotenv import dotenv_values, load_dotenv
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


ROOT = Path(__file__).resolve().parents[1]
TASKS_PATH = ROOT / "benchmarks" / "adaptive_rag_tasks.json"
LUNA_MODEL = "gpt-5.6-luna"
EXPECTED_DOCUMENTS = {
    "Analisi Comportamentale Raptor.pdf",
    "Contratto Legale Classificato.pdf",
    "InGen: Inventario Pre-Operativo Isla Sorna.pdf",
    "InGen: Memorandum - Decisione di Classificazione (Codice VELO).pdf",
    "Northbyte_Systems_Payslip_August_2026.pdf",
    "Northbyte_Systems_Payslip_July_2026.pdf",
    "Asteria_Employee_Health_Benefits_Guide_2026.pdf",
}


@dataclass(frozen=True)
class GateResult:
    """Non-secret result of the DEV/PROD parity gate."""

    status: str
    blockers: list[str]
    dev: dict[str, Any]
    production: dict[str, Any] | None


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prod-config-snapshot",
        type=Path,
        help=(
            "Non-secret JSON from Railway/deployment configuration. It must contain "
            "model, timeout_seconds, max_retries, prompt_digests, and stages."
        ),
    )
    parser.add_argument(
        "--output-dir", type=Path, help="Directory for the isolated benchmark artefacts."
    )
    parser.add_argument(
        "--prepare-july-fixture",
        action="store_true",
        help="Create the declared synthetic July payslip in --output-dir only.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Reserved for the full execution phase; requires a passing parity gate.",
    )
    return parser.parse_args()


def _prompt_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_dev_configuration() -> dict[str, Any]:
    """Load DEV values without emitting credentials or copying them elsewhere."""
    values = dotenv_values(ROOT / ".env.local")
    # The application normally performs this load in ``main.py``. Reproduce it
    # here because this command intentionally does not import the HTTP app.
    load_dotenv(ROOT / ".env.local", override=False)
    from app.core.config import settings  # pylint: disable=import-outside-toplevel

    return {
        "environment": "DEV",
        "model": settings.LLM_MODEL,
        "openai_key_configured": bool(values.get("OPENAI_API_KEY")),
        "timeout_seconds": settings.OPENAI_TIMEOUT_SECONDS,
        "max_retries": settings.OPENAI_MAX_RETRIES,
        "reasoning_effort": None,
        "temperature": None,
        "structured_output": {
            "parser": "JSON parser over text completion",
            "classification": "Pydantic QueryClassification",
            "answer": "Pydantic AnswerWithEvidence",
        },
        "prompt_digests": {
            "rag": hashlib.sha256(settings.RAG_SYSTEM_PROMPT.encode()).hexdigest(),
            "classification": hashlib.sha256(
                settings.CLASSIFICATION_PROMPT_TEMPLATE.encode()
            ).hexdigest(),
            "reformulation": hashlib.sha256(
                settings.QUERY_REFORMULATION_PROMPT.encode()
            ).hexdigest(),
        },
    }


def _load_snapshot(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {"model", "timeout_seconds", "max_retries", "prompt_digests", "stages"}
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(f"Production snapshot is incomplete: {', '.join(missing)}")
    return payload


def _parity_gate(dev: dict[str, Any], production: dict[str, Any] | None) -> GateResult:
    blockers: list[str] = []
    if dev["model"] != LUNA_MODEL:
        blockers.append(f"DEV model is {dev['model']!r}, expected {LUNA_MODEL!r}.")
    if not dev["openai_key_configured"]:
        blockers.append("DEV OpenAI key is not configured.")
    if production is None:
        blockers.append("No non-secret production configuration snapshot was supplied.")
    else:
        for key in ("model", "timeout_seconds", "max_retries", "prompt_digests"):
            if production.get(key) != dev.get(key):
                blockers.append(f"DEV and PROD differ for {key}.")
        if production.get("model") != LUNA_MODEL:
            blockers.append("Production snapshot does not resolve gpt-5.6-luna.")
    return GateResult(
        status="PASS" if not blockers else "BLOCKED",
        blockers=blockers,
        dev=dev,
        production=production,
    )


def _july_payslip_pdf() -> bytes:
    """Create a declared benchmark-only PDF; it is never uploaded to production."""
    text = (
        "Northbyte Systems Oy\\n"
        "PAYSLIP / PALKKALASKELMA\\n"
        "Pay period 01.07.2026 - 31.07.2026 | Payment date 31.07.2026\\n"
        "Employee Elias Korhonen\\n"
        "TOTAL TAXABLE GROSS EUR 5,400.00\\n"
        "NET PAYABLE EUR 3,400.00\\n"
        "Payment method Bank transfer\\n"
        "Synthetic benchmark fixture."
    )
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    writer = PdfWriter()
    page = writer.add_blank_page(612, 792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
    )
    lines = escaped.split("\\n")
    commands = ["BT /F1 12 Tf 72 720 Td"]
    for line in lines:
        commands.append(f"({line}) Tj")
        commands.append("0 -18 Td")
    commands.append("ET")
    stream = DecodedStreamObject()
    stream.set_data(" ".join(commands).encode("latin-1"))
    page.replace_contents(stream)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def _write_july_fixture(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / "Northbyte_Systems_Payslip_July_2026.pdf"
    destination.write_bytes(_july_payslip_pdf())
    return destination


def _validate_task_set() -> dict[str, int]:
    payload = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    tasks = payload["tasks"]
    counts = {route: sum(task["route"] == route for task in tasks) for route in ("DIRECT", "COMPUTE", "RAG")}
    if counts != {"DIRECT": 10, "COMPUTE": 8, "RAG": 12}:
        raise ValueError(f"Unexpected route distribution: {counts}")
    if len(tasks) != 30:
        raise ValueError("The benchmark must contain exactly 30 primary tasks.")
    if set(payload["corpus"]["documents"]) != EXPECTED_DOCUMENTS:
        raise ValueError("The frozen corpus declaration has changed.")
    return counts


def _metadata() -> dict[str, Any]:
    dependencies = subprocess.check_output(
        [sys.executable, "-m", "pip", "show", "chromadb", "langchain-openai", "openai", "pypdf"],
        text=True,
    )
    return {
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT.parent, text=True).strip(),
        "date": date.today().isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "dependencies": dependencies,
        "index_policy": "new temporary local Chroma directory; synthetic benchmark user only",
        "pricing_source": "https://developers.openai.com/api/docs/models/gpt-5.6-luna",
        "prices_usd_per_million_tokens": {"input": 0.20, "cached_input": 0.02, "output": 1.20},
    }


def main() -> None:
    args = _arguments()
    # Environment variables affect this isolated runner process only. They are
    # set before importing any application configuration or OpenAI adapter.
    os.environ["ENVIRONMENT"] = "development"
    os.environ["LLM_MODEL"] = LUNA_MODEL
    output_dir = args.output_dir or Path(tempfile.mkdtemp(prefix="dih-adaptive-benchmark-"))
    dev = _load_dev_configuration()
    production = _load_snapshot(args.prod_config_snapshot)
    gate = _parity_gate(dev, production)
    report: dict[str, Any] = {
        "metadata": _metadata(),
        "task_distribution": _validate_task_set(),
        "parity_gate": asdict(gate),
        "output_dir": str(output_dir),
    }
    if args.prepare_july_fixture:
        report["generated_benchmark_fixture"] = str(_write_july_fixture(output_dir))
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "preflight.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if args.run and gate.status != "PASS":
        raise SystemExit("Refusing DEV benchmark because the production-parity gate is blocked.")
    if args.run:
        raise SystemExit("Parity passed, but the execution phase has not yet been implemented.")


if __name__ == "__main__":
    main()
