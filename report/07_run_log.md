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

## Bước 13 – Chạy thật plan SPIKE

### Reset, thời gian và lệnh

- Reset SUT bắt đầu `2026-11-18 01:15:09 +07`, hoàn tất `01:15:16 +07`, bằng `scripts/reset_sut.sh`; kết quả thật: `SUT reset. Backend PID: 774397 | users seeded: 300`. Việc restart backend reset DB và trạng thái lockout; script seed 300 user.
- JMeter bắt đầu `2026-11-18 01:15:17 +07`; JMeter log ghi test bắt đầu `2026 Nov 18 01:15:18 ICT`; tải kết thúc `2026-11-18 01:21:19 +07` (JMeter log `01:21:19 ICT`), lệnh kết thúc lúc `01:21:22 +07`, exit code `0`.
- Monitor chạy nền song song trước JMeter; trap gửi SIGINT và chờ monitor kết thúc sau JMeter.
- Monitor start time: `2026-11-18T01:15:16+0700`, immediately before JMeter; the shell command was `scripts/monitor_backend.sh results/monitor/23120190_Spike_20261118.csv`.
- Lệnh thực tế (Java 17; không override tải):
  ```bash
  export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
  export PATH="$JAVA_HOME/bin:$PATH"
  jmeter -n -t test-plans/23120190_Spike_20261117.jmx -l results/jtl/23120190_Spike_20261118.jtl -e -o results/html/23120190_Spike_20261118/ -j results/23120190_Spike_20261118_jmeter.log
  ```
- Stdout/stderr tee: `results/23120190_Spike_20261118_console.log`. JMeter tạo HTML dashboard thành công.

### Kết quả

Nguồn metric tổng thể: `results/html/23120190_Spike_20261118/statistics.json`, entry `Total`; response time đơn vị ms, throughput requests/sec.

| Metric | Giá trị |
|---|---:|
| Samples tổng | 27,965 |
| Errors | 0 (0.0%) |
| Average (`meanResTime`) | 75.25227963525879 ms |
| p90 (`pct1ResTime`) | 12 ms |
| p95 (`pct2ResTime`) | 17 ms |
| p99 (`pct3ResTime`) | 32 ms |
| Throughput | 77.92645681929645 requests/sec |

JTL `results/jtl/23120190_Spike_20261118.jtl` xác nhận 27,965 samples, lỗi 0; 27,760 luồng chính và 205 `Negative login`, tất cả thành công theo assertion. Negative login trả HTTP 401 22 lần và HTTP 403 183 lần; phản hồi 403 là lockout của user dùng nhánh đăng nhập sai, được chấp nhận trong plan, không phải lỗi sample. SUT đã reset trước test để xóa lockout.

Phân nhóm theo `threadName` trong JTL: `Spike baseline` có 4,001 sample chính, `Spike burst` có 23,759 sample chính; cả hai 0 lỗi. Đây là hai nhóm chạy chồng lấp, **không phải hai pha thời gian**. 703 sample recovery được worker xác định là phần con của nhóm baseline sau burst, không cộng thêm vào 27,760 mẫu chính. JMX cấu hình baseline 10 VU/360s và burst thêm 190 VU, delay 120s, duration 120s, ramp-up 5s. Log bắt đầu lập lịch nhóm baseline `01:15:18.944`, burst `01:15:20.495`; mốc lập lịch burst không phải mốc burst bắt đầu gửi HTTP. Theo timestamp JTL, HTTP của burst bắt đầu ở offset xấp xỉ 120s so với test; tải kết thúc `01:21:19`. Không dùng Spike để khẳng định breakpoint.

Monitor CSV `results/monitor/23120190_Spike_20261118.csv`: 357 mẫu, `2026-11-18T01:15:16+0700`–`2026-11-18T01:21:22+0700`.

| Tài nguyên backend | Max mẫu CSV |
|---|---:|
| CPU (`cpu_percent`) | 24.1% |
| RSS (`rss_mb`) | 125.42 MiB |

CPU là lifetime-average `%CPU` từ `ps`, lấy mẫu mỗi giây, không phải peak instantaneous; RSS được script đổi từ KiB sang MiB. Max là cao nhất trong các mẫu quan sát được.

Artifacts: JTL `results/jtl/23120190_Spike_20261118.jtl`; HTML `results/html/23120190_Spike_20261118/`; monitor `results/monitor/23120190_Spike_20261118.csv`; runtime log `results/23120190_Spike_20261118_jmeter.log`; console `results/23120190_Spike_20261118_console.log`.

## Bước 15 – Chạy thật plan SOAK

### Reset, lệnh và thời gian

- Trước reset: `2026-11-18 01:30:44 +07`; `scripts/reset_sut.sh` hoàn tất `01:30:50 +07`, kết quả `SUT reset. Backend PID: 829842 | users seeded: 300`. Backend restart reset DB, cart RAM và lockout; script seed 300 tài khoản.
- Monitor được khởi chạy nền trước JMeter, CSV bắt đầu `2026-11-18T01:30:50+0700`. Sau khi tải kết thúc, trap gửi SIGINT và chờ monitor kết thúc.
- JMeter chạy từ `01:30:51` đến khi lệnh trả về `01:43:00 +07`, exit code `0`; JMeter log bắt đầu test `2026 Nov 18 01:30:52 ICT` và kết thúc `2026 Nov 18 01:42:53 ICT`. Run time thực đo theo JMeter log xấp xỉ 12 phút 1 giây; cấu hình là 203 VU, ramp-up 60 s, duration 720 s; không override thread/ramp/duration/loops. Log xác nhận bắt đầu 203 threads và cả 203 hoàn tất.
- Java 17:
  ```bash
  export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
  export PATH="$JAVA_HOME/bin:$PATH"
  scripts/reset_sut.sh
  scripts/monitor_backend.sh results/monitor/23120190_Soak_20261118.csv &
  jmeter -n -t test-plans/23120190_Soak_20261118.jmx -l results/jtl/23120190_Soak_20261118.jtl -e -o results/html/23120190_Soak_20261118/ -j results/23120190_Soak_20261118_jmeter.log -Jwriter_file=results/jtl/23120190_Soak_20261118_writer.jtl
  ```
- Lệnh JMeter thực tế được bọc `set -o pipefail`, tee stdout/stderr vào `results/23120190_Soak_20261118_console.log`, và trap dừng/wait monitor. HTML report được tạo thành công.

### Kết quả và nguồn

Nguồn tổng thể: `results/html/23120190_Soak_20261118/statistics.json`, entry `Total`; response time ms, `pct1ResTime`=p90, `pct2ResTime`=p95, `pct3ResTime`=p99.

| Metric | Giá trị |
|---|---:|
| Samples tổng (canonical JTL) | 158,591 |
| Errors | 0 (0.0%) |
| Average | 32.449016652898884 ms |
| p90 / p95 / p99 | 15 / 21 / 59 ms |
| Throughput | 220.33168329899428 requests/sec |

JTL canonical `results/jtl/23120190_Soak_20261118.jtl`: 157,462 samples luồng chính, 0 lỗi; `Negative login` 1,129 sample, đều thành công theo assertion, gồm HTTP 401: 6 và HTTP 403: 1,123. Tất cả 158,591 mẫu thành công; các phản hồi 401/403 là kết quả được chấp nhận cho login sai. SUT đã reset trước lần chạy để xóa lockout. Writer JTL phụ `results/jtl/23120190_Soak_20261118_writer.jtl` có cùng 158,591 sample; đây là bản ghi trùng từ Simple Data Writer, không cộng vào tổng canonical.

Monitor `results/monitor/23120190_Soak_20261118.csv`: 710 mẫu, từ `2026-11-18T01:30:50+0700` đến `2026-11-18T01:42:59+0700`.

| Tài nguyên backend | Max mẫu CSV |
|---|---:|
| CPU (`cpu_percent`) | 32.6% |
| RSS (`rss_mb`) | 127.80 MiB |

CPU là lifetime-average `%CPU` của `ps` tại thời điểm lấy mẫu mỗi giây, không phải instantaneous peak; RSS được monitor script đổi từ KiB sang MiB. Các mức tối đa chỉ áp dụng cho mẫu quan sát được trong khoảng monitor. Chưa kết luận RAM ceiling thực hay leak; cần bước 16.

Artifacts: canonical JTL `results/jtl/23120190_Soak_20261118.jtl`; writer JTL phụ `results/jtl/23120190_Soak_20261118_writer.jtl`; HTML `results/html/23120190_Soak_20261118/`; monitor CSV `results/monitor/23120190_Soak_20261118.csv`; JMeter log `results/23120190_Soak_20261118_jmeter.log`; console `results/23120190_Soak_20261118_console.log`.
