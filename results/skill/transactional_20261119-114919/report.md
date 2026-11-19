# Performance test – group `transactional` – PASS
## A. Số liệu (script tính từ JTL)

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

## B. Phân tích của AI
- Checkout chậm nhất theo p95: 14 ms; Add cart 3 ms, Get cart 3 ms, My orders 4 ms. Đây là so sánh giá trị đo trực tiếp, chưa xác định nguyên nhân chậm.
- Toàn bộ 2260 request trả HTTP 200; lỗi theo success=false là 0, tương ứng 0.0%. Không ghi nhận mã HTTP lỗi trong lần chạy này.
- Biên SLO rộng trong lần smoke này: Checkout p95 14 ms so với ngưỡng 100 ms; Add cart và Get cart p95 3 ms, My orders 4 ms so với ngưỡng 75 ms. Lỗi 0.0% so với ngưỡng 0.1%. Setup login không được gate.
- RSS đầu 88.48 MB, cuối 99.77 MB, cực đại 99.77 MB qua 121 mẫu. Điểm cuối cao hơn điểm đầu, nhưng chưa đủ kết luận memory leak hay tăng đơn điệu; tích lũy dữ liệu hoặc warm-up chỉ là giả thuyết.
- Kết luận chỉ áp dụng lần chạy tối đa 20 thread, span đo 119.3 s, throughput 18.94 req/s; chưa chứng minh khả năng chịu tải cao hơn hoặc độ ổn định dài hạn.

## C. Người cần kiểm tra
- [ ] Mở `html/index.html`, đối chiếu tổng request, error % và p95 Checkout với summary; percentile nearest-rank có thể khác nhẹ dashboard JMeter.
- [ ] Xác nhận htop xuất hiện trong video ghi màn hình; AI chưa xác minh video.
- [ ] Đánh giá SLO trong `.claude/skills/perf-endpoint-group/groups/transactional.json` có phù hợp yêu cầu thực tế hay không.

## D. File
Các đường dẫn sau tương đối với thư mục báo cáo này:
- Plan: `23120190_Load_20261119.jmx`
- JTL thô: `run.jtl`
- Dashboard: `html/` (mở `html/index.html`)
- Số liệu: `summary.json`
- Bảng kết quả: `summary.md`
- Monitor: `monitor.csv`
- Log JMeter: `jmeter.log`
