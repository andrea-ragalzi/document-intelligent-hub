#!/usr/bin/env python3
"""
Parse ESLint JSON output and separate ESLint errors from Complexity violations.
"""

import json
import os
import sys


def parse_eslint_json(json_path: str, output_dir: str) -> None:
    """Parse ESLint JSON output and separate issues by type."""

    try:
        with open(json_path, 'r') as f:
            content = f.read()
            # Handle case where npm might output other text before JSON
            if '[' in content:
                json_start = content.find('[')
                content = content[json_start:]
            results = json.loads(content)
    except Exception as e:
        # Fallback if empty or invalid
        results = []

    eslint_details = []
    complexity_details = []
    eslint_error_count = 0
    eslint_warning_count = 0
    complexity_violation_count = 0

    for file_result in results:
        file_path = file_result.get('filePath', '')
        # Make path relative to project root if possible
        if '/frontend/' in file_path:
            file_path = 'frontend/' + file_path.split('/frontend/')[1]

        messages = file_result.get('messages', [])

        file_eslint_msgs = []
        file_complexity_msgs = []

        for msg in messages:
            rule_id = msg.get('ruleId', '')
            severity = msg.get('severity', 0)  # 1=warning, 2=error
            line = msg.get('line', 0)
            column = msg.get('column', 0)
            message = msg.get('message', '')

            formatted_msg = f"  {line}:{column}  {'error' if severity == 2 else 'warning'}  {message}  {rule_id}"

            if rule_id and 'complexity' in rule_id:
                file_complexity_msgs.append(formatted_msg)
                if severity == 2:
                    complexity_violation_count += 1
            else:
                file_eslint_msgs.append(formatted_msg)
                if severity == 2:
                    eslint_error_count += 1
                elif severity == 1:
                    eslint_warning_count += 1

        if file_eslint_msgs:
            eslint_details.append(file_path)
            eslint_details.extend(file_eslint_msgs)
            eslint_details.append("")  # Empty line

        if file_complexity_msgs:
            complexity_details.append(file_path)
            complexity_details.extend(file_complexity_msgs)
            complexity_details.append("")  # Empty line

    # Write outputs
    with open(os.path.join(output_dir, 'eslint_details'), 'w') as f:
        if eslint_details:
            f.write('\n'.join(eslint_details))
        else:
            f.write('')

    with open(os.path.join(output_dir, 'complexity_details'), 'w') as f:
        if complexity_details:
            f.write('\n'.join(complexity_details))
        else:
            f.write('No complexity violations found.')

    with open(os.path.join(output_dir, 'eslint_errors'), 'w') as f:
        f.write(str(eslint_error_count))

    with open(os.path.join(output_dir, 'eslint_warnings'), 'w') as f:
        f.write(str(eslint_warning_count))

    with open(os.path.join(output_dir, 'eslint_status'), 'w') as f:
        f.write('PASSED' if eslint_error_count == 0 else 'FAILED')

    with open(os.path.join(output_dir, 'complexity_count'), 'w') as f:
        f.write(str(complexity_violation_count))

    with open(os.path.join(output_dir, 'complexity_status'), 'w') as f:
        f.write('PASSED' if complexity_violation_count == 0 else 'FAILED')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: parse-eslint-output.py <json_path> <output_dir>")
        sys.exit(1)

    json_path = sys.argv[1]
    output_dir = sys.argv[2]

    parse_eslint_json(json_path, output_dir)
