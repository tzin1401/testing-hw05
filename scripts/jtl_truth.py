#!/usr/bin/env python3
"""Calculate reproducible JMeter reference metrics directly from canonical JTLs."""
import csv
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAMES = ('Load', 'Stress', 'Spike', 'Soak')
LABELS = ('01 Login', '02 Products', '03 Product detail', '04 Add cart',
          '05 Get cart', '06 Checkout', '07 My orders')
SPIKE_PHASES = ((0, 120), (120, 180), (180, 240), (240, 360))
METHOD = {
    'inputs': 'Four canonical JTLs; Soak writer is compared only by row count and timestamp range, not added as a run.',
    'variants': {'all': 'Every sample', 'main': 'Only these seven exact labels: ' + ', '.join(LABELS)},
    'errors': 'success=false; 401/403 with success=true is counted separately, not as an error.',
    'duration': 'max(timeStamp + elapsed) - min(timeStamp), milliseconds; throughput=count*1000/duration. Start timestamps are not assumed to be sorted.',
    'percentiles': 'Nearest rank: sorted elapsed[ceil(p * count) - 1]; elapsed, Latency and Connect are in milliseconds.',
    'minutes': 'Half-open 60 s windows by sample start, with common origin at the first start of the entire run. The final window ends at max completion of the entire run; RPS uses the actual window width. Empty windows have null p95.',
    'stress': 'Group by Stress stage N in threadName; RPS uses each group min start to max completion. Post-ramp selects starts at least 30 s after the first observed stage start in that variant; RPS uses selected samples min start to max completion.',
    'spike': 'Phases are half-open by sample start relative to first start of the entire run; requests crossing a boundary belong to their start phase. RPS uses the specified phase width. Starts at or beyond 360 s are reported separately.',
    'threads': 'Unique threadName counts distinct threads observed across the window, not concurrent VUs. allThreads min/max are sample snapshots across all thread groups, not exact continuous concurrency peaks.',
    'html_comparison': 'Compare Total and each label to HTML using absolute numeric tolerance 0.000001; missing entries are differences. main versus Total has a different filter when samples are excluded. Percentile estimator, throughput denominator or other report configuration may differ; causes are not assumed without evidence.',
}


def load_jtl(path):
    samples = []
    with path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        required = {'timeStamp', 'elapsed', 'label', 'responseCode', 'success', 'threadName', 'Latency', 'Connect'}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f'{path}: missing required columns')
        for line, row in enumerate(reader, 2):
            try:
                start, elapsed, latency, connect = (int(row[k]) for k in ('timeStamp', 'elapsed', 'Latency', 'Connect'))
                threads = int(row['allThreads']) if 'allThreads' in row else None
                if start <= 0 or min(elapsed, latency, connect) < 0 or (threads is not None and threads < 0) or row['success'] not in ('true', 'false') or not row['label'] or not row['responseCode'] or not row['threadName']:
                    raise ValueError('invalid sample values')
                samples.append((start, elapsed, row['label'], row['responseCode'], row['success'] == 'true', row['threadName'], latency, connect, threads))
            except (ValueError, TypeError, KeyError) as exc:
                raise ValueError(f'{path}:{line}: {exc}') from exc
    if not samples:
        raise ValueError(f'{path}: no samples')
    return samples


def percentile(sorted_values, p):
    return sorted_values[math.ceil(p * len(sorted_values)) - 1] if sorted_values else None


def metrics(samples, duration_ms=None):
    if not samples:
        return {'count': 0, 'error_count': 0, 'error_pct': None, 'accepted_401_403': 0,
                'duration_ms': duration_ms, 'rps': 0.0 if duration_ms and duration_ms > 0 else None,
                'mean_ms': None, 'p50_ms': None, 'p90_ms': None, 'p95_ms': None,
                'p99_ms': None, 'max_ms': None, 'mean_latency_ms': None, 'mean_connect_ms': None,
                'unique_threads': 0, 'min_all_threads': None, 'max_all_threads': None}
    values = sorted(s[1] for s in samples)
    errors = sum(not s[4] for s in samples)
    if duration_ms is None:
        duration_ms = max(s[0] + s[1] for s in samples) - min(s[0] for s in samples)
    return {'count': len(samples), 'error_count': errors, 'error_pct': errors * 100 / len(samples),
            'accepted_401_403': sum(s[3] in ('401', '403') and s[4] for s in samples),
            'duration_ms': duration_ms, 'rps': len(samples) * 1000 / duration_ms if duration_ms > 0 else None,
            'mean_ms': sum(values) / len(values),
            **{f'p{p}_ms': percentile(values, p / 100) for p in (50, 90, 95, 99)},
            'max_ms': values[-1], 'mean_latency_ms': sum(s[6] for s in samples) / len(samples),
            'mean_connect_ms': sum(s[7] for s in samples) / len(samples),
            'unique_threads': len({s[5] for s in samples}),
            'min_all_threads': min((s[8] for s in samples if s[8] is not None), default=None),
            'max_all_threads': max((s[8] for s in samples if s[8] is not None), default=None)}


def analyze(samples, origin, end, name):
    by_label, by_minute = {}, {}
    for s in samples:
        by_label.setdefault(s[2], []).append(s)
        by_minute.setdefault((s[0] - origin) // 60000, []).append(s)
    summary = metrics(samples)
    labels = {label: metrics(group) for label, group in sorted(by_label.items())}
    minutes = []
    for index in range(max(max(by_minute, default=0) + 1, (end - origin + 59999) // 60000)):
        start = origin + index * 60000
        stop = min(start + 60000, end)
        minutes.append({'index': index, 'start_offset_ms': start - origin, 'end_offset_ms': stop - origin,
                        **metrics(by_minute.get(index, []), stop - start)})
    assert sum(x['count'] for x in labels.values()) == summary['count']
    assert sum(x['count'] for x in minutes) == summary['count']
    result = {'summary': summary, 'labels': labels, 'minutes': minutes}
    if name == 'Stress':
        stages = {}
        for s in samples:
            match = re.search(r'\bStress stage (\d+)\b', s[5])
            if not match:
                raise ValueError(f'unrecognized stress threadName: {s[5]}')
            stages.setdefault(int(match.group(1)), []).append(s)
        result['stages'] = {str(k): metrics(v) for k, v in sorted(stages.items())}
        result['stages_post_30s'] = {}
        for k, v in sorted(stages.items()):
            cutoff = min(s[0] for s in v) + 30000
            result['stages_post_30s'][str(k)] = metrics([s for s in v if s[0] >= cutoff])
        assert sum(x['count'] for x in result['stages'].values()) == summary['count']
    if name == 'Spike':
        phases = {}
        for start, stop in SPIKE_PHASES:
            group = [s for s in samples if start * 1000 <= s[0] - origin < stop * 1000]
            phases[f'{start}-{stop}s'] = metrics(group, (stop - start) * 1000)
        outside = [s for s in samples if not 0 <= s[0] - origin < 360000]
        result['phases'] = phases
        result['outside_phases'] = metrics(outside)
        assert sum(x['count'] for x in phases.values()) + len(outside) == summary['count']
    return result


HTML_FIELDS = {'sampleCount': 'count', 'errorCount': 'error_count', 'errorPct': 'error_pct',
               'meanResTime': 'mean_ms', 'medianResTime': 'p50_ms', 'pct1ResTime': 'p90_ms',
               'pct2ResTime': 'p95_ms', 'pct3ResTime': 'p99_ms', 'maxResTime': 'max_ms', 'throughput': 'rps'}


def compare_html(variant, html):
    differences = []
    entries = {'Total': variant['summary'], **variant['labels']}
    for label in sorted(set(entries) | set(html)):
        if label not in entries or label not in html:
            differences.append({'entry': label, 'field': 'entry', 'jtl': 'present' if label in entries else None,
                                'html': 'present' if label in html else None})
            continue
        for html_key, key in HTML_FIELDS.items():
            actual, reported = entries[label][key], html[label].get(html_key)
            if not isinstance(reported, (int, float)) or actual is None or abs(actual - reported) > 0.000001:
                differences.append({'entry': label, 'field': html_key, 'jtl': actual, 'html': reported})
    return differences


def self_check():
    assert percentile([1, 2, 3, 4], .5) == 2
    assert percentile([1, 2, 3, 4], .95) == 4
    assert percentile([], .95) is None
    samples = [(1000, 100, LABELS[0], '200', True, 'Stress stage 1 1-1', 90, 10, 1),
               (61000, 200, 'Negative login', '401', True, 'Stress stage 1 1-1', 100, 0, 2),
               (361000, 300, LABELS[1], '500', False, 'Stress stage 2 2-1', 200, 0, 3)]
    result = analyze(samples, 1000, 361300, 'Spike')
    assert result['summary']['count'] == 3 and result['summary']['error_count'] == 1
    assert result['summary']['accepted_401_403'] == 1 and result['summary']['duration_ms'] == 360300
    assert result['minutes'][1]['count'] == 1 and result['minutes'][-1]['duration_ms'] == 300
    assert result['phases']['0-120s']['count'] == 2 and result['outside_phases']['count'] == 1
    assert analyze(samples, 1000, 361300, 'Stress')['stages']['2']['count'] == 1


def render(data):
    lines = ['# Ground truth from JTL', '', '## Method', '']
    for key, value in data['method'].items():
        lines.append(f'- **{key}:** {json.dumps(value, ensure_ascii=False) if isinstance(value, dict) else value}')
    lines += ['', '## Soak writer comparison', '', 'This comparison checks only count and timestamp range; matching does not prove row-by-row identity.', '',
              '| File | Rows | Min start (ms epoch) | Max start (ms epoch) |', '|---|---:|---:|---:|']
    for key, value in data['soak_writer_comparison'].items():
        lines.append(f"| {key} | {value['count']} | {value['min_timestamp']} | {value['max_timestamp']} |")
    def table(title, rows):
        lines.extend(['', title, '', '| Group | Count | Errors | Error % | Accepted 401/403 | Duration ms | RPS | Mean ms | p50 ms | p90 ms | p95 ms | p99 ms | Max ms | Mean Latency ms | Mean Connect ms | Unique threads | Min allThreads | Max allThreads |',
                      '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|'])
        for label, m in rows:
            keys = ('count', 'error_count', 'error_pct', 'accepted_401_403', 'duration_ms', 'rps', 'mean_ms', 'p50_ms', 'p90_ms', 'p95_ms', 'p99_ms', 'max_ms', 'mean_latency_ms', 'mean_connect_ms', 'unique_threads', 'min_all_threads', 'max_all_threads')
            def fmt(v):
                return '—' if v is None else (f'{v:.6f}' if isinstance(v, float) else str(v))
            lines.append('| ' + str(label).replace('|', '\\|') + ' | ' + ' | '.join(fmt(m[k]) for k in keys) + ' |')
    for name, run in data['runs'].items():
        lines += ['', f'## {name}', '', f"JTL: `{run['jtl']}`; HTML: `{run['html']}`; common origin: {run['origin_ms']} ms; last completion: {run['end_ms']} ms."]
        for variant_name, variant in run['variants'].items():
            lines += ['', f'### {variant_name}']
            table('Summary', [('Total', variant['summary'])])
            table('Labels', variant['labels'].items())
            table('Minutes (offsets in ms)', ((f"{x['index']}: {x['start_offset_ms']}–{x['end_offset_ms']}", x) for x in variant['minutes']))
            if 'stages' in variant:
                table('Stress stages', variant['stages'].items())
                table('Stress stages after first 30 seconds', variant['stages_post_30s'].items())
            if 'phases' in variant:
                table('Spike phases and starts outside phases', list(variant['phases'].items()) + [('outside', variant['outside_phases'])])
            lines += ['', '#### HTML differences', '', '| Entry | HTML field | JTL | HTML |', '|---|---|---:|---:|']
            for d in variant['html_differences']:
                lines.append(f"| {d['entry']} | {d['field']} | {d['jtl']} | {d['html']} |")
            if not variant['html_differences']:
                lines.append('| No differences | — | — | — |')
    return '\n'.join(lines) + '\n'


def main():
    self_check()
    data = {'method': METHOD, 'runs': {}}
    soak = None
    print('Run    Variant     Count    Errors       RPS     p95 ms')
    for name in NAMES:
        base = f'23120190_{name}_20261118'
        jtl = f'results/jtl/{base}.jtl'
        html_path = f'results/html/{base}/statistics.json'
        samples = load_jtl(ROOT / jtl)
        if name == 'Soak':
            soak = samples
        origin = min(s[0] for s in samples)
        end = max(s[0] + s[1] for s in samples)
        if end <= origin:
            raise ValueError(f'{jtl}: nonpositive run duration')
        with (ROOT / html_path).open(encoding='utf-8') as f:
            html = json.load(f)
        main_samples = [s for s in samples if s[2] in LABELS]
        variants = {}
        for variant_name, subset in (('all', samples), ('main', main_samples)):
            variant = analyze(subset, origin, end, name)
            variant['html_differences'] = compare_html(variant, html)
            variants[variant_name] = variant
            m = variant['summary']
            print(f"{name:6} {variant_name:7} {m['count']:9} {m['error_count']:9} {str(round(m['rps'], 3)) if m['rps'] is not None else 'n/a':>9} {str(m['p95_ms']):>10}")
        assert variants['all']['summary']['count'] == variants['main']['summary']['count'] + sum(s[2] not in LABELS for s in samples)
        data['runs'][name] = {'jtl': jtl, 'html': html_path, 'origin_ms': origin, 'end_ms': end, 'variants': variants}
    writer_path = 'results/jtl/23120190_Soak_20261118_writer.jtl'
    writer = load_jtl(ROOT / writer_path)
    def bounds(samples):
        return {'count': len(samples), 'min_timestamp': min(s[0] for s in samples), 'max_timestamp': max(s[0] for s in samples)}
    data['soak_writer_comparison'] = {'results/jtl/23120190_Soak_20261118.jtl': bounds(soak), writer_path: bounds(writer)}
    output = ROOT / 'results/analysis'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'ground_truth.json').write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    (output / 'ground_truth.md').write_text(render(data), encoding='utf-8')
    print('Self-check passed; wrote results/analysis/ground_truth.json and ground_truth.md')


if __name__ == '__main__':
    main()
