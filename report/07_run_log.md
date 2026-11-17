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

## Bước 13 – Chạy thật plan STRESS

### Reset, lệnh và trạng thái HTML

- Reset SUT lúc `2026-11-18 00:58:12 +07` bằng `scripts/reset_sut.sh`; SUT đã được reset trước lần chạy. Không reset lại khi tạo báo cáo offline.
- JMeter bắt đầu `2026-11-18 00:58:19 +07` và kết thúc `2026-11-18 01:08:21 +07`; log xác nhận JMeter 5.6.3, Java 17.0.21, Linux amd64, 12 processors, max heap 1 GiB.
- Monitor chạy song song: `scripts/monitor_backend.sh results/monitor/23120190_Stress_20261118.csv`; tiến trình monitor được dừng sau khi tải kết thúc.
- Lệnh tải thực tế:
  ```bash
  export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
  export PATH="$JAVA_HOME/bin:$PATH"
  jmeter -n -t test-plans/23120190_Stress_20261117.jmx -l results/jtl/23120190_Stress_20261118.jtl -e -o results/html/23120190_Stress_20261118/ -j results/23120190_Stress_20261118_jmeter.log
  ```
- Console được lưu tại `results/23120190_Stress_console.log`. Lệnh tải kết thúc với lỗi HTML output directory đã tồn tại; directory cũ `results/html/23120190_Stress_20261118/` không bị xóa hay ghi đè. Directory đã có `index.html`, `statistics.json`, `content/`, `sbadmin2-1.0.7/`; statistics cũ khớp report offline được phục hồi, không phải một test lần nữa.
- Phục hồi report chỉ đọc JTL hiện có, không reset SUT hay chạy monitor:
  ```bash
  export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
  export PATH="$JAVA_HOME/bin:$PATH"
  jmeter -g results/jtl/23120190_Stress_20261118.jtl -o results/html/23120190_Stress_20261118_recovered/ -j results/23120190_Stress_20261118_recovery_jmeter.log
  ```
  Lệnh hoàn tất thành công; report có `statistics.json`. Run ban đầu và recovery log lần lượt ở `results/23120190_Stress_20261118_jmeter.log` và `results/23120190_Stress_20261118_recovery_jmeter.log`.

### Tổng kết và tài nguyên

Nguồn tổng thể: `results/html/23120190_Stress_20261118_recovered/statistics.json`, entry `Total` (các trường response time ms; `pct1ResTime`=p90, `pct2ResTime`=p95, `pct3ResTime`=p99). Đây là statistics tính từ JTL gốc.

| Metric | Giá trị |
|---|---:|
| Samples tổng | 175,882 |
| Errors | 0 (0.0%) |
| Average | 67.0124 ms |
| p90 / p95 / p99 | 843.9 / 1,023 / 1,194.99 ms |
| Throughput | 293.0917 requests/sec |

JTL `results/jtl/23120190_Stress_20261118.jtl`: 174,621 main-flow samples (7 labels), không lỗi; `Negative login` có 1,261 sample thành công theo assertion, gồm HTTP 403: 1,253 và HTTP 401: 8. Các 401/403 là phản hồi mong muốn của nhánh đăng nhập sai, không phải lỗi load. Tổng từng label lấy từ JTL: Login 25,199; Products 25,125; Product detail 25,070; Add cart 25,007; Get cart 24,916; Checkout 24,735; My orders 24,569.

Monitor `results/monitor/23120190_Stress_20261118.csv`: 595 mẫu, `2026-11-18T00:58:18+0700`–`2026-11-18T01:08:27+0700`. Cao nhất trong các mẫu: `cpu_percent` 32.6%, `rss_mb` 171.64 MiB. CPU là lifetime-average `%CPU` từ `ps` được lấy mẫu, không phải instantaneous peak; RSS đã đổi sang MiB bởi script.

### Từng bậc và stable window

JTL `timeStamp` là sample start time. Mốc đầu cửa sổ lấy từ `STRESS_STAGE_START` trong JMeter log; cuối cửa sổ trong bảng được tính bằng mốc này +150 giây, **không phải timestamp kết thúc Thread Group quan sát trực tiếp**. Loại 30 giây đầu để tạo cửa sổ ổn định danh nghĩa 120 giây, lọc đồng thời theo `threadName` của đúng bậc và 7 label luồng chính. p95 là nearest-rank elapsed; RPS = số mẫu trong cửa sổ danh nghĩa /120 giây. Gate có thể chạy sau lúc scheduler bắt đầu nên cuối cửa sổ danh nghĩa có thể muộn hơn lúc nhóm thực sự kết thúc.

| Stage | VU cấu hình | Cửa sổ danh nghĩa từ mốc gate | Stable window danh nghĩa | Main samples | Errors | p95 | RPS |
|---|---:|---|---|---:|---:|---:|---:|
| 1 | 50 | 00:58:21.118–01:00:51.118 | 00:58:51.118–01:00:51.118 | 13,889 | 0 (0%) | 12 ms | 115.742 |
| 2 | 100 | 01:00:50.765–01:03:20.765 | 01:01:20.765–01:03:20.765 | 27,738 | 0 (0%) | 17 ms | 231.150 |
| 3 | 200 | 01:03:20.796–01:05:50.796 | 01:03:50.796–01:05:50.796 | 54,175 | 0 (0%) | 50 ms | 451.458 |
| 4 | 290 | 01:05:50.972–01:08:20.972 | 01:06:20.972–01:08:20.972 | 56,493 | 0 (0%) | 947 ms | 470.775 |

Cuối cửa sổ danh nghĩa bậc 4 là 01:08:20.972; log ghi tải kết thúc lúc 01:08:21.633. Gate log cho các bậc trước bậc kế tiếp: stage 1 15,767 mẫu/p95 12 ms, stage 2 31,275/p95 17 ms, stage 3 61,173/p95 48 ms; cả ba `errors=0.0`, `continue=true`. Stage 4 được chạy hết; summary log ghi 66,406 mẫu, lỗi 0%, p95 906 ms. Các gate lấy thống kê tích lũy toàn stage theo script, còn bảng stable-window loại 30 giây ramp-up; hai loại cửa sổ không thay thế nhau. Tất cả gate đều tiếp tục và mọi stable window danh nghĩa đều thỏa ngưỡng lỗi ≤5% và p95 ≤2,000 ms. 290 VU là mức ổn định quan sát được cao nhất và cũng là bậc cao nhất đã thử; do chưa vượt ngưỡng ở 290 VU, breakpoint/threshold chưa tìm thấy. Không có bậc nào bị bỏ qua.

Artifacts: JTL `results/jtl/23120190_Stress_20261118.jtl`; monitor CSV `results/monitor/23120190_Stress_20261118.csv`; report offline `results/html/23120190_Stress_20261118_recovered/`; HTML output ban đầu lỗi do thư mục có sẵn nhưng directory cũ được giữ nguyên.
