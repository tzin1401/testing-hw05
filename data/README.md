# Dữ liệu test (CSV)

Workflow được tham số hóa bằng CSV, theo yêu cầu Task 1 của đề.

| File | Nguồn | Dùng cho |
|---|---|---|
| `users.csv` | Sinh bằng `python3 scripts/gen_users.py` (300 tài khoản `perf001`–`perf300`, mật khẩu `Perf@NNNa`) | Script `reset_sut.sh` đăng ký các tài khoản này vào SUT |
| `users_main.csv` | `perf001`–`perf290`, tách ra từ `users.csv` | Login của luồng chính |
| `users_lock.csv` | `perf291`–`perf300` với mật khẩu **sai** | Kích hoạt lockout (khoảng 5% request), tách riêng để luồng chính không bị khóa |
| `products.csv` | `product_id` lấy theo 5 sản phẩm seed trong `eshop-sut/backend/database.js`; `price` và `name` lấy từ `GET /api/products` | Xem chi tiết sản phẩm, thêm vào giỏ, checkout |

Chạy backend trước, sau đó chạy `python3 scripts/gen_data.py`. Script đọc `users.csv`, tách 290 tài khoản chính và 10 tài khoản lockout (mật khẩu cố ý sai), rồi bổ sung `price` và `name` từ `GET http://localhost:3000/api/products` theo `product_id`; giữ nguyên `product_id`, `keyword`, `quantity` trong `products.csv`. Có thể chạy lại script sau khi SUT khởi động; script kiểm tra số lượng và dữ liệu đầu vào trước khi ghi.

Giám sát backend bằng `scripts/monitor_backend.sh <output.csv>`; mỗi giây ghi timestamp, CPU (%) và RSS (MiB), dừng bằng Ctrl+C hoặc khi tiến trình kết thúc. CPU là giá trị `%cpu` do `ps` cung cấp.

**Vì sao cần 300 user:**
- SUT chỉ seed sẵn 2 user, không đủ cho nhiều VU.
- Spike lên tới khoảng 300 VU.
- Mỗi lần restart backend, DB bị reset nên `reset_sut.sh` phải đăng ký lại các tài khoản này.
