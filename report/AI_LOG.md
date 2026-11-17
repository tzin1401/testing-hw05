# AI Audit Log

## #1 – 2026-11-17 23:00 (giờ VN)
- **AI tool:** omp – sonic (openai-codex/gpt-6-luna); Manager (openai-codex/gpt-6.1-sol)
- **Bước:** Task 1 – Bước 0 – Khởi tạo môi trường
- **Prompt:**
  > Bước 0 – Khởi tạo môi trường làm bài.
  > 1. Trong /home/zinn/zinn/testing/hw05, chạy `git init -b main` (nếu chưa có), rồi `git remote add origin https://github.com/tzin1401/testing-hw05.git` (nếu chưa có remote). Tạo .gitignore gồm: eshop-sut/, results/server.log, *.log.
  > 2. Kiểm tra và ghi lại phiên bản của: java, jmeter, node, git.
  > 3. Chạy scripts/reset_sut.sh. Xác nhận `curl -s localhost:3000/api/products` trả JSON có 5 sản phẩm, và login perf001@eshop.com / Perf@001a trả token.
  > 4. Ghi kết quả vào report/00_environment.md, dạng bảng: công cụ | phiên bản | lệnh kiểm tra.
  > Xong khi: có .gitignore, `git remote -v` hiện đúng origin, có report/00_environment.md với số phiên bản thật, SUT trả 200.
- **AI output:**
  > Đã khởi tạo Git nhánh main ở hw05, thêm origin đúng URL và tạo .gitignore. Worker chạy reset SUT rồi lỗi dịch vụ trước khi ghi tài liệu; Manager hoàn tất report/00_environment.md và entry này. Kiểm tra trực tiếp Java 25.0.5.0.3, JMeter 5.6.3, Node v22.22.1, Git 2.53.0; API products HTTP 200 có 5 sản phẩm; login tài khoản perf001 HTTP 200 có token. Không sửa SUT, không tạo .jtl, không push. Bối cảnh chung và quy tắc worker được truyền kèm theo TASK1_PROMPTS.md Phần B.
- **Human review:** _(để trống – người dùng tự điền)_

## #2 – 2026-11-17 23:04 (giờ VN)
- **AI tool:** omp – scout; Manager (openai-codex/gpt-6.1-sol)
- **Bước:** Task 1 – Bước 1
- **Prompt:**
  > Bước 1 – Phân tích API cho Flow 1 (chỉ đọc, không sửa file nào ngoài file báo cáo).
  > Đọc eshop-sut/backend/server.js, eshop-sut/api_specification.md, eshop-sut/README.md. Với từng endpoint của Flow 1, liệt kê:
  >   method, path, cần token hay không, request body, response mẫu (gọi thử bằng curl để lấy response thật), mã lỗi có thể xảy ra, truy vấn DB bên dưới (đọc hay ghi SQLite).
  > Sau đó chỉ ra:
  >   (a) Mỗi endpoint thuộc nhóm nào (Auth/Read/Transactional) và lý do.
  >   (b) Biến nào phải trích xuất để truyền giữa các request (token, user.id, product price, orderId...).
  >   (c) Các bẫy khi load test: lockout, price string/number, cart không xóa, SQLite khóa ghi, server đơn luồng.
  > Ghi kết quả vào report/01_api_analysis.md.
  > Xong khi: đủ 7 endpoint, mỗi endpoint có response thật lấy từ curl, có mục (a)(b)(c).
- **AI output:**
  > Scout đọc code/spec và phân tích tĩnh nhưng không có shell. Manager gọi thật workflow, chạy curl cho đủ 7 endpoint và tạo report/01_api_analysis.md: body, token, response thật, lỗi từ code, SQL, nhóm endpoint, biến liên kết và bẫy. Không sửa SUT. Bối cảnh chung theo Phần B TASK1_PROMPTS.md được truyền kèm.
- **Human review:** _(để trống – người dùng tự điền)_
