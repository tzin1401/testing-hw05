# Kết quả nhóm `transactional` – PASS

Nguồn: `results/skill/transactional_20261119-005420/run.jtl` (số liệu do script tính từ JTL thô, không do AI gõ).

Tổng: 2291 request, 19.37 req/s trong 118.3 s, lỗi 0.0%, p95 16 ms, max 57 ms, tối đa 20 thread.

| Label | Count | RPS | Error % | Mean | p90 | p95 | p99 | Max | Mã HTTP | SLO |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| T0 Setup login | 20 | 2.28 | 0.0 | 7.0 | 6 | 13 | 39 | 39 | 200×20 | not gated |
| T1 Add cart | 573 | 4.89 | 0.0 | 2.7 | 3 | 4 | 5 | 9 | 200×573 | PASS (p95 <= 75 ms, error <= 0.1%) |
| T2 Get cart | 571 | 4.9 | 0.0 | 2.3 | 3 | 3 | 4 | 5 | 200×571 | PASS (p95 <= 75 ms, error <= 0.1%) |
| T3 Checkout | 567 | 4.89 | 0.0 | 14.2 | 21 | 23 | 26 | 57 | 200×567 | PASS (p95 <= 100 ms, error <= 0.1%) |
| T4 My orders | 560 | 4.85 | 0.0 | 3.7 | 5 | 6 | 19 | 26 | 200×560 | PASS (p95 <= 75 ms, error <= 0.1%) |

RAM backend (RSS): đầu 88.19 MB, max 101.16 MB, cuối 101.16 MB (120 mẫu, 1 s/mẫu).

Phương pháp: Percentiles are nearest-rank on `elapsed`: sorted[ceil(p*n)-1]. Error = success=false.
