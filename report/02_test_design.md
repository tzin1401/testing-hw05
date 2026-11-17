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
