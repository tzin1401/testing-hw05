## Mô tả lỗi
Tài khoản bị khóa ngay sau **2** lần đăng nhập sai (spec: 3 lần) và bị khóa khoảng **180 giây** (spec: 30 giây). Nguyên nhân trong code: mỗi lần sai bộ đếm cộng `+2` thay vì `+1` (`server.js:54`), thời gian khóa `180000` ms (`server.js:57`).

## Môi trường
- OS: Ubuntu 26.04 (Linux 7.0.0-43-generic), máy `zinn-Nitro-AN515-57`
- SUT: [ttbhanh/eshop-sut](https://github.com/ttbhanh/eshop-sut) commit `85af3ba`, backend Node.js v22.22.1 + SQLite
- URL: `http://localhost:3000`
- Công cụ: curl; SUT được reset bằng `scripts/reset_sut.sh` trước khi tái hiện
- Account test: `perf290@eshop.com` / `Perf@290a`

## Steps to reproduce
1. Đăng nhập sai lần 1:
   ```bash
   curl -i -H 'Content-Type: application/json' -d '{"email":"perf290@eshop.com","password":"WrongPass1!"}' http://localhost:3000/api/login
   ```
2. Lặp lại bước 1 (đăng nhập sai lần 2).
3. Đăng nhập với **mật khẩu đúng** `Perf@290a`.
4. Thử lại mật khẩu đúng sau ~35 giây và sau ~181 giây.

## Actual result
- Bước 1, 2: `401 {"error":"Invalid email or password"}`
- Bước 3 (mới sai 2 lần): `403 {"error":"Tài khoản đã bị khóa. Vui lòng thử lại sau."}`
- Sau ~35 s và ~179 s vẫn `403`; chỉ sau ~181 s mới `200`.

## Expected result
Theo README FR-02: mỗi lần sai tăng bộ đếm **đúng 1**; chỉ khóa khi sai **từ 3 lần trở lên** liên tiếp, khóa **30 giây**. Sau 2 lần sai, mật khẩu đúng phải đăng nhập được (`200`).

## Evidence
Response thật (tái hiện 2026-11-18):
```text
wrong1 401
wrong2 401
correct password -> 403 {"error":"Tài khoản đã bị khóa. Vui lòng thử lại sau."}
```
Log đầy đủ các mốc 35 s / 179 s / 181 s: `results/repro/flow1_bugs_20261118.txt` trong repo này.
