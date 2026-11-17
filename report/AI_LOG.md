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

## #3 – 2026-11-17 23:04 (giờ VN)
- **AI tool:** omp – sonic; Manager (openai-codex/gpt-6.1-sol)
- **Bước:** Task 1 – Bước 11
- **Prompt:**
  > Bước 11 – Thu thập thông tin phần cứng THẬT của máy test.
  > Chạy: hostname, lscpu, free -h, lsblk -d -o NAME,SIZE,ROTA,MODEL, uname -a, cat /etc/os-release. Nếu có screenfetch hoặc neofetch thì chạy thêm.
  > Ghi vào report/05_hardware.md một bảng spec: Hostname, OS, Kernel, CPU (model, số core/thread), RAM, Disk, Java, Node, JMeter. Mọi giá trị phải copy từ output lệnh.
  > Xong khi: bảng đầy đủ, hostname đúng như output của lệnh `hostname`.
- **AI output:**
  > Tạo report/05_hardware.md với bảng spec và output nguồn: hostname zinn-Nitro-AN515-57; i5-11400H, 6 core/12 thread, RAM 30 GiB, OS/kernel/disk và Java/Node/JMeter. Chưa có screenfetch/neofetch, chưa chụp ảnh. Manager đối chiếu bảng với output trong báo cáo. Không ghi số liệu tải giả; bối cảnh chung Phần B TASK1_PROMPTS.md được truyền kèm.
- **Human review:** _(để trống – người dùng tự điền)_

## #4 – 2026-11-17 23:04 (giờ VN)
- **AI tool:** omp – Design (openai-codex/gpt-6.1-terra)
- **Bước:** Task 1 – Bước 2 – Thiết kế kịch bản
- **Prompt:**
  > Bước 2 – Thiết kế 3 kịch bản Load / Stress / Spike cho Flow 1. CHỈ thiết kế, CHƯA tạo file .jmx.
  > Input: report/01_api_analysis.md. Máy test: 12 CPU core, 30 GB RAM. Backend Node.js chạy đơn luồng, dùng SQLite.
  > Với mỗi kịch bản, đề xuất kèm LÝ DO cụ thể:
  >   - Số thread (VU), ramp-up, thời lượng hoặc số vòng, think-time (loại timer và khoảng giá trị).
  >   - Load: tải bình thường. Stress: tăng bậc đến khi lỗi > 5% hoặc p95 > 2 giây. Spike: tăng vọt rồi hạ.
  >   - Assertion cho từng request: status code, kèm JSON assertion cho token/orderId/mảng. Lưu ý price string/number.
  >   - Cách xử lý lockout: thêm khoảng 5% request login SAI dùng nhóm tài khoản riêng perf291..perf300 (đặt trong Throughput Controller). Request này coi 401/403 là ĐÚNG. Luồng chính dùng perf001..perf290. Ghi rõ các bước reset giữa các lần chạy (reset_sut.sh hoặc chờ 180 giây).
  >   - Listener khác nhau cho mỗi plan: Load = Summary Report; Stress = Aggregate Report; Spike = Response Time Graph.
  >   - Giải thích ngắn: workflow phủ đủ 3 nhóm endpoint như thế nào.
  > Ghi vào report/02_test_design.md, kèm một bảng tổng hợp thông số.
  > Xong khi: có đủ 3 kịch bản, mỗi thông số đều có lý do, có mục lockout và mục listener.
  > Thông tin thực đã xác minh report/05_hardware.md: 6 physical cores, 12 logical threads (không phải 12 core), 30 GiB RAM. Dùng số thực này và ghi rõ sai lệch giả định trong prompt. Thiết kế cả property loops để smoke 1 vòng/2 vòng kết thúc thật, duration không khiến smoke treo; Stress tăng bậc có dấu thời gian để phân tích từng bậc và Spike thấp-cao-thấp thực tế, không chỉ đổi tên. Không đưa thêm phạm vi Soak ở bước này.
- **AI output:**
  > Tạo report/02_test_design.md với ba kịch bản, bảng thông số và lý do, assertion theo workflow, xử lý login sai/lockout và reset, listener riêng, lịch stress/spike cùng chế độ smoke loops. Đối chiếu thông số phần cứng với báo cáo; chưa tạo JMX hay chạy tải.
- **Human review:** _(để trống – người dùng tự điền)_

## #5 – 2026-11-17 23:06 (giờ VN)
- **AI tool:** omp – DataMonitor (openai-codex/gpt-6.1-terra)
- **Bước:** Task 1 – Bước 3 – Chuẩn bị dữ liệu và script giám sát tài nguyên
- **Prompt:**
  > Bước 3 – Chuẩn bị dữ liệu và script giám sát tài nguyên.
  > 1. Dữ liệu (data/). Đọc data/README.md trước. data/users.csv đã được sinh bằng scripts/gen_users.py, không tạo lại bằng tay.
  >    - users_main.csv: perf001..perf290 (cột email,password), lấy từ data/users.csv.
  >    - users_lock.csv: perf291..perf300 với mật khẩu SAI (ví dụ WrongPass1!).
  >    - products.csv: giữ nguyên các cột product_id,keyword,quantity. Thêm cột price và name, lấy từ GET /api/products thật (không tự đoán giá).
  >    - Mọi file CSV đều có header.
  >    - Viết code tách/sinh 2 file trên (users_main, users_lock) và cột price/name thành script (ví dụ thêm vào scripts/gen_users.py hoặc tạo scripts/gen_data.py), để chạy lại ra đúng kết quả. Cập nhật data/README.md nếu có gì thay đổi.
  > 2. Viết scripts/monitor_backend.sh <output.csv>:
  >    - Mỗi 1 giây ghi: timestamp, %CPU, RSS (MB) của tiến trình `node server.js` (tìm PID bằng `pgrep -f "^node server.js"`). Có thể dùng `ps -o %cpu=,rss= -p PID`.
  >    - Dừng khi nhận Ctrl+C hoặc khi tiến trình chết.
  > 3. Thử chạy monitor 5 giây và in ra vài dòng đầu.
  > Xong khi: có 3 file CSV với số dòng đúng (290 / 10 / 5), monitor chạy được và ghi ra CSV đúng định dạng.
  > Đọc report/02_test_design.md. Chỉ sửa/tạo scripts/gen_data.py (hoặc gen_users.py nếu phù hợp), scripts/monitor_backend.sh, data CSV, data/README.md, report/AI_LOG.md. Không sửa users.csv. Dữ liệu CSV đầu ra được sinh bởi script chạy thật; không tự ghi dữ liệu phỏng đoán. Không chạy smoke/5 giây kiểm tra trong coding agent: hoàn tất code rồi Manager giao sonic thực thi generator, kiểm tra dữ liệu và monitor một lần; chưa ghi claim kiểm tra đã pass. Giữ product_id/keyword/quantity đang có khi bổ sung price/name từ API. Script phải có self-check nhỏ cho input/output, không framework/tests dư thừa. File executable nếu cần.
- **AI output:**
  > Tạo scripts/gen_data.py tách tài khoản và bổ sung dữ liệu sản phẩm từ API, scripts/monitor_backend.sh ghi CPU/RSS theo thời gian; cập nhật data/README.md. Chưa chạy generator hoặc kiểm tra monitor; Manager sẽ thực hiện theo yêu cầu, nên chưa xác nhận dữ liệu hay kết quả giám sát.
  > Xác minh sau đó bởi sonic: generator chạy thật, kiểm tra CSV/API PASS với 290/10/5 dòng dữ liệu; monitor 5 giây kết thúc SIGINT exit 0, ghi 5 dòng tại results/monitor/step3_smoke.csv. Manager đọc CSV monitor, timestamp 23:07:59–23:08:03 +07, CPU 0.3%, RSS 80.60 MiB; không coi đây là số liệu load test.
- **Human review:** _(để trống – người dùng tự điền)_
