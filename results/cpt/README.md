# Continuous performance artifacts

`slo.json` lấy p95/p99 theo endpoint và SLO error all ≤ 0,1% từ [Task 2 §4](../../report/TASK2_REPORT.md#4-ngưỡng-cuối-cùng). Percentile dùng `jtl_truth.metrics`, nearest-rank. Latency chỉ bảy label chính sau initial ramp, gồm cả sample lỗi; Negative login không thuộc latency Auth. Error all = `success=false` / tất cả sample toàn run, kể cả ramp, và kiểm riêng từng cửa sổ 120 giây sau initial ramp; cửa sổ cuối ngắn hơn 120 giây vẫn được kiểm và đánh dấu partial, kết thúc ở thời điểm sample cuối kết thúc. Main diagnostic dùng mẫu số bảy label sau ramp. Sample được gán theo thời điểm bắt đầu; 401/403 Negative được JMeter đánh dấu success không tính lỗi. Cửa sổ rỗng INCONCLUSIVE. Gate không chứng nhận throughput.

Mặc định ≥500 sample/label và ≥1.000 sample main/run, cho cả baseline lẫn candidate để so relative. 500 là chính sách định trước, không phải dự báo đảm bảo smoke đủ mẫu: khoảng 25 quan sát đuôi p95 nhưng chỉ 5 ở p99; retry và tier dài giúp tăng bằng chứng. Đủ mẫu thì FAIL nếu p95 > 1,20 baseline **và** tăng ≥5 ms, hoặc p95/p99 vượt SLO; error all toàn run hoặc một cửa sổ >0,1% cũng FAIL. Thiếu mẫu baseline không che absolute SLO của candidate đủ mẫu. Label ít mẫu INCONCLUSIVE không che FAIL hợp lệ. Thiếu metadata/baseline, cấu hình khác hoặc lỗi hạ tầng là INCONCLUSIVE (exit 2), không phải PASS. Pipeline chỉ exit 1 nếu cả hai lần FAIL; retry PASS không xác nhận FAIL. Hai FAIL tạo alert text local với lý do và đường dẫn bằng chứng cho người điều tra; không tạo Issue. Pipeline không cập nhật baseline.

Mỗi JTL có sidecar `<file>.meta.json`: nguồn và SHA-256 JTL, commit SUT, profile (kể cả stages/delay), bộ lọc, hostname/platform/architecture, đường dẫn và SHA-256 plan thực tế, SHA-256 CSV. Baseline JSON lưu metadata, metrics, min_samples và kết quả absolute gate; gate JSON lưu hash, metadata và metrics của baseline đã dùng. So sánh yêu cầu profile/filter/machine/plan/data giống nhau. Commit là provenance, không bắt buộc giống candidate. `--profile` phải đúng với lệnh JMeter thực tế: sidecar không thể tự chứng minh profile người vận hành khai báo. Cần cùng máy, runtime/JMeter và môi trường, kiểm soát tải nền; hostname và platform không chứng minh mọi yếu tố này giống nhau. Chạy lại gate được phép ghi lại gate JSON; `--make-baseline` là hành động thủ công tường minh, có thể ghi đè baseline sau khi đủ mẫu và đạt absolute gate.

## Bootstrap smoke A (người duyệt thực hiện, không chạy trong pipeline)

Từ root HW05, sau khi tự checkout đúng commit SUT, kiểm tra tree SUT không có thay đổi ngoài DB runtime và node_modules đã biết. Đảm bảo cổng 3000, JMeter, Java 17, Node/dependencies, curl và data sẵn sàng. Các lệnh sau tạo artifact mới; không chạy lại vào cùng thư mục. Baseline chỉ được tạo nếu đủ mẫu và đạt absolute SLO/error; không gọi đây là vượt relative gate.

```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
mkdir results/cpt/bootstrap_smoke
bash scripts/reset_sut.sh
jmeter -n -t test-plans/23120190_Load_20261117.jmx -l results/cpt/bootstrap_smoke/run.jtl -e -o results/cpt/bootstrap_smoke/html -Jthreads=30 -Jrampup=15 -Jduration=180 -Jlock_percent=5
python3 scripts/perf_gate.py --baseline results/cpt/baseline.json --write-metadata results/cpt/bootstrap_smoke/run.jtl --profile smoke
python3 scripts/perf_gate.py --baseline results/cpt/baseline.json --make-baseline results/cpt/bootstrap_smoke/run.jtl
```

Sau khi người có thẩm quyền duyệt baseline, B chạy diff thật với cùng candidate commit A, ví dụ `bash scripts/cpt_pipeline.sh main^ main` khi checkout `main` tại commit mong muốn. BASE=HEAD có thể skip. Kết quả mỗi lần ở `results/cpt/<shortsha>_<attempt>/`, chứa JTL, HTML, metadata, gate JSON. Thư mục tồn tại khiến pipeline dừng INCONCLUSIVE, không ghi đè/append; chọn `CPT_RUN_ID` khác cho lần mới. Reset được thực hiện trước mỗi attempt; SUT phải đã checkout HEAD, không có staged/unstaged/untracked khác ngoài DB runtime và node_modules. Không tự stash, checkout, xóa hay restore SUT.

## CI mẫu

Copy `ci/github-actions-perf.yml` vào SUT `.github/workflows/` sau khi cài self-hosted runner nhãn `linux`, `x64`, `performance` trên máy baseline, Java/JMeter/Node/curl/flock và dependency backend. Thiết lập `HW05_REPOSITORY` (owner/repo), `HW05_REF` (commit tools đã duyệt), secret `HW05_READ_TOKEN` có quyền read HW05, `CPT_BASELINE_DIR` là đường dẫn tuyệt đối bền vững trên runner chứa baseline đã duyệt. Checkout tools tại workspace root và SUT tại `eshop-sut/`; workspace phải có data, plans, scripts và results. Runner phải chuyên dụng/tin cậy; không chạy code PR không tin cậy trên runner có credentials hay mạng nhạy cảm. Serialize bằng concurrency và flock; không có workload khác dùng SUT.

Push/PR dùng smoke Load 30/15/180; nightly dùng Load 50/50/600 (users/ramp/duration giây). Weekly chạy lần lượt ba plan gốc: Stress bốn stage nối tiếp 50/100/200/290 users, mỗi stage ramp 30 s và duration 150 s; Spike baseline 10 users ramp 10 s duration 360 s đồng thời burst 190 users delay 120 s, ramp 5 s, duration 120 s; Soak 203 users ramp 60 s duration 720 s. Negative mặc định 5%. Lọc latency sau initial ramp, không bỏ ramp các stage sau hoặc burst; so với baseline cùng plan/profile/filter. Mỗi plan reset riêng, và retry reset lại. Schedule ép chạy; baseline riêng `nightly_baseline.json`, `stress_baseline.json`, `spike_baseline.json`, `soak_baseline.json`, không so với smoke `baseline.json`. Thiếu baseline là INCONCLUSIVE. Các tier chưa có số đo; theo dõi chi phí và báo động giả. Soak từng có p95 1.013 ms trong cửa sổ 120–240 s dù không đổi code ([bằng chứng](../../report/08_endurance.md)); hai FAIL cần người điều tra trước khi kết luận nguyên nhân.

Bootstrap các tier khác thủ công tương tự smoke, tạo thư mục mới cho từng run, reset trước mỗi run, rồi chạy JMeter với lệnh tương ứng bên dưới; sau đó thay `smoke` bằng tier trong `--profile` và `baseline.json` bằng `<tier>_baseline.json` trong hai lệnh metadata và make-baseline. Người duyệt đặt baseline đã tạo vào thư mục bền vững của runner.

```bash
jmeter -n -t test-plans/23120190_Load_20261117.jmx -l results/cpt/bootstrap_nightly/run.jtl -e -o results/cpt/bootstrap_nightly/html -Jthreads=50 -Jrampup=50 -Jduration=600 -Jlock_percent=5
jmeter -n -t test-plans/23120190_Stress_20261117.jmx -l results/cpt/bootstrap_stress/run.jtl -e -o results/cpt/bootstrap_stress/html
jmeter -n -t test-plans/23120190_Spike_20261117.jmx -l results/cpt/bootstrap_spike/run.jtl -e -o results/cpt/bootstrap_spike/html
jmeter -n -t test-plans/23120190_Soak_20261118.jmx -l results/cpt/bootstrap_soak/run.jtl -e -o results/cpt/bootstrap_soak/html
```

Unit test dùng CSV tổng hợp trong thư mục tạm để kiểm tra parser và quyết định, không phải JTL hay kết quả JMeter. Không lưu fixture trong results.
