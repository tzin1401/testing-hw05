# Bug report Flow 1

Ngày tái hiện: 2026-11-18 (giờ VN). SUT reset một lần trước lần tái hiện. Raw `results/repro/flow1_bugs_20261118.txt` chứng minh lockout và price; các request cart/checkout trong file đó trả 403 nên **không chứng minh BUG-02/03**. Manager sửa quy trình giữ token thật trong bộ nhớ, chỉ che bản in, rồi thu curl thành công lúc 02:06:55 +07 trong `results/repro/checkout_cart_20261118.txt`; không sửa SUT hoặc chạy lại load. Môi trường: Linux; SUT Node.js/Express + SQLite tại `http://localhost:3000`; JMeter 5.6.3/JDK 17 test profile (không chạy JMeter ở bước này). Lệnh reset đầu phiên: `scripts/reset_sut.sh`.

## BUG-01 – Khóa tài khoản sau hai lần sai và giữ khóa khoảng 180 giây

- **Môi trường:** Như trên; tài khoản `perf290@eshop.com`, thử sai hai lần liên tiếp.
- **Các bước tái hiện (curl):**
  ```bash
  curl -i -H 'Content-Type: application/json' -d '{"email":"perf290@eshop.com","password":"WrongPass1!"}' http://localhost:3000/api/login
  curl -i -H 'Content-Type: application/json' -d '{"email":"perf290@eshop.com","password":"WrongPass1!"}' http://localhost:3000/api/login
  # Sau đúng hai lần sai, gửi mật khẩu đúng; thử lại ở các mốc ~35s, ~179s và ~181s tính từ lần sai thứ hai.
  curl -i -H 'Content-Type: application/json' -d '{"email":"perf290@eshop.com","password":"Perf@290a"}' http://localhost:3000/api/login
  ```
- **Kết quả thực tế:** Hai lần sai đều HTTP 401. Mật khẩu đúng ngay sau đó và tại khoảng 35 giây, 179 giây trả HTTP 403; khoảng 181 giây trả HTTP 200. Thời điểm chính xác và elapsed có trong raw output; mốc trên là phép đo quanh 179–181 giây, không tuyên bố độ chính xác đúng 180 giây. Source tăng `login_attempts` thêm 2 ở `server.js:54`, đặt `lockedUntil` thêm 180000 ms ở dòng 57.
- **Kết quả mong đợi (README.md FR-02, dòng 41–42):** “Sau mỗi lần đăng nhập sai, hệ thống tăng bộ đếm lên đúng 1 đơn vị”; từ 3 lần sai liên tiếp mới khóa 30 giây.
- **Mức độ:** Medium – người dùng đúng mật khẩu bị từ chối sau hai lần nhập sai và phải chờ lâu hơn yêu cầu.
- **Bằng chứng:** `results/repro/flow1_bugs_20261118.txt` (lock wrong 1/2, correct immediate, ~35s/~179s/~181s).

Trích response thật: hai lần sai `401 {"error":"Invalid email or password"}`; đúng mật khẩu trước hết khóa `403 {"error":"Tài khoản đã bị khóa. Vui lòng thử lại sau."}`; tại khoảng 181 giây `200 {"message":"Login successful",...}` (token đã che trong raw).

## BUG-02 – Checkout lưu nguyên tổng tiền do client cung cấp

- **Môi trường:** Như trên; tài khoản riêng `perf289@eshop.com`.
- **Các bước tái hiện (curl):**
  ```bash
  TOKEN=$(curl -sS -H 'Content-Type: application/json' -d '{"email":"perf289@eshop.com","password":"Perf@289a"}' http://localhost:3000/api/login | python3 -c 'import json,sys; print(json.load(sys.stdin)["token"])')
  curl -i -H "Authorization: Bearer $TOKEN" http://localhost:3000/api/cart
  curl -i http://localhost:3000/api/products/2
  curl -i -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"id":2,"name":"Samsung Galaxy S24 Ultra","price":28000000,"quantity":1}' http://localhost:3000/api/cart
  curl -i -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"total_amount":1,"shipping_address":"test"}' http://localhost:3000/api/checkout
  curl -i -H "Authorization: Bearer $TOKEN" http://localhost:3000/api/orders/my-orders
  ```
- **Kết quả thực tế:** Login và API cart/checkout/orders đều HTTP 200. Product 2 có giá thật 28,000,000; checkout nhận body total_amount=1; orders trả đơn vừa tạo có `total_amount:1`. Backend lấy `total_amount` từ request body rồi ghi thẳng vào DB (`server.js:297–307`). Raw output chứa response từng request.
- **Kết quả mong đợi (README.md FR-08, dòng 105, 107):** Tổng tiền được tính từ giỏ hàng, người dùng không chỉnh sửa; “Backend phải tự tính lại tổng tiền; không chấp nhận giá trị `total_amount` do client gửi lên.”
- **Mức độ:** High – đơn hàng lưu sai tổng tiền so với mặt hàng trong giỏ.
- **Bằng chứng:** `results/repro/checkout_cart_20261118.txt`, curl lúc 02:06:55 +07: checkout `200 {"message":"Checkout successful","orderId":1}`; my-orders trả `[{"id":1,"user_id":291,"total_amount":1,"status":"pending","shipping_address":"test","created_at":"2026-11-17 19:06:55"}]`. Lượt 403 trong raw cũ chỉ là thử nghiệm không hợp lệ, không dùng làm bằng chứng checkout.

## BUG-03 – Giỏ hàng vẫn còn sau checkout

- **Môi trường:** Cùng tài khoản và đơn ở BUG-02.
- **Các bước tái hiện (curl):** Thực hiện login, thêm product 2 và checkout như BUG-02; tiếp tục:
  ```bash
  curl -i -H "Authorization: Bearer $TOKEN" http://localhost:3000/api/cart
  ```
- **Kết quả thực tế:** Checkout HTTP 200 nhưng GET cart sau đó vẫn trả item product 2. Source checkout chỉ insert order; không xóa `userCarts` (`server.js:297–309`); cart được giữ trong đối tượng RAM (`server.js:14`, `284–294`). Đây chứng minh retention sau một checkout, không tự nó chứng minh RAM leak vô hạn. Độ dốc RSS quan sát riêng trong Soak là 1.470 MiB/phút, và report 08 xác định đây không chứng minh nguyên nhân hay leak không giới hạn.
- **Kết quả mong đợi (README.md FR-08, dòng 108):** “Sau thanh toán thành công, giỏ hàng được xóa.”
- **Mức độ:** Medium – nội dung giỏ cũ xuất hiện lại và có thể dẫn đến thao tác nhầm; retention state cũng không được thu hồi sau thanh toán.
- **Bằng chứng:** `results/repro/checkout_cart_20261118.txt`: trước checkout và sau checkout đều HTTP 200 với `[{"id":2,"name":"Samsung Galaxy S24 Ultra","price":28000000,"quantity":1}]`; checkout giữa hai request trả 200. Định lượng Soak riêng: `report/08_endurance.md`, `results/analysis/endurance.json`.

## BUG-04 – Kiểu JSON của price khác nhau giữa product detail và product list

- **Môi trường:** Như trên; endpoint công khai, không cần token.
- **Các bước tái hiện (curl):**
  ```bash
  curl -i http://localhost:3000/api/products
  curl -i http://localhost:3000/api/products/1
  curl -i http://localhost:3000/api/products/2
  ```
- **Kết quả thực tế:** List và `/api/products/1` trả `price` dạng number (`30000000`); `/api/products/2` trả dạng string (`"28000000"`). Raw có response JSON thật; detail ID 2 còn được xác nhận trong `results/repro/checkout_cart_20261118.txt`. Đây là finding về tính nhất quán/khả năng tương thích; `server.js:162` chủ động chuyển `row.price` sang string với ID chẵn.
- **Kết quả mong đợi:** README FR-06 dòng 85 chỉ yêu cầu hiển thị ảnh/tên/giá/mô tả/danh mục, không quy định kiểu JSON. API specification mục 3.2 không định nghĩa response schema; ví dụ body admin mục 3.3 dùng price dạng number. Do đó kỳ vọng thống nhất number là **inference về consistency**, không phải vi phạm một yêu cầu kiểu dữ liệu được nêu trong FR-06.
- **Mức độ:** Low – client phải chuẩn hóa kiểu giá; không khẳng định mọi client hiện tại lỗi.
- **Bằng chứng:** `results/repro/flow1_bugs_20261118.txt` (product list, product1 corrected, product2 corrected).

## BUG-05 – Mật khẩu lưu plaintext và xuất hiện trong response login

- **Môi trường:** Cùng SUT của BUG-02/03; tài khoản demo `perf289@eshop.com`.
- **Tái hiện bằng curl:** Đã chạy lúc 02:06:55 +07, không chạy lại ở rà soát cuối:
  ```bash
  curl -sS -X POST http://localhost:3000/api/login \
    -H 'Content-Type: application/json' \
    -d '{"email":"perf289@eshop.com","password":"Perf@289a"}'
  ```
- **Thực tế:** HTTP 200; JSON response có `user.password` bằng nguyên văn `"Perf@289a"`. Trường này nằm trong response thật ở dòng 2 của `results/repro/checkout_cart_20261118.txt`; token đã che. `server.js:23–24` đưa nguyên password vào `INSERT users`, dòng 46 so sánh plaintext, dòng 52 trả toàn bộ user đọc từ DB.
- **Mong đợi:** README mục 9, SEC-01 dòng 278: “Mật khẩu **không** được lưu dưới dạng plaintext.” Mục này ghi rõ **Tham khảo**, không giả làm FR bắt buộc. Loại mật khẩu khỏi response login là khuyến nghị bảo mật, không phải trích một yêu cầu response schema.
- **Mức độ:** High (đánh giá rủi ro lưu credential đọc được; không tuyên bố đã khai thác tài khoản người khác).
- **Bằng chứng:** `results/repro/checkout_cart_20261118.txt` dòng 1–2, mã nguồn và SEC-01 như trên. Không sửa SUT hoặc tạo thêm request để có bằng chứng.

## Quan sát hiệu năng (không phải bug curl đã tái hiện)

Không chạy lại performance test theo phạm vi. Soak JTL ghi nhận minute index 3 có p95 **2,244 ms**, RPS **171.183**, error **0%**; đây là episode vượt tiêu chí 2,000 ms được mô tả trong `report/08_endurance.md`, không có căn cứ quy nguyên nhân cho một lỗi cụ thể, và curl trực tiếp không tái hiện tải/latency này. Nguồn: `results/jtl/23120190_Soak_20261118.jtl`, `results/analysis/endurance.json`, `results/monitor/23120190_Soak_20261118.csv`. Không tạo bug report riêng cho performance.
