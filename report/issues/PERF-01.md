## Mô tả lỗi
Khi lượng truy cập tăng đột ngột (10 → 200 user trong 5 giây), thời gian phản hồi tăng vọt trong khoảng **60 giây đầu**: p95 từ **30 ms lên 1.505 ms** (~50 lần), request chậm nhất **4,6 giây**. Không có lỗi HTTP và hệ thống tự hồi phục sau ~1 phút, nhưng người dùng sẽ thấy trang treo vài giây lúc cao điểm. Ở Stress, cùng mức 200 user tăng dần trong 30 giây chỉ có p95 **48 ms**, nên vấn đề nằm ở **tốc độ tăng tải**, không phải mức tải. Nghi vấn: Node.js đơn luồng xếp hàng các request login/checkout ghi SQLite đồng thời.

## Môi trường
- OS: Ubuntu 26.04 (Linux 7.0.0-43-generic), máy `zinn-Nitro-AN515-57`
- SUT: [ttbhanh/eshop-sut](https://github.com/ttbhanh/eshop-sut) commit `85af3ba`, backend Node.js v22.22.1 + SQLite
- URL: `http://localhost:3000`
- Công cụ: curl; SUT được reset bằng `scripts/reset_sut.sh` trước khi tái hiện
- JMeter 5.6.3 (JDK 17), JMeter và SUT chạy chung một máy (12 luồng CPU, 30 GiB RAM)
- Account test: `perf001`–`perf290` (`data/users_main.csv`)

## Steps to reproduce
1. `scripts/reset_sut.sh`
2. Chạy plan Spike (10 VU nền; thêm 190 VU sau 120 s, ramp 5 s, giữ 120 s):
   ```bash
   jmeter -n -t test-plans/23120190_Spike_20261117.jmx -l results/jtl/23120190_Spike_20261118.jtl
   ```
3. Tính p95 theo pha từ file `.jtl` (cột `elapsed`, bỏ sampler `Negative login`).

## Actual result
| Pha (tính từ lúc bắt đầu) | Số mẫu | p95 | Max | Lỗi |
|---|---|---|---|---|
| 0–120 s (10 VU) | 1.378 | 30 ms | 149 ms | 0 |
| **120–180 s (vừa tăng lên 200 VU)** | 11.207 | **1.505 ms** | **4.633 ms** | 0 |
| 180–240 s (200 VU, ổn định) | 13.790 | 17 ms | 90 ms | 0 |
| 240–360 s (về 10 VU) | 1.385 | 11 ms | 19 ms | 0 |

## Expected result
p95 duy trì dưới ngưỡng chấp nhận của bài test trong suốt đợt tăng tải đột ngột, không có request chậm hơn 2 giây (ngưỡng p95 2.000 ms dùng trong plan Stress). Mức tải 200 VU đã được chứng minh là xử lý được (pha 180–240 s).

## Evidence
- Raw log: `results/jtl/23120190_Spike_20261118.jtl`
- HTML report: `results/html/23120190_Spike_20261118/`
- Ảnh JMeter + htop lúc đỉnh tải: `evidence/spike_run.png` (summary `Avg: 324 Max: 4633`)
- Ảnh pha hồi phục: `evidence/spike_recovery.png`
