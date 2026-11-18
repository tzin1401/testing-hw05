# Bước 20 – Phân tích độc lập kết quả JMeter

## Phương pháp và giới hạn

- Nguồn số liệu là bốn file `results/jtl/23120190_{Load,Stress,Spike,Soak}_20261118.jtl`; mỗi dòng là một sample, kể cả `Negative login`. Không gộp `23120190_Soak_20261118_writer.jtl` vì đây là bản ghi trùng của cùng lần Soak, không phải lần chạy khác.
- Với từng file, tổng request là số dòng dữ liệu; error % = 100 × số dòng `success=false` / tổng dòng. HTTP 401/403 không mặc nhiên là lỗi theo tiêu chí này: riêng `Negative login` chủ đích sai có thể được đánh dấu thành công. Vì vậy error % không thể dùng một mình để đánh giá số đăng nhập thành công.
- Throughput toàn lần = tổng số dòng / (thời điểm kết thúc muộn nhất `timeStamp + elapsed` − `timeStamp` bắt đầu sớm nhất), đổi ms sang giây. Đây là khoảng quan sát từ sample, có thể ngắn hơn thời lượng cấu hình do ramp và khoảng chờ. Các số được làm tròn; thời gian đáp ứng tính bằng ms.
- Mean là trung bình `elapsed`; p90/p95/p99 dùng nearest-rank: sắp `elapsed` tăng dần, lấy phần tử ở vị trí `ceil(p × N)` theo chỉ số từ 1. Max là `elapsed` lớn nhất. Label chậm nhất được xác định theo **mean**, không phải theo max; mọi label đều được đưa vào so sánh.
- Các cửa sổ thời gian dùng `timeStamp` bắt đầu sample so với sample đầu tiên của chính file, cận trái đóng và cận phải mở. RPS cửa sổ = số sample bắt đầu trong cửa sổ / độ rộng cửa sổ. Sample vượt qua ranh giới vẫn thuộc cửa sổ nó bắt đầu; các cửa sổ được làm tròn theo thời điểm sample đầu nên có thể lệch nhẹ so với ranh giới thread group thực tế. Cửa sổ gồm cả ramp-up/ramp-down nếu có.
- Các nhận định nguyên nhân bên dưới là giả thuyết từ mẫu độ trễ, không phải bằng chứng đo CPU, bộ nhớ, I/O hay cơ chế nội bộ. Không suy ra được thành công nghiệp vụ hoặc nguyên nhân gốc chỉ từ JTL.

## Load

Nguồn và lọc: toàn bộ sample trong `results/jtl/23120190_Load_20261118.jtl`.

| Chỉ số | Kết quả |
|---|---:|
| Tổng request | 33.775 |
| Khoảng quan sát; throughput theo công thức trên | 599,439 s; 56,34 request/s |
| `success=false`; error % | 0; 0,000% |
| Mean / p90 / p95 / p99 / max | 3,22 / 10 / 11 / 18 / 95 ms |

Lọc theo `label`, **06 Checkout** chậm nhất theo mean: 11,41 ms; p95 18 ms, max 95 ms (4.772 sample). Không có label nào có `success=false`. Riêng `Negative login` có 5 response 401 và 236 response 403, đều `success=true`: đây là mã HTTP không thành công nhưng được phép bởi tiêu chí sampler, không phải lỗi JMeter theo phép đếm trên.

**Bottleneck có khả năng:** Checkout là ứng viên cần khảo sát đầu tiên vì mean cao nhất; song độ trễ thấp và không có phép đo tài nguyên nên chưa thể khẳng định có nút thắt hệ thống hoặc xác định thành phần cụ thể.

## Stress

Nguồn và lọc: toàn bộ sample trong `results/jtl/23120190_Stress_20261118.jtl`.

| Chỉ số | Kết quả |
|---|---:|
| Tổng request | 175.882 |
| Khoảng quan sát; throughput | 600,092 s; 293,09 request/s |
| `success=false`; error % | 0; 0,000% |
| Mean / p90 / p95 / p99 / max | 67,01 / 143 / 496 / 1.030 / 1.690 ms |

Lọc theo `label`, **06 Checkout** chậm nhất theo mean: 175,94 ms; p95 977 ms, max 1.690 ms (24.735 sample). Không có label nào có `success=false`. Lọc `Negative login`: 8 response 401 và 1.253 response 403, tất cả `success=true`.

Diễn biến theo các cửa sổ 150 s trong cùng file (phân loại bằng thời điểm bắt đầu sample; các bậc cấu hình 50/100/200/290 VU, mỗi bậc có ramp):

| Cửa sổ xấp xỉ bậc | Số sample | RPS cửa sổ | Mean / p95 / p99 (ms) | Error % |
|---|---:|---:|---:|---:|
| 0–150 s, 50 VU | 15.886 | 105,91 | 3,35 / 12 / 21 | 0 |
| 150–300 s, 100 VU | 31.503 | 210,02 | 4,37 / 17 / 28 | 0 |
| 300–450 s, 200 VU | 61.616 | 410,77 | 12,91 / 48 / 79 | 0 |
| 450–600 s, 290 VU | 66.877 | 445,85 | 161,49 / 905 / 1.152 | 0 |

Độ trễ đã tăng thấy rõ ở bậc **200 VU** so với 100 VU, còn suy giảm nghiêm trọng nhất bắt đầu ở **290 VU**: p95 tăng từ 48 lên 905 ms trong khi RPS chỉ tăng từ 410,77 lên 445,85. Ranh giới cửa sổ gần nhưng không trùng chính xác ranh giới nhóm nên không diễn giải chúng là các phép đo steady-state thuần túy.

**Bottleneck có khả năng:** một tài nguyên dùng chung bị tranh chấp hoặc hàng đợi xử lý tăng khi đồng thời cao, đặc biệt trên đường Checkout; việc nhiều label cùng chậm và throughput gần bão hòa phù hợp với giả thuyết này. JTL không chỉ ra tài nguyên đó là CPU, database, disk hay thành phần nào khác.

## Spike

Nguồn và lọc: toàn bộ sample trong `results/jtl/23120190_Spike_20261118.jtl`.

| Chỉ số | Kết quả |
|---|---:|
| Tổng request | 27.965 |
| Khoảng quan sát; throughput | 358,864 s; 77,93 request/s |
| `success=false`; error % | 0; 0,000% |
| Mean / p90 / p95 / p99 / max | 75,25 / 24 / 158 / 2.115 / 4.633 ms |

Lọc theo `label`, **06 Checkout** chậm nhất theo mean: 195,92 ms; p95 1.798 ms, max 4.502 ms (3.896 sample). Max toàn lần thuộc **03 Product detail**, không phải Checkout. Không có label nào có `success=false`. Lọc `Negative login`: 22 response 401 và 183 response 403, tất cả `success=true`.

Diễn biến theo thời điểm bắt đầu sample trong cùng file:

| Cửa sổ | Số sample | RPS cửa sổ | Mean / p95 / p99 (ms) | Error % |
|---|---:|---:|---:|---:|
| 60–120 s, gần nền trước spike | 721 | 12,02 | 7,00 / 37 / 53 | 0 |
| 120–180 s, đầu spike | 11.291 | 188,18 | 179,22 / 1.497 / 3.322 | 0 |
| 180–240 s, cuối spike | 13.890 | 231,50 | 4,94 / 17 / 29 | 0 |
| 240–300 s, sau spike | 695 | 11,58 | 3,14 / 11 / 13 | 0 |

`threadName` cho thấy nhóm burst bắt đầu sample đầu ở 119,220 s và sample cuối kết thúc ở 239,844 s tính từ sample đầu của file, nên hai ranh giới cửa sổ gần đúng chứ không trùng hoàn toàn thời điểm burst. Khi tải tăng đột ngột, độ trễ đuôi tăng mạnh trong cửa sổ đầu; sang cửa sổ sau p95 và p99 phục hồi ngay cả khi tải burst còn hiện diện, và sau burst trở lại mức nền. Không quan sát được `success=false`.

**Bottleneck có khả năng:** tranh chấp/hàng đợi tạm thời khi tăng tải nhanh, có thể ảnh hưởng mạnh đến Checkout. Sự phục hồi trong khi vẫn có tải cao cho thấy không đủ cơ sở kết luận một nút thắt thường trực hoặc xác định thành phần nội bộ.

## Soak

Nguồn và lọc: toàn bộ sample trong `results/jtl/23120190_Soak_20261118.jtl`, không cộng file writer trùng.

| Chỉ số | Kết quả |
|---|---:|
| Tổng request | 158.591 |
| Khoảng quan sát; throughput | 719,783 s; 220,33 request/s |
| `success=false`; error % | 0; 0,000% |
| Mean / p90 / p95 / p99 / max | 32,45 / 17 / 29 / 753 / 6.344 ms |

Lọc theo `label`, **06 Checkout** chậm nhất theo mean: 89,14 ms; p95 74 ms, max 6.282 ms (22.418 sample). Max toàn lần thuộc **02 Products**, không phải Checkout. Không có label nào có `success=false`. Lọc `Negative login`: 6 response 401 và 1.123 response 403, tất cả `success=true`.

Các cửa sổ 120 s trong cùng file:

| Cửa sổ | Số sample | RPS cửa sổ | Mean / p95 / p99 (ms) | Error % |
|---|---:|---:|---:|---:|
| 0–120 s | 21.588 | 179,90 | 4,76 / 17 / 30 | 0 |
| 120–240 s | 24.551 | 204,59 | 158,33 / 1.013 / 3.589 | 0 |
| 240–360 s | 27.364 | 228,03 | 24,06 / 24 / 145 | 0 |
| 360–480 s | 28.376 | 236,47 | 5,54 / 20 / 37 | 0 |
| 480–600 s | 28.398 | 236,65 | 5,58 / 20 / 33 | 0 |
| 600–720 s | 28.314 | 235,95 | 6,44 / 21 / 44 | 0 |

Có một đợt chậm lớn trong khoảng 120–240 s, sau đó độ trễ giảm và throughput ổn định hơn. Cuối lần chạy p95/p99 cao hơn nhẹ so với hai cửa sổ trước, nhưng không có xu hướng suy giảm liên tục rõ ràng trong khoảng quan sát; không thể từ đó loại trừ vấn đề xuất hiện sau thời gian soak dài hơn. Cửa sổ đầu gồm ramp, cửa sổ cuối có kết thúc thread.

**Bottleneck có khả năng:** tranh chấp tài nguyên hoặc hàng đợi theo đợt, với Checkout là đường cần khảo sát; dữ liệu không đủ để xác định nguyên nhân đợt chậm hoặc kết luận rò rỉ bộ nhớ/tài nguyên.

## Đề xuất ngưỡng

Đây là **mục tiêu đề xuất**, không phải cam kết đã đạt hay capacity đã chứng minh. Áp dụng cho Flow 1 trên máy và cấu hình test tương đương lần đo, tại mức đề xuất 200 VU; cần chạy lại để kiểm chứng. So sánh `elapsed` theo nearest-rank như phần phương pháp Bước 20. Chia sample theo `label`: Auth = `01 Login`; Read = gộp `02 Products`, `03 Product detail`; Transactional = gộp `04 Add cart`, `05 Get cart`, `06 Checkout`, `07 My orders`. `Negative login` là kiểm thử âm riêng, không gộp vào latency Auth.

| Nhóm | p95 tối đa | p99 tối đa | Lý do và cách tính |
|---|---:|---:|---|
| Auth | 50 ms | 100 ms | Lọc Soak 360–600 s, 8.049 login: p95/p99 là 19/37 ms; Stress 300–450 s, 8.835 login: 51/81 ms. Mục tiêu làm tròn gần mức Stress, dành khoảng đệm cho đuôi; 51 ms cho thấy lần Stress đã vượt nhẹ mục tiêu p95. |
| Read | 50 ms | 100 ms | Gộp hai label Read: Soak 360–600 s có 16.107 sample, p95/p99 20/36 ms; Stress 300–450 s có 17.578 sample, 52/84 ms. Mục tiêu gần mức Stress và cao hơn mức Soak ổn định; Stress vượt nhẹ p95. |
| Transactional | 50 ms | 100 ms | Gộp bốn label Transactional: Soak 360–600 s có 32.216 sample, p95/p99 20/34 ms; Stress 300–450 s có 34.761 sample, 45/76 ms. Mục tiêu làm tròn lên để có khoảng đệm. |

Các phép lọc trên dùng file JTL của run tương ứng, chọn sample theo `timeStamp` trong cửa sổ tương đối từ sample đầu, cận trái đóng và cận phải mở; các cửa sổ Stress gồm cả ramp của bậc. Ngưỡng trên là cho **phân phối gộp mỗi nhóm**, không bảo đảm từng endpoint riêng đạt ngưỡng: nên báo thêm p95/p99 từng label, đặc biệt Checkout. Khi đánh giá endurance, tính cả giai đoạn sau ramp thay vì chỉ chọn đoạn tốt: Soak 120–240 s cho p95/p99 Auth 1.054/2.181 ms, Read 303/1.594 ms và Transactional 1.408/3.908 ms, đều vượt mục tiêu đề xuất. Vì thế không coi lần Soak này đã đạt SLO liên tục.

- **Error tối đa: 0,1%** số sample có `success=false`, tính riêng toàn run và từng cửa sổ 120 s sau ramp, gồm mọi label. Trong bốn JTL ở Bước 20, quan sát là 0%; 0,1% là mức dung sai đề xuất, không phải tỷ lệ lỗi đã đo hoặc hiệu quả cải thiện. Theo dõi riêng phân bố response code và kết quả nghiệp vụ; `Negative login` có 401/403 được đánh dấu `success=true`, không được coi là đăng nhập thành công.
- **Throughput tối thiểu: 200 request/s** tính số sample bắt đầu / 120 s ở mỗi cửa sổ sau ramp tại tải mục tiêu, gồm mọi label, đồng thời phải đạt các SLO độ trễ và lỗi. Cùng phép tính, Soak đạt 204,59 request/s ở 120–240 s và 228,03–236,65 request/s ở các cửa sổ 240–720 s; Stress 300–450 s đạt 410,77 request/s. Đây là ngưỡng bảo thủ đề xuất, không phải chứng nhận hiệu năng: cửa sổ Soak 120–240 s đạt throughput nhưng vi phạm độ trễ.
- **Endurance threshold ứng viên: 200 VU, tối thiểu 200 request/s**, cần kiểm chứng bằng lần soak mới đủ dài và kiểm tra từng cửa sổ sau ramp theo toàn bộ SLO trên. Soak có tối đa 203 thread nhưng xuất hiện đợt chậm rõ rệt 120–240 s; Stress bậc 200 VU chỉ kéo dài khoảng 150 s và có ramp. Do đó **chưa xác lập được số user tối đa chịu ổn định** hay RPS endurance tương ứng từ bằng chứng hiện có; 200 VU là điểm thử tiếp, không phải giới hạn tối đa đã chứng minh. Số thread JMeter cũng không tự chứng minh số người dùng thực.
- **Cảnh báo p95 regression:** so từng nhóm endpoint giữa hai run có cùng workflow, tải, cửa sổ sau ramp, cách lọc và máy; báo khi p95 mới vừa lớn hơn 1,20 lần p95 baseline **và** tăng ít nhất 5 ms. Chỉ xét nhóm có ít nhất 1.000 sample ở mỗi run; nếu ít hơn, báo thiếu dữ liệu thay vì kết luận không regression. Ngưỡng 20% và sàn 5 ms là quy tắc đề xuất nhằm tránh cảnh báo do thay đổi tuyệt đối rất nhỏ, không phải biến thiên thực nghiệm đã đo hay mức ý nghĩa thống kê. Ví dụ, baseline p95 Read 20 ms ở Soak 360–600 s sẽ kích hoạt từ 25 ms; cửa sổ Stress 300–450 s có tải/thời đoạn khác nên không dùng trực tiếp làm cặp so sánh hợp lệ. Một cảnh báo regression độc lập với việc đạt hay vi phạm SLO tuyệt đối.
