#!/usr/bin/env python3
"""Anti-hallucination check: every number in the AI-written section of report.md must exist in summary.json.

Usage: check_claims.py <run_dir>
Reads <run_dir>/report.md, takes the text under the heading that starts with "## B" (AI interpretation)
up to the next "## " heading, and looks up each number in summary.json. Exit 0 if all found, 1 otherwise.
Step labels (A1, T3...), thresholds from the group SLO and small counts (<= 10) are allowed.
"""
import json
import re
import sys
from pathlib import Path


def numbers(obj, out):
    if isinstance(obj, bool):
        return out
    if isinstance(obj, (int, float)):
        out.add(round(float(obj), 2))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            numbers(v, out)
            if re.fullmatch(r'\d+', str(k)):
                out.add(float(k))  # HTTP codes are dict keys
    elif isinstance(obj, list):
        for v in obj:
            numbers(v, out)
    return out


def main():
    run = Path(sys.argv[1])
    summary = json.loads((run / 'summary.json').read_text())
    text = (run / 'report.md').read_text()
    m = re.search(r'^## B.*?$(.*?)(?=^## |\Z)', text, re.S | re.M)
    if not m:
        print('report.md has no "## B" section')
        return 1
    section = re.sub(r'\b[ART]\d\b', '', m.group(1))  # drop step labels like A1, T3
    known = numbers(summary, set())
    bad = []
    for raw in re.findall(r'(?<![\w.])\d+(?:[.,]\d+)?', section):
        v = round(float(raw.replace(',', '.')), 2)
        if v > 10 and v not in known:
            bad.append(raw)
    if bad:
        print('Số không có trong summary.json (phải sửa hoặc ghi rõ nguồn):', ', '.join(sorted(set(bad))))
        return 1
    print(f'OK: mọi số trong mục B đều có trong summary.json ({len(known)} giá trị tham chiếu).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
