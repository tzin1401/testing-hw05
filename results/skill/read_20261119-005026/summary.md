# Kết quả nhóm `read` – PASS

Nguồn: `results/skill/read_20261119-005026/run.jtl` (số liệu do script tính từ JTL thô, không do AI gõ).

Tổng: 142 request, 5.03 req/s trong 28.2 s, lỗi 0.0%, p95 4 ms, max 27 ms, tối đa 5 thread.

| Label | Count | RPS | Error % | Mean | p90 | p95 | p99 | Max | Mã HTTP | SLO |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| R1 Products | 48 | 1.73 | 0.0 | 3.9 | 5 | 5 | 27 | 27 | 200×48 | PASS (p95 <= 75 ms, error <= 0.1%) |
| R2 Product detail | 48 | 1.78 | 0.0 | 3.2 | 4 | 4 | 5 | 5 | 200×48 | PASS (p95 <= 75 ms, error <= 0.1%) |
| R3 Categories | 46 | 1.76 | 0.0 | 3.0 | 4 | 4 | 5 | 5 | 200×46 | PASS (p95 <= 75 ms, error <= 0.1%) |

RAM backend (RSS): đầu 89.35 MB, max 89.35 MB, cuối 80.5 MB (32 mẫu, 1 s/mẫu).

Phương pháp: Percentiles are nearest-rank on `elapsed`: sorted[ceil(p*n)-1]. Error = success=false.
