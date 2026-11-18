## Mô tả lỗi
Sau khi checkout thành công, giỏ hàng **không được xóa**: `GET /api/cart` vẫn trả sản phẩm vừa mua. Giỏ lưu trong biến RAM `userCarts` (`server.js:14`), và handler checkout (`server.js:297–309`) không xóa nó.

## Môi trường
- OS: Ubuntu 26.04 (Linux 7.0.0-43-generic), máy `zinn-Nitro-AN515-57`
- SUT: [ttbhanh/eshop-sut](https://github.com/ttbhanh/eshop-sut) commit `85af3ba`, backend Node.js v22.22.1 + SQLite
- URL: `http://localhost:3000`
- Công cụ: curl; SUT được reset bằng `scripts/reset_sut.sh` trước khi tái hiện
- Account test: `perf289@eshop.com` / `Perf@289a`

## Steps to reproduce
1. Thực hiện bước 1–3 như issue #2 (login → thêm sản phẩm id=2 → checkout).
2. Gọi lại giỏ hàng:
   ```bash
   curl -H "Authorization: Bearer $TOKEN" http://localhost:3000/api/cart
   ```

## Actual result
`200 [{"id":2,"name":"Samsung Galaxy S24 Ultra","price":28000000,"quantity":1}]`: sản phẩm đã thanh toán vẫn nằm trong giỏ.

## Expected result
Theo README FR-08: "Sau thanh toán thành công, giỏ hàng được xóa." `GET /api/cart` phải trả `[]`.

## Evidence
```text
POST /api/checkout -> 200 {"message":"Checkout successful","orderId":1}
GET  /api/cart     -> 200 [{"id":2,"name":"Samsung Galaxy S24 Ultra","price":28000000,"quantity":1}]
```
Log đầy đủ: `results/repro/checkout_cart_20261118.txt`. Ảnh hưởng dưới tải (RAM backend tăng chậm trong Soak 12 phút): `report/08_endurance.md`.
