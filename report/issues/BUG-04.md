## Mô tả lỗi
`GET /api/products/{id}` trả `price` **kiểu khác nhau** tùy id: id lẻ là number, id chẵn là string. Code `server.js:162` cố ý chuyển `row.price` sang string khi `id % 2 === 0`. Client phải tự chuẩn hóa kiểu, dễ gây lỗi tính tiền phía frontend (ví dụ `"28000000" * 1` hoặc cộng chuỗi).

## Môi trường
- OS: Ubuntu 26.04 (Linux 7.0.0-43-generic), máy `zinn-Nitro-AN515-57`
- SUT: [ttbhanh/eshop-sut](https://github.com/ttbhanh/eshop-sut) commit `85af3ba`, backend Node.js v22.22.1 + SQLite
- URL: `http://localhost:3000`
- Công cụ: curl; SUT được reset bằng `scripts/reset_sut.sh` trước khi tái hiện
- Account test: không cần (endpoint công khai)

## Steps to reproduce
1. `curl http://localhost:3000/api/products/1`
2. `curl http://localhost:3000/api/products/2`
3. `curl http://localhost:3000/api/products` (so sánh với danh sách)

## Actual result
- id=1: `"price": 30000000` (number)
- id=2: `"price": "28000000"` (string)
- Danh sách `/api/products`: mọi `price` đều là number.

## Expected result
`price` luôn cùng một kiểu (number), thống nhất giữa danh sách và chi tiết, giống ví dụ body ở API spec mục 3.3. *Ghi chú: README FR-06 không quy định kiểu JSON; kỳ vọng này dựa trên tính nhất quán của API.*

## Evidence
```text
GET /api/products/1 -> price = 30000000      (int)
GET /api/products/2 -> price = '28000000'    (str)
```
Log đầy đủ: `results/repro/flow1_bugs_20261118.txt`.
