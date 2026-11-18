## Mô tả lỗi
`POST /api/checkout` lưu nguyên `total_amount` do client gửi lên, không tính lại từ giỏ hàng. Người dùng có thể mua sản phẩm 28.000.000 ₫ với tổng tiền **1 ₫**. Code: `server.js:297–307` lấy `total_amount` từ request body rồi `INSERT` thẳng vào bảng `orders`.

## Môi trường
- OS: Ubuntu 26.04 (Linux 7.0.0-43-generic), máy `zinn-Nitro-AN515-57`
- SUT: [ttbhanh/eshop-sut](https://github.com/ttbhanh/eshop-sut) commit `85af3ba`, backend Node.js v22.22.1 + SQLite
- URL: `http://localhost:3000`
- Công cụ: curl; SUT được reset bằng `scripts/reset_sut.sh` trước khi tái hiện
- Account test: `perf289@eshop.com` / `Perf@289a`

## Steps to reproduce
1. Đăng nhập, lấy token:
   ```bash
   TOKEN=$(curl -s -H 'Content-Type: application/json' -d '{"email":"perf289@eshop.com","password":"Perf@289a"}' http://localhost:3000/api/login | python3 -c 'import json,sys;print(json.load(sys.stdin)["token"])')
   ```
2. Thêm sản phẩm id=2 (giá 28.000.000) vào giỏ:
   ```bash
   curl -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"id":2,"name":"Samsung Galaxy S24 Ultra","price":28000000,"quantity":1}' http://localhost:3000/api/cart
   ```
3. Checkout với `total_amount = 1`:
   ```bash
   curl -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"total_amount":1,"shipping_address":"test"}' http://localhost:3000/api/checkout
   ```
4. Xem lịch sử đơn: `curl -H "Authorization: Bearer $TOKEN" http://localhost:3000/api/orders/my-orders`

## Actual result
Checkout `200 {"message":"Checkout successful","orderId":1}`; đơn hàng được lưu với `"total_amount":1`.

## Expected result
Theo README FR-08: "Backend phải tự tính lại tổng tiền; không chấp nhận giá trị `total_amount` do client gửi lên." Đơn phải có tổng **28.000.000** (tính từ giỏ) hoặc request bị từ chối.

## Evidence
```text
POST /api/cart      -> 200 {"message":"Added to cart"}
POST /api/checkout  -> 200 {"message":"Checkout successful","orderId":1}
GET  /api/orders/my-orders -> 200
[{"id":1,"user_id":291,"total_amount":1,"status":"pending","shipping_address":"test","created_at":"2026-11-18 07:12:46"}]
```
Log đầy đủ: `results/repro/checkout_cart_20261118.txt`.
