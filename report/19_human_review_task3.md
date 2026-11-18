# Bước 34 – Human review Task 3

Mình đọc `report/16_cpt_proposal.md`, `16a_sut_change_map.md`, `17_cpt_demo.md`, `18_task3_check.md` và tự chạy lại hai lệnh kiểm chứng. Đây là nhận định của mình về ngưỡng, đánh đổi và vai trò AI, không phải bản sao của report 18.

## 1. Hai lệnh mình đã chạy

### 1.1 Unit test

```bash
python3 -m unittest scripts/test_perf_gate.py
```

Kết quả:

```text
..................
----------------------------------------------------------------------
Ran 18 tests in 1.589s

OK
```

Exit code 0. Mình chạy đúng lệnh trong đề, không sửa test hay ngưỡng.

### 1.2 Gate trên JTL của demo D

```bash
python3 scripts/perf_gate.py --baseline results/cpt/baseline.json \
  --candidate results/cpt/fc8660e7a8c6_1/run.jtl
```

Kết quả chính:

```text
Label                         count  p95  p99  errors
01 Login                        814    4   10      0
02 Products                     811    4   10      0
03 Product detail               814    4   12      0
04 Add cart                     814    3    4      0
05 Get cart                     816    3    3      0
06 Checkout                     813   46   49      0
07 My orders                    814    5   10      0
all: errors 0/6040 (0.0%)
main: errors 0/5696 (0.0%)
window 15000-135000 ms: errors 0/4187 (0.0%)
window 135000-179669 ms partial: errors 0/1549 (0.0%)
FAIL 06 Checkout: p95 regression
```

Exit code **1**. Đây là FAIL có chủ đích của demo D, không phải lỗi hạ tầng: baseline Checkout p95 23 ms, D1 46 ms, vượt cả 1,20× lẫn mức tăng 5 ms. D2 trong report 17/18 là 45 ms và cũng FAIL; mình không chạy lại D2 trong bước này.

## 2. Ngưỡng 1,20× + 5 ms có hợp lý không?

Luật thực thi là p95 mới **lớn hơn 1,20× baseline** và **tăng ít nhất 5 ms**, không phải lấy 1,20× baseline rồi cộng thêm 5 ms. Với baseline Checkout 23 ms, ngưỡng hiệu dụng là 28 ms: vừa vượt 27,6 ms, vừa đủ 5 ms. Với Add cart baseline 3 ms, ngưỡng là 8 ms vì mức tăng 5 ms mới là điều kiện thứ hai.

Nhìn vào A/A:

| Label | A – baseline p95 | B – cùng commit p95 | Lệch |
|---|---:|---:|---:|
| 01 Login | 4 | 4 | 0 |
| 02 Products | 5 | 5 | 0 |
| 03 Product detail | 4 | 4 | 0 |
| 04 Add cart | 3 | 3 | 0 |
| 05 Get cart | 3 | 3 | 0 |
| 06 Checkout | 23 | 17 | −6 |
| 07 My orders | 5 | 5 | 0 |

Độ lệch tuyệt đối lớn nhất là **6 ms tại Checkout, theo chiều giảm**, và chỉ có **0 cảnh báo trong 1 lần so sánh**. Một cặp A/A không đo được tỷ lệ báo động giả của cả quần thể, cũng không đo được nhiễu tăng. Điểm này quan trọng: nếu lấy B làm baseline, A 23 ms sẽ FAIL vì `23 > 1,20 × 17 = 20,4` và `23 − 17 = 6 ≥ 5`, dù code không đổi. Vì vậy **1,20× + 5 ms là ngưỡng khởi đầu hợp lý, chưa phải ngưỡng đã được chứng minh thống kê**.

Mình thấy luật này có hai mặt:

- Phần 1,20× chặn các thay đổi tương đối lớn ở endpoint có p95 cao; phần 5 ms chặn nhiễu vài ms ở endpoint rất nhanh.
- Sàn 5 ms cũng tạo điểm mù: Add cart 3 → 7 ms là tăng 133% nhưng vẫn PASS vì mới +4 ms; Products 5 → 9 ms cũng PASS. Đây là W3 trong report 18, không phải lỗi đọc số. SLO tuyệt đối 50–75 ms cũng không bắt được các mức này.

Kết luận của mình: giữ nguyên luật đã chốt trước demo, không chỉnh sau khi thấy D. Trước khi bật CI thật, cần ít nhất 3 lượt A/A cùng commit, chọn **một lượt thật làm baseline đại diện** (giữ JTL/hash/metadata), và chỉ duyệt khi các cặp theo cả hai chiều đều PASS. Nếu vẫn thấy báo động giả, thay đổi ngưỡng phải là một quyết định mới, có dữ liệu và được ghi trước khi chạy, không phải chỉnh cho D hay A/A đẹp hơn.

## 3. Đánh đổi mình chọn

Mình chọn **ưu tiên ít báo động giả** cho gate mỗi commit.

Lý do:

- Một baseline chỉ là một lượt đo; A/A đã lệch 6 ms ở Checkout. Máy dùng chung, reset và thứ tự chạy có thể tạo dao động mà code không đổi. Nếu hạ ngưỡng để bắt mọi thay đổi nhỏ, CI sẽ FAIL oan trên chính commit không đổi, làm mất niềm tin vào gate.
- Một FAIL oan kéo theo chạy lại một lượt smoke nữa: thêm khoảng 3 phút cấu hình và overhead, chưa kể thời gian người đọc artifact. Với gate mỗi commit, chi phí này lặp lại thường xuyên.
- Retry hai lần trong pipeline chỉ lặp **candidate**, không lặp baseline. Vì vậy retry không sửa được nhiễu baseline; ưu tiên giảm báo động giả là hợp lý hơn trong điều kiện hiện tại.

Mình chấp nhận cái giá: bỏ sót các thay đổi nhỏ ở endpoint nhanh, ví dụ Add cart 3 → 7 ms. Bù lại bằng:

- SLO tuyệt đối p95/p99 và error;
- tầng đêm/tuần dài hơn, đặc biệt Soak cho rò rỉ RAM;
- rà soát baseline định kỳ và chạy lại khi nghi ngờ;
- không bật CI thật trước khi baseline ổn định.

Mình không chọn “ít bỏ sót bằng mọi giá” lúc này, vì muốn làm vậy phải hạ ngưỡng hoặc bỏ sàn 5 ms, mà chưa có đủ A/A để biết bao nhiêu là nhiễu. Sau khi có nhiều lượt cùng commit, có thể siết riêng cho endpoint nhanh; đó là thay đổi có dữ liệu, không phải phản ứng với một lần demo.

## 4. AI nên và không nên làm gì trong pipeline

| AI được làm | AI không được làm |
|---|---|
| Đọc diff, phân loại file và gợi ý tầng test (smoke/nightly/weekly). | Tự cập nhật `baseline.json` hoặc tự duyệt baseline mới. |
| Tóm tắt gate, chỉ ra label FAIL/INCONCLUSIVE và artifact liên quan. | Tự đóng cảnh báo, tự tạo/đóng Issue hoặc tự kết luận regression đã hết. |
| Viết nháp Issue kèm commit, profile, JTL, gate JSON và lý do. | Tự duyệt SLO/policy, tự đổi ngưỡng 1,20×/5 ms/N=500, hoặc tự ký human review. |
| Cảnh báo khi thiếu policy, baseline không tương thích, hoặc artifact không đủ mẫu. | Biến INCONCLUSIVE thành PASS, che lần FAIL đầu, hoặc bỏ qua lỗi hạ tầng. |
| Đề xuất cải tiến quy trình để người duyệt xem xét. | Tự chạy JMeter, commit, push hay thay đổi SUT khi chưa được người dùng yêu cầu. |

Lý do: baseline là mốc so sánh; nếu AI tự cập nhật baseline sau một lần PASS, một regression thật có thể bị hợp thức hóa thành chuẩn mới. Cảnh báo và Issue cần người kiểm tra bằng chứng, retry và tác động thực tế; AI có thể sai hoặc bỏ qua ngữ cảnh. Tách quyền đo/tóm tắt của AI khỏi quyền duyệt baseline, policy và Issue là cách giữ gate có trách nhiệm.

## 5. Quyết định của mình cho bước 34

- Mình chấp nhận kết quả demo smoke: 18 test pass; C skip không tạo JTL; D FAIL cả hai lượt chỉ ở Checkout; SUT đã về `main`, không còn dòng delay.
- Mình **chưa duyệt baseline/policy cho tầng deep và chưa bật CI thật**. Baseline smoke hiện tại chỉ đủ cho demo, chưa đủ để gọi là baseline sản xuất. Trước khi bật cần: ít nhất 3 lượt A/A, chọn một lượt đại diện, duyệt SLO/policy deep, ghi hash policy và kiểm soát quyền ghi.
- Mình giữ N=500 mỗi label, tối thiểu 1.000 main sample/run, luật 1,20× + 5 ms và SLO Task 2. Không chỉnh ngưỡng sau demo D.

## 6. Kết luận

Ngưỡng 1,20× + 5 ms là điểm khởi đầu hợp lý nhưng chưa được chứng minh; A/A một cặp cho thấy baseline có thể dao động 6 ms và đảo chiều sẽ báo FAIL oan. Mình chọn ưu tiên ít báo động giả cho gate mỗi commit, chấp nhận bỏ sót nhỏ ở endpoint nhanh và bù bằng SLO, tầng đêm/tuần và rà soát baseline. AI được đọc diff, gợi ý tầng, tóm tắt và viết nháp; AI không được tự cập nhật baseline, tự đóng cảnh báo hay tự duyệt policy. Hai lệnh kiểm chứng đã chạy đúng; D1 FAIL với exit 1 là kết quả mong đợi.
