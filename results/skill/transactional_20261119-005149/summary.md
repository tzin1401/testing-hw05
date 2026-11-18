# Kết quả nhóm `transactional` – PASS

Nguồn: `results/skill/transactional_20261119-005149/run.jtl` (số liệu do script tính từ JTL thô, không do AI gõ).

Tổng: 143 request, 4.94 req/s trong 28.9 s, lỗi 0.0%, p95 16 ms, max 37 ms, tối đa 5 thread.

| Label | Count | RPS | Error % | Mean | p90 | p95 | p99 | Max | Mã HTTP | SLO |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| T0 Setup login | 5 | 3.53 | 0.0 | 10.2 | 37 | 37 | 37 | 37 | 200×5 | not gated |
| T1 Add cart | 36 | 1.35 | 0.0 | 3.2 | 4 | 5 | 6 | 6 | 200×36 | PASS (p95 <= 75 ms, error <= 0.1%) |
| T2 Get cart | 36 | 1.38 | 0.0 | 2.5 | 3 | 4 | 4 | 4 | 200×36 | PASS (p95 <= 75 ms, error <= 0.1%) |
| T3 Checkout | 33 | 1.37 | 0.0 | 15.3 | 23 | 28 | 28 | 28 | 200×33 | PASS (p95 <= 100 ms, error <= 0.1%) |
| T4 My orders | 33 | 1.39 | 0.0 | 3.4 | 4 | 4 | 4 | 4 | 200×33 | PASS (p95 <= 75 ms, error <= 0.1%) |

RAM backend (RSS): đầu 89.21 MB, max 90.27 MB, cuối 80.13 MB (33 mẫu, 1 s/mẫu).

Phương pháp: Percentiles are nearest-rank on `elapsed`: sorted[ceil(p*n)-1]. Error = success=false.
