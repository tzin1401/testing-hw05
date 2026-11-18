#!/usr/bin/env python3
"""Compute metrics + SLO verdict from a raw JMeter .jtl (CSV) for one endpoint group. Stdlib only.

Usage: analyze.py <run.jtl> <group.json> <out_dir> [monitor.csv]
Writes <out_dir>/summary.json and summary.md. Exit 0 = PASS, 1 = FAIL, 2 = bad input.
Percentiles are nearest-rank on `elapsed`: sorted[ceil(p*n)-1]. Error = success=false.
"""
import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path


def pct(values, p):
    return values[math.ceil(p * len(values)) - 1] if values else None


def stats(rows):
    el = sorted(r['elapsed'] for r in rows)
    start = min(r['ts'] for r in rows)
    end = max(r['ts'] + r['elapsed'] for r in rows)
    span = max(end - start, 1)
    errors = sum(not r['ok'] for r in rows)
    return {'count': len(rows), 'errors': errors, 'error_pct': round(100 * errors / len(rows), 3),
            'rps': round(len(rows) * 1000 / span, 2), 'span_s': round(span / 1000, 1),
            'mean_ms': round(sum(el) / len(el), 1), 'p50_ms': pct(el, .5), 'p90_ms': pct(el, .9),
            'p95_ms': pct(el, .95), 'p99_ms': pct(el, .99), 'max_ms': el[-1],
            'codes': dict(Counter(r['code'] for r in rows))}


def load(path):
    rows = []
    with open(path, newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            rows.append({'ts': int(r['timeStamp']), 'elapsed': int(r['elapsed']), 'label': r['label'],
                         'code': r['responseCode'], 'ok': r['success'] == 'true',
                         'threads': int(r.get('allThreads') or 0)})
    return rows


def monitor(path):
    with open(path, newline='') as f:
        m = [r for r in csv.DictReader(f)]
    if not m:
        return None
    rss = [float(r['rss_mb']) for r in m]
    return {'samples': len(m), 'rss_first_mb': rss[0], 'rss_max_mb': max(rss), 'rss_last_mb': rss[-1],
            'note': 'cpu_percent from ps is a lifetime average, not instantaneous; use htop in the video for live CPU.'}


def main():
    if len(sys.argv) not in (4, 5):
        print(__doc__)
        return 2
    jtl, group_path, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    group = json.load(open(group_path, encoding='utf-8'))
    rows = load(jtl)
    if not rows:
        print(f'{jtl}: no samples')
        return 2
    steps = {s['label']: s for s in group.get('setup', []) + group['steps']}
    slo = group['slo']
    labels, verdicts = {}, []
    for label in sorted({r['label'] for r in rows}):
        m = stats([r for r in rows if r['label'] == label])
        step = steps.get(label, {})
        if step.get('slo') is False or label not in steps:
            m['slo'] = 'not gated'
        else:
            p95_max = step.get('slo_p95_ms', slo['p95_ms'])
            m['slo_p95_limit_ms'] = p95_max
            fails = []
            if m['p95_ms'] > p95_max:
                fails.append(f"p95 {m['p95_ms']} > {p95_max} ms")
            if m['error_pct'] > slo['error_pct']:
                fails.append(f"error {m['error_pct']}% > {slo['error_pct']}%")
            m['slo'] = 'FAIL: ' + '; '.join(fails) if fails else f'PASS (p95 <= {p95_max} ms, error <= {slo["error_pct"]}%)'
            verdicts.append(not fails)
        labels[label] = m
    missing = [l for l in (s['label'] for s in group['steps']) if l not in labels]
    verdict = 'PASS' if verdicts and all(verdicts) and not missing else 'FAIL'
    summary = {'group': group['name'], 'jtl': str(jtl), 'verdict': verdict, 'missing_labels': missing,
               'max_all_threads': max(r['threads'] for r in rows), 'total': stats(rows), 'labels': labels,
               'slo': slo, 'method': __doc__.strip().splitlines()[-1]}
    if len(sys.argv) == 5 and Path(sys.argv[4]).exists():
        summary['monitor'] = monitor(sys.argv[4])
    out.mkdir(parents=True, exist_ok=True)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    t = summary['total']
    md = [f"# Kết quả nhóm `{group['name']}` – {verdict}", '',
          f"Nguồn: `{jtl}` (số liệu do script tính từ JTL thô, không do AI gõ).", '',
          f"Tổng: {t['count']} request, {t['rps']} req/s trong {t['span_s']} s, lỗi {t['error_pct']}%, "
          f"p95 {t['p95_ms']} ms, max {t['max_ms']} ms, tối đa {summary['max_all_threads']} thread.", '',
          '| Label | Count | RPS | Error % | Mean | p90 | p95 | p99 | Max | Mã HTTP | SLO |',
          '|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|']
    for label, m in labels.items():
        codes = ', '.join(f'{k}×{v}' for k, v in sorted(m['codes'].items()))
        md.append(f"| {label} | {m['count']} | {m['rps']} | {m['error_pct']} | {m['mean_ms']} | {m['p90_ms']} | "
                  f"{m['p95_ms']} | {m['p99_ms']} | {m['max_ms']} | {codes} | {m['slo']} |")
    if missing:
        md += ['', f"**Thiếu label (không có sample):** {', '.join(missing)} → FAIL."]
    if summary.get('monitor'):
        mo = summary['monitor']
        md += ['', f"RAM backend (RSS): đầu {mo['rss_first_mb']} MB, max {mo['rss_max_mb']} MB, cuối {mo['rss_last_mb']} MB "
               f"({mo['samples']} mẫu, 1 s/mẫu)."]
    md += ['', f"Phương pháp: {summary['method']}"]
    (out / 'summary.md').write_text('\n'.join(md) + '\n')
    print('\n'.join(md))
    return 0 if verdict == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
