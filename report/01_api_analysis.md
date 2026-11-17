# Bước 1 – Phân tích API Flow 1

Nguồn tĩnh: `eshop-sut/backend/server.js`, `api_specification.md`, `README.md` (scout đọc). Manager xác minh workflow qua HTTP và chạy curl tuần tự cả bảy endpoint; response curl ngày 2026-11-17 23:03 +07 được trích dưới đây. Token được che trong tài liệu.

## Hợp đồng, phân nhóm và SQLite

| Method / path | Nhóm và lý do | Token | Request body | SQLite / lỗi từ code |
|---|---|---|---|---|
| POST `/api/login` | Auth: xác thực | Không | `{email,password}` | `SELECT * FROM users WHERE email = ?`; đúng: `UPDATE users SET login_attempts = 0, locked_until = NULL WHERE id = ?`; sai: `UPDATE users SET login_attempts = ?, locked_until = ? WHERE id = ?`. 401 sai tài khoản/mật khẩu, 403 đang khóa, 500 lỗi SELECT |
| GET `/api/products` | Read: danh sách sản phẩm | Không | Không | `SELECT * FROM products`; có `search`: `SELECT * FROM products WHERE name LIKE '%…%'`. Nhánh search có 500 lỗi DB; nhánh không search không xử lý err riêng |
| GET `/api/products/{id}` | Read: chi tiết sản phẩm | Không | Không | `SELECT * FROM products WHERE id = ?`. Không tìm thấy trả **200 `{}`**, không phải 404; không xử lý err riêng |
| POST `/api/cart` | Transactional: thêm trạng thái giỏ | Bearer | `{id,name,price,quantity}` | Không truy vấn DB, push vào mảng RAM; 401 thiếu token, 403 token sai |
| GET `/api/cart` | Transactional: kiểm tra trạng thái giỏ trong giao dịch | Bearer | Không | Không truy vấn DB; 401/403 như trên |
| POST `/api/checkout` | Transactional: tạo đơn | Bearer | `{total_amount,shipping_address}` | `INSERT INTO orders (user_id, total_amount, status, shipping_address) VALUES (?, ?, ?, ?)`; status `pending`. 401/403, 500 nếu INSERT lỗi |
| GET `/api/orders/my-orders` | Transactional: xác nhận đơn vừa tạo (thao tác DB là đọc) | Bearer | Không | `SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC`; 401/403, không xử lý err DB riêng |

Mã lỗi trên là kết luận từ code, không tuyên bố đã kích hoạt các lỗi bằng runtime ở bước này. Body JSON lỗi cú pháp còn có thể bị middleware JSON parser từ chối trước route.

## Response thật

Các JSON dưới đây trích response curl runtime; danh sách sản phẩm chỉ trích phần tử đầu và số phần tử, không giả làm toàn bộ response.

### 1. POST /api/login

Body `{"email":"perf002@eshop.com","password":"Perf@002a"}`:

```json
{"message":"Login successful","token":"<redacted; thực tế không rỗng>","user":{"id":4,"name":"Perf User 002","email":"perf002@eshop.com","password":"Perf@002a","role":"user","login_attempts":0,"locked_until":null,"reset_token":null,"shipping_address":null,"phone":null}}
```

### 2. GET /api/products

Response là mảng 5 phần tử; trích phần tử đầu:

```json
{"id":1,"name":"iPhone 15 Pro Max","price":30000000,"description":"Điện thoại cao cấp của Apple","imageUrl":"https://placehold.co/300x300/png?text=iPhone+15","category_id":1}
```

### 3. GET /api/products/2

```json
{"id":2,"name":"Samsung Galaxy S24 Ultra","price":"28000000","description":"Màn hình hiển thị xuất sắc, camera siêu zoom","imageUrl":"https://placehold.co/300x300/png?text=Samsung+S24","category_id":1}
```

### 4. POST /api/cart

Body `{"id":2,"name":"Samsung Galaxy S24 Ultra","price":28000000,"quantity":1}`:

```json
{"message":"Added to cart"}
```

### 5. GET /api/cart

```json
[{"id":2,"name":"Samsung Galaxy S24 Ultra","price":28000000,"quantity":1}]
```

### 6. POST /api/checkout

Body `{"total_amount":28000000,"shipping_address":"HW05 Flow 1 test address"}`:

```json
{"message":"Checkout successful","orderId":2}
```

### 7. GET /api/orders/my-orders

```json
[{"id":2,"user_id":4,"total_amount":28000000,"status":"pending","shipping_address":"HW05 Flow 1 test address","created_at":"2026-11-17 16:03:34"}]
```

## Trích xuất và truyền biến

- Login: `$.token` → `Authorization: Bearer ${token}`; `$.user.id` → đối chiếu chủ đơn.
- CSV chọn product ID và quantity; detail cung cấp id/name/price thật. Chuẩn hóa price số hay chuỗi bằng phép chuyển số có kiểm tra, không so sánh kiểu cứng.
- Cart dùng đúng sản phẩm của vòng hiện tại; `total_amount = price × quantity`, không lấy tổng giỏ tích lũy.
- Checkout: `$.orderId` → kiểm tra có đơn tương ứng trong my-orders, đúng user và total_amount.

## Bẫy cần thiết kế

- Login sai cộng 2; lần sai thứ hai đặt khóa 180 giây nhưng response lần đó vẫn 401; lần tiếp trong thời gian khóa trả 403. Tách perf291..perf300 khỏi tài khoản luồng chính.
- Giá detail ID chẵn là string; ID lẻ number. List vẫn trả số trong response quan sát.
- `userCarts` lưu RAM, mỗi POST append, checkout không xóa. Đây là tăng giữ dữ liệu theo số thao tác; chưa đo RAM nên chưa kết luận độ dốc/ceiling.
- SQLite có ghi từ login và checkout: tranh chấp ghi là rủi ro cần đo, không coi SQLITE_BUSY là lỗi đã quan sát.
- Callback Express chạy trên event loop Node trong một process của script reset; I/O SQLite bất đồng bộ, không đồng nghĩa mọi công việc hệ thống chỉ dùng một thread. Chưa đo điểm bão hòa.
- Reset bằng `scripts/reset_sut.sh` trước mỗi lần chạy: restart xóa DB/giỏ RAM và seed lại tài khoản; không chỉ đợi hết 180 giây vì bộ đếm sai còn tồn tại.

## Tái lập bằng curl

```bash
TOKEN=$(curl -fsS -X POST localhost:3000/api/login -H 'Content-Type: application/json' -d '{"email":"perf001@eshop.com","password":"Perf@001a"}' | jq -r .token)
curl -fsS localhost:3000/api/products
curl -fsS localhost:3000/api/products/2
curl -fsS -X POST localhost:3000/api/cart -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"id":2,"name":"Samsung Galaxy S24 Ultra","price":28000000,"quantity":1}'
curl -fsS localhost:3000/api/cart -H "Authorization: Bearer $TOKEN"
curl -fsS -X POST localhost:3000/api/checkout -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"total_amount":28000000,"shipping_address":"HW05 Flow 1 test address"}'
curl -fsS localhost:3000/api/orders/my-orders -H "Authorization: Bearer $TOKEN"
```

Block trên dùng perf001 để tái lập; lần lấy response curl trong báo cáo dùng perf002 (cùng mật khẩu theo mẫu). ID đơn và thời điểm thay đổi theo lần chạy. Không reset giữa các request của workflow.
