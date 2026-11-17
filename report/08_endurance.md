# Endurance verification

## Reproduction and determinism

```bash
mkdir -p results/analysis
python3 scripts/summarize.py --soak-jtl results/jtl/23120190_Soak_20261118.jtl --soak-monitor results/monitor/23120190_Soak_20261118.csv --stress-jtl results/jtl/23120190_Stress_20261118.jtl --stress-monitor results/monitor/23120190_Stress_20261118.csv > results/analysis/endurance.json
```

Exact inputs: `results/jtl/23120190_Soak_20261118.jtl`, `results/monitor/23120190_Soak_20261118.csv`, `results/jtl/23120190_Stress_20261118.jtl`, `results/monitor/23120190_Stress_20261118.csv`. The prescribed test command `python3 -m unittest discover -s scripts -p test_summarize.py` passed (3 tests). Repeated the summarizer with identical arguments to `/tmp/hw05_endurance_repeat.json`; `cmp` exit code **0**. SHA-256 of `results/analysis/endurance.json`, checked directly by Manager: `72588ddba12361cc5ef85243b6dfd2bc8205369e093be17ba2ee6ca1385904c2`. The temporary repeat was removed.

## Method

All metrics below are from `results/analysis/endurance.json`. p95 uses nearest rank: sorted elapsed values at index `ceil(0.95*n)-1`. JTL timestamps are sample starts; negative-login samples are excluded from main metrics. Soak minute zero begins at the first main sample; the first 60 seconds are ramp, then post-ramp. Minute buckets use half-open start-time windows; RPS is sample count divided by actual window seconds, including the final partial minute. Stress is grouped by stage; each post-ramp window starts 30 seconds after the first main sample in that stage. A stable stage is one with error <=5% and p95 <=2000 ms; threshold is the first post-ramp stage exceeding either threshold, or null if none observed. Monitor RSS is process RSS in MiB (ps RSS KiB / 1024), CPU is process-lifetime average, and slope is ordinary least squares against actual timestamp minutes. Peaks are observed samples, not hard memory ceilings. (Source definitions: JSON `method`; bucket/window values: JSON `soak.main.minutes` / `stress.main.stages`; original monitor inputs listed above.)

## Soak: 12 observed minute buckets

Source fields: JSON `soak.main.minutes[]` (`minute_index`, `sample_count`, `rps`, `p95_ms`, `error_percent`, `window_seconds`). Windows are sample-start windows; final window is partial.

| Minute | Main n | RPS | p95 ms | Error % | Window s |
|---:|---:|---:|---:|---:|---:|
| 0 | 7,364 | 122.733 | 14 | 0 | 60.000 |
| 1 | 14,066 | 234.433 | 19 | 0 | 60.000 |
| 2 | 14,109 | 235.150 | 19 | 0 | 60.000 |
| 3 | 10,271 | 171.183 | 2,244 | 0 | 60.000 |
| 4 | 13,010 | 216.833 | 45 | 0 | 60.000 |
| 5 | 14,156 | 235.933 | 19 | 0 | 60.000 |
| 6 | 14,063 | 234.383 | 20 | 0 | 60.000 |
| 7 | 14,112 | 235.200 | 20 | 0 | 60.000 |
| 8 | 14,097 | 234.950 | 19 | 0 | 60.000 |
| 9 | 14,100 | 235.000 | 21 | 0 | 60.000 |
| 10 | 14,098 | 234.967 | 22 | 0 | 60.000 |
| 11 | 14,016 | 234.448 | 20 | 0 | 59.783 |

### Endurance breach hidden by the aggregate

Minute index **3** (180–240 s after the first main sample) has **p95 2,244 ms**, above the **2,000 ms** criterion, with **171.183 RPS** and **0% errors**. Source: `soak.main.minutes[3]` in the JSON. Thus the 203-VU Soak did **not** meet the latency criterion in every minute, even though its full-run HTML p95 is 21 ms. No claim of uninterrupted 12-minute stability or of a proven sustained-capacity threshold follows from this run. The 290-VU result below is a short Stress-stage observation, not a contradiction and not a replacement for the Soak time series. The data alone does not identify the cause of this latency episode.

## Stress stages (post-ramp)

Source fields: JSON `stress.main.stages[].post_30s_ramp` (`sample_count`, `rps`, `p95_ms`, `error_percent`, `unique_vu`); VU count is observed unique VU, not the planned stage label.

| Stage | Observed VU | n | RPS | p95 ms | Error % |
|---:|---:|---:|---:|---:|---:|
| 1 | 50 | 13,847 | 116.100 | 12 | 0 |
| 2 | 100 | 27,726 | 231.137 | 17 | 0 |
| 3 | 200 | 54,166 | 451.173 | 50 | 0 |
| 4 | 290 | 56,469 | 468.556 | 947 | 0 |

JSON `stress.main.max_observed_stable_post_ramp`: **290 VU**, **468.556 RPS**, p95 **947 ms**; `first_threshold_exceeded_post_ramp` is **null** (none observed in these stages). This is the maximum observed stable stage, not an extrapolation or proven breakpoint. Soak main load was **203 VU**, approximately **70% of the 290 VU stress stage**, not 70% of stress RPS. The configured/data target of **290 VU was not surpassed**; no evidence here establishes behavior beyond that point.

## Process monitoring and interpretation

Source fields: JSON `soak.monitor` and `stress.monitor` (`rss_mib_max`, `rss_mib_mean`, `rss_ols_slope_mib_per_minute`, `cpu_percent_max`, `cpu_percent_mean`, `sample_count`).

| Run | RSS max MiB | RSS mean MiB | RSS OLS slope MiB/min | CPU max % | CPU mean % | Monitor samples |
|---|---:|---:|---:|---:|---:|---:|
| Soak | 127.80 | 121.79 | 1.470 | 32.6 | 27.287 | 710 |
| Stress | 171.64 | 126.28 | 6.028 | 32.6 | 21.397 | 595 |

Derived maximum observed RSS across these two monitor outputs is `max(soak.monitor.rss_mib_max, stress.monitor.rss_mib_max) = max(127.80, 171.64) = **171.64 MiB**`; it is not a hard memory ceiling.

As documented in [`01_api_analysis.md`](01_api_analysis.md), code retains cart entries in the in-memory `userCarts` collection: POST appends and checkout does not clear it. That retention is a code fact. The positive soak RSS OLS slope over this approximately 12-minute observation is only **consistent with** increasing retained state; it does not prove an unbounded memory leak or establish causality. RSS varies and is not itself a leak diagnosis.

Negative-login samples were excluded from the main tables as specified; their counts/codes are available separately in JSON `soak.negative_login` and `stress.negative_login`.
