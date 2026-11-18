# Task 2 – Checklist cuối (Bước 28)

Rà soát kỹ thuật: Manager `openai-codex/gpt-6.1-sol` hoàn tất lúc 20:04 (giờ VN); worker dự phòng `TaskTwoFinalFallback` (`openai-codex/gpt-6.1-terra`) chạy kiểm chứng lúc 16:18 rồi bị `usage_limit_reached`. Reviewer chuyên biệt ban đầu bị 429, nên checklist này giữ lịch sử hai lần lỗi và không gán PASS cho chúng. Sau đó reviewer độc lập `TaskTwoFinalReview` (`anthropic/claude-sonnet-5-5`) chạy lại lúc 22:15–22:17 và kết luận **PASS**; xem §4.

## 1. Checklist theo yêu cầu

| Tiêu chí | Kết quả | File chứng minh / phạm vi |
|---|---|---|
| Có phân tích AI trên JTL và ngưỡng AI đề xuất | ✅ | [11_ai_analysis.md](11_ai_analysis.md), các mục phân tích và “Đề xuất ngưỡng”; [TASK2_REPORT.md](TASK2_REPORT.md) §1–2, §4. |
| Mỗi lỗi đọc số có giá trị đúng từ JTL; kiểm tra ngẫu nhiên 5 giá trị | ✅ | [12_misinterpretation_hunt.md](12_misinterpretation_hunt.md) kết luận **0 lỗi số liệu cứng** được xác nhận, không tạo lỗi giả. Script và kiểm tra 5 giá trị tại §2 dưới đây đều thành công. N6 được sinh viên coi là **lỗi thiết kế ngưỡng**, không phải đọc sai số. |
| Mỗi đề xuất tối ưu được phân loại và giải thích | ✅ | [13_optimization_review.md](13_optimization_review.md) §4, §9 và [TASK2_REPORT.md](TASK2_REPORT.md) §5: đủ 7 đề xuất, gồm 4 FEASIBLE, 2 PARTIALLY FEASIBLE, 1 HALLUCINATED theo nghĩa không áp dụng hiện trạng. Có đối chiếu mã SUT và giới hạn. |
| Có human review của sinh viên | ✅ | [14_human_review_task2.md](14_human_review_task2.md), gồm lệnh sinh viên đã tự chạy, điểm đồng ý/không đồng ý và lựa chọn ngưỡng. Manager giữ nguyên nội dung, không điền thay nhận định. |
| AI_LOG có entry cho bước 20–25 và 27 | ✅ | [AI_LOG.md](AI_LOG.md): bước 20→#26, 21→#27, 22→#29, 23→#28, 24→#30, 25→#31, 27→#32. Thứ tự #28/#29 do bước 23 chạy song song. Bước 26 là human review, không tạo entry AI giả. |

Phân loại khả thi là đánh giá tĩnh, **không phải** benchmark cải thiện. Đề xuất #6 vốn có điều kiện: SQLite `INSERT` có transaction ngầm, nhưng Checkout hiện không có transaction tường minh nhiều SQL để rút ngắn; nhãn không đồng nghĩa analyst bịa hiện trạng. Pool không có yêu cầu API bắt buộc WAL. Ước tính CPU D5 không phải số đo ground truth hay bằng chứng nguyên nhân.

## 2. Kiểm chứng thực chạy

Worker dự phòng đã chạy tại 16:18 ngày 2026-11-18 (giờ VN):

```bash
python3 scripts/jtl_truth.py
```

Output gốc: `Self-check passed; wrote results/analysis/ground_truth.json and ground_truth.md`. Có bảng kết quả `all`/`main` cho đủ Load, Stress, Spike, Soak. Manager khôi phục hai kết quả đã hoàn tất từ transcript worker sau lỗi dịch vụ, **không chạy lại** các lệnh để xác nhận lỗi hoặc thay cho những lệnh sinh viên tự chạy.

Chọn 5 trường bằng `random.Random(28).sample(pool, 5)` từ 14 số đo p95/p99 endpoint tại [TASK2_REPORT.md](TASK2_REPORT.md) §4; không chọn SLO chính sách làm số đo. Nguồn: `23120190_Stress_20261118.jtl`, từng label, thời điểm bắt đầu tương đối `[300000,450000)` ms. Dùng chính `load_jtl()`/`metrics()` của script, nearest-rank trên `elapsed`; không đổi thuật toán. Cửa sổ xấp xỉ bậc 200 VU, có ramp và một số sample bậc kế tiếp, không phải steady state đã chứng nhận.

| Giá trị được chọn | Báo cáo (ms) | JTL qua script (ms) | Sample đúng bộ lọc | Kết quả |
|---|---:|---:|---:|---|
| 01 Login p99 | 81 | 81 | 8835 | ✅ |
| 06 Checkout p99 | 93 | 93 | 8671 | ✅ |
| 02 Products p95 | 52 | 52 | 8803 | ✅ |
| 05 Get cart p95 | 23 | 23 | 8710 | ✅ |
| 05 Get cart p99 | 38 | 38 | 8710 | ✅ |

Lệnh truy vấn đã chạy, từ thư mục gốc repo:

```bash
python3 - <<'PY'
import random,sys
sys.path.insert(0,'scripts'); import jtl_truth as T
pool=[(label,field,v) for label,p95,p99 in [('01 Login',51,81),('02 Products',52,82),('03 Product detail',53,87),('04 Add cart',22,38),('05 Get cart',23,38),('06 Checkout',60,93),('07 My orders',53,85)] for field,v in [('p95_ms',p95),('p99_ms',p99)]]
selected=random.Random(28).sample(pool,5)
s=T.load_jtl(T.ROOT/'results/jtl/23120190_Stress_20261118.jtl'); origin=min(x[0] for x in s)
for label,field,reported in selected:
 m=T.metrics([x for x in s if 300000<=x[0]-origin<450000 and x[2]==label],150000)
 print(label,field,'report=',reported,'jtl=',m[field], 'count=',m['count'], 'match=',reported==m[field])
PY
```

Cả 5 dòng output có `match= True`. [JSON](../results/analysis/ground_truth.json)/[Markdown](../results/analysis/ground_truth.md) mặc định không biểu diễn mọi cửa sổ tùy chọn này; vì vậy dùng helper trên JTL với đúng bộ lọc, không lấy percentile toàn run để đối chiếu percentile cửa sổ.

## 3. Giới hạn và việc người dùng còn làm

| Trạng thái | Việc | Người xử lý / hướng xử lý |
|---|---|---|
| ✅ | Đã có kết luận review độc lập **cuối** từ worker | `TaskTwoFinalReview` (`anthropic/claude-sonnet-5-5`) chạy 22:15–22:17, verdict **PASS**; entry #34 trong [AI_LOG.md](AI_LOG.md), chi tiết §4. Hai lần lỗi 429/`usage_limit_reached` trước đó vẫn được ghi trong lịch sử, không tính là PASS. |
| ✅ | Human review của entry AI #32 và #33 | Đã điền trong [AI_LOG.md](AI_LOG.md) ngày 2026-11-18. |
| ✅ | Human review của entry AI #34 | Đã điền trong [AI_LOG.md](AI_LOG.md) ngày 2026-11-18. |
| ✅ | Hai diễn đạt trong human review | Đã sửa [14](14_human_review_task2.md) dòng 174 (bản ghi trùng chỉ làm sample/RPS tăng gấp đôi; mean, p95, error % không đổi) và dòng 226 (p95 gộp là phân vị trên phân phối mẫu gộp, không phải trung bình có trọng số các p95 endpoint). |

Bước 28 không sửa JTL, test plan, SUT, analyst report/11 hay human report/14; sau bước 28, sinh viên đã tự sửa hai diễn đạt ở report/14 như bảng trên. Các SLO mới vẫn là đề xuất, chưa chứng minh maximum stable users hoặc hiệu quả tối ưu. Checklist này không xác nhận hoàn tất Task 3, Skill, video, PDF, đóng gói hoặc nộp toàn bộ HW05; không push hay tạo Issue.

## 4. Review độc lập cuối (Bước 28)

Reviewer `TaskTwoFinalReview` (`anthropic/claude-sonnet-5-5`) chạy lại sau khi hết 429, trong bản sao read-only của repo, lúc 22:15–22:17 ngày 2026-11-18. Kết luận: **PASS** kỹ thuật cho Bước 28; cả 5 tiêu chí đạt; không có lỗi số liệu mới.

- Tự chạy `python3 scripts/jtl_truth.py`: `Self-check passed`.
- Tự chọn 5 giá trị bằng seed 2028 và tính lại từ JTL: 5/5 khớp (count Login Soak `[360,600)` 8049; count Spike `[120,180)` 11291; p95 Soak `[240,250)` 3885; mean Stress all-run 67,01; count Products Soak `[360,600)` 8054).
- Tự tính lại 184 giá trị trong `report/12` và `report/14`: 0 lệch.
- Xác nhận N6 là 1 lỗi thiết kế ngưỡng; Checkout p95 60 ms ở Stress `[300,450)`; hai câu report/14 dòng 174 và 226 đúng thống kê; filter `all`/`main` không gán sai.
- Không sửa file nào trong lúc review.

Sáu lỗi nhỏ reviewer nêu đã được xử lý sau review: mâu thuẫn dòng 60/62 và thiếu owner dòng 58 của file này; lệch mốc giờ dòng 3/19; khoảng đệm `1,4–2,2` ở report/14 dòng 191; nhãn "Throughput tại 200 VU" ở dòng 203; danh sách entry `#26–#31` ở dòng 293. Không còn ❌ kỹ thuật nào trong phạm vi Bước 28.
