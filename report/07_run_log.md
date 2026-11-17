# Bước 13 – Chạy thật plan LOAD

## Reset và lệnh chạy

- Trước khi reset: `2026-11-18 00:36:25 +07` (`date '+%Y-%m-%d %H:%M:%S %Z'`).
- Reset lúc khoảng `2026-11-18 00:36:25–00:36:32 +07`: `scripts/reset_sut.sh`. Kết quả thật: `SUT reset. Backend PID: 642837 | users seeded: 300`. Script dừng backend cũ, khởi động lại backend, chờ `/api/products` sẵn sàng rồi đăng ký 300 users từ `data/users.csv`; DB và lockout được reset khi backend restart.
- JMeter bắt đầu `2026-11-18 00:36:46 +07`, hoàn tất `2026-11-18 00:46:51 +07`, exit code `0`. JMeter báo test bắt đầu lúc `2026 Nov 18 00:36:47 ICT` và kết thúc `2026 Nov 18 00:46:48 ICT`.
- Monitor được khởi chạy nền trước JMeter và dừng tự động khi JMeter kết thúc (trap gửi SIGINT, chờ PID monitor).
- Lệnh monitor: `scripts/monitor_backend.sh results/monitor/23120190_Load_20261118.csv`
- JMeter dùng Java 17. Lệnh tái lập cùng plan và đầu ra (cần tên output mới nếu chạy lại):
  ```bash
  export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
  export PATH="$JAVA_HOME/bin:$PATH"
  jmeter -n -t test-plans/23120190_Load_20261117.jmx -l results/jtl/23120190_Load_20261118.jtl -e -o results/html/23120190_Load_20261118/ -j results/23120190_Load_20261118_jmeter.log
  ```
- Console: `results/23120190_Load_console.log` (stdout/stderr được tee; exit code JMeter được giữ riêng).

## Kết quả

Nguồn thống kê tổng thể: `results/html/23120190_Load_20261118/statistics.json`, entry `Total`. `pct1ResTime`, `pct2ResTime`, `pct3ResTime` tương ứng p90, p95, p99 trong HTML statistics JSON; response times là ms, throughput là requests/sec.

| Metric | Giá trị |
|---|---:|
| Samples tổng | 33,775 |
| Errors tổng | 0 (0.0%) |
| Average (`meanResTime`) | 3.216432272390819 ms |
| p90 (`pct1ResTime`) | 10 ms |
| p95 (`pct2ResTime`) | 11 ms |
| p99 (`pct3ResTime`) | 18 ms |
| Throughput | 56.34434863263818 requests/sec |

JTL `results/jtl/23120190_Load_20261118.jtl` được đọc riêng để tách loại sample: 33,534 sample luồng chính, 0 lỗi; 241 sample `Negative login`, đều được đánh dấu thành công theo assertion của plan. Negative login nhận HTTP 401 5 lần và HTTP 403 236 lần; không có lỗi sample nào, vì hai mã này là kết quả mong muốn của nhánh đăng nhập sai. Không phát hiện lỗi luồng chính hay lockout ngoài các phản hồi 403 dự kiến trong nhánh negative. SUT đã được reset trước lần chạy để xóa trạng thái lockout.

Nguồn tài nguyên: `results/monitor/23120190_Load_20261118.csv`, 592 mẫu, từ `2026-11-18T00:36:45+0700` đến `2026-11-18T00:46:51+0700`.

| Metric backend | Tối đa đã lấy từ CSV |
|---|---:|
| CPU (`cpu_percent`) | 9.6% |
| RSS (`rss_mb`; script chia KiB cho 1024) | 119.65 MiB |

CPU trong CSV là `%CPU` từ `ps`, giá trị lifetime average được lấy mẫu mỗi giây, không phải peak instantaneous CPU. CSV cung cấp các giá trị được quan sát trong những lần lấy mẫu; max nêu trên là max của các mẫu đó.

## Artifacts

- JTL: `results/jtl/23120190_Load_20261118.jtl`
- HTML report: `results/html/23120190_Load_20261118/` (có `statistics.json`)
- Monitor CSV: `results/monitor/23120190_Load_20261118.csv`
- JMeter log: `results/23120190_Load_20261118_jmeter.log`
- Console log: `results/23120190_Load_console.log`
