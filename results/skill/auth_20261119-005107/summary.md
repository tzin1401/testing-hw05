# Kết quả nhóm `auth` – PASS

Nguồn: `results/skill/auth_20261119-005107/run.jtl` (số liệu do script tính từ JTL thô, không do AI gõ).

Tổng: 143 request, 4.9 req/s trong 29.2 s, lỗi 0.0%, p95 6 ms, max 37 ms, tối đa 5 thread.

| Label | Count | RPS | Error % | Mean | p90 | p95 | p99 | Max | Mã HTTP | SLO |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| A1 Login | 71 | 2.46 | 0.0 | 5.2 | 6 | 7 | 37 | 37 | 200×71 | PASS (p95 <= 75 ms, error <= 0.1%) |
| A2 Get profile | 69 | 2.47 | 0.0 | 4.3 | 5 | 6 | 9 | 9 | 200×69 | PASS (p95 <= 75 ms, error <= 0.1%) |
| A3 Negative login | 3 | 0.18 | 0.0 | 4.0 | 4 | 4 | 4 | 4 | 401×2, 403×1 | not gated |

RAM backend (RSS): đầu 88.11 MB, max 88.11 MB, cuối 81.22 MB (33 mẫu, 1 s/mẫu).

Phương pháp: Percentiles are nearest-rank on `elapsed`: sorted[ceil(p*n)-1]. Error = success=false.
