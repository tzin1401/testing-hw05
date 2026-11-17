# Bước 19 – Rà soát cuối Task 1

Ngày rà soát: 2026-11-18 02:22 (giờ VN). Phạm vi: Task 1 theo Mục 6, Mục 11 và Mục 14 của đề. Task 2, Task 3 và Agent Skill nằm ngoài phạm vi và **không** được coi là hoàn thành.

Rà soát chỉ đọc và đối chiếu. Không chạy lại tải, không reset SUT, không chạy lại broad check. Các self-test và kiểm tra determinism của `scripts/summarize.py` lấy từ [08_endurance.md](08_endurance.md), đã chạy ở bước 16.

Quy ước: ✅ đạt, có file chứng minh. ❌ chưa đạt hoặc có sai sót, có hướng xử lý ở mục 4. ⚠ đạt nhưng có giới hạn cần biết.

## 0. Việc đã kiểm tra trực tiếp ở bước này

- `grep` các `ResultCollector`, `HTTPSamplerProxy`, `CSVDataSet`, `JSONPostProcessor` và assertion trong 4 file `.jmx`.
- Đọc script assertion JSR223 của plan Load.
- Parse CSV 5 JTL và đếm dòng; so với `Total.sampleCount` của `statistics.json`.
- Rút ngẫu nhiên 5 trường của bảng kết quả trong `TASK1_REPORT.md` để so với `statistics.json` (mục 1.5).
- Đọc `results/analysis/endurance.json`; tính `sha256sum` và so với [08_endurance.md](08_endurance.md).
- Đọc các ảnh `evidence/hardware.png`, `load_run.webp`, `stress_run.png`, `spike_run.png`, `soak_run.png`, `load_result.png`, `spike_result.png`, `soak_result.png`, `stress_result.png`.
- Đối chiếu số dòng trích trong `09_bugs.md` với `eshop-sut/backend/server.js` và `eshop-sut/README.md`.
- Kiểm tra link nội bộ của `TASK1_REPORT.md` và `README.md`: 93 link, 0 thiếu. Con số này khớp với kết quả Manager đã báo; kiểm tra lại chỉ để xác nhận.

## 1. Checklist theo yêu cầu bước 19

### 1.1 Test plan

| Mục | KQ | Bằng chứng |
|---|:-:|---|
| 3 plan đúng tên `{StudentID}_{Type}_{YYYYMMDD}` | ✅ | [Load](../test-plans/23120190_Load_20261117.jmx), [Stress](../test-plans/23120190_Stress_20261117.jmx), [Spike](../test-plans/23120190_Spike_20261117.jmx), cộng [Soak](../test-plans/23120190_Soak_20261118.jmx). Ngày trong tên plan là ngày tạo (11-17, Soak 11-18). Kết quả mang ngày chạy 20261118, theo [07_run_log.md](07_run_log.md). |
| Cùng workflow | ✅ | Cả 4 plan có đủ 7 sampler `01 Login`, `02 Products`, `03 Product detail`, `04 Add cart`, `05 Get cart`, `06 Checkout`, `07 My orders`, kèm `Negative login`. Path: `/api/login`, `/api/products`, `/api/products/${product_id}`, `/api/cart` (POST và GET), `/api/checkout`, `/api/orders/my-orders`. Stress có 4 nhóm × 8 sampler, Spike 2 nhóm × 8. Cả 4 JTL đều có đủ 7 label + `Negative login` (đếm ở mục 1.2). |
| Đủ 3 nhóm endpoint | ✅ | Auth = login. Read = list + detail. Transactional = cart + checkout + my-orders. Xem [TASK1_REPORT.md](TASK1_REPORT.md) mục 2 và [02_test_design.md](02_test_design.md). |
| Dữ liệu từ CSV | ✅ | `CSVDataSet`: `data/users_main.csv` (290 dòng), `data/products.csv` (5), `data/users_lock.csv` (10), đều có header. Biến token, user_id và order_id lấy bằng JSON Extractor (`$.token;$.user.id`, `$.orderId`). |
| Assertion có nội dung | ✅ | JSR223 "Workflow response checks" kiểm tra HTTP 200, token/user.id khớp biến, sản phẩm có trong list, giá (cả string và number) bằng BigDecimal, phần tử cuối của giỏ, `orderId` số nguyên dương khớp biến, `my-orders` khớp `total_amount`. Nhánh login sai chấp nhận 401/403. Nhánh `default` ép fail. |
| 3 listener khác nhau | ✅ | Mỗi plan đúng 1 `ResultCollector`. Load = `SummaryReport`. Stress = `StatVisualizer` (Aggregate Report, tên "Stress report"). Spike = `RespTimeGraphVisualizer`. Soak = `SimpleDataWriter` (plan bổ sung, loại thứ tư, không trùng loại nào). |

### 1.2 Raw log, HTML, soak, ngưỡng

| Mục | KQ | Bằng chứng |
|---|:-:|---|
| 3 JTL đầy đủ + Soak | ✅ | Số dòng dữ liệu parse bằng CSV bằng đúng `Total.sampleCount` của HTML, 0 sample fail. Load 33,775. Stress 175,882. Spike 27,965. Soak 158,591. Mỗi JTL có 7 label luồng chính + `Negative login` (Load 241, Stress 1,261, Spike 205, Soak 1,129). Thời điểm sửa file cuối của JTL trùng giây kết thúc JMeter (Load 00:46:48, Stress 01:08:21, Spike 01:21:19, Soak 01:42:53). `git diff` không thấy JTL bị đổi sau khi commit. File: `results/jtl/23120190_{Load,Stress,Spike,Soak}_20261118.jtl`. |
| JTL writer của Soak không cộng đôi | ✅ | `results/jtl/23120190_Soak_20261118_writer.jtl` có cùng 158,591 dòng. Chỉ dùng JTL chính cho mọi con số. |
| 3 thư mục HTML + Soak | ✅ | `results/html/23120190_{Load,Spike,Soak}_20261118/` và Stress. Stress dùng bản `23120190_Stress_20261118_recovered/` làm bản chính trong báo cáo. Có sai sót ghi chú, xem ❌ mục 4.1. |
| Có Soak | ✅ | 203 VU, ramp 60 s, 720 s. [07_run_log.md](07_run_log.md) mục Soak, [08_endurance.md](08_endurance.md). |
| Ngưỡng có số cụ thể | ✅⚠ | Stress sau ramp, mức ổn định quan sát cao nhất: **290 VU, 468.556 RPS, p95 947 ms, 0% lỗi**; chưa vượt ngưỡng nào. Soak 203 VU: phút index 3 có **p95 2,244 ms > 2,000 ms**, 171.183 RPS, 0% lỗi, trong khi p95 tổng chỉ 21 ms. Không đánh PASS ổn định suốt 12 phút. RSS cực đại quan sát: Stress **171.64 MiB**, Soak **127.80 MiB**; độ dốc Soak **1.470 MiB/phút**. Đây không phải trần RAM cứng và không chứng minh leak. Nguồn: [endurance.json](../results/analysis/endurance.json). SHA-256 `72588ddb…04c2` khớp báo cáo. Self-test 3 PASS và `cmp` exit 0 lấy từ 08. |

⚠ Chưa có breakpoint đến 290 VU. Cause của phút 3 chưa xác định. Các ảnh `soak_run.png` (01:41) và `stress_run.png` (01:07) cho thấy cùng lúc còn nhiều tiến trình khác tiêu thụ CPU (gnome-shell, Chrome, OBS, `gst-video-thumbnailer`); đây là quan sát, không phải kết luận nguyên nhân.

### 1.3 Hardware và reset lockout

| Mục | KQ | Bằng chứng |
|---|:-:|---|
| Hardware report | ✅ | [05_hardware.md](05_hardware.md) (bảng spec + output lệnh) và [hardware.png](../evidence/hardware.png). |
| Hostname khớp | ✅⚠ | `zinn-Nitro-AN515-57` giống nhau trong `hostname` (chạy lại lúc rà soát), 05_hardware.md, `hardware.png` và tiêu đề terminal của 4 ảnh run. Việc khớp với "các HW trước" chỉ có người dùng xác nhận trong Human review #3; tôi không có bằng chứng độc lập của bài cũ. |
| Ghi các bước reset lockout | ✅ | [07_run_log.md](07_run_log.md) ghi thời điểm reset từng lần (Load 00:36:25, Stress 00:58:12, Spike 01:15:09, Soak 01:30:44). [02_test_design.md](02_test_design.md) mục "Tài khoản, lockout và reset" (dòng 47–52). [TASK1_REPORT.md](TASK1_REPORT.md) mục 6. Script [reset_sut.sh](../scripts/reset_sut.sh). Raw lockout: [flow1_bugs_20261118.txt](../results/repro/flow1_bugs_20261118.txt): sau 2 lần sai trả 401/401; mật khẩu đúng trả **403 ở ~35 s và ~179 s, 200 ở ~181 s**. Plan tách tài khoản login sai (perf291–300). |

### 1.4 AI sai gì, vì sao, bug report

| Mục | KQ | Bằng chứng |
|---|:-:|---|
| Có mục AI sai gì / vì sao | ✅ | [TASK1_REPORT.md](TASK1_REPORT.md) mục 4. Bảng 7 lỗi kèm nguyên nhân (prompt, giới hạn model, đặc điểm endpoint, môi trường) trong [06_human_review.md](06_human_review.md) (do người dùng viết). Chi tiết ở [03_review_load.md](03_review_load.md) và [04_review_stress_spike.md](04_review_stress_spike.md), mỗi file có mục "Đã sửa" kèm lý do AI bỏ sót. Lỗi báo cáo "200 cart/checkout" ban đầu thực tế trả 403 đã được Manager sửa. |
| Có bug report | ✅ | [09_bugs.md](09_bugs.md): BUG-01 lockout (Medium), BUG-02 checkout tin `total_amount` (High), BUG-03 giỏ không xóa sau checkout (Medium), BUG-04 kiểu giá string/number (Low, suy luận consistency vì spec FR-06 không quy định kiểu). Raw: `results/repro/flow1_bugs_20261118.txt` và [checkout_cart_20261118.txt](../results/repro/checkout_cart_20261118.txt) (checkout HTTP 200 `orderId 1`, `total_amount 1`, giỏ còn nguyên). Số dòng trích `server.js` (14, 54, 57, 162, 284–309) và `README.md` (41, 42, 85, 105, 107, 108) đã đối chiếu, đúng. Episode p95 2,244 ms ghi riêng là quan sát hiệu năng, không đếm là bug. |
| Đăng GitHub Issues | ❌ | Chưa đăng. Manager đã đọc API Issues công khai trả `[]` lúc kiểm tra; tôi không kiểm tra lại. Việc của người dùng, xem mục 5. |

### 1.5 Số liệu `TASK1_REPORT.md` so với `statistics.json`

Rút ngẫu nhiên 5 trường bằng `random.sample` trên 16 ô (4 run × samples, error%, p95, RPS) của bảng mục 5. Nguồn JSON: Load/Spike/Soak lấy `results/html/23120190_<Run>_20261118/`, Stress lấy `results/html/23120190_Stress_20261118_recovered/` (bản gốc cùng nội dung):

| Run | Trường | Trong báo cáo | `statistics.json` → `Total` | KQ |
|---|---|---:|---:|:-:|
| Stress | `throughput` | 293.092 | 293.0917259… | ✅ |
| Stress | `pct2ResTime` (p95) | 1,023 | 1023.0 | ✅ |
| Spike | `pct2ResTime` (p95) | 17 | 17.0 | ✅ |
| Soak | `pct2ResTime` (p95) | 21 | 21.0 | ✅ |
| Soak | `sampleCount` | 158,591 | 158591 | ✅ |

Đối chiếu toàn bộ 16 ô của bảng: 0 lệch. Số endurance ở mục 7 của báo cáo khớp [endurance.json](../results/analysis/endurance.json): 290 VU, 468.556 RPS, p95 947; Soak phút 3 p95 2244, 171.183 RPS; RSS 171.64 / 127.80 MiB (khớp max của CSV monitor); slope 1.4701 MiB/phút.

### 1.6 `AI_LOG.md` có entry cho mọi bước 0–18

| Bước | Entry |
|---|---|
| 0 | #1 |
| 1 | #2 |
| 2 | #4 |
| 3 | #5 |
| 4 | #6, #7 |
| 5 | #8 |
| 6 | #9 |
| 7 | #10 |
| 8 | #11 |
| 9 | #12 |
| 10 | #13 |
| 11 | #3 |
| 12 | **không có entry AI, có chủ ý**: đây là bước người dùng tự làm, không có prompt AI; file của người dùng là [06_human_review.md](06_human_review.md) |
| 13 | #14 (Load), #15 (Stress), #16 (Spike) |
| 14 | #17 |
| 15 | #18 |
| 16 | #19, #20 |
| 17 | #21, #22 |
| 18 | #23 |
| 19 | #24 (entry của bước này) |

Kết quả: ✅ có entry cho mọi bước AI 0–11 và 13–18. Bước 12 không bịa entry AI.

Human review: #1–#13 do người dùng điền. #14–#18 để trống; #19–#23 còn placeholder; #24 mới. Tôi không điền và không sửa phần của người dùng.

## 2. Đối chiếu Mục 6 (Task 1), Mục 11, Mục 14

| Điều khoản của đề | KQ | Ghi chú |
|---|:-:|---|
| Mục 6: thiết kế bằng AI từng bước, có lý do thông số | ✅ | AI_LOG #4–#12; [02_test_design.md](02_test_design.md). |
| Mục 6: dữ liệu CSV | ✅ | Mục 1.1. |
| Mục 6: 3 loại report view khác nhau | ✅ | Mục 1.1. |
| Mục 6: review và sửa plan, nêu AI sai gì | ✅ | Mục 1.4. |
| Mục 6: chạy 3 kịch bản, ảnh công cụ + resource monitor mỗi run | ✅⚠ | 4 ảnh run + ảnh kết quả. Ghi chú mục 4.3. |
| Mục 6: hardware report | ✅ | Mục 1.3. |
| Mục 6: reset lockout giữa các run, có tài liệu | ✅ | Mục 1.3. |
| Mục 6: raw log + thư mục HTML | ✅ | Mục 1.2. |
| Mục 6: endurance 10–15 phút, số cụ thể | ✅⚠ | Soak 12 phút; giới hạn ở mục 1.2. |
| Mục 6: video ≥ 6 phút YouTube unlisted | ❌ | Việc của người dùng. |
| Mục 6: log bug trên GitHub Issues kèm ảnh | ❌ | Việc của người dùng (bản nháp bug đã xong). |
| Mục 11: tên plan đúng định dạng | ✅ | Mục 1.1. |
| Mục 11: JTL raw đầy đủ | ✅ | Mục 1.2. Không có dấu hiệu sửa tay: mtime trùng giờ kết thúc run, `git diff` không đổi. |
| Mục 11: video có tool + monitor cùng khung, giọng tự thuyết minh | ❌ | Việc của người dùng. |
| Mục 11: hostname hardware khớp | ✅⚠ | Mục 1.3. |
| Mục 14: tên zip `<StudentID>_HW05_AI_Performance_<3 chữ số>.zip` | ❌ | Chưa đóng gói; chờ điểm tự chấm. |
| Mục 14: main report Markdown + PDF | ✅ MD, ❌ PDF | [TASK1_REPORT.md](TASK1_REPORT.md); chưa có PDF. |
| Mục 14: link repo GitHub public | ❌ | Chưa push: không có remote-tracking ref `origin/main`. Người dùng tự push. |
| Mục 14: 3 test plan, 3 JTL, 3 HTML | ✅ | Mục 1.1–1.2. |
| Mục 14: ảnh resource monitor + hardware | ✅ | `evidence/` (12 ảnh). |
| Mục 14: link video unlisted | ❌ | [README.md](../README.md) ghi chưa có URL. |
| Mục 14: AI Critique 200–300 từ (Mục 10) | ❌ | Không có file nào; chỉ có lời hẹn trong 06 mục 3.1. Người dùng tự viết. |
| Mục 14: AI Audit Report (Markdown + PDF) | ✅ MD, ❌ PDF | [AI_LOG.md](AI_LOG.md); chưa có PDF. |
| Mục 14: Git commit log dạng text | ✅ | [GIT_LOG.md](GIT_LOG.md). Là snapshot đến commit `4ca15e5`, nêu rõ không gồm commit sau; xem mục 4.5. |
| Mục 14: bug report kèm ảnh Issues | ❌ | Mục 1.4. |
| Mục 14: README có bảng tự chấm + test summary | ✅ | [README.md](../README.md). Cột điểm để trống cho người dùng; video để trống. |

## 3. Kết luận nhanh

- Phần agent làm đạt, trừ **một sai sót ghi chú** ở mục 4.1 cần Manager sửa.
- Có một **bug bị bỏ sót** ở mục 4.2 (đề xuất, chưa tự thêm).
- Phần còn thiếu đều của người dùng (mục 5).

## 4. Phát hiện cần xử lý

### 4.1 ❌ Ghi sai nguyên nhân phải tạo HTML Stress "phục hồi" (agent sửa, mức P2, không đổi số liệu)

Các chỗ ghi sai:
- `report/07_run_log.md:64`: "Lệnh tải kết thúc với lỗi HTML output directory đã tồn tại…"
- `report/07_run_log.md:102`: "HTML output ban đầu lỗi do thư mục có sẵn…"
- `report/TASK1_REPORT.md:47`: "HTML Stress được tạo offline từ JTL vì thư mục HTML ban đầu đã tồn tại…"
- Hệ quả: nhãn "HTML phục hồi" ở `TASK1_REPORT.md:43` và `README.md:26`.
- `report/AI_LOG.md` entry #15 cũng có câu tương tự; log chỉ nối thêm, không sửa.

Bằng chứng trên đĩa:
- `results/23120190_Stress_20261118_jmeter.log` dòng 1618–1621: JMeter báo INFO "found non empty folder with following content [statistics.json], will be ignored", rồi "Dashboard generated".
- `results/23120190_Stress_console.log` không có dòng lỗi nào, chỉ cảnh báo `StatusConsoleListener` và dòng kết thúc bình thường.
- Dòng INFO giống hệt cũng có ở `results/23120190_Stress_20261118_recovery_jmeter.log:92`. Đây là hành vi bình thường của JMeter vì exporter JSON ghi `statistics.json` trước. [INFERENCE] worker hiểu nhầm INFO này là lỗi.
- `results/html/23120190_Stress_20261118/` có `index.html`, `content/`, `sbadmin2-1.0.7/`, `statistics.json` tạo lúc 01:08:26 (run kết thúc 01:08:21). `diff -rq` với `..._recovered/` cho kết quả giống hệt.
- Thư mục gốc **chưa được git track** (`git status`: `??`), nên bản HTML do run thật tạo ra không nằm trong repo.

Hướng xử lý (Manager, không cần chạy lại tải):
1. Sửa ba chỗ trên: HTML gốc đã tạo thành công; `_recovered` là bản tạo lại từ JTL, giống hệt, dùng để đối chiếu.
2. Khuyến nghị đổi bản chính sang thư mục gốc `23120190_Stress_20261118/` (tên đồng bộ với 3 run kia; do run thật tạo) và cập nhật link trong `TASK1_REPORT.md` bảng mục 5, `README.md:26`, `07_run_log.md:75`, `02_test_design.md:79`. Chỉ giữ `_recovered` như bản đối chiếu hoặc xóa khi người dùng đồng ý.
3. `git add results/html/23120190_Stress_20261118/` ở commit bước 19.

### 4.2 ⚠ Bug chưa có trong `09_bugs.md`: mật khẩu plaintext và bị trả về trong response login (đề xuất)

- Spec: `eshop-sut/README.md:278` SEC-01 "Mật khẩu **không** được lưu dưới dạng plaintext" (mục 9 ghi "Tham khảo").
- Code: `server.js:23-24` lưu `password` thẳng vào DB; `server.js:46` so sánh plaintext; `server.js:52` `res.json({ message: "Login successful", token, user })` trả cả hàng `user` gồm `password`.
- Bằng chứng đã có sẵn: `results/repro/checkout_cart_20261118.txt` dòng 2, response `POST /api/login` chứa `"password": "Perf@289a"`; cũng có `reset_token`, `locked_until`.
- Việc cần: Manager hoặc người dùng quyết định có thêm BUG-05 vào [09_bugs.md](09_bugs.md) hay không. Nếu thêm, phải cập nhật số bug ở `TASK1_REPORT.md` mục 8 và `README.md` ("3 bug + 1 finding" thành số mới). Chỉ ghi nhận mức "SEC-01 theo spec tham khảo"; không khẳng định mức độ nghiêm trọng ngoài spec.

### 4.3 ⚠ Giới hạn của bằng chứng ảnh (người dùng đọc, không bắt buộc sửa)

- Ảnh `load_run.webp`, `stress_run.png`, `spike_run.png`, `soak_run.png` cho thấy htop + terminal `tail -F results/..._jmeter.log` (dòng `summary` của JMeter) cùng một khung, tiêu đề terminal có hostname `zinn-Nitro-AN515-57`. Phần "công cụ" là log của JMeter chạy non-GUI, không phải cửa sổ console JMeter trực tiếp. TA có thể chấp nhận hoặc không; chưa rõ.
- Đối chiếu PID `node server.js`: Load 642837 (khớp run log), Spike 774397 (khớp run log). Stress 717606 (run log không ghi PID Stress, không đối chiếu được). Soak cột PID bị cắt, còn thấy đuôi `…42` [INFERENCE] khớp PID 829842 trong run log.
- Giờ trên ảnh nằm trong khoảng chạy (Load 00:44–00:46, Stress 01:07, Spike 01:18, Soak 01:41). Cột `Active` khớp (50 / 290 / 200 / 203).
- Các ảnh `*_result.png` là màn hình terminal ở dòng `summary` cuối (33775 / 175882 / 27965 / 158591 samples, 0 lỗi), khớp tổng JTL và HTML. Không phải ảnh dashboard HTML. Đề không yêu cầu ảnh dashboard.
- Nhiều ảnh có biểu tượng ghi hình/OBS ở thanh trên; [INFERENCE] người dùng đã quay hoặc đang quay. Không có file video trong repo và chưa có URL.
- CPU trong CSV monitor là `%CPU` lifetime-average của `ps`, không phải CPU tức thời (đã ghi trong run log).
- Gợi ý nhỏ: `05_hardware.md` ghi `screenfetch`/`neofetch` chưa cài ở bước 11, còn `hardware.png` là ảnh kiểu neofetch chụp sau đó. Nên ghi thêm một dòng tên công cụ tạo ảnh. Không ảnh hưởng hostname.

### 4.4 ⚠ Nhãn bước trong AI_LOG

#19 và #21 ghi "Task 2 – Bước 16/17" trong khi #20 và #22 (cùng bước) ghi "Task 1". Log chỉ nối thêm nên không sửa; người dùng có thể ghi chú ở Human review. Entry bước này ghi "Task 1 – Bước 19".

### 4.5 ⚠ Việc đóng gói (Manager / người dùng, lúc nộp)

- `report/GIT_LOG.md` là snapshot dừng ở `4ca15e5`, không gồm `69e2616` (commit báo cáo) và các commit sau. Snapshot này tự nêu giới hạn đó và không sai. Trước khi nộp, xuất lại một lần từ `git log --date=iso-strict` (không đệ quy tự bao gồm commit chứa chính file).
- File chưa được track: `CLAUDE.md`, `agent.md`, `HW05_CHON_WORKFLOW.pdf`, `TASK1_PROMPTS.md`, `VIDEO_SCRIPT.md`, `03 - github_bug_management.pptx.pdf`, và `results/html/23120190_Stress_20261118/`. Nếu commit bằng `git add -A` thì tất cả bị đưa vào repo công khai. Người dùng nên quyết định file nào để lại.
- `.gitignore` có `*.log`, nên các log JMeter/console (`results/*.log`) không nằm trong repo. Nếu muốn nộp các log này, đưa vào zip. Đề chỉ yêu cầu `.jtl`.

## 5. Việc NGƯỜI DÙNG còn phải làm

Danh sách này là việc chỉ người dùng làm được. Chưa việc nào được báo là xong.

1. **Ảnh chụp**
   - Ảnh trang GitHub Issues sau khi đăng từng issue (mục 6 của đề yêu cầu "with screenshots").
   - Ảnh JMeter + htop cho 3 run và Soak, cùng `hardware.png`: đã có trong `evidence/`; xem ghi chú ở 4.3 nếu muốn bổ sung.
2. **Video** YouTube **unlisted**, **≥ 6 phút**, tool và resource monitor cùng khung, **giọng thuyết minh tiếng Việt của chính bạn**. Gắn URL vào [README.md](../README.md) (dòng "Video YouTube"). Kịch bản tham khảo: `VIDEO_SCRIPT.md`.
3. **Đăng GitHub Issues** (agent không đăng): BUG-01..04 (và BUG-05 nếu bạn đồng ý thêm). Gắn ảnh, rồi bổ sung URL từng issue vào `09_bugs.md`, `TASK1_REPORT.md` và `README.md`.
4. **Điền Human review** cho entry `#14`–`#24` trong [AI_LOG.md](AI_LOG.md) (11 entry). `#14`–`#18` để trống, `#19`–`#23` còn placeholder. Bạn cũng có thể ghi bổ sung sau `06_human_review.md` cho các bước 13–18 nếu muốn; agent không viết thay.
5. **AI Critique 200–300 từ** (Mục 10 của đề): chưa có. Phải là bài viết của bạn: AI sai/thiên lệch/thiếu ở đâu, vì sao không bắt được, và nguyên tắc bạn rút ra.
6. **Xuất PDF**: báo cáo chính; AI Critique + AI Audit Report.
7. **Điền điểm tự chấm** vào bảng trong [README.md](../README.md); điểm 3 chữ số dùng cho tên zip.
8. **Push** repo công khai `https://github.com/tzin1401/testing-hw05` (`git push -u origin main`) sau khi xem lại các file chưa track ở 4.5.
9. **Đóng gói zip** `23120190_HW05_AI_Performance_<điểm 3 chữ số>.zip` và nộp Moodle.
10. (Tùy chọn) nếu muốn kết luận chắc hơn về endurance, chạy thêm một Soak mới: reset SUT, tên output mới, không ghi đè. Không bắt buộc; kết quả hiện tại đã báo trung thực kèm phút 3 vượt ngưỡng.

## 6. Ngoài phạm vi, không tuyên bố xong

- **Task 2** (AI phân tích log, tìm misinterpretation, phân loại feasible/hallucinated), **Task 3** (đề xuất Continuous Performance Testing + flow chart) và **Agent Skill** (+ video demo skill) chưa làm trong phạm vi bước này.
- Mục "Task 2" trong nhãn #19/#21 chỉ là nhãn; không có phân tích đề xuất tối ưu feasible/hallucinated nào đã được thực hiện.

## 7. Giới hạn của lần rà soát (Not checked)

- Không chạy lại tải, không reset SUT, không chạy lại self-test `summarize.py`; chỉ dùng kết quả đã ghi ở 08 và đối chiếu SHA-256.
- Không kiểm tra lại trạng thái Issues công khai; dùng kết quả Manager đã báo (`[]`).
- Không kiểm tra hostname của các bài HW trước; chỉ dựa vào Human review #3 của người dùng.
- Không kiểm tra video, PDF (chưa tồn tại), push công khai.

## 8. Cập nhật xử lý của Manager – 2026-11-18 02:31 (giờ VN)

Bảng và nhận xét ở trên là bản rà soát độc lập tại 02:22; các phát hiện cần agent sửa đã được xử lý sau đó như sau. Những mục của người dùng vẫn chưa được đánh dấu hoàn tất.

- **4.1 đã sửa:** JMeter gốc đã tạo HTML Stress thành công. Sửa `07_run_log.md`, `TASK1_REPORT.md`, `README.md`, `02_test_design.md`; bản chính chuyển về `results/html/23120190_Stress_20261118/`. Bản `_recovered` giữ làm đối chiếu lịch sử, không có lần chạy tải mới. Đưa HTML gốc vào commit cuối. Entry #15 giữ nguyên theo quy tắc append-only; đính chính ở #25.
- **4.2 đã xử lý:** thêm BUG-05 vào `09_bugs.md` từ response curl có sẵn (`checkout_cart_20261118.txt`, dòng 2) và source register/login. SEC-01 được ghi đúng là tham khảo. Báo cáo và README hiện đếm **4 bug có bằng chứng + 1 finding tương thích kiểu giá**, không cộng episode hiệu năng thành bug chức năng.
- **4.4 đính chính:** nhãn “Task 2” ở entry #19/#21 là nhãn sai; thực tế là bước 16/17 của Task 1. Không sửa entry cũ, ghi đính chính ở #25. Không coi Task 2/3/Skill đã làm.
- **4.5 cập nhật:** xuất lại Git log đến `69e2616` trước commit cuối; snapshot vẫn không tự bao gồm commit chứa nó. Không đưa tài liệu khác của người dùng chưa được yêu cầu vào commit.
- **Tài liệu smoke:** cập nhật ghi chú Soak ở `02_test_design.md` để trỏ bằng chứng `05b_soak_smoke.md` đã pass, không còn ghi “chưa chạy”.
- **Human review hiện cần điền:** các entry mới **#14–#25**, gồm bản rà soát và đính chính này. Manager không điền thay.

**Kết luận sau xử lý:** artefact kỹ thuật và báo cáo Task 1 đã có; các số liệu không đổi. Chưa sẵn sàng nộp toàn bộ HW05 vì các mục ❌ do người dùng ở mục 5 còn mở. Giới hạn ảnh non-GUI/log cùng htop, Soak phút 3 vượt ngưỡng, chưa có breakpoint và RSS chỉ là mức quan sát vẫn được giữ nguyên, không che kết quả xấu.


Xác minh sau cập nhật: script kiểm tra **37 link file nội bộ** trong checklist này, **0 target thiếu**; so sánh JSON xác nhận statistics Stress gốc bằng bản xuất đối chiếu. Không chạy lại JMeter hoặc thay đổi số liệu.
