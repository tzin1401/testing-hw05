#!/usr/bin/env python3
"""Summarize canonical JMeter and backend monitor files as deterministic JSON."""
import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime
import json
import math
import re
import sys


def percentile(values):
    if not values:
        raise ValueError('cannot calculate p95 without samples')
    return sorted(values)[math.ceil(0.95 * len(values)) - 1]


def bucket_index(timestamp, start):
    return (timestamp - start) // 60000


def is_main(row):
    return row['label'] != 'Negative login'


def read_jtl(path):
    main, negative = [], []
    with open(path, newline='', encoding='utf-8-sig') as source:
        for row in csv.DictReader(source):
            start, elapsed = int(row['timeStamp']), int(row['elapsed'])
            if start <= 0 or elapsed < 0 or row['success'] not in ('true', 'false'):
                raise ValueError(f'{path}: invalid sample timestamp, elapsed or success')
            if not row['threadName'] or not row['label']:
                raise ValueError(f'{path}: missing thread name or label')
            sample = {'start': start, 'elapsed': elapsed, 'success': row['success'] == 'true',
                      'thread': row['threadName'], 'code': row['responseCode']}
            (main if is_main(row) else negative).append(sample)
    if not main:
        raise ValueError(f'{path}: no main samples')
    return main, negative


def negative_summary(samples):
    return {'sample_count': len(samples), 'success_count': sum(s['success'] for s in samples),
            'failure_count': sum(not s['success'] for s in samples),
            'response_codes': dict(sorted(Counter(s['code'] for s in samples).items()))}


def end_time(samples):
    # A zero-millisecond sample still occupies one millisecond for a meaningful window.
    return max(s['start'] + max(s['elapsed'], 1) for s in samples)


def summary(samples, start, end):
    if end <= start:
        raise ValueError('sample window must have positive duration')
    errors = sum(not s['success'] for s in samples)
    return {'window_start_epoch_ms': start, 'window_end_epoch_ms': end,
            'window_seconds': (end - start) / 1000, 'sample_count': len(samples),
            'unique_vu': len({s['thread'] for s in samples}), 'errors': errors,
            'error_percent': 100 * errors / len(samples) if samples else None,
            'p95_ms': percentile([s['elapsed'] for s in samples]) if samples else None,
            'rps': len(samples) * 1000 / (end - start)}


def soak_summary(samples):
    start, end = min(s['start'] for s in samples), end_time(samples)
    buckets = defaultdict(list)
    for sample in samples:
        buckets[bucket_index(sample['start'], start)].append(sample)
    minutes = []
    for index in range(bucket_index(end - 1, start) + 1):
        left, right = start + index * 60000, min(start + (index + 1) * 60000, end)
        minutes.append({'minute_index': index, **summary(buckets[index], left, right)})
    ramp_end = min(start + 60000, end)
    ramp = [s for s in samples if s['start'] < ramp_end]
    after = [s for s in samples if s['start'] >= start + 60000]
    return {'all': summary(samples, start, end), 'minutes': minutes,
            'ramp_60s': summary(ramp, start, ramp_end),
            'post_ramp': summary(after, start + 60000, end) if after and end > start + 60000 else None}


def stress_summary(samples):
    stages = defaultdict(list)
    for sample in samples:
        match = re.fullmatch(r'Stress stage (\d+) \d+-\d+', sample['thread'])
        if not match:
            raise ValueError(f"unrecognized stress thread name: {sample['thread']}")
        stages[int(match.group(1))].append(sample)
    result = []
    for number, group in sorted(stages.items()):
        start, end = min(s['start'] for s in group), end_time(group)
        post = [s for s in group if s['start'] >= start + 30000]
        result.append({'stage': number, 'all': summary(group, start, end),
                       'post_30s_ramp': summary(post, start + 30000, end)
                       if post and end > start + 30000 else None})
    threshold = None
    stable = []
    for stage in result:
        metrics = stage['post_30s_ramp']
        if metrics is None:
            continue
        if metrics['error_percent'] > 5 or metrics['p95_ms'] > 2000:
            if threshold is None:
                threshold = {'stage': stage['stage'], **metrics}
        else:
            stable.append({'stage': stage['stage'], **metrics})
    return {'stages': result, 'first_threshold_exceeded_post_ramp': threshold,
            'max_observed_stable_post_ramp': max(stable, key=lambda s: (s['unique_vu'], s['rps'])) if stable else None}


def monitor_summary(path):
    times, rss, cpu = [], [], []
    with open(path, newline='', encoding='utf-8-sig') as source:
        for row in csv.DictReader(source):
            timestamp = datetime.fromisoformat(row['timestamp'])
            if timestamp.utcoffset() is None:
                raise ValueError(f'{path}: monitor timestamps must include timezone')
            timestamp = timestamp.timestamp()
            memory, usage = float(row['rss_mb']), float(row['cpu_percent'])
            if not all(math.isfinite(x) for x in (timestamp, memory, usage)) or memory < 0 or usage < 0:
                raise ValueError(f'{path}: invalid monitor value')
            if times and timestamp <= times[-1]:
                raise ValueError(f'{path}: monitor timestamps must increase')
            times.append(timestamp)
            rss.append(memory)
            cpu.append(usage)
    if len(times) < 2:
        raise ValueError(f'{path}: at least two monitor samples are required')
    minutes = [(t - times[0]) / 60 for t in times]
    mean_time, mean_rss = sum(minutes) / len(minutes), sum(rss) / len(rss)
    slope = sum((t - mean_time) * (m - mean_rss) for t, m in zip(minutes, rss)) / sum((t - mean_time) ** 2 for t in minutes)
    return {'sample_count': len(times), 'rss_mib_max': max(rss), 'rss_mib_mean': mean_rss,
            'rss_ols_slope_mib_per_minute': slope, 'cpu_percent_max': max(cpu),
            'cpu_percent_mean': sum(cpu) / len(cpu)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('soak-jtl', 'soak-monitor', 'stress-jtl', 'stress-monitor'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    try:
        soak, soak_negative = read_jtl(args.soak_jtl)
        stress, stress_negative = read_jtl(args.stress_jtl)
        result = {
            'sources': vars(args),
            'method': {
                'samples': 'JTL timeStamp is start in epoch ms; elapsed is duration in ms. Negative login excluded from main metrics and summarized separately.',
                'windows': 'Half-open windows assign samples by start; end is maximum sample start plus max(elapsed, 1 ms). RPS is sample count divided by actual window width, including the final partial minute; empty buckets have zero RPS and null p95/error percentage.',
                'soak': 'Minute zero starts at first main sample. Ramp is first 60 s; post-ramp starts at 60 s. Windows differ from report/07, so stable RPS may differ.',
                'stress': 'Group by Stress stage N thread name; post-ramp begins 30 s after first main sample in each stage. Threshold is first post-ramp stage with error > 5% or nearest-rank p95 > 2000 ms; null means not observed. Stable is highest actual unique VU among qualifying post-ramp stages, then RPS; it is not a proven breakpoint.',
                'percentile': 'Nearest-rank p95: sorted elapsed[ceil(0.95*n)-1].',
                'monitor': 'rss_mb is ps RSS KiB divided by 1024 (MiB); slope is ordinary least squares against actual timestamp minutes. CPU is ps process-lifetime average, not instantaneous utilization. Observed peak RSS is not a hard memory ceiling; RSS alone over 12 minutes does not prove a leak.'},
            'soak': {'main': soak_summary(soak), 'negative_login': negative_summary(soak_negative), 'monitor': monitor_summary(args.soak_monitor)},
            'stress': {'main': stress_summary(stress), 'negative_login': negative_summary(stress_negative), 'monitor': monitor_summary(args.stress_monitor)},
        }
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as exc:
        parser.exit(2, f'error: {exc}\n')


if __name__ == '__main__':
    main()
