#!/usr/bin/env python3
"""Classify SUT changes for the fixed API workload (change map 16a)."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND_FILES = {'backend/package.json', 'backend/package-lock.json', 'run_servers.sh'}
FRONTENDS = ('frontend-admin/', 'frontend-mobile/', 'frontend-web/')


def classify(path):
    if (path.startswith('backend/') and path.endswith('.js')) or path in BACKEND_FILES:
        return 'backend'
    if path.startswith(FRONTENDS) or path.endswith('.md'):
        return 'non-impacting'
    return 'unknown'


def decide(files, message):
    message = message.lower()
    if '[perf]' in message:
        return 'run', '[perf] explicitly requests a run'
    if '[skip perf]' in message:
        return 'skip', '[skip perf] overrides changes, including backend; regression risk is accepted'
    kinds = {classify(f) for f in files}
    if 'backend' in kinds:
        return 'run', 'backend change'
    if 'unknown' in kinds:
        return 'run', 'unknown impact; conservative run'
    return 'skip', 'no impact on the fixed API workload'


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT / 'eshop-sut'), *args])


def main():
    if len(sys.argv) != 3:
        sys.exit('usage: perf_decide.py BASE HEAD')
    base, head = sys.argv[1:]
    files = git('diff', '--no-renames', '--name-only', '-z', base, head).decode().split('\0')[:-1]
    message = git('show', '-s', '--format=%B', head).decode()
    decision, reason = decide(files, message)
    print(json.dumps({'decision': decision, 'reason': reason, 'files': files}, ensure_ascii=False))


if __name__ == '__main__':
    main()
