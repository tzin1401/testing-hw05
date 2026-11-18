# Bước 32 – Demo CPT trên commit SUT thật

## 1. Phạm vi và kết quả A–D

Bốn lượt JMeter thật: A một lượt, B một lượt, D hai lượt. C không chạy JMeter. Cả bốn dùng Load plan `23120190_Load_20261117.jmx`, 30 VU, ramp 15 s, duration 180 s, Negative 5%; reset trước mỗi lượt. Giữ nguyên SLO Task 2, N=500 mỗi label, tối thiểu 1.000 main sample/run cho relative gate, luật p95 mới >1,20 baseline **và** tăng ≥5 ms. Không đổi ngưỡng sau khi thấy kết quả.

Metrics được gate tính bằng `jtl_truth.load_jtl()`/`metrics()`, nearest-rank. Latency theo từng label chính, sample bắt đầu sau initial ramp; error all toàn run và cửa sổ 120 s sau ramp, cửa sổ cuối có thể partial. Main diagnostic sau ramp khác mẫu số/thời gian của all whole-run. Metadata/profile/filter/machine/plan/CSV tương thích. HTML là artifact đi kèm, không dùng để thay số gate có bộ lọc khác.

| Kịch bản | Commit SUT | Decision | Gate / exit pipeline | Bằng chứng |
|---|---|---|---|---|
| A – bootstrap trên main | `85af3ba875c88283615e22cb108f13e2fccaf0e9` | Chạy smoke thủ công theo bước A, không gọi decide | PASS absolute/error/count; **chưa có relative gate**. Reset/JMeter exit 0, tạo baseline thành công. | [JTL](../results/cpt/bootstrap_smoke/run.jtl), [HTML](../results/cpt/bootstrap_smoke/html/index.html), [baseline/gate](../results/cpt/baseline.json), [execution](../results/cpt/demo_A_execution.json) |
| B – A/A cùng commit | `85af3ba875c88283615e22cb108f13e2fccaf0e9` | run, diff thật `main^..main` | PASS, exit 0; một attempt, không retry | [JTL](../results/cpt/85af3ba875c8_1/run.jtl), [gate](../results/cpt/85af3ba875c8_1/run_gate.json), [execution](../results/cpt/demo_B_execution.json) |
| C – docs-only | `4506e466a84ec0a25d3397ce8fd234f5d766b872` | skip sau fix lock, lý do `no impact on the fixed API workload` | SKIP, exit 0; **không gọi gate**, không reset/JMeter, không có JTL | [execution sau fix + inventory](../results/cpt/demo_C_after_fix_execution.json); lỗi lần đầu được giữ riêng tại §3 |
| D – thêm delay Checkout | `fc8660e7a8c6685cc7ed9c48b84de972d4323677` | run, diff `main..perf-demo/slow-checkout` | Cả hai attempt FAIL chỉ vì `06 Checkout: p95 regression`; exit pipeline **1** | [D1 JTL](../results/cpt/fc8660e7a8c6_1/run.jtl), [D1 gate](../results/cpt/fc8660e7a8c6_1/run_gate.json), [D2 JTL](../results/cpt/fc8660e7a8c6_2/run.jtl), [D2 gate](../results/cpt/fc8660e7a8c6_2/run_gate.json), [alert local](../results/cpt/fc8660e7a8c6_smoke_alert.txt), [execution/stdout](../results/cpt/demo_D_execution.json) |

Nguồn p95 cho từng kịch bản ở §2. Commit C chỉ thêm một dòng comment README, commit D chỉ thêm đúng dòng `app.use("/api/checkout", (req, res, next) => setTimeout(next, 30));` trước route Checkout, đều trên nhánh local, không commit vào main/push. Commit dùng cơ chế chọn đúng dòng/file, không stage DB. A tạo baseline bằng lệnh explicit đã được người dùng cho phép ở bước 32A; pipeline không tự cập nhật baseline sau B hay D.

## 2. Số đo từ baseline/gate JSON

| Label | A p95 (ms) | B p95 (ms) | D1 p95 (ms) | D2 p95 (ms) |
|---|---:|---:|---:|---:|
| 01 Login | 4 | 4 | 4 | 4 |
| 02 Products | 5 | 5 | 4 | 4 |
| 03 Product detail | 4 | 4 | 4 | 4 |
| 04 Add cart | 3 | 3 | 3 | 3 |
| 05 Get cart | 3 | 3 | 3 | 3 |
| 06 Checkout | 23 | 17 | 46 | 45 |
| 07 My orders | 5 | 5 | 5 | 4 |

Độ lệch p95 tuyệt đối lớn nhất trong A/A là **6 ms**, tại Checkout và theo chiều giảm. B không có label regression/SLO/error FAIL: **0 cảnh báo trong 1 lần A/A**. Đây không phải ước lượng tin cậy của tỷ lệ báo động giả trên quần thể; một cặp không xác lập độ nhiễu hai chiều hay chứng minh ngưỡng tối ưu. Không diễn giải lock lỗi của C thành báo động giả về p95.

D bắt được regression ở Checkout ở cả hai lượt; không có label khác bị gate đánh dấu regression, cũng không có SLO/error FAIL. Mức tăng thực không cần bằng đúng 30 ms middleware do thời gian nền biến động; không điều chỉnh số hoặc baseline để khớp delay danh nghĩa.

| Run | All sample toàn run | Error all |
|---|---:|---:|
| A | 6073 | 0 |
| B | 6112 | 0 |
| D1 | 6040 | 0 |
| D2 | 6067 | 0 |

Các gate JSON lưu count/p95/p99 từng label, error windows, SLO fingerprint và baseline đã dùng; mỗi label đều đủ N. Không coi Negative 401/403 đã được assertion chấp nhận là lỗi hoặc latency Auth.

## 3. Kết quả khác kỳ vọng và sửa nguyên nhân

- A: lệnh metadata/baseline ban đầu thiếu `--baseline`, argparse từ chối. Bổ sung đúng tham số và dùng nguyên JTL, không chạy lại JMeter; baseline được tạo PASS. Record thời gian A chỉ đo reset + JMeter, không đo riêng các lệnh CLI sửa lỗi này.
- C lần đầu exit **2**, `INCONCLUSIVE: SUT already in use`, trước decide/reset/JMeter. [Record gốc](../results/cpt/demo_C_execution.json) giữ nguyên, không thay thành skip. `lsof` xác nhận backend Node PID 3894385 giữ FD 9 của `.sut.lock` do kế thừa từ pipeline B qua reset.
- Sửa [pipeline](../scripts/cpt_pipeline.sh): đóng FD 9 trong child gọi reset, cha vẫn giữ lock xuyên suốt pipeline. Không xóa lock file, không né kiểm tra bằng cách chuyển decide lên trước lock. Thêm [regression test](../scripts/test_perf_gate.py) chạy CLI trong workspace tạm: backend stub còn sống sau khi pipeline thoát, nhưng tiến trình khác phải lấy được lock thật bằng `fcntl.flock`. Không sinh JTL giả.
- [Reset bảo trì ngoài pipeline](../results/cpt/demo_lock_cleanup_execution.json) dừng holder cũ và khởi động backend không thừa hưởng FD 9; `lsof` sau đó không có holder. Chạy C sau fix đúng một lần: skip, inventory JTL trước/sau không đổi. Không có JMeter bổ sung từ sự cố này.
- Sau fix, executor chạy một lần mỗi check: unittest **15 tests / 1.055 s / OK / exit 0**; `bash -n scripts/cpt_pipeline.sh` exit 0, không output. Ngưỡng/SLO/baseline/gate math không thay đổi trong fix này.
- Mẫu CI có job condition chặn PR từ fork trước khi dùng self-hosted runner; tài liệu nêu trust boundary. Đây là kiểm soát ở file mẫu, **chưa triển khai/chạy CI trên GitHub**.

## 4. Cleanup và thời gian thực

[Cleanup E](../results/cpt/demo_E_execution.json) chạy trong EXIT trap sau D: switch về main exit 0, HEAD đúng `85af3ba875c88283615e22cb108f13e2fccaf0e9`, log `85af3ba first upload`, grep dòng delay không có kết quả (exit 1), reset exit 0. Backend mới PID 3952534. Giữ hai nhánh `perf-demo/docs-only` và `perf-demo/slow-checkout` làm bằng chứng local, không push.

Working tree SUT sau cleanup vẫn là ` M backend/database.sqlite` và `?? backend/node_modules/`, đúng loại trạng thái runtime ban đầu. Source đã về main, **không gọi toàn bộ working tree sạch**. DB được reset theo yêu cầu demo, không cam kết byte DB bằng trước test; không restore/xóa thay đổi người dùng hay dependency.

Thời lượng thực từ monotonic clock trong execution JSON, không lấy ước tính cấu hình làm số đo:

| Khoảng lệnh đã đo | Giây thực | Nguồn |
|---|---:|---|
| A | 189.079 | [record](../results/cpt/demo_A_execution.json) |
| B | 189.383 | [record](../results/cpt/demo_B_execution.json) |
| C_initial | 0.025 | [record](../results/cpt/demo_C_execution.json) |
| lock_cleanup | 5.805 | [record](../results/cpt/demo_lock_cleanup_execution.json) |
| C_after_fix | 0.070 | [record](../results/cpt/demo_C_after_fix_execution.json) |
| D_E | 384.618 | [record](../results/cpt/demo_D_execution.json) |

Tổng các khoảng lệnh được ghi nhận: **768.980 s (12.82 phút)**. D_E đã bao gồm cleanup; không cộng E lần nữa, không bịa thời gian E riêng. Tổng này không bao gồm riêng các CLI bootstrap recovery chưa đo.

Từ start epoch A đến end epoch D+cleanup: **1431.771 s (23.86 phút)**, tương ứng `2026-11-18 22:44:17 +0700` → `2026-11-18 23:08:09 +0700`. Đây là tổng thời gian tường của demo gồm cả điều phối/chờ/sửa bug giữa các lượt, không phải CPU time. Không khẳng định máy chỉ bận trong các khoảng đã đo, hoặc coi một cặp A/A là kiểm chứng toàn bộ mọi tier.
