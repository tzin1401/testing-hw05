# Bước 2 – Thiết kế Load / Stress / Spike cho Flow 1

Nguồn: `report/01_api_analysis.md`, `report/05_hardware.md`. Đây là thông số **đề xuất để đo**, không phải kết quả hoặc khả năng chịu tải đã xác minh. Máy thực có **6 nhân vật lý / 12 luồng logic**, RAM **30 GiB**; giả định “12 CPU core, 30 GB” trong prompt nhầm luồng logic thành nhân vật lý và khác đơn vị RAM. Node xử lý callback trên một event loop; SQLite có ghi ở login và checkout. JMeter và SUT cùng máy có thể tranh chấp tài nguyên, nên theo dõi cả hai khi chạy; không suy ra ngưỡng bão hòa từ cấu hình máy.

## Workflow và assertion chung

Mỗi vòng tuần tự: POST login → GET products → GET product detail → POST cart → GET cart → POST checkout → GET my-orders. Login là **Auth**; list và detail là **Read**; cart, checkout và my-orders là **Transactional** (my-orders đọc DB nhưng xác nhận giao dịch). Tất cả request chính yêu cầu HTTP 200 và các kiểm tra sau; lỗi assertion được tính là lỗi sampler:

| Request | JSON assertion / dữ liệu liên kết |
|---|---|
| POST `/api/login` | `$.token` là chuỗi không rỗng, `$.user.id` tồn tại; trích token và user ID cho vòng hiện tại. |
| GET `/api/products` | Root là mảng không rỗng; chọn ID hợp lệ từ CSV và xác nhận ID này có trong mảng. |
| GET `/api/products/{id}` | Root là object, `$.id` bằng ID đã chọn, `$.name` không rỗng; `$.price` tồn tại, chuyển được thành số hữu hạn dương dù là string hay number. Không ép assertion kiểu number; `{}` phải thất bại. |
| POST `/api/cart` | Body lấy id/name/price đã kiểm tra và quantity từ CSV; JSON `$.message` bằng `Added to cart`. |
| GET `/api/cart` | Root là mảng, có phần tử khớp id và quantity vừa thêm; không yêu cầu giỏ chỉ có một phần tử vì checkout không xóa giỏ. |
| POST `/api/checkout` | Gửi `total_amount = price × quantity` của vòng hiện tại và địa chỉ; `$.orderId` tồn tại, là số nguyên dương; trích orderId. |
| GET `/api/orders/my-orders` | Root là mảng, có đơn với `id = orderId`, `user_id = user.id` và `total_amount` bằng số đã gửi. Không giả định thứ tự hay chỉ có một đơn. |

Xóa biến trích xuất ở đầu mỗi vòng; nếu login hoặc detail thất bại, đánh dấu lỗi và bỏ các bước phụ thuộc của vòng đó, không tái sử dụng token/giá cũ. Token gửi Bearer cho cart, checkout và my-orders. Kiểm tra root array, kiểu linh hoạt và quan hệ giữa phần tử bằng JSON assertion hoặc JSR223 assertion; không chỉ kiểm tra JSONPath tồn tại mà bỏ qua giá trị.

## Bảng tổng hợp thông số

Thời gian tính từ lúc bắt đầu test, đơn vị giây. Các số VU là mục tiêu đồng thời, không phải RPS; thời gian đáp ứng và think-time quyết định tốc độ thực.

| Plan | VU, ramp và lịch | Thời lượng đo mặc định | Think-time giữa các request | Listener |
|---|---|---|---|---|
| Load | 50 VU, ramp 50 s | 600 s kể từ start, gồm ramp | Uniform Random Timer 500–1500 ms | Summary Report |
| Stress | 4 bậc lần lượt 50, 100, 200, 290 VU; mỗi bậc ramp 30 s | 4 × 150 s = 600 s nếu không dừng sớm | Uniform Random Timer 250–750 ms | Aggregate Report |
| Spike | Nền 10 VU ramp 10 s; thêm 190 VU ramp 5 s tại t=120 s, hết tại t=240 s | 360 s, gồm ramp | Uniform Random Timer 500–1500 ms | Response Time Graph |

Timer chỉ áp dụng giữa các request của workflow chính, không vô tình áp dụng trước sampler login sai; cài đặt uniform bằng constant delay bằng cận dưới và random delay bằng độ rộng khoảng. Không chèn timer sau request cuối; thời gian vòng thực còn gồm thời gian response.

## Load – tải bình thường

50 VU trong 600 s, ramp 50 s để tránh khởi động đồng loạt. Đây là mức nền bảo thủ để quan sát hành vi bình thường của event loop và SQLite trên máy dùng chung, không khẳng định phản ánh lưu lượng sản xuất. Think-time 0,5–1,5 s mô phỏng thời gian người dùng đọc/chuyển bước và tránh vòng lặp liên tục không thực tế. Dùng **Summary Report** để xem tổng quan số mẫu, lỗi và thời gian; JTL/HTML non-GUI vẫn là nguồn phân tích sau chạy.

## Stress – tăng bậc và ngưỡng dừng

Dùng các Thread Group tuần tự, mỗi bậc 150 s tính cả ramp 30 s: **[0,150): 50**, **[150,300): 100**, **[300,450): 200**, **[450,600): 290 VU**. Mỗi nhóm chỉ hoạt động trong cửa sổ của mình, kết thúc hẳn trước nhóm kế tiếp; không cộng chồng thành 640 VU. 290 là trần theo số tài khoản chính, không phải năng lực SUT. Các bậc tăng dần giúp khoanh vùng thay đổi; 30 s ramp giảm hiệu ứng đồng loạt, 120 s còn lại dành cho quan sát tương đối ổn định. Think-time 0,25–0,75 s ngắn hơn Load để tạo áp lực tăng dần; 150 s/bậc là điểm bắt đầu, không bảo đảm đủ mẫu thống kê.

Ghi timestamp bắt đầu thực tế của test và từng bậc; phân đoạn JTL theo các khoảng trên, tách riêng 30 s ramp khỏi 120 s ổn định, đối chiếu thời điểm thực khi sampler kết thúc trễ. Báo số mẫu, error % và p95 mỗi bậc cho toàn bộ request chính, đồng thời theo từng nhãn endpoint; không trộn login sai dự kiến vào mẫu chính. Tính error = sampler thất bại / tổng sampler chính, p95 từ elapsed của cùng tập; phải nêu số mẫu. Sau mỗi bậc, nếu error > 5% **hoặc** p95 > 2000 ms thì dừng, không chạy bậc tiếp; nếu tự động hóa kiểm tra giữa bậc chưa có thì người vận hành theo dõi và dừng thủ công. Nếu đạt 290 VU mà chưa vượt ngưỡng, báo chưa tìm được điểm vượt trong phạm vi thiết kế, không suy đoán. Dùng **Aggregate Report** cho thống kê phân vị và lỗi; đối chiếu với JTL được phân đoạn vì listener gộp cả lần chạy không đại diện từng bậc.

## Spike – thấp → cao → thấp

Nhóm nền 10 VU chạy từ t=0 đến t=360 s, ramp 10 s; nhóm tăng đột biến thêm 190 VU bắt đầu t=120 s, ramp 5 s và kết thúc tại t=240 s. Vậy mục tiêu xấp xỉ 10 → 200 → 10 VU; mốc 120–125 s là ramp, sau 240 s phải xác nhận nhóm spike đã kết thúc, vì request đang chạy có thể hoàn tất trễ. Tách nhóm và ghi timestamp để phân tích nền trước, đỉnh và phục hồi; giữ nền sau đỉnh 120 s để quan sát khả năng phục hồi. Think-time 0,5–1,5 s như Load để thay đổi chính là số VU, không đồng thời đổi hành vi. 190 VU bổ sung tạo mức nhảy rõ nhưng giữ dưới 290 tài khoản chính. **Response Time Graph** quan sát đường thời gian trước/trong/sau spike; dùng JTL để tính và đối chiếu, không coi đồ thị là nguồn percentile theo bậc.

## Tài khoản, lockout và reset

- Luồng chính dùng riêng `perf001..perf290` từ `data/users.csv`; phân bổ độc quyền theo VU đang hoạt động, không recycle đồng thời. Ở Stress nhóm kế tiếp chỉ khởi chạy sau khi nhóm trước kết thúc; Spike nền và nhóm tăng dùng các dải không giao nhau. Nếu không đủ tài khoản thì dừng cấu hình, không chia sẻ ngầm.
- Sau login chính, đặt một **Throughput Controller** chế độ percent executions = 5% quanh sampler POST login sai độc lập. Chọn trong `perf291..perf300`, gửi mật khẩu cố ý sai; không dùng token/kết quả đó cho workflow chính. Khoảng 5% lượt đi qua controller tạo login sai, tương đương khoảng 4,76% tổng lượt login khi mỗi vòng có một login chính; do làm tròn và cách phân phối theo thread, tỷ lệ thực kiểm tra bằng số mẫu. Tài khoản sai dùng chung có chủ đích và có thể bị khóa; không trộn vào CSV tài khoản chính.
- Sampler sai phải cho HTTP **401 hoặc 403** là thành công, còn mọi mã khác hoặc lỗi kết nối là thất bại; cấu hình assertion ghi đè đánh giá lỗi HTTP mặc định của JMeter trước khi kiểm tra tập mã. Không áp assertion token của login chính cho sampler này. Khi báo error chung phải nói rõ có/không gồm sampler sai; ngưỡng stress chỉ dùng sampler chính.
- Trước **mỗi lần chạy**, chạy `scripts/reset_sut.sh` và chờ script hoàn tất: restart xóa DB và giỏ RAM, seed lại dữ liệu/tài khoản. Chờ 180 s chỉ cho hết thời hạn khóa, **không thay thế reset**: không reset giỏ/DB và bộ đếm sai có thể còn; nếu chỉ muốn quan sát hết khóa trong cùng lần chạy có thể chờ 180 s rồi kiểm tra, nhưng trước lần chạy tiếp vẫn reset.

## Chế độ smoke và chế độ đo

Thiết kế property `loops` mặc định `-1` cho chạy theo thời gian; giá trị dương là số vòng **mỗi VU**. Với `loops=1` hoặc `loops=2`, tắt scheduler/duration và mọi start delay của các nhóm được bật, dùng số VU smoke nhỏ (ví dụ một VU), chỉ chạy một nhóm đại diện workflow và login sai có thể không được chọn bởi controller 5%; các vòng phải kết thúc tự nhiên sau đúng 1/2 vòng, không chờ hết lịch 600/360 s. Không dùng cùng lúc duration vô hạn và loop controller vô hạn trong smoke. Kiểm tra riêng sampler sai nếu cần bằng cấu hình chạy kiểm thử phù hợp, không thay đổi tỷ lệ của lần đo.

Ở chế độ đo `loops=-1`, bật scheduler cho các nhóm và đặt duration/delay đúng lịch từng plan; vòng lặp vô hạn chỉ tồn tại trong cửa sổ đã định. Scheduler không bảo đảm ngắt sampler đang chạy đúng mốc, nên cấu hình timeout kết nối/response hữu hạn và ghi nhận thời gian kết thúc thực. Stress cần cơ chế dừng ở ranh giới bậc sau đánh giá ngưỡng như trên; không được để các nhóm tự tiếp tục nếu chưa đánh giá. Thiết kế này chưa tạo file JMX và chưa chạy tải.

## Thực thi Stress/Spike và chế độ xác minh nhanh

Chạy từ thư mục `hw05`, với `JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64` và `$JAVA_HOME/bin` đứng đầu `PATH`. Reset SUT trước mỗi lần chạy. Các override dưới đây chỉ dành cho smoke, không phải kết quả tải thật.

- Stress mặc định có 4 Thread Group tuần tự; `threads` override số VU mỗi bậc, `rampup` mặc định 30, `duration` mặc định 150 cho **mỗi** bậc. Pool tài khoản tách theo bậc vì các bậc không đồng thời.
- Stress dùng sampler gate nội bộ `SampleResult.setIgnore()` trước HTTP, không thêm listener/JTL sample. Assertion tích lũy elapsed và số lỗi request chính; khi nhóm trước kết thúc, gate bậc sau tính nearest-rank p95 và error trên toàn bậc, bỏ login sai. Vượt 5% hoặc 2000 ms, hoặc không có mẫu, thì không cho HTTP bậc mới và yêu cầu dừng test. Log có `STRESS_STAGE_START`, `STRESS_GATE`, `STRESS_STAGE_SUMMARY`; phân tích ổn định sau ramp vẫn cần đọc JTL riêng, không lấy metric gate toàn bậc thay thế.
- Spike mặc định baseline 10 VU/360 s/ramp 10 s; burst thêm 190 VU, delay 120 s, duration 120 s, ramp 5 s. Property riêng: `spike_threads`, `spike_delay`, `spike_duration`, `spike_rampup`. Hai nhóm chia sẻ pool để không dùng chung tài khoản đang hoạt động.
- `loops>0` mặc định chỉ bật nhóm đại diện của mỗi plan bằng số thread 0 ở nhóm còn lại; `stage_smoke=true` bật cả 4 nhóm Stress; `timeline_smoke=true` bật burst cả khi dùng loops hữu hạn. Scheduler bật khi `loops=-1`. Không reset SUT giữa các bậc trong cùng một plan.

```bash
# Thêm -l và -j với tên output mới cho từng lần; reset trước từng lệnh.
jmeter -n -t test-plans/23120190_Stress_20261117.jmx -Jthreads=1 -Jrampup=1 -Jloops=1
jmeter -n -t test-plans/23120190_Spike_20261117.jmx -Jthreads=1 -Jrampup=1 -Jloops=1
jmeter -n -t test-plans/23120190_Stress_20261117.jmx -Jthreads=1 -Jrampup=1 -Jloops=1 -Jstage_smoke=true
jmeter -n -t test-plans/23120190_Spike_20261117.jmx -Jthreads=1 -Jspike_threads=1 -Jrampup=1 -Jspike_rampup=1 -Jloops=-1 -Jduration=24 -Jspike_delay=8 -Jspike_duration=8
```

## Soak – tải kéo dài

Chọn **203 VU = 70% × 290 VU**, với 290 là bậc ổn định cao nhất đã quan sát, không phải breakpoint: bảng stable window trong `report/07_run_log.md` ghi bậc 290 VU có 56.493 mẫu chính, 0% lỗi, p95 947 ms, 470,775 request/s theo cửa sổ danh nghĩa. `results/html/23120190_Stress_20261118/statistics.json` tổng hợp cả lần Stress, không phải riêng cửa sổ ổn định. Soak giữ think-time Load 500–1500 ms, khác Stress 250–750 ms; 70% là tỷ lệ VU, không phải RPS. Script về sau dùng cửa sổ JTL khác, cho 468,556 RPS; xem [08_endurance.md](08_endurance.md).

Plan `test-plans/23120190_Soak_20261118.jmx` dùng Duration 720 giây (12 phút, bao gồm ramp-up 60 giây), mặc định `threads=203`, `rampup=60`, `duration=720`, `loops=-1`. Giữ workflow, assertion, CSV và login sai của Load. Listener duy nhất **Simple Data Writer** ghi bản phụ mặc định `results/jtl/23120190_Soak_20261118_writer.jtl`, đổi bằng `-Jwriter_file=...`; dùng đường dẫn khác cho `-l` JTL chính, không cộng số mẫu hai file vì là hai bản ghi cùng sự kiện.

Smoke 1 thread, 1 vòng: reset SUT trước khi chạy, dùng Java 17 và output mới, riêng nhau:

```bash
scripts/reset_sut.sh
jmeter -n -t test-plans/23120190_Soak_20261118.jmx -Jthreads=1 -Jrampup=1 -Jloops=1 -Jwriter_file=results/jtl/23120190_Soak_20261118_smoke_writer.jtl -l results/jtl/23120190_Soak_20261118_smoke.jtl
```

`loops=1` tắt scheduler để kết thúc sau một vòng. Smoke sau tạo plan đã đạt 7/7 sampler chính; writer phụ cũng đúng 7 mẫu: [05b_soak_smoke.md](05b_soak_smoke.md).
