# Bước 12 – Human review

## 1. Kiểm chứng độc lập (đã chạy thật ngày 2026-11-17)

Bản sửa ở bước 9 và smoke ở bước 10 **chưa** chạy nhánh mặc định của Stress (không truyền `-Jthreads`). Lỗi High #S1 nằm đúng ở nhánh này. Vì vậy mình chạy lại để kiểm tra:

```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 PATH=$JAVA_HOME/bin:$PATH
scripts/reset_sut.sh
jmeter -n -t test-plans/23120190_Stress_20261117.jmx -Jduration=5 -Jrampup=1 -l /tmp/s1.jtl -j /tmp/s1.log
grep -E "Starting thread group|STRESS_GATE" /tmp/s1.log
```

| Stage | Threads (log) | Gate của bậc trước |
|---|---|---|
| 1 | 50 | — |
| 2 | 100 | samples=448, errors=0.0, p95=148 ms, continue=true |
| 3 | 200 | samples=1043, errors=0.0, p95=35 ms, continue=true |
| 4 | 290 | samples=1709, errors=0.0, p95=613 ms, continue=true |

→ **#S1 đã được sửa đúng**: 50/100/200/290, không còn 50/100/100/100.

Spike mặc định cũng đã được kiểm tra: baseline 10 VU, burst 190 VU, đúng thiết kế.

> Số p95 ở bảng trên lấy từ lượt chạy rút gọn (5 s mỗi bậc, ramp 1 s). Lượt này chỉ để xác minh số thread, **không dùng làm kết quả đo**.

## 2. AI đã sai gì và vì sao (tổng hợp từ report/03, 04, 04a)

| # | AI sai / thiếu | Mức độ | Phát hiện bởi | Nguyên nhân |
|---|---|---|---|---|
| 1 | Thiếu `use_keepalive`, nên mỗi request gửi `Connection: close`. p95 bị tính cả thời gian mở kết nối TCP, tải không giống trình duyệt thật. | Medium | Reviewer bước 5 | Giới hạn model: tưởng default giống plan tạo bằng GUI, không kiểm tra default thật. |
| 2 | Assertion giỏ hàng dùng `any`. Giỏ không bao giờ bị xóa nên assertion luôn đúng từ khoảng vòng thứ 5, kể cả khi add-to-cart hỏng. | Medium | Reviewer bước 5 | Đặc điểm endpoint (giỏ không bị xóa). Smoke 1 vòng không lộ ra. |
| 3 | Khi login lỗi, vòng lặp quay lại ngay, không có think-time. SUT đang yếu sẽ bị dồn thêm login liên tục. | Medium | Reviewer bước 5 | Prompt chỉ nói think-time cho luồng thành công, không nói gì về nhánh lỗi. |
| 4 | `props.get(key, default)` trong Groovy **ghi** default vào props, nên Stress chạy mặc định chỉ lên 50/100/100/100 VU, không bao giờ chạm 200/290. | **High** | Reviewer bước 8 | Model hiểu nhầm overload `Map.get` của Groovy. Smoke luôn truyền `-Jthreads` nên không thấy lỗi. |
| 5 | Tên timer Stress ghi "500–1500 ms" nhưng giá trị thật là 250–750 ms. | Low | Reviewer bước 8 | Copy từ Load, không đối chiếu lại. |
| 6 | Plan dùng Groovy trong thuộc tính thread group, chạy lỗi với Java 25 (`Unsupported class file major version 69`). Phải chạy bằng Java 17. | Medium | Smoke bước 7 (04a) | Giới hạn môi trường: JMeter 5.6.3 kèm Groovy 3 chưa hỗ trợ Java 25. |
| 7 | Prompt bước 2 ghi "12 CPU core, 30 GB". Máy thật có 6 nhân vật lý / 12 luồng, 30 GiB. | Low | Agent bước 2 tự phát hiện | **Chất lượng prompt**: thông tin sai nằm trong chính prompt. |

## 3. Nhận xét thêm mà AI reviewer chưa nêu, hoặc nêu chưa đủ

1. **Plan phức tạp quá mức cần thiết.** Có pool tài khoản `synchronized` với fallback đọc file, gate Groovy giữa các bậc, `__groovy` trong thuộc tính thread group. Nhiều lỗi (#4, #6) sinh ra từ chính độ phức tạp này. Một plan đơn giản hơn chỉ dùng CSV, JSON Extractor, Response Assertion và Ultimate/Stepping Thread Group thì dễ review hơn. Mình chấp nhận giữ nguyên vì đã sửa và kiểm chứng, nhưng sẽ nêu rõ điểm này trong AI critique.
2. **Trần 290 VU do số tài khoản, không phải do năng lực SUT.** Ràng buộc "mỗi VU một tài khoản" đến từ chính prompt. Lượt kiểm chứng ở mục 1 chưa có lỗi nào ở 200 VU, nên Stress **có thể không chạm điểm gãy**. Nếu chạy thật mà vẫn không vượt ngưỡng, mình sẽ giảm think-time của Stress hoặc tăng số tài khoản trong `gen_users.py`; đây là quyết định của mình.
3. **JMeter và SUT chạy chung một máy.** Assertion JSR223 parse JSON ở mọi sample tốn CPU phía JMeter. Script `monitor_backend.sh` chỉ theo dõi `node`. Khi chạy thật mình sẽ mở htop xem cả `java` (JMeter); khi phân tích p95 cao phải xét cả khả năng do JMeter quá tải.
4. **Smoke bước 10 chưa phủ nhánh login sai.** Cả 3 plan đều có 0 sample `Negative login`, vì Throughput Controller 5% không được chọn trúng trong 2 vòng. Nhánh này mới chỉ được thử ở bước 6, với `lock_percent=100` trên Load. Lần chạy thật sẽ có login sai; mình sẽ kiểm tra trong `.jtl` rằng mẫu 401/403 được đánh dấu success.
5. **Bước 10 không chạy nhánh mặc định của Stress.** Đã bù bằng mục 1.
