# Bước 0 – Môi trường

Kiểm tra ngày 2026-11-17 23:00 (+07, giờ Việt Nam).

| Công cụ | Phiên bản | Lệnh kiểm tra |
|---|---|---|
| Java | OpenJDK 25.0.5.0.3; build 25.0.5.0.3+1-1-26.04.1-Ubuntu | `java -version` |
| JMeter | Apache JMeter 5.6.3 | `jmeter --version` |
| Node.js | v22.22.1 | `node --version` |
| Git | 2.53.0 | `git --version` |

## Git

Đã khởi tạo repository tại thư mục `hw05`, nhánh `main`; không thay đổi repository lồng `eshop-sut`.

Output `git remote -v`:

```text
origin https://github.com/tzin1401/testing-hw05.git (fetch)
origin https://github.com/tzin1401/testing-hw05.git (push)
```

`.gitignore` chứa `eshop-sut/`, `results/server.log`, `*.log`. Chưa push.

## Kiểm tra SUT

Worker đã chạy thành công `./scripts/reset_sut.sh` trước kiểm tra API. Script restart backend và đăng ký tài khoản từ `data/users.csv`.

Manager kiểm tra trực tiếp:

| Kiểm tra | Lệnh | Kết quả thực tế |
|---|---|---|
| Danh sách sản phẩm | `curl -sS -o /tmp/hw05-step0-products.json -w 'products HTTP %{http_code}\n' http://localhost:3000/api/products` | HTTP 200 |
| Số sản phẩm | `jq '{count:length,ids:map(.id)}' /tmp/hw05-step0-products.json` | count = 5; ids = [1, 2, 3, 4, 5] |
| Đăng nhập | `curl -sS -X POST http://localhost:3000/api/login -H 'Content-Type: application/json' -d '{"email":"perf001@eshop.com","password":"Perf@001a"}' -w '\nHTTP %{http_code}\n'` | HTTP 200; có trường token không rỗng, không lưu token vào báo cáo |

JMeter in cảnh báo package scanning deprecated khi kiểm tra phiên bản; chưa chạy test plan nên chưa xác minh tương thích runtime Java/JMeter.

## Phân công và giới hạn

`sonic` thực hiện khởi tạo Git, `.gitignore`, kiểm tra phiên bản, reset và gọi API; dịch vụ worker lỗi trước khi ghi báo cáo. Manager hoàn tất tài liệu và xác minh các tiêu chí. Chưa tạo test plan, chưa chạy performance test, chưa tạo `.jtl`.

## Java 17 cho JMeter

Lượt smoke Java 17 được quan sát trong `/tmp/hw05-load-java17.log` ghi `java.version=17.0.21.0.3`. Để chọn runtime này cho các lần chạy JMeter tiếp theo:

```sh
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"
```

Phiên bản Java 25 ở bảng trên là kết quả kiểm tra môi trường ban đầu; việc chọn Java 17 không thay đổi kết quả lịch sử đó. Lượt Java 17 vẫn gặp lỗi cấu hình JSON extractor; xem `report/02a_load_smoke.md`.
