# Bước 33 – Rà soát Task 3 (Continuous Performance Testing) – bản chốt

Rà soát độc lập, chỉ đọc. Không sửa source/tài liệu/JTL/SUT/AI log; không commit, push, tạo Issue, JMeter, reset, đổi nhánh hay ngưỡng.
Mốc thời gian (giờ VN): audit đầu 23:15–23:17; review có mục tiêu sau handoff 23:29; bằng chứng bổ sung từ executor 23:28 (render) và 23:32:57 (18 tests). Bản chốt tổng hợp lúc 23:34.
Phạm vi: đề mục "Task 3" (PDF dòng 216–220), `report/16`, `16a`, `17`, `cpt_pipeline.sh`, `perf_decide.py`, `perf_gate.py`, `test_perf_gate.py`, `ci/github-actions-perf.yml`, `results/cpt/*`.
Đề yêu cầu: mô hình theo dõi commit SUT, quyết định có chạy test không, báo p95 regression, flow chart, thảo luận trade-off (chi phí, báo động giả).

**Nguồn bằng chứng:** phần "tôi chạy" là lệnh reviewer thực hiện (15 tests lúc đầu, 17 tests sau handoff). Phần "executor" là kết quả do executor chạy và Manager chuyển lại (render, 18 tests); tôi không chạy lại và không tự nhận. Sau bản 17 tests, tôi không chạy thêm lệnh nào.

## 1. Checklist (8 tiêu chí)

| # | Tiêu chí | | Bằng chứng (file:dòng / nguồn) |
|---|---|---|---|
| 1 | Mô hình theo dõi commit SUT, đã chạy trên commit thật | ✅ | Trigger `ci/github-actions-perf.yml:4-9`, chọn `base`/`head` `:45-54`; kiểm HEAD `cpt_pipeline.sh:8-10`. Chạy thật trên 3 commit `eshop-sut`: `85af3ba` (A, B), `4506e46` (C), `fc8660e` (D) – `results/cpt/demo_{A,B,C_after_fix,D}_execution.json`. Hạn chế: CI **chưa chạy trên GitHub**; "theo dõi" thực tế là `cpt_pipeline.sh BASE HEAD` chạy tay. |
| 2 | Bộ quyết định chạy/không chạy; demo C chứng minh skip | ✅ | Luật `perf_decide.py:22-35` (`[perf]` > `[skip perf]` > backend > unknown > skip); test `DecisionTests`. `demo_C_after_fix_execution.json`: `decision:"skip"`, `rc:0`, `jtl_paths_before == jtl_paths_after`, `new_jtl_paths:[]`. Skip thoát ở `cpt_pipeline.sh:31`, trước policy/reset/JMeter. Lần C đầu exit 2 (lock FD 9 do backend kế thừa) giữ nguyên ở `demo_C_execution.json`. |
| 3 | Phát hiện p95 regression; demo D chứng minh FAIL; tự chạy lại gate | ✅ | Tôi chạy lại hai lần (§2): D1 Checkout p95 **46**, D2 **45**, baseline **23**; cả hai exit **1**, `FAIL 06 Checkout: p95 regression`, không label khác. Tính tay: 23×6 = 138 < 230 (D1) và 225 (D2); chênh +23/+22 ≥ 5. Khớp `17 §2` và `run_gate.json`. Alert: `results/cpt/fc8660e7a8c6_smoke_alert.txt`. |
| 4 | Flow chart có và khớp code (mỗi nhánh chart có trong `cpt_pipeline.sh`) | ✅ | Ánh xạ ở §3 (tôi đối chiếu từng cạnh với code). Render chart mới (khối Mermaid ở `report/16_cpt_proposal.md` §6, snapshot `39DB`): executor chạy `npx` mermaid-cli + Chrome `--no-sandbox`, stdout `Generating single mermaid chart`, exit 0, lúc 23:28; đã xem SVG, thấy nhãn force / policy guard / lỗi Git / lỗi artifact+metadata / exit code, đã xóa file tạm (nguồn: executor qua Manager, tôi không render lại). Khối Mermaid không đổi byte kể từ lần render đó; Manager chỉ sửa chú thích bên dưới. |
| 5 | Trade-off chi phí + báo động giả, có số A/A | ✅ | `16 §8`, `17 §2`. Tôi đối chiếu với JSON: A Checkout 23, B 17, lệch 6 ms theo chiều giảm, 0 cảnh báo / 1 chiều so sánh. Chi phí đo thật: A 189.079 s, B 189.383 s cho cấu hình 180 s (overhead ≈ 9 s ≈ 5%); D+cleanup 384.618 s (2 attempt). Soak 120–240 s p95 1.013 ms trích đúng. `16 §8` ghi rõ đảo baseline B thì A sẽ FAIL (W2). |
| 6 | Code: unittest pass; luật 1,20× + 5 ms đúng; không chỉnh ngưỡng sau kết quả | ✅ | Unittest (tôi): **15 tests OK** lúc audit đầu, **17 tests OK** sau handoff. Unittest (executor, 23:32:57): **18 tests OK**, 1.438 s, exit 0, sau khi owner thêm 1 test CLI với 2 trường hợp invalid policy. Luật `perf_gate.py:83`: `p95_mới*5 > p95_cũ*6 and chênh >= 5` ⇔ `> 1,20×` và `≥ 5 ms` (số nguyên); `test_regression` 30→40 → 1, `test_small_absolute_delta` 10→13 → 0. `slo.json` sha256 `f120db11d053f41889ca73cf28dc8ff1aec45648aa0c02723443b872bac36502` (không đổi), 7 hàng khớp Task 2 §4. Lịch sử commit: `perf_gate.py` + `slo.json` vào ở `2fe9b49` (22:42) trước A (22:44:17); giữa `2fe9b49` và `d717569` chỉ đổi `cpt_pipeline.sh` (±1 dòng) và test. N=500 + 1.000 main chốt ở AI_LOG #36 (22:39), #37 (22:42), trước demo. Sau handoff: code production không đổi so với lần tôi kiểm 17 tests (Manager xác nhận), `:83` và các ngưỡng không đụng. |
| 7 | `eshop-sut` về main, `server.js` không có delay | ✅ | Audit đầu: `git -C eshop-sut branch --show-current` = `main`; HEAD `85af3ba875c88283615e22cb108f13e2fccaf0e9` = `origin/main`; `grep -nF -e delay -e setTimeout eshop-sut/backend/server.js` rc 1. Hai nhánh local `perf-demo/*` còn (đúng `17 §4`). Không chạy lại sau handoff; không chạy `git status` SUT, trạng thái DB/node_modules lấy từ `17 §4`. |
| 8 | Điểm yếu mà `16` chưa nêu | ✅ | W1–W9 ở §4; W1 là MUST FIX và đã có guard trong code. Warm-up, thứ tự label: không có case, không đưa vào. |

Không có ❌ trong 8 tiêu chí.

## 2. Lệnh đã chạy (reviewer) và kết quả thực

**Audit đầu (23:15–23:17):**

| Lệnh | Quan sát | rc |
|---|---|---:|
| `python3 -m unittest scripts.test_perf_gate` | `Ran 15 tests in 1.086s` / `OK` | 0 |
| `perf_gate.py --baseline results/cpt/baseline.json --candidate results/cpt/fc8660e7a8c6_1/run.jtl` | Checkout 813 mẫu p95 46 / p99 49; error 0/6040; `FAIL 06 Checkout: p95 regression` | 1 |
| tương tự `fc8660e7a8c6_2` | Checkout 816 mẫu p95 45 / p99 49; error 0/6067; `FAIL 06 Checkout: p95 regression` | 1 |

**Sau handoff (23:29), chạy một lần:**

| Lệnh | Quan sát | rc | Kỳ vọng |
|---|---|---:|---|
| `python3 -m unittest scripts/test_perf_gate.py` | `Ran 17 tests in 1.253s` / `OK` | 0 | 0 ✅ |
| `bash -n scripts/cpt_pipeline.sh` | không output | 0 | 0 ✅ |
| `python3 scripts/perf_gate.py --check-policy --baseline results/cpt/baseline.json --profile smoke` | không output (policy sẵn sàng) | 0 | 0 ✅ |
| gate D1 (`.../fc8660e7a8c6_1/run.jtl`) | Checkout 813, p95 46, p99 49; 6 label còn lại p95 ≤ 5; error 0/6040; `FAIL 06 Checkout: p95 regression` | 1 | 1 ✅ |
| gate D2 (`.../fc8660e7a8c6_2/run.jtl`) | Checkout 816, p95 45, p99 49; 6 label còn lại p95 ≤ 4; error 0/6067; `FAIL 06 Checkout: p95 regression` | 1 | 1 ✅ |

**Bằng chứng executor (không phải lệnh của tôi):** unittest 23:32:57 → `Ran 18 tests in 1.438s` / `OK`, exit 0; render Mermaid 23:28 → exit 0 (mục 4).

Hai bài test thêm giữa 15 và 17: `test_policy_hash_mismatch_is_inconclusive_but_absolute_failure_survives` và `test_deep_profile_without_policy_stops_before_reset`. Bài thứ 18 (owner thêm sau bản 17) là test CLI cho `--check-policy` với hai trường hợp invalid policy. Nó đóng khoảng trống "`check_policy` không có test trực tiếp" mà tôi nêu ở bản trước. Tôi chỉ nhận số 18 và kết quả từ executor.

**Artifact D1/D2 (quyết định đã đóng):** lệnh `--candidate` ghi lại `run_gate.json`; lần chạy đầu của tôi dùng đường dẫn baseline tương đối nên `baseline.path` trong `fc8660e7a8c6_1/run_gate.json` và `_2/run_gate.json` đổi từ `/home/zinn/zinn/testing/hw05/results/cpt/baseline.json` thành `results/cpt/baseline.json` (đúng 1 dòng mỗi file; metric/status/hash không đổi). Manager chấp nhận giữ hai file như output tính lại do chương trình sinh ra và commit chúng; không `git checkout`, không sửa tay, không động vào JTL thô. Ghi nhận ở đây để minh bạch: thay đổi này do lệnh gate của reviewer gây ra, không phải sửa dữ liệu.

## 3. Flow chart (`16 §6`, bản mới) ↔ `cpt_pipeline.sh`

| Nút/cạnh | Code |
|---|---|
| `A → D` kiểm HEAD/tree/lock/profile; `D → X` (exit 2) | HEAD `:8-10`; staged `:12`; tree lạ `:13-15`; lock `:16-17`; tier lạ `:25` |
| `D → B` đọc diff + message HEAD; `B → X` lỗi BASE/Git | `perf_decide.py` `:29` `|| exit 2` |
| `V` CPT_FORCE = 1 → `R`; không → `Q` | `:31` (`CPT_FORCE != 1` mới được skip) |
| `Q → Skip → C` stdout, exit 0; `Q → Run → R` | in JSON `:30`; `exit 0` `:31` |
| `R → T` baseline + SLO tương thích; không → `X` | deep tier thiếu `CPT_SLO` `:32-34`; `--check-policy` `:38-40`; trước `mkdir` `:45` |
| `T → E` tạo thư mục artifact + reset; lỗi → `X` | `mkdir` `:45`; `reset_sut.sh 9>&-` `:46` |
| `E → F` chạy + metadata; lỗi → `X` | `jmeter` `:47`; `--write-metadata` `:48` |
| `F → G` gate; `G → X` INCONCLUSIVE/lỗi | `:49-52` (status ≠ 0/1 → exit 2) |
| `G → H` PASS, `exit 0` | `:51` |
| `G → I → J → K` FAIL, retry với artifact riêng | `for attempt in 1 2` `:42`, `:44-48` |
| `K → L` FAIL cả hai → alert, exit 1 | `:54-64` |
| `K → M` PASS sau FAIL, exit 0 | `:51` (cùng đường với H) |
| `L → U`, duyệt/baseline/Issue | ngoài code (README, `--make-baseline`) |

Mọi cạnh và nhánh của chart mới đều có dòng tương ứng; ba nhánh thiếu ở bản cũ (`decide` lỗi, `CPT_FORCE`, artifact/metadata lỗi) đã được vẽ. Nit trước đây về nút `F` ("Chạy smoke" trong khi tier deep chạy plan riêng) đã được xử lý bằng chú thích: hình minh họa luồng smoke, các tier theo lịch chạy cùng luồng nhưng theo plan ở `16 §3`; khối Mermaid không đổi. Nút `H`/`M`/skip là exit code + stdout/artifact, không có thông báo riêng (đã ghi ở `16 §6`).

## 4. Điểm yếu và trạng thái

**W1 – MUST FIX → đã xử lý trong code (profile policy readiness).**
- Phát hiện đầu: tầng Stress/Spike/Soak dùng `slo.json` smoke; trên 3 JTL Task 1 (ramp 30/10/60 s, `perf_gate.measure()`), cả 7 label vượt SLO (Checkout p95: Stress 980, Spike 1798; Soak p99 3434 vs 150; Login Soak p95 38 đạt nhưng p99 645 > 125).
- Đính chính đã ACK: không phải "không bao giờ có baseline"; absolute SLO FAIL ≠ regression; mức MUST FIX là **readiness/scope của policy**.
- Đã sửa: `cpt_pipeline.sh:32-37` bắt buộc `CPT_SLO` cho stress/spike/soak, không fallback về smoke; `:38-40` gọi `perf_gate.py --check-policy` trước `mkdir`/reset/JMeter, lỗi → INCONCLUSIVE exit 2. `perf_gate.py:111-134` (`check_policy`) kiểm: schema/giá trị SLO, baseline `PASS`, `min_samples ≥ 500`, hash SLO, profile, filter, hostname/platform/arch, hash plan và CSV, provenance, ≥ 1.000 main, từng label ≥ 500, baseline PASS với SLO đang dùng. `:183-184` thêm cờ `baseline SLO policy hash mismatch`. CI mẫu đọc `$CPT_BASELINE_DIR/<tier>_slo.json`, `unset CPT_SLO` cho smoke/nightly. Smoke/nightly mặc định, N=500, 1.000 main, 1,20/+5 không đổi.
- Test: `test_deep_profile_without_policy_stops_before_reset`; `test_policy_hash_mismatch_…` (hash lệch → INCONCLUSIVE rc 2, vi phạm SLO tuyệt đối vẫn FAIL rc 1); test CLI `--check-policy` với 2 trường hợp invalid policy (executor, 18 tests). Tôi chạy `--check-policy` trên baseline smoke thật → rc 0.
- Giới hạn còn lại (readiness, không phải lỗi code): chưa có policy/baseline deep do con người duyệt; weekly sẽ INCONCLUSIVE (CI đỏ) cho tới khi step 34 quyết định. Đường code đã cấu hình đầy đủ nhưng **chưa có lần chạy nào của deep tier**; không tuyên bố weekly đã pass.

**W2 – Baseline một lượt; chiều ngược của A/A báo FAIL (rủi ro vận hành).**
- Cùng commit: Checkout p95 **23** (baseline) và **17** (B). Nếu baseline là B: `23×5 = 115 > 17×6 = 102` và `+6 ≥ 5` → `REGRESSION` trên code không đổi. Retry cùng baseline chỉ giảm nhiễu của candidate.
- Lát theo thời gian (tính từ JTL): A 15 → 22 → 25; B 20 → 19 → 15; D1 45 → 47 → 46, ở các lát **30 s / 30 s / 105 s** (15–45, 45–75, 75–180 s); lát cuối dài hơn nên không so biên độ trực tiếp. Nguyên nhân chưa biết.
- Đã ghi vào `16 §5, §8`. Xử lý vận hành (chưa có code): chạy ≥ 3 lượt cùng commit, **chọn một lượt thật làm đại diện** (giữ JTL, hash, metadata), chỉ duyệt khi mọi cặp theo cả hai chiều PASS; không tổng hợp median p95 mất JTL nguồn.

**W3 – Sàn +5 ms làm mù 6/7 label ở smoke (giới hạn).** Baseline p95: Login 4, Products 5, Detail 4, Add cart 3, Get cart 3, My orders 5. Add cart 3→7 (+133%) vẫn PASS (`+4 < 5`); Products 5→9 cũng PASS; SLO 50–75 ms không bắt; p99 chỉ so với SLO. Đã ghi ở `16 §8` mục "Bỏ sót" (đánh dấu là giả định, không phải số đo); luật giữ nguyên.

**W4 – FAIL rồi PASS thoát exit 0, không cờ flaky (rủi ro vận hành).** `cpt_pipeline.sh:51` `exit 0` ở attempt 2; chỉ có `<sha>_1/run_gate.json` còn FAIL. Đính chính đã ACK: xác suất p² chỉ đúng khi hai lượt độc lập; cùng máy/baseline có thể tương quan, không mặc định. Đây là hệ quả của luật "hai FAIL mới báo" do đề chọn, không vi phạm đặc tả. `16 §8` đã ghi; code chưa thêm artifact flaky.

**W5 – CI mẫu (chưa chạy trên GitHub, [INFERENCE]).** Nguồn chính thức (tôi đã đọc): https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency – mặc định `queue: single`, chỉ 1 lượt pending, lượt mới thay lượt cũ; `queue: max` cho tới 100 pending. Hệ quả suy ra: P1 (backend) đang chờ bị P2 (chỉ Markdown) thay; P2 dùng `BASE = event.before` nên diff chỉ có `.md` → skip. Thêm: `on: push` + `pull_request` không lọc nhánh → PR cùng repo đo hai lần cùng SHA. `16 §8` đã ghi; CI mẫu chưa sửa. Hướng: `queue: max`, `push: branches: [main]`, lưu SHA đo gần nhất làm `BASE`.

**W6 – Marker chỉ đọc message HEAD (hợp đồng đã chốt).** Push 2 commit: c1 sửa `backend/server.js`, c2 có `[skip perf]` → skip cả dải. Đúng hợp đồng `perf_decide.py BASE HEAD`; `16 §2` đã ghi.

**W7 – Baseline cố định, không phải commit BASE.** Lỗi đã vào main tiếp tục FAIL ở các commit backend sau cho tới khi có baseline mới. Đính chính đã ACK: alert (`cpt_pipeline.sh:57`) in **đường dẫn** baseline, không in commit; commit baseline nằm trong gate JSON `baseline.metadata.source_commit`. `16 §5` đã ghi đúng.

**W8 – Nhận diện máy gồm cả chuỗi kernel (vận hành; tài liệu đã bổ sung).** `baseline.json` lưu `platform: "Linux-7.0.0-43-generic-x86_64-with-glibc2.43"`. `check_policy` (`perf_gate.py:119,123`) và gate (`:178-180`) so bằng nhau. Nâng kernel (ví dụ `-43` → `-44`) làm mọi tier INCONCLUSIVE (`baseline provenance or environment mismatch`) cho tới khi người duyệt tạo lại baseline. Đúng theo thiết kế nhận diện chặt. Manager đã thêm đoạn prose ở `16`: nâng kernel ⇒ INCONCLUSIVE, cần duyệt lại baseline (theo báo cáo của Manager; tôi chưa đọc lại đoạn này).

**W9 – "Đã duyệt" không kiểm được bằng code (vận hành; tài liệu đã bổ sung).** `load_slo` chỉ kiểm số hữu hạn, không âm, `error_pct ≤ 100`. Case: `CPT_SLO` trỏ tới file SLO sao chép với p95/p99 = 1e9 vẫn qua `--check-policy` (baseline phải khớp hash và PASS với chính file đó). Phê duyệt là kiểm soát của người và quyền truy cập runner, không phải của code. Manager đã thêm đoạn prose ở `16` về phê duyệt thủ công, hash policy và kiểm soát truy cập (theo báo cáo của Manager; tôi chưa đọc lại). Hướng vận hành: ghi hash policy đã duyệt trong tài liệu duyệt (step 34).

**Không đưa vào (không có case):** cache warm-up (lát 15–45 s của A là 15 ms, thấp nhất; B 20; D phẳng); thứ tự label.

## 5. Phân loại và hướng xử lý

| Loại | Mục | Trạng thái / hành động |
|---|---|---|
| MUST FIX – đã xử lý | W1 | Guard trong code + test; step 34 phải quyết định policy/baseline deep đã duyệt trước khi bật CI |
| Đã đóng (so với bản trước) | test trực tiếp `--check-policy`; render chart mới; nit chart `F`; W8, W9 ở `16`; artifact D1/D2 | Test 18 và render do executor; nit/W8/W9 do Manager sửa tài liệu; artifact Manager chấp nhận giữ |
| Rủi ro vận hành / cần người | W2 (quy trình duyệt baseline), W3, W4, W5, W6, W7 | Đã ghi ở `16`; không có code sửa; quyết định trước khi bật CI thật |
| Cần người ở step 34 | policy + baseline deep đã duyệt; hash policy; baseline smoke ≥ 3 lượt chọn đại diện | Chưa làm, chưa chạy |

## 6. Kết luận

Task 3 đủ 8 tiêu chí: mô hình, quyết định chạy/skip (demo C), phát hiện p95 (demo D, tôi tính lại 2 lần, exit 1), flow chart khớp code và đã render, trade-off có số A/A, code + test pass (15 → 17 do tôi, 18 do executor), SUT về `main` không còn delay. Không phát hiện ngưỡng nào bị đổi sau khi thấy kết quả. MUST FIX duy nhất (W1) đã có guard và test; còn lại là điều kiện vận hành và quyết định của người (policy/baseline deep chưa được duyệt, không phải lỗi code đã biết).

Chưa kiểm: CI trên GitHub; deep tier với policy/baseline đã duyệt (chưa có đầu vào, chưa chạy); `git status` SUT sau cleanup; nội dung chính xác của hai đoạn prose W8/W9 và chú thích chart mới ở `16` (nhận qua Manager).

## Ghi chú xuất bản và bàn giao của Manager

Báo cáo trên do `TaskThreeReview` (`anthropic/claude-sonnet-5-5`) trả về; Manager xuất bản và chỉ chuẩn hóa tham chiếu snapshot `39DB`, không đổi kết luận. Các khuyến nghị đo lặp baseline/duyệt policy deep là điều kiện trước khi vận hành CI, không tăng yêu cầu của bước 34 thành chạy thêm JMeter. Bước 34 theo prompt: sinh viên tự chạy hai lệnh kiểm chứng, viết report/19 và điền Human review; có thể quyết định chưa duyệt baseline/policy để triển khai.
