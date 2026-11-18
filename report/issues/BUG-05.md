## Mô tả lỗi
Mật khẩu người dùng được **lưu dạng plaintext** trong DB và **trả nguyên văn** trong response của `POST /api/login` (trường `user.password`). Code: `server.js:23–24` INSERT nguyên mật khẩu, dòng 46 so sánh plaintext, dòng 52 trả toàn bộ bản ghi user.

## Môi trường
- OS: Ubuntu 26.04 (Linux 7.0.0-43-generic), máy `zinn-Nitro-AN515-57`
- SUT: [ttbhanh/eshop-sut](https://github.com/ttbhanh/eshop-sut) commit `85af3ba`, backend Node.js v22.22.1 + SQLite
- URL: `http://localhost:3000`
- Công cụ: curl; SUT được reset bằng `scripts/reset_sut.sh` trước khi tái hiện
- Account test: `perf289@eshop.com` / `Perf@289a`

## Steps to reproduce
1. Gọi API đăng nhập:
   ```bash
   curl -s -H 'Content-Type: application/json' -d '{"email":"perf289@eshop.com","password":"Perf@289a"}' http://localhost:3000/api/login
   ```
2. Xem trường `user.password` trong response.

## Actual result
`200`, response chứa `"user": {"id":291, "email":"perf289@eshop.com", "password":"Perf@289a", ...}`.

## Expected result
Theo README SEC-01 (mục tham khảo bảo mật): "Mật khẩu **không** được lưu dưới dạng plaintext." Mật khẩu phải được hash (bcrypt/argon2) và **không bao giờ** xuất hiện trong response API.

## Evidence
```text
POST /api/login -> 200
user = {'id': 291, 'email': 'perf289@eshop.com', 'password': 'Perf@289a'}   (token đã lược bỏ)
```
Log đầy đủ: `results/repro/checkout_cart_20261118.txt`, dòng 1–2.
