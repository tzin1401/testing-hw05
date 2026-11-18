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
