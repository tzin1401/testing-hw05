#!/usr/bin/env python3
"""Compare JMeter samples using Task 2's nearest-rank metrics and SLOs."""
import argparse
import hashlib
import json
import math
import platform
import socket
import subprocess
import sys
from pathlib import Path

try:
    from .jtl_truth import LABELS, load_jtl, metrics
except ImportError:
    from jtl_truth import LABELS, load_jtl, metrics

ROOT = Path(__file__).resolve().parent.parent
PLANS = {'smoke': '23120190_Load_20261117.jmx', 'nightly': '23120190_Load_20261117.jmx',
         'stress': '23120190_Stress_20261117.jmx', 'spike': '23120190_Spike_20261117.jmx',
         'soak': '23120190_Soak_20261118.jmx'}
PROFILES = {
    'smoke': {'threads': 30, 'rampup': 15, 'duration': 180, 'lock_percent': 5, 'stages': 'single group'},
    'nightly': {'threads': 50, 'rampup': 50, 'duration': 600, 'lock_percent': 5, 'stages': 'single group'},
    'stress': {'threads': [50, 100, 200, 290], 'rampup': 30, 'duration': 600, 'lock_percent': 5,
               'stages': 'four sequential groups, each duration 150s and ramp 30s; delay 0'},
    'spike': {'threads': [10, 190], 'rampup': 10, 'duration': 360, 'lock_percent': 5,
              'stages': 'concurrent baseline 10 users 360s ramp 10s; burst 190 users delay 120s duration 120s ramp 5s'},
    'soak': {'threads': 203, 'rampup': 60, 'duration': 720, 'lock_percent': 5, 'stages': 'single group'},
}
DATA = ROOT / 'data'
SLO = ROOT / 'results/cpt/slo.json'
FILTER = 'latency/main after initial ramp; error all whole run and 120s windows after initial ramp; sample start timestamps'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metadata(path, profile_name):
    profile = PROFILES[profile_name]
    plan = ROOT / 'test-plans' / PLANS[profile_name]
    commit = subprocess.check_output(['git', '-C', str(ROOT / 'eshop-sut'), 'rev-parse', 'HEAD'], text=True).strip()
    return {'source_jtl': str(path.resolve()), 'source_sha256': digest(path), 'source_commit': commit,
            'profile': {'name': profile_name, **profile}, 'plan': str(plan.relative_to(ROOT)),
            'filter': FILTER, 'machine': {'hostname': socket.gethostname(), 'platform': platform.platform(), 'machine': platform.machine()},
            'plan_sha256': digest(plan), 'data_sha256': {p.name: digest(p) for p in sorted(DATA.glob('*.csv'))}}


def sidecar(path):
    return Path(str(path) + '.meta.json')


def measure(path, meta):
    samples = load_jtl(path)
    origin = min(s[0] for s in samples)
    start = origin + meta['profile']['rampup'] * 1000
    end = max(s[0] + s[1] for s in samples)
    post = [s for s in samples if s[0] >= start]
    main = [s for s in post if s[2] in LABELS]
    windows = []
    for lower in range(start, end, 120000):
        upper = min(lower + 120000, end)
        window = metrics([s for s in samples if lower <= s[0] < upper])
        windows.append({'start_ms': lower - origin, 'end_ms': upper - origin,
                        'partial': upper - lower < 120000, 'metrics': window})
    return {'labels': {label: metrics([s for s in main if s[2] == label]) for label in LABELS},
            'all': metrics(samples), 'main': metrics(main), 'error_windows': windows}


def evaluate(candidate, baseline, slo, minimum):
    failures, incomplete = [], []
    relative_ready = baseline is not None and candidate['main']['count'] >= 1000 and baseline['main']['count'] >= 1000
    for label in LABELS:
        current = candidate['labels'][label]
        old = baseline['labels'][label] if baseline else None
        if current['count'] < minimum:
            incomplete.append(f'{label}: candidate has fewer than {minimum} samples')
        else:
            for p in ('p95_ms', 'p99_ms'):
                if current[p] > slo['labels'][label][p]:
                    failures.append(f'{label}: {p} exceeds SLO')
            if relative_ready and old['count'] >= minimum and current['p95_ms'] * 5 > old['p95_ms'] * 6 and current['p95_ms'] - old['p95_ms'] >= 5:
                failures.append(f'{label}: p95 regression')
        if old and old['count'] < minimum:
            incomplete.append(f'{label}: baseline has fewer than {minimum} samples')
    if candidate['main']['count'] < 1000 or (baseline and baseline['main']['count'] < 1000):
        incomplete.append('fewer than 1000 main samples per run')
    if candidate['all']['error_pct'] > slo['error_pct']:
        failures.append('whole-run all-sample error rate exceeds SLO')
    if not candidate['error_windows']:
        incomplete.append('no post-ramp error windows')
    for window in candidate['error_windows']:
        m = window['metrics']
        if not m['count']:
            incomplete.append(f"empty error window {window['start_ms']}-{window['end_ms']} ms")
        elif m['error_pct'] > slo['error_pct']:
            failures.append(f"error window {window['start_ms']}-{window['end_ms']} ms exceeds SLO")
    return ('FAIL' if failures else 'INCONCLUSIVE' if incomplete else 'PASS'), failures, incomplete


def load_slo(path):
    slo = json.loads(path.read_text())
    values = [slo['error_pct']]
    values.extend(slo['labels'][label][key] for label in LABELS for key in ('p95_ms', 'p99_ms'))
    if any(type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in values) or values[0] > 100:
        raise ValueError('invalid SLO thresholds')
    return slo


def check_policy(baseline_path, slo_path, profile_name):
    slo = load_slo(slo_path)
    base = json.loads(baseline_path.read_text())
    bm = base['metadata']
    if base['status'] != 'PASS' or base['min_samples'] < 500 or base['slo_sha256'] != digest(slo_path):
        raise ValueError('baseline not approved/passing or SLO hash mismatch')
    if bm['profile'] != {'name': profile_name, **PROFILES[profile_name]} or bm['filter'] != FILTER:
        raise ValueError('baseline profile/filter mismatch')
    machine = {'hostname': socket.gethostname(), 'platform': platform.platform(), 'machine': platform.machine()}
    plan = ROOT / 'test-plans' / PLANS[profile_name]
    data = {p.name: digest(p) for p in sorted(DATA.glob('*.csv'))}
    if (not all(bm.get(k) for k in ('source_jtl', 'source_sha256', 'source_commit')) or
            bm['machine'] != machine or bm['plan'] != str(plan.relative_to(ROOT)) or
            bm['plan_sha256'] != digest(plan) or not data or bm['data_sha256'] != data):
        raise ValueError('baseline provenance or environment mismatch')
    measured = base['metrics']
    if measured['main']['count'] < 1000:
        raise ValueError('baseline has fewer than 1000 main samples')
    for label in LABELS:
        m = measured['labels'][label]
        if m['count'] < 500 or not isinstance(m['p95_ms'], (int, float)) or not isinstance(m['p99_ms'], (int, float)):
            raise ValueError(f'invalid baseline metrics for {label}')
    if evaluate(measured, None, slo, 500)[0] != 'PASS':
        raise ValueError('baseline metrics do not pass the active SLO')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--candidate', type=Path)
    parser.add_argument('--make-baseline', type=Path)
    parser.add_argument('--slo', type=Path, default=SLO)
    parser.add_argument('--min-samples', type=int, default=500)
    parser.add_argument('--write-metadata', type=Path)
    parser.add_argument('--check-policy', action='store_true')
    parser.add_argument('--profile', choices=PLANS, default='smoke')
    args = parser.parse_args()
    try:
        if args.min_samples < 500:
            raise ValueError('minimum must be at least 500 per label')
        if args.check_policy:
            check_policy(args.baseline, args.slo, args.profile)
            return 0
        if args.write_metadata:
            meta = metadata(args.write_metadata, args.profile)
            with sidecar(args.write_metadata).open('x') as f:
                json.dump(meta, f, indent=2)
            return 0
        if bool(args.candidate) == bool(args.make_baseline):
            raise ValueError('choose exactly one of --candidate and --make-baseline')
        path = args.candidate or args.make_baseline
        meta = json.loads(sidecar(path).read_text())
        required = ('source_jtl', 'source_sha256', 'source_commit', 'profile', 'filter', 'machine', 'plan', 'plan_sha256', 'data_sha256')
        if any(not meta.get(k) for k in required) or meta['source_sha256'] != digest(path) or meta['filter'] != FILTER:
            raise ValueError('missing or invalid candidate metadata')
        if meta['profile'].get('name') not in PROFILES or meta['profile'] != {'name': meta['profile']['name'], **PROFILES[meta['profile']['name']]} or meta['plan'] != 'test-plans/' + PLANS[meta['profile']['name']] or set(meta['machine']) != {'hostname', 'platform', 'machine'} or not all(meta['machine'].values()):
            raise ValueError('incomplete profile or machine metadata')
        slo = load_slo(args.slo)
        result = measure(path, meta)
        baseline = None
        base = None
        compatibility = []
        if args.candidate:
            try:
                base = json.loads(args.baseline.read_text())
                baseline = base['metrics']
                bm = base['metadata']
                for key in ('profile', 'filter', 'machine', 'plan_sha256', 'data_sha256'):
                    if not bm.get(key) or bm[key] != meta[key]:
                        compatibility.append(f'incompatible or missing {key}')
                if base.get('status') != 'PASS' or not bm.get('source_commit') or not bm.get('source_sha256') or not bm.get('source_jtl') or base.get('min_samples', 0) < 500:
                    compatibility.append('incomplete baseline provenance')
                if base.get('slo_sha256') != digest(args.slo):
                    compatibility.append('baseline SLO policy hash mismatch')
            except (OSError, ValueError, KeyError, TypeError) as exc:
                compatibility.append(f'baseline unavailable or invalid: {exc}')
        status, failures, incomplete = evaluate(result, baseline if not compatibility else None, slo, args.min_samples)
        incomplete.extend(compatibility)
        if compatibility and status == 'PASS':
            status = 'INCONCLUSIVE'
        print('Label                         count  p95  p99  errors')
        for label, m in result['labels'].items():
            print(f"{label:29} {m['count']:5} {str(m['p95_ms']):>4} {str(m['p99_ms']):>4} {m['error_count']:6}")
        for group in ('all', 'main'):
            m = result[group]
            print(f"{group}: errors {m['error_count']}/{m['count']} ({m['error_pct']}%)")
        for window in result['error_windows']:
            m = window['metrics']
            print(f"window {window['start_ms']}-{window['end_ms']} ms{' partial' if window['partial'] else ''}: errors {m['error_count']}/{m['count']} ({m['error_pct']}%)")
        print(status, '; '.join(failures + incomplete))
        report = {'status': status, 'failures': failures, 'inconclusive': incomplete, 'metadata': meta, 'metrics': result,
                  'slo_source': str(args.slo), 'slo_sha256': digest(args.slo),
                  'baseline': {'path': str(args.baseline), 'sha256': digest(args.baseline),
                               'metadata': base['metadata'], 'metrics': base['metrics']} if base and not compatibility else None}
        if args.make_baseline:
            if status == 'PASS':
                report['min_samples'] = args.min_samples
                with args.baseline.open('w') as f:
                    json.dump(report, f, indent=2)
            else:
                print('Baseline not created', file=sys.stderr)
        else:
            out = path.parent / (path.stem + '_gate.json')
            with out.open('w') as f:
                json.dump(report, f, indent=2)
        return {'PASS': 0, 'FAIL': 1, 'INCONCLUSIVE': 2}[status]
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        if args.candidate and not args.write_metadata:
            try:
                out = args.candidate.parent / (args.candidate.stem + '_gate.json')
                with out.open('w') as f:
                    json.dump({'status': 'INCONCLUSIVE', 'inconclusive': [str(exc)]}, f, indent=2)
            except OSError:
                pass
        print(f'INCONCLUSIVE: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
