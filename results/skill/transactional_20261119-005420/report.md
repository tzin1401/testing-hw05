# Performance test – group `transactional` – PASS
## A. Số liệu (script tính từ JTL)

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
## B. Phân tích của AI
- **Chậm nhất là T3 Checkout:** p95 23 ms, mean 14.2 ms, max 57 ms. Các bước còn lại có p95 từ 3 đến 6 ms (T1 4 ms, T2 3 ms, T4 6 ms). Giả thuyết: checkout ghi đơn hàng vào DB nên tốn hơn các bước chỉ đọc/ghi giỏ hàng. JTL chỉ cho thấy *là* chậm hơn, không cho thấy *vì sao*.
- **Lỗi:** 0 lỗi trên 2291 request; mọi response đều là HTTP 200 (200×2291). Login setup chạy 20 lần, đều 200.
- **Biên SLO:** rộng. T3 p95 23 ms so với ngưỡng riêng của checkout (xem cột SLO ở mục A); T1/T2/T4 p95 tối đa 6 ms so với ngưỡng 75 ms. Lưu ý đây là profile smoke 20 thread, 19.37 req/s; biên rộng ở mức tải này không chứng minh được gì cho tải load/stress.
- **Đuôi T4 My orders:** p99 19 ms trong khi p95 chỉ 6 ms. Giả thuyết: danh sách đơn của mỗi user dài dần theo số lần checkout trong lúc chạy.
- **RAM backend (RSS):** từ 88.19 MB lên 101.16 MB, và giá trị cuối bằng max (101.16 MB) qua 120 mẫu. Xu hướng tăng, chưa thấy giảm lại; 2 phút là quá ngắn để kết luận có rò rỉ bộ nhớ (giả thuyết, cần chạy profile load lâu hơn).
## C. Người cần kiểm tra
- [ ] Mở `html/index.html`, so sánh 2–3 số với mục A: tổng 2291 request, lỗi 0%, p95 của T3 Checkout (dashboard có thể lệch nhẹ vì cách tính percentile khác nearest-rank).
- [ ] Xác nhận htop có trong video quay màn hình lúc JMeter chạy.
- [ ] Quyết định SLO trong `groups/transactional.json` (p95 75 ms, riêng checkout 100 ms, error 0.1%) có hợp lý không, vì số đo thực tế thấp hơn ngưỡng rất nhiều.
## D. File
- Plan: `23120190_Load_20261119.jmx`
- JTL thô: `run.jtl`
- HTML report: `html/index.html`
- Số liệu: `summary.json`, `summary.md`
- Monitor RAM: `monitor.csv`
- JMeter log: `jmeter.log`
