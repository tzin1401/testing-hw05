# Kết quả nhóm `transactional` – PASS

Nguồn: `results/skill/transactional_20261119-114919/run.jtl` (số liệu do script tính từ JTL thô, không do AI gõ).

Tổng: 2260 request, 18.94 req/s trong 119.3 s, lỗi 0.0%, p95 12 ms, max 32 ms, tối đa 20 thread.

| Label | Count | RPS | Error % | Mean | p90 | p95 | p99 | Max | Mã HTTP | SLO |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| T0 Setup login | 20 | 2.02 | 0.0 | 4.7 | 5 | 7 | 32 | 32 | 200×20 | not gated |
| T1 Add cart | 568 | 4.8 | 0.0 | 1.8 | 3 | 3 | 4 | 8 | 200×568 | PASS (p95 <= 75 ms, error <= 0.1%) |
| T2 Get cart | 560 | 4.78 | 0.0 | 1.6 | 2 | 3 | 3 | 6 | 200×560 | PASS (p95 <= 75 ms, error <= 0.1%) |
| T3 Checkout | 557 | 4.79 | 0.0 | 11.0 | 13 | 14 | 19 | 25 | 200×557 | PASS (p95 <= 100 ms, error <= 0.1%) |
| T4 My orders | 555 | 4.81 | 0.0 | 2.3 | 3 | 4 | 10 | 13 | 200×555 | PASS (p95 <= 75 ms, error <= 0.1%) |

RAM backend (RSS): đầu 88.48 MB, max 99.77 MB, cuối 99.77 MB (121 mẫu, 1 s/mẫu).

Phương pháp: Percentiles are nearest-rank on `elapsed`: sorted[ceil(p*n)-1]. Error = success=false.
