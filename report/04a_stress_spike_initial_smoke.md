# Bước 7 – Stress/Spike smoke verification

**Kết quả: PASS cho các smoke đã chạy; failure-gate proof chưa thực hiện.** Chỉ smoke 1 VU, không phải performance test/full schedule. Dùng JMeter 5.6.3, Java 17 (`JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64`); timeout mỗi lệnh JMeter 90 giây. Mỗi lượt bên dưới đều chạy `./scripts/reset_sut.sh` ngay trước JMeter (reset xác nhận backend PID và seed 300 users). Không tạo/sửa thủ công JTL.

## Stress cơ bản

```sh
timeout 90s jmeter -n -t test-plans/23120190_Stress_20261117.jmx -Jthreads=1 -Jrampup=1 -Jloops=1 -l results/smoke/step7_stress_initial_20261117.jtl
```

Exit 0; JTL có 7 samples, mỗi sampler chính đúng một lần: `01 Login`, `02 Products`, `03 Product detail`, `04 Add cart`, `05 Get cart`, `06 Checkout`, `07 My orders`. Cả 7 trả HTTP 200, `success=true`, `failureMessage` rỗng. Summary: `7`, `Err: 0 (0.00%)`; log không có ERROR/Exception.

## Spike cơ bản

```sh
timeout 90s jmeter -n -t test-plans/23120190_Spike_20261117.jmx -Jthreads=1 -Jrampup=1 -Jloops=1 -l results/smoke/step7_spike_initial_20261117.jtl
```

Exit 0; 7 samples, bảy sampler chính đều một lần, HTTP 200, `success=true`, `failureMessage` rỗng. Summary: `7`, `Err: 0 (0.00%)`; không ERROR/Exception.

## Stress stage smoke

```sh
timeout 90s jmeter -n -t test-plans/23120190_Stress_20261117.jmx -Jthreads=1 -Jrampup=1 -Jloops=1 -Jstage_smoke=true -l results/smoke/step7_stress_stages_20261117.jtl -j results/smoke/step7_stress_stages_20261117_jmeter.log
```

Chạy sau reset. Exit 0; JTL có đúng 28 main samples (7 mỗi group `Stress stage 1`–`Stress stage 4`), tất cả `success=true`, HTTP 200; không có gate/internal sample trong JTL. Summary `28`, `Err: 0 (0.00%)`. JMeter runtime log ghi đủ ba gate, tất cả continuation thật `continue=true`: previous stage 1, 2, 3 lần lượt samples=7, errors=0.0%, p95=31, 14, 11 ms. Log cũng ghi stage 2, 3, 4 bắt đầu với `allowed=true`. Final summaries: stage 1–4 mỗi stage samples=7/errors=0.0%, p95 lần lượt 31/14/11/13 ms. Không ERROR/Exception. Bằng chứng log này lấy từ lần chạy lặp lại có `-j` tường minh; lần chạy đầu không ghi được JMeter runtime log riêng.

## Spike compressed timeline smoke

```sh
timeout 90s jmeter -n -t test-plans/23120190_Spike_20261117.jmx -Jthreads=1 -Jspike_threads=1 -Jrampup=1 -Jspike_rampup=1 -Jloops=-1 -Jduration=24 -Jspike_delay=8 -Jspike_duration=8 -Jtimeline_smoke=true -l results/smoke/step7_spike_timeline_20261117.jtl
```

Chạy sau reset; property `timeline_smoke=true` cần thiết để bật burst VU khi override dùng `loops=-1`. Exit 0, 37 samples, summary `Err: 0 (0.00%)`, không ERROR/Exception. Dựa trên JTL timestamps tương đối từ sample đầu (offset 0): baseline bắt đầu ở 0s; burst thread `Spike burst 2-1` samples xuất hiện ở 7.692s, tiếp tục đến 15.610s; sau đó không còn burst samples. Baseline `Spike baseline 1-1` có samples suốt khoảng 0–23.204s, gồm lúc burst hoạt động, rồi burst kết thúc và baseline tiếp tục. Điều này quan sát được low/high/low theo threadName/timing. Không đòi hỏi burst cycle đủ 7 samples; đây là window scheduler, không phải cam kết hoàn tất vòng.

Theo plan XML, ThreadGroup baseline scheduler bật khi `loops=-1`, duration lấy `duration` (24s); burst bật trong mode này với delay `spike_delay` (8s) và duration `spike_duration` (8s). Đây là cấu hình yêu cầu của plan; JTL trên ghi nhận burst samples xấp xỉ 7.7–15.6s kể từ sample đầu tiên, không suy diễn chính xác thread start/end chỉ từ sample timestamps. Chưa cần/đọc bytecode `ThreadGroup.scheduleThread`; không đưa ra tuyên bố sâu hơn về JMeter delay/duration ngoài plan và quan sát.

## Failure gate proof

Chưa chứng minh được stop-on-threshold. `HOST`/`PORT` trong plan là Test Plan User Defined Variables (không phải `${__P(...)}`); không override được an toàn bằng `-JHOST`/`-JPORT`, và plan không sửa đổi. Stage smoke chứng minh chỉ continuation ở healthy thresholds, không phải nhánh dừng khi threshold fail.

**Nguồn:** JTL và log tại `results/smoke/step7_*_20261117.jtl`/`.log`, đặc biệt `step7_stress_stages_20261117_jmeter.log`; plan source `test-plans/23120190_Stress_20261117.jmx` và `test-plans/23120190_Spike_20261117.jmx`. Không chạy performance test/full schedule; không cập nhật `AI_LOG.md`.
## Stress stop-gate verification

### Java 17 stop-gate verification

- Runtime from the same Bash invocation as JMeter: `JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64`; `java -version` reported `17.0.21.0.3`; `jmeter -v` reported JMeter 5.6.3. This run is distinct from the previous Java 25 attempt, which failed with Groovy `Unsupported class file major version 69`.
- Exact test command (after `scripts/reset_sut.sh`): `timeout 90s jmeter -n -t test-plans/23120190_Stress_20261117.jmx -Jthreads=1 -Jrampup=1 -Jloops=1 -Jstage_smoke=true -Jlock_percent=0 -l results/smoke/step7_stress_stop_java17_20261117.jtl -j results/smoke/step7_stress_stop_java17_20261117.log`
- Lockout setup: wrong-password login attempts returned **401**, **401**, **403** (the latter still **403** after 0.2 seconds). JMeter exit code was **0**. JTL contains exactly one sample: `01 Login`, response **403**, `success=false`, assertion `Expected HTTP 200`; no HTTP samples from stage 2 or later.
- Runtime log records `STRESS_GATE previous=1 samples=1 errors=100.0 p95_ms=23 continue=false` and stage 2 `allowed=false`, followed by `Test stopped - no more thread groups will be started`. Summary: 1 sample, 1 error (100.00%). Thus the Java17 run demonstrates the requested failure gate and suppression of later HTTP traffic.
- Cleanup: `scripts/reset_sut.sh` ran after JMeter and reset the SUT (backend PID 427901; 300 users seeded). No `.jtl` was manually created or edited; `AI_LOG.md` was not changed.