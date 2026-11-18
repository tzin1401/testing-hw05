# Task 2 – Phân tích AI và đối chiếu

## 1. Cách làm

AI analyst tạo [phân tích và đề xuất](11_ai_analysis.md) độc lập, không xem số đã kiểm chứng và không đọc mã SUT; người viết báo cáo này không phải analyst. Ground truth được tính từ JTL bằng [scripts/jtl_truth.py](../scripts/jtl_truth.py), ghi tại [ground_truth.md](../results/analysis/ground_truth.md) và [ground_truth.json](../results/analysis/ground_truth.json); sau đó [reviewer đối chiếu](12_misinterpretation_hunt.md), [đánh giá tối ưu](13_optimization_review.md) với mã SUT và [sinh viên review](14_human_review_task2.md).

Nguồn là bốn JTL canonical [Load](../results/jtl/23120190_Load_20261118.jtl), [Stress](../results/jtl/23120190_Stress_20261118.jtl), [Spike](../results/jtl/23120190_Spike_20261118.jtl), [Soak](../results/jtl/23120190_Soak_20261118.jtl); không cộng bản writer Soak ghi trùng. `all` gồm mọi sample; `main` chỉ gồm bảy label workflow. Error là `success=false`; Negative login sai có chủ đích với 401/403 được đánh dấu thành công không phải login nghiệp vụ thành công. Percentile dùng nearest-rank trên `elapsed` (ms). Cửa sổ `[a,b)` chọn theo thời điểm bắt đầu sample tương đối với sample đầu của run; RPS cửa sổ là số sample bắt đầu chia độ rộng cửa sổ. RPS toàn run dùng span từ bắt đầu sớm nhất đến kết thúc muộn nhất. Chi tiết và sự khác nhau giữa phân đoạn stage, cửa sổ và HTML ở [ground truth – Method](../results/analysis/ground_truth.md#method) và [review 12 §4](12_misinterpretation_hunt.md#4-khác-biệt-đã-kiểm-nhưng-không-phải-lỗi-analyst).

## 2. Tóm tắt phân tích AI và ngưỡng đề xuất

Theo [analyst](11_ai_analysis.md), Checkout chậm nhất theo mean trong từng run; Stress tăng độ trễ mạnh ở bậc cao, Spike có đuôi chậm rồi phục hồi, còn Soak có một đợt chậm. Các nguyên nhân tranh chấp hoặc hàng đợi chỉ là giả thuyết, không được JTL chứng minh. Cần chú ý độ phân giải thời gian: với **all** trong JTL Soak, cửa sổ 120–240 s có mean 158,33 ms và p95 1.013 ms ([11 – Soak](11_ai_analysis.md#soak)); cửa sổ 180–240 s có mean 368,54 ms, p95 2.213 ms, p99 4.121 ms ([13 – M4](13_optimization_review.md#3-bằng-chứng-đo-tái-sử-dụng-nguồn-và-bộ-lọc)). Theo [14 §2.5](14_human_review_task2.md), bucket 220–230 s có mean 716,1 ms và p95 3.833 ms; p95 cao nhất trong bảng bucket là 4.263 ms ở 230–240 s. Đỉnh mean và đỉnh p95 không cùng bucket. Các con số all này không phải biến thể main loại Negative login.

[Ngưỡng analyst](11_ai_analysis.md#đề-xuất-ngưỡng) là p95/p99 tối đa **50/100 ms** cho từng phân phối gộp Auth, Read và Transactional tại mức thử đề xuất 200 VU. Auth là Login; Read gộp Products và Product detail; Transactional gộp Add cart, Get cart, Checkout và My orders. Negative login được xét riêng, không thuộc latency Auth. Analyst đồng thời đề xuất error ≤ 0,1%, throughput ≥ 200 request/s và quy tắc regression ở §4 dưới đây. Analyst đã nói rõ Stress vượt nhẹ mục tiêu p95 Auth/Read và khuyến nghị báo thêm từng endpoint, đặc biệt Checkout; đây là mục tiêu đề xuất, không phải cam kết đã đạt.

## 3. Bảng misinterpretation

[Review 12 §1–4](12_misinterpretation_hunt.md#1-kết-luận) tìm **0 lỗi số liệu cứng** trong phạm vi phân tích và ngưỡng của analyst: các trường được kiểm khớp JTL theo phương pháp đã công bố. Không có lỗi đọc số được xác nhận để đưa vào bảng lỗi.

| AI nói | Giá trị đúng từ JTL / bộ lọc | Loại sai |
|---|---|---|
| Không có lỗi số liệu cứng được xác nhận | Các trường được kiểm khớp theo phương pháp công bố; xem [12 §2](12_misinterpretation_hunt.md). | Không có lỗi đọc số xác nhận |
| Auth và Read có mục tiêu p95/p99 50/100 ms; analyst ghi Stress đã vượt nhẹ p95 ([11](11_ai_analysis.md#đề-xuất-ngưỡng)). | Stress `[300,450)` s, Auth/Login p95 51 ms, Read gộp p95 52 ms; Checkout riêng p95 60 ms ([12 N6](12_misinterpretation_hunt.md#4-khác-biệt-đã-kiểm-nhưng-không-phải-lỗi-analyst), [14 §2.4](14_human_review_task2.md)). | N6: reviewer không tính là misreading; sinh viên đánh giá là **một lỗi thiết kế ngưỡng**, mở rộng nhận xét sang Checkout, không phải lỗi đọc số ([14 §3.2](14_human_review_task2.md#32-không-đồng-ý-n6-phải-là-một-lỗi-không-chỉ-là-ghi-chú)). |

Transactional gộp p95 45 ms không đảm bảo Checkout đạt 50 ms: p95 gộp là phân vị trên phân phối mẫu gộp, **không phải trung bình có trọng số các p95 endpoint**. Analyst đã nêu giới hạn của phép gộp; kiểm tra từng label bổ sung bằng chứng, không chứng minh analyst đã đưa ra claim sai.

## 4. Ngưỡng cuối cùng

Theo lựa chọn thiết kế của sinh viên tại [14 §3.2](14_human_review_task2.md#32-không-đồng-ý-n6-phải-là-một-lỗi-không-chỉ-là-ghi-chú), dùng SLO theo endpoint thay cho SLO phân phối gộp của AI. Cột đo là p95/p99 `elapsed`, ms, từng label trong JTL Stress `[300,450)` s theo [14 §2.4](14_human_review_task2.md).

| Endpoint | Đo p95/p99 (ms) | SLO p95/p99 tối đa (ms) | So với đề xuất AI 50/100 ms theo nhóm |
|---|---:|---:|---|
| 01 Login | 51/81 | 75/125 | Thay đổi |
| 02 Products | 52/82 | 75/125 | Thay đổi |
| 03 Product detail | 53/87 | 75/125 | Thay đổi |
| 04 Add cart | 22/38 | 50/100 | Cùng trị số, đổi phạm vi sang endpoint |
| 05 Get cart | 23/38 | 50/100 | Cùng trị số, đổi phạm vi sang endpoint |
| 06 Checkout | 60/93 | 100/150 | Thay đổi |
| 07 My orders | 53/85 | 75/125 | Thay đổi |

Các ngưỡng mới cho headroom theo lựa chọn chính sách của sinh viên và tránh che endpoint chậm; chưa được kiểm chứng thống kê. Đây là thay đổi thiết kế SLO, không sửa số đo hay chứng minh cải thiện. Một SLO có thể cố ý chặt hơn số đo hiện tại; không bắt buộc gate phải xanh. Cửa sổ trên xấp xỉ bậc 200 VU, gồm ramp và một số sample bậc kế tiếp, không phải chứng nhận steady state ([12 N2](12_misinterpretation_hunt.md#4-khác-biệt-đã-kiểm-nhưng-không-phải-lỗi-analyst)).

Giữ các mục tiêu còn lại từ [11 – Đề xuất ngưỡng](11_ai_analysis.md#đề-xuất-ngưỡng) và [14 §3.2](14_human_review_task2.md#32-không-đồng-ý-n6-phải-là-một-lỗi-không-chỉ-là-ghi-chú):

- **Error ≤ 0,1%:** `success=false` chia tổng sample **all**, cho toàn run và từng cửa sổ 120 s sau ramp. Theo dõi thêm error **main** với mẫu số main và response code/kiểm tra nghiệp vụ riêng, tránh Negative login được chấp nhận che lỗi chức năng; không thay mẫu số SLO all.
- **Throughput ≥ 200 request/s:** số sample **all** bắt đầu chia độ rộng từng cửa sổ 120 s sau ramp tại tải mục tiêu, đồng thời đánh giá SLO độ trễ và lỗi. Stress `[300,450)` s đo 410,77 request/s all theo cửa sổ 150 s, không phải steady-state chính xác ([11 – Stress](11_ai_analysis.md#stress)). Đạt throughput riêng không chứng minh đạt độ trễ.
- **Regression:** báo khi p95 mới > 1,20 lần baseline **và** tăng ≥ 5 ms, với ≥ 1.000 sample mỗi run; cùng workflow, profile/tải, cửa sổ sau ramp, bộ lọc và hardware. Ví dụ baseline 20 ms → 25 ms chỉ minh họa số học; không ghép Stress với Soak khác profile/cửa sổ làm cặp so sánh.
- **Endurance:** 200 VU chỉ là ứng viên cần thử, chưa xác lập maximum stable users hay RPS endurance. Soak tối đa 203 thread có đợt chậm; không suy số RPS đo tại Soak 203 VU thành phép đo tại 200 VU ([11](11_ai_analysis.md#đề-xuất-ngưỡng)).

## 5. Phân loại đề xuất tối ưu

Tổng hợp từ [review 13 §4](13_optimization_review.md#4-bảng-tổng-hợp) và cách hiểu #6 tại [14 §3.3](14_human_review_task2.md#33-về-phân-loại-trong-report-13). Đây là đánh giá tĩnh, không phải bằng chứng hiệu quả hay benchmark; không có mức cải thiện định lượng.

| Đề xuất | Phân loại | Cơ sở và giới hạn |
|---|---|---|
| Index truy vấn | FEASIBLE có điều kiện | Có ứng viên `orders(user_id)`; cần đo query plan và chi phí ghi, chưa chứng minh là bottleneck. |
| Pool SQLite | PARTIALLY FEASIBLE | Có thể dùng nhiều kết nối cùng file nhưng chỉ một writer, có nguy cơ tranh chấp và lỗi; cần thiết kế, đo và kiểm tra correctness. |
| SQLite WAL | FEASIBLE | File DB hỗ trợ WAL; với một kết nối không suy ra đọc song song với ghi; lợi ích chưa đo. |
| Cache sản phẩm | FEASIBLE | Giá trị có thể thấp; cần invalidation và giữ đúng hành vi. |
| Node cluster | PARTIALLY FEASIBLE | Cart trong RAM mỗi process và khởi tạo DB ở mỗi worker gây rủi ro correctness. |
| Rút ngắn transaction Checkout | HALLUCINATED **(không áp dụng hiện trạng, không phải bịa đặt)** | Analyst nêu có điều kiện; Checkout là một `INSERT` tự commit. SQLite vẫn có transaction ngầm, nhưng không có transaction tường minh nhiều SQL để rút ngắn. |
| Đo event-loop delay | FEASIBLE phần đo | Có công cụ đo; chưa xác định xử lý nào để chuyển worker hay nguyên nhân gốc. |

Ưu tiên đo trước, sau đó cân nhắc WAL hoặc index nếu có bằng chứng phù hợp ([14 §5](14_human_review_task2.md#5-đề-xuất-tối-ưu-đáng-làm-nhất)). Ước tính CPU D5 trong review 13 không phải ground truth và không chứng minh nguyên nhân.

## 6. Nhận định của sinh viên

Xem [Human review Task 2](14_human_review_task2.md).
