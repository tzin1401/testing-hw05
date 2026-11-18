# Task 2 – Checklist cuối (Bước 28)

Rà soát kỹ thuật: Manager `openai-codex/gpt-6.1-sol`, 2026-11-18 20:04 (giờ VN). Đây **không phải** bản review độc lập cuối của worker: reviewer chuyên biệt bị 429; worker dự phòng `TaskTwoFinalFallback` (`openai-codex/gpt-6.1-terra`) chạy xong hai lệnh kiểm chứng rồi bị `usage_limit_reached`. Manager đọc output thực tế và hoàn tất checklist, không gán kết luận PASS cho hai worker đã lỗi.

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

| Trạng thái | Việc còn lại | Người xử lý / hướng xử lý |
|---|---|---|
| ❌ | Chưa có kết luận review độc lập **cuối** từ worker | Khi dịch vụ khả dụng, giao reviewer đọc checklist và hồ sơ Task 2 để có kết luận độc lập; không cần chạy lại JMeter. Hai lần thử hiện tại bị 429 và `usage_limit_reached`, không được tính là đã duyệt. Các review độc lập bước 24–25 vẫn có ở report/12–13. |
| ❌ | Human review của entry AI #32 và #33 chưa được sinh viên điền | Sinh viên đọc báo cáo/checklist rồi tự điền trong [AI_LOG.md](AI_LOG.md); Manager để trống. |
| ❌ | Hai diễn đạt trong human review cần sinh viên tự xem lại trước khi nộp | [14](14_human_review_task2.md) dòng 174: cộng bản trùng không làm “mọi metric sai gấp đôi”; mẫu/RPS tăng, nhưng nhân bản đồng đều không tự nhân đôi mean/percentile/max/error %. Dòng 226: p95 gộp không phải trung bình có trọng số các p95 endpoint. Sinh viên tự sửa nếu đồng ý; Manager không viết thay. [TASK2_REPORT.md](TASK2_REPORT.md) §3 đã dùng định nghĩa percentile đúng. |

Không sửa JTL, test plan, SUT, analyst report/11 hay human report/14 trong bước này. Các SLO mới vẫn là đề xuất, chưa chứng minh maximum stable users hoặc hiệu quả tối ưu. Checklist này không xác nhận hoàn tất Task 3, Skill, video, PDF, đóng gói hoặc nộp toàn bộ HW05; không push hay tạo Issue.
