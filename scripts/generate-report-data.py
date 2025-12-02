#!/usr/bin/env python3
"""
Generate quality gate report data in JSON format.
This script reads temporary result files and outputs a JSON report with timestamp.
"""

import json
import os
import sys
import time


def read_temp_file(temp_dir: str, filename: str, default: str = "") -> str:
    """Read content from a temporary file."""
    try:
        with open(os.path.join(temp_dir, filename), 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return default


def generate_report_json(temp_dir: str, report_path: str) -> None:
    """Generate the quality gate report JSON file."""

    # Read previous timestamp to ensure strict ordering
    last_timestamp_ms = 0
    if os.path.exists(report_path):
        try:
            with open(report_path, 'r') as f:
                old_data = json.load(f)
                last_timestamp_ms = old_data.get('timestampMs', 0)
        except:
            pass

    # Calculate new timestamp with strict ascending guarantee
    current_timestamp_ms = int(time.time() * 1000)
    if current_timestamp_ms <= last_timestamp_ms:
        current_timestamp_ms = last_timestamp_ms + 1

    # Format human readable timestamp
    seconds = current_timestamp_ms / 1000.0
    timestamp_human = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(seconds))
    timestamp_human += f".{current_timestamp_ms % 1000:03d}"

    # Read all result files
    prettier_status = read_temp_file(temp_dir, 'prettier_status', 'PENDING')
    prettier_issues = read_temp_file(temp_dir, 'prettier_count', '0')
    prettier_details = read_temp_file(temp_dir, 'prettier_details', '')

    typescript_status = read_temp_file(temp_dir, 'typescript_status', 'PENDING')
    typescript_errors = read_temp_file(temp_dir, 'typescript_errors', '0')
    typescript_warnings = read_temp_file(temp_dir, 'typescript_warnings', '0')
    typescript_details = read_temp_file(temp_dir, 'typescript_details', '')

    eslint_status = read_temp_file(temp_dir, 'eslint_status', 'PENDING')
    eslint_errors = read_temp_file(temp_dir, 'eslint_errors', '0')
    eslint_warnings = read_temp_file(temp_dir, 'eslint_warnings', '0')
    eslint_details = read_temp_file(temp_dir, 'eslint_details', '')

    complexity_status = read_temp_file(temp_dir, 'complexity_status', 'PENDING')
    complexity_violations = read_temp_file(temp_dir, 'complexity_count', '0')
    complexity_details = read_temp_file(temp_dir, 'complexity_details', '')

    black_status = read_temp_file(temp_dir, 'black_status', 'PENDING')
    black_issues = read_temp_file(temp_dir, 'black_count', '0')
    black_details = read_temp_file(temp_dir, 'black_details', '')

    mypy_status = read_temp_file(temp_dir, 'mypy_status', 'PENDING')
    mypy_errors = read_temp_file(temp_dir, 'mypy_errors', '0')
    mypy_notes = read_temp_file(temp_dir, 'mypy_notes', '0')
    mypy_details = read_temp_file(temp_dir, 'mypy_details', '')

    pylint_status = read_temp_file(temp_dir, 'pylint_status', 'PENDING')
    pylint_errors = read_temp_file(temp_dir, 'pylint_errors', '0')
    pylint_warnings = read_temp_file(temp_dir, 'pylint_warnings', '0')
    pylint_conventions = read_temp_file(temp_dir, 'pylint_conventions', '0')
    pylint_refactors = read_temp_file(temp_dir, 'pylint_refactors', '0')
    pylint_info_raw = read_temp_file(temp_dir, 'pylint_info', '0')
    pylint_details = read_temp_file(temp_dir, 'pylint_details', '')

    # Combine conventions, refactors, and info into single "info" count
    try:
        pylint_info_total = int(pylint_conventions) + int(pylint_refactors) + int(pylint_info_raw)
    except (ValueError, TypeError):
        pylint_info_total = 0

    lizard_status = read_temp_file(temp_dir, 'lizard_status', 'PENDING')
    lizard_violations = read_temp_file(temp_dir, 'lizard_count', '0')
    lizard_details = read_temp_file(temp_dir, 'lizard_details', '')

    overall_status = sys.argv[2] if len(sys.argv) > 2 else "RUNNING"

    # Helper to format severity with multiple levels
    def format_severity(*parts):
        """Format severity string, showing only non-zero values."""
        formatted = []
        for count, label in parts:
            try:
                count_int = int(count)
                if count_int > 0:
                    formatted.append(f"{count_int} {label}")
            except (ValueError, TypeError):
                # Skip N/A or invalid values
                continue
        return ", ".join(formatted) if formatted else "0 issues"

    # Helper to format single value
    def format_single(count, label):
        """Format single severity value."""
        try:
            count_int = int(count)
            return f"{count_int} {label}" if count_int > 0 else f"0 {label}"
        except (ValueError, TypeError):
            return f"0 {label}"

    # Build JSON structure
    data = {
        "timestamp": timestamp_human,
        "timestampMs": current_timestamp_ms,
        "overallStatus": overall_status,
        "terminalOutput": "",
        "frontend": [
            {
                "name": "Prettier",
                "role": "Code Formatting",
                "status": prettier_status,
                "severity": format_single(prettier_issues, "files"),
                "details": prettier_details
            },
            {
                "name": "TypeScript",
                "role": "Type Checking & Compilation",
                "status": typescript_status,
                "severity": format_severity((typescript_errors, "errors"), (typescript_warnings, "warnings")),
                "details": typescript_details
            },
            {
                "name": "ESLint",
                "role": "Linter (Quality)",
                "status": eslint_status,
                "severity": format_severity((eslint_errors, "errors"), (eslint_warnings, "warnings")),
                "details": eslint_details
            },
            {
                "name": "ESLint Complexity",
                "role": "Cyclomatic Complexity (Max 15)",
                "status": complexity_status,
                "severity": format_single(complexity_violations, "violations"),
                "details": complexity_details
            }
        ],
        "backend": [
            {
                "name": "Black",
                "role": "Code Formatting",
                "status": black_status,
                "severity": format_single(black_issues, "files"),
                "details": black_details
            },
            {
                "name": "MyPy",
                "role": "Type Checking (Strict)",
                "status": mypy_status,
                "severity": format_severity((mypy_errors, "errors"), (mypy_notes, "notes")),
                "details": mypy_details
            },
            {
                "name": "Pylint",
                "role": "Linter (Quality)",
                "status": pylint_status,
                "severity": format_severity((pylint_errors, "errors"), (str(pylint_warnings), "warnings"), (str(pylint_info_total), "info")),
                "details": pylint_details
            },
            {
                "name": "Lizard",
                "role": "Cyclomatic Complexity (Max 15)",
                "status": lizard_status,
                "severity": format_single(lizard_violations, "violations"),
                "details": lizard_details
            }
        ]
    }

    # Write JSON file
    with open(report_path, 'w') as f:
        json.dump(data, f, indent=4)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: generate-report-data.py <temp_dir> <overall_status> <report_path>")
        sys.exit(1)

    temp_dir = sys.argv[1]
    overall_status = sys.argv[2]
    report_path = sys.argv[3] if len(sys.argv) > 3 else 'report-data.json'

    generate_report_json(temp_dir, report_path)
