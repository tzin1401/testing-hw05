# Bước 5 – Review độc lập test plan Load

Đối tượng: `test-plans/23120190_Load_20261117.jmx`. Đối chiếu `report/02_test_design.md`, `eshop-sut/backend/server.js`, `report/02a_load_smoke.md`. Chỉ đọc code/JMX; **không sửa JMX, không chạy test**. Số dòng dưới đây là số dòng của file `.jmx`.

Giới hạn bằng chứng: smoke duy nhất là 1 VU, 1 vòng (`report/02a_load_smoke.md`, 7 sampler pass, negative 401 pass). Chưa có lần chạy 50 VU nào, nên mọi nhận định về hành vi dưới tải là suy luận từ code (đánh dấu `[INFERENCE]`).

## Kết luận: **NEEDS FIX**

3 lỗi mức Medium (#1–#3) nên sửa trước khi chạy đo chính thức; còn lại là Low/Info. Không có lỗi High: workflow, extractor, header Authorization, lockout, total_amount và listener đều đúng (xem mục "Đã kiểm tra và đúng").

## Danh sách lỗi

### #1 [Medium] Mọi HTTP sampler (dòng 23, 42, 47, 48, 50, 52, 53, 57) – thiếu `HTTPSampler.use_keepalive` nên mỗi request gửi `Connection: close`

- **Vấn đề:** XML không có thuộc tính `HTTPSampler.use_keepalive` ở sampler nào (`grep use_keepalive` trên file .jmx: 0 kết quả), và HTTP Request Defaults (dòng 14) không mang thuộc tính này. Đọc `ApacheJMeter_http.jar` 5.6.3 bằng `javap -c`: `HTTPSamplerBaseSchema` đặt mặc định `HTTPSampler.use_keepalive = false` (`iconst_0`), và `HTTPHC4Impl` khi `getUseKeepAlive()` sai thì `setHeader("Connection","close")`. Plan tạo bằng GUI luôn ghi `true`; plan viết tay này thì không. Hệ quả `[INFERENCE]`: mỗi request mở một TCP connection mới trên localhost (~57 req/s ước tính, xem #8), thời gian connect nằm trong `elapsed`/p95, và Node nhận tải khác với trình duyệt thật (tái dùng kết nối). Smoke 1 VU không phát hiện vì chỉ đo pass/fail.
- **Cách sửa:** thêm `<boolProp name="HTTPSampler.use_keepalive">true</boolProp>` vào cả 8 `HTTPSamplerProxy` (dòng 23, 42, 47, 48, 50, 52, 53, 57). Không cần thêm cấu trúc nào khác.

### #2 [Medium] `05 Get cart`, dòng 90 – assertion gần như luôn đúng vì giỏ không bao giờ bị xóa

- **Vấn đề:** `json.any { it.id == id && it.quantity == qty }`. Giỏ của một user chỉ tăng (`server.js:290-295` chỉ `push`, checkout dòng 297-309 không xóa giỏ) và `products.csv` chỉ có 5 sản phẩm với quantity cố định theo sản phẩm. Từ vòng thứ ~5 của mỗi VU, giỏ đã chứa phần tử cũ khớp `id`+`quantity` của vòng này, nên assertion đúng dù lần `POST /api/cart` hiện tại không được lưu. Thiết kế (`02_test_design.md`) nói "có phần tử khớp id và quantity vừa thêm"; hiện thực chỉ kiểm tra "có phần tử khớp", không đảm bảo "vừa thêm".
- **Cách sửa:** `server.js:293` push vào cuối mảng và tài khoản được cấp độc quyền cho một VU, nên kiểm tra phần tử cuối: `assert json instanceof List && json && json[-1].id == id && json[-1].quantity == qty; break`.

### #3 [Medium] Login chính thất bại (dòng 23 + 44–46) – vòng lặp quay lại ngay, không có think-time

- **Vấn đề:** Timer duy nhất (dòng 46) nằm trong `IfController "Authenticated"` (dòng 44). Khi `login_ok != 'true'` (backend chết/connection refused, 5xx, timeout, login assertion fail), toàn bộ nhánh bị bỏ qua và vòng sau bắt đầu ngay bằng `01 Login`, không có delay nào (thread group `on_sample_error=continue`, dòng 17). `[INFERENCE]` 50 VU sẽ gọi login liên tục không nghỉ trong suốt thời gian còn lại của 600 s, tạo hàng chục nghìn sample lỗi, làm phình JTL/HTML report và tạo tải khác hẳn thiết kế đúng lúc SUT đang yếu nhất. Ngoài ra nhánh phụ thuộc không chạy nên không có sample lỗi tương ứng (xem #9).
- **Cách sửa:** thêm một `IfController` cạnh dòng 44 với điều kiện `${__groovy(vars.get('login_ok') != 'true')}` (Interpret as expression = true), bên trong đặt một `Flow Control Action` (Pause 1000 ms). Không đặt Timer trước login để giữ nguyên nhịp tải 6 think-time/vòng đúng thiết kế.

### #4 [Low] Assertion `switch (label)`, dòng 75–97 – không có `default`

- **Vấn đề:** nhãn sampler được hard-code. Nếu đổi tên sampler (ví dụ sửa "04 Add cart"), assertion chỉ còn kiểm tra HTTP 200 + parse được JSON (dòng 72–73) mà không báo lỗi, tức quay lại đúng kiểu assertion yếu mà thiết kế cấm.
- **Cách sửa:** thêm trước dòng `}` đóng switch: `default: assert false : "No check for label " + label`.

### #5 [Low] Dòng 77–78 và 92–94 – assertion kiểm tra JSON thô, nhưng Authorization/`order_id` dùng biến từ extractor (default `NOT_FOUND`)

- **Vấn đề:** `01 Login` chỉ xác nhận `json.token` không rỗng (dòng 78); header `Bearer ${token}` (dòng 45) lấy từ JSON extractor (dòng 39) có default `NOT_FOUND`. Nếu extractor và assertion lệch nhau (đổi JSONPath, đổi cấu trúc response), `login_ok=true` nhưng header thành `Bearer NOT_FOUND` → 04–07 trả 403 (`authenticateToken` `server.js:100-108`) và lỗi bị quy cho cart/checkout thay vì extractor. Tương tự `order_id` (dòng 54) với `06 Checkout`. Hiện tại hai bên đọc cùng body nên chưa lỗi thật; smoke 1 VU pass.
- **Cách sửa:** trong case `'01 Login'` thêm `assert vars.get('token') == json.token`; trong case `'06 Checkout'` thêm `assert vars.get('order_id') == json.orderId.toString()`. JMeter chạy PostProcessor trước Assertion nên biến đã có giá trị.

### #6 [Low] Đường dẫn CSV (dòng 20–22) và `new File('data/users_main.csv')` (dòng 29) – chỉ chạy đúng khi cwd = thư mục hw05

- **Vấn đề:** tất cả đường dẫn là tương đối (`data/...`), không hard-code absolute path (đúng yêu cầu). Nhưng file đọc thủ công ở dòng 29 chỉ resolve theo cwd của JVM; nếu chạy `jmeter -t` từ thư mục khác lỗi sẽ xuất hiện ngay ở CSV Data Set (smoke chạy từ hw05 nên pass). Việc CSV Data Set có resolve thêm theo thư mục chứa JMX hay không là `[INFERENCE]`, chưa kiểm tra.
- **Cách sửa:** không cần đổi plan. Ghi rõ trong tài liệu chạy test: chạy từ thư mục hw05, đúng lệnh `jmeter -n -t test-plans/... -l results/jtl/... -e -o results/html/...` trong `CLAUDE.md`.

### #7 [Info] Pool tài khoản main (dòng 20, 25–38) – CSV tiêu thụ mỗi iteration nhưng `account_email` cố định; fallback đọc file

Câu hỏi được giao: lỗi thật hay chỉ lệch thiết kế?

- **Cơ chế:** `Main accounts` (shareMode.all, recycle=true) nạp một dòng mới vào `main_email/main_password` ở **mỗi** iteration của mỗi VU, nhưng PreProcessor chỉ dùng dòng đó ở iteration đầu của VU (`if (!vars.get('account_email'))`), rồi giữ `account_email` suốt vòng đời thread (`account_email` không nằm trong danh sách `vars.remove`, dòng 38). Các dòng nạp ở iteration sau bị bỏ.
- **Có lỗi người dùng nhìn thấy không?** Không. Evidence: (a) `account_email` ổn định nên mỗi VU luôn login đúng một tài khoản, my-orders/cart của VU không lẫn với VU khác; (b) tài khoản main `perf001..290` tách khỏi `perf291..300` ở lockout, nên không bị khóa (chỉ login sai mới cộng `login_attempts`, `server.js:54-62`); (c) `[INFERENCE]` với mặc định 50 VU, ramp 50 s, ~6 s/vòng, VU thứ 50 khởi động ở ~t=49 s sau khoảng 240 dòng đã tiêu thụ (< 290), nên không có va chạm và nhánh fallback đọc file (dòng 29–31) **không chạy** ở cấu hình mặc định. Nhánh này chỉ phát huy khi tăng `threads`/giảm tốc độ vòng làm CSV quay vòng (>290 dòng đã dùng), lúc đó nó chọn tài khoản chưa dùng đúng như thiết kế ("không chia sẻ ngầm"); hết tài khoản thì ném lỗi rõ ràng.
- **Kết luận:** lệch thiết kế nhẹ, không phải defect. Việc tiêu thụ CSV thừa là vô hại về chức năng và chi phí. **Không đòi thêm abstraction**: giữ nguyên. Nếu muốn, chỉ thêm một dòng chú thích trong report: "CSV `users_main` chỉ quyết định tài khoản ở vòng đầu của VU; phần độc quyền do `props load.accounts` bảo đảm". `props` là global của JVM nên chạy lại plan trong cùng JMeter GUI session sẽ giữ tập cũ; chạy non-GUI theo quy định (mỗi lần một JVM) không bị ảnh hưởng.

### #8 [Info] Ramp-up, think-time, số thread – hợp lý

- 50 VU, ramp 50 s (1 VU/s; dòng 17), duration 600 s tính cả ramp: đúng bảng thiết kế. 50 << 290 tài khoản, đủ độc quyền.
- Timer `ConstantTimer.delay=500` + `RandomTimer.range=1000` = 500–1500 ms (đúng cú pháp Uniform Random Timer), áp dụng cho 6 request 02–07, không áp dụng trước login chính và login sai (đúng thiết kế).
- `[INFERENCE]` ~6 s/vòng ⇒ ~8 vòng/s ≈ 55–60 req/s tổng. Mức nền bảo thủ cho Node đơn luồng; chưa được đo bằng lần chạy 50 VU.
- Thiết kế đúng: không có lỗi cần sửa ở mục này (riêng think-time khi login lỗi xem #3).

### #9 [Info] Error % có thể thấp hơn thực tế do cơ chế dừng bước phụ thuộc

Các `IfController` (dòng 44, 49, 51, 56) bỏ qua bước sau khi login/detail/cart/checkout lỗi, đúng thiết kế ("bỏ các bước phụ thuộc"). Hệ quả khi phân tích: tỉ lệ lỗi của cart/checkout/my-orders chỉ tính trên các vòng đã tới được bước đó. Khi báo cáo cần nêu số sample từng nhãn, không chỉ error % của TOTAL. TOTAL của Summary Report cũng **gồm** `Negative login` (401/403 được đánh dấu thành công).

### #10 [Info] Login sai – đa số mẫu rơi vào nhánh 403 khóa, không phải nhánh sai mật khẩu

`server.js:32-62`: sai mật khẩu cộng +2 vào `login_attempts`, khóa khi ≥ 3 ⇒ lần sai thứ 2 khóa 180 s; trong lúc khóa `/api/login` trả 403 trước khi so mật khẩu (dòng 40-44, trước khi so mật khẩu ở dòng 46). Với 10 tài khoản và ~245 login sai trong 600 s (`[INFERENCE]`, 5% × ~4900 vòng), phần lớn mẫu là 403. Đây là chủ ý của thiết kế ("có thể bị khóa"), assertion chấp nhận 401 và 403 nên không sinh lỗi giả. Chỉ cần nêu trong phân tích rằng mẫu 403 là đường rẻ (không đụng SQLite).

### #11 [Info] Các CSV var `keyword`, `csv_price`, `csv_name` (dòng 21) không được dùng

Giá lấy từ response SUT, không so với `products.csv`. Đúng thiết kế (chỉ yêu cầu price hữu hạn dương) nên không phải lỗi; có thể bỏ cột khỏi `variableNames` nhưng đổi vị trí cột không cần thiết, nên giữ.

## Đã kiểm tra và đúng

| Hạng mục | Kết quả | Bằng chứng |
|---|---|---|
| Assertion không chỉ kiểm tra 200 | Đúng | Dòng 72–97: parse JSON, kiểm tra token/user.id, `id` có trong mảng, name, price, message `Added to cart`, `orderId` số nguyên dương, my-orders khớp `id`, `user_id`, `total_amount` (BigDecimal `compareTo`). Lỗi gán vào `AssertionResult` (dòng 98–101). Riêng `05` yếu, xem #2. |
| Price string/number | Đúng | Dòng 84: `new BigDecimal(json.price.toString())` + `> 0`. SUT trả string với id chẵn (`server.js:159-165`); `{}` cho id lạ làm `json.id == id` sai nên thất bại. |
| Lockout tách riêng | Đúng | Negative login dùng `lock_email/lock_password` (`users_lock.csv`, perf291–300 mật khẩu `WrongPass1!`), khác `users_main.csv` (perf001–290). |
| 401/403 là đúng | Đúng | Dòng 66–70: `prev.setSuccessful(code in ['401','403'])`; mã khác hoặc lỗi kết nối thất bại. Smoke negative: 401 → success. Assertion gắn theo nhãn nên không áp assertion token cho login sai. |
| Throughput Controller 5% | Đúng | Dòng 41: `style=1` (percent), `percentThroughput=${__P(lock_percent,5)}`, `perThread=false`. Smoke `lock_percent=100` sinh đúng 1 Negative login. |
| Extractor | Đúng | Dòng 39: `$.token;$.user.id`, match `1;1`, default `NOT_FOUND;NOT_FOUND`; dòng 54: `$.orderId`. Các key native đã đối chiếu ở 02a. Biến được xóa mỗi vòng (dòng 38) nên không dùng lại token/giá cũ. |
| Header / Authorization | Đúng | Content-Type JSON ở mức plan (dòng 15). `Bearer ${token}` (dòng 45) trong `Authenticated` bao phủ 02–07, gồm 04/05/06/07 cần token (`server.js` cart/checkout/my-orders đều qua `authenticateToken`). Login và Negative login nằm ngoài scope, không gửi token. |
| CSV Sharing mode / Recycle | Đúng | Cả 3 CSV `shareMode.all`, `recycle=true`, `stopThread=false`, `ignoreFirstLine=true`; header khớp (dòng 20–22; products.csv có header `product_id,keyword,quantity,price,name`). Một dòng sản phẩm dùng nhất quán trong cả vòng vì CSV nạp một lần ở đầu iteration. |
| total_amount không cộng dồn | Đúng | Dòng 86: `total_amount = price × qty` của đúng sản phẩm vòng này; body cart chỉ gồm một sản phẩm (dòng 87). Dòng 38 xóa `total_amount` mỗi vòng. Checkout không dùng giỏ (`server.js:297-309`) nên giỏ tích lũy không ảnh hưởng. Dòng 96 so sánh đúng `total_amount` đã gửi. |
| Listener | Đúng | Duy nhất một `ResultCollector` loại `SummaryReport` (dòng 102); không có listener khác. |
| Smoke | Đạt | 7/7 sampler pass, Negative login 401 pass (02a); chưa có lần chạy 50 VU. |

## Việc cần làm theo thứ tự

1. Sửa #1, #2, #3 trong JMX (do người/agent được giao sửa, reviewer không sửa).
2. Tùy chọn #4, #5.
3. Chạy lại `scripts/reset_sut.sh`, smoke `-Jthreads=1 -Jloops=2`, rồi chạy đo `jmeter -n` từ thư mục hw05 (xem #6).

## Đã sửa

Các nguyên nhân bỏ sót dưới đây là nhận định `[INFERENCE]` từ prompt và bản plan ở bước 4, không phải kết luận về quá trình nội bộ của model.

| Lỗi | Đã sửa | Vì sao AI bước 4 có thể bỏ sót |
|---|---|---|
| #1 Medium – thiếu keep-alive | Đặt `HTTPSampler.use_keepalive=true` cho cả 8 HTTP sampler. | Giới hạn model: giả định mặc định JMeter giống cấu hình GUI thay vì kiểm tra default thực tế. |
| #2 Medium – cart khớp phần tử cũ | Kiểm tra phần tử cuối không rỗng có đúng `id` và `quantity`; tài khoản main độc quyền cho mỗi VU và endpoint thêm vào cuối. | Đặc điểm endpoint: giỏ tồn tại qua checkout, nên assertion `any` có thể khớp dữ liệu cũ; smoke một vòng không phơi bày. |
| #3 Medium – login thất bại lặp ngay | Thêm nhánh login thất bại với Flow Control Action pause 1000 ms, không tạo HTTP request; nhánh thành công giữ nguyên think-time. | Prompt nhấn mạnh think-time workflow thành công nhưng không chỉ rõ nhịp khi login lỗi; model bỏ sót nhánh lỗi. |
| #4 Low – switch thiếu default | Thêm `default` làm assertion thất bại với nhãn không được kiểm tra. | Giới hạn model: chỉ xét các nhãn hiện tại, chưa xét nhãn bị đổi hoặc thêm. |
| #5 Low – chưa đối chiếu extractor | So sánh `token`, `user_id` với JSON login và `order_id` với JSON checkout trước khi đánh dấu bước thành công. | Prompt yêu cầu extractor và assertion nhưng không nói rõ phải đối chiếu giá trị trích xuất với response; model kiểm tra riêng từng phần. |
| #6 Low – thiếu hướng dẫn cwd | Ghi rõ cwd và Java 17 trong lệnh bên dưới; không đổi đường dẫn tương đối của plan. | Prompt yêu cầu đường dẫn tương đối so với hw05 nhưng chưa yêu cầu ghi rõ cwd khi chạy. |

Không thay pool #7: reviewer xác định đây là lệch thiết kế, không phải lỗi consumer-visible. Các mục #8–#11 là thông tin, không yêu cầu sửa plan. Review không ghi nhận lỗi High.

Chạy smoke từ thư mục `/home/zinn/zinn/testing/hw05`, dùng Java 17 và reset trước lượt chạy:

```sh
cd /home/zinn/zinn/testing/hw05
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"
scripts/reset_sut.sh
jmeter -n -t test-plans/23120190_Load_20261117.jmx -Jthreads=1 -Jrampup=1 -Jloops=1 -l /tmp/hw05-load-step6.jtl -j /tmp/hw05-load-step6.log
```

Chưa chạy smoke sau các sửa đổi này; kết quả cũ ở `02a_load_smoke.md` không xác nhận bản mới.
