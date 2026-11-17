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

## #6 – 2026-11-17 23:11 (giờ VN)
- **AI tool:** omp – LoadPlan (openai-codex/gpt-6.1-terra)
- **Bước:** Task 1 – Bước 4 – Tạo test plan Load
- **Prompt:**
  > Bước 4 – Tạo test plan LOAD cho JMeter 5.6.3 theo report/02_test_design.md.
  > File: test-plans/23120190_Load_<YYYYMMDD>.jmx (lấy ngày bằng `date +%Y%m%d`).
  > Plan phải có:
  >   - User Defined Variables: HOST=localhost, PORT=3000. Có HTTP Request Defaults.
  >   - Số thread, ramp-up, thời lượng phải đọc từ property: ${__P(threads,<mặc định>)}, ${__P(rampup,..)}, ${__P(duration,..)}, để có thể override bằng -J khi smoke test.
  >   - CSV Data Set Config: data/users_main.csv và data/products.csv, đường dẫn tương đối so với thư mục hw05.
  >   - Đủ 7 request của Flow 1, đúng thứ tự.
  >   - JSON Extractor: $.token và $.user.id từ login; $.orderId từ checkout.
  >   - HTTP Header Manager: Content-Type: application/json, và Authorization: Bearer ${token} cho các request cần token.
  >   - Assertion theo thiết kế ở bước 2.
  >   - Think-time theo thiết kế.
  >   - Throughput Controller khoảng 5% cho login sai, dùng data/users_lock.csv. Assertion chấp nhận 401/403.
  >   - total_amount gửi lên = price × quantity của đúng sản phẩm trong vòng lặp hiện tại. KHÔNG cộng dồn theo giỏ hàng, vì giỏ hàng không bao giờ bị xóa.
  >   - Listener DUY NHẤT: Summary Report.
  > Kiểm tra cú pháp: chạy `jmeter -n -t <file> -Jthreads=1 -l /tmp/check.jtl` với 1 thread, 1 vòng. Xem log có lỗi không, rồi xóa /tmp/check.jtl.
  > Xong khi: file mở được, chạy 1 vòng không có lỗi parse, tất cả sampler đều pass.
  > Chỉ tạo Load .jmx và ghi AI_LOG; không chạy JMeter trong coding agent. Manager giao sonic smoke sau. Đọc report/02_test_design.md, dùng loops property rõ ràng: smoke -Jloops=1 kết thúc 1 vòng, threads/rampup/duration override. Mặc định đo theo thời gian 50VU/50s/600s. Không hardcode CSV absolute path. Main account chọn một lần/VU, độc quyền đang chạy, không đọc user mới mỗi iteration. Vẫn phải dùng CSV Data Set Config main/products; dùng Once Only Controller hoặc cấu hình iteration đúng để giữ main email/password; không tạo CSV phụ ngoài yêu cầu. Chú ý JMeter CSV configs có thể chạy mỗi vòng dù scope Once Only: xác minh implementation đúng, nếu cần init pool một lần bằng JSR223 đọc CSV nhưng phải giữ CSV Config thực sự cung cấp main data (không config chết). Lock CSV riêng, negative sampler phải nhận 401/403 là success, Throughput 5%. Negative branch không ghi đè main token, đặt sau login chính nhưng không đổi thứ tự 7 request chính. Per-request meaningful JSON assertions, dependencies skip on failed prerequisite, reset variables mỗi vòng, convert price string/number and total numeric. Uniform timer chỉ trước requests 2..7, không trước login sai. Main smoke không nhất thiết chọn negative; cho property lock_percent=100 để kiểm tra riêng âm khi smoke (mặc định5). Dùng response/connect timeout hữu hạn. Không thêm script generator JMX hay abstraction chưa cần.
- **AI output:**
  > Tạo test-plans/23120190_Load_20261117.jmx theo Flow 1 và thiết kế Load; chưa chạy JMeter hay xác nhận sampler pass, để Manager kiểm tra smoke theo yêu cầu.
- **Human review:** _(để trống – người dùng tự điền)_

## #7 – 2026-11-17 23:14 (giờ VN)
- **AI tool:** omp – FixExtractor (openai-codex/gpt-6.1-terra)
- **Bước:** Task 1 – Bước 4 – Sửa test plan Load
- **Prompt:**
  > Bước 4 chưa hoàn tất, sửa file test-plans/23120190_Load_20261117.jmx. Smoke trên Java17 lỗi ArrayIndexOutOfBoundsException trong JSONPostProcessor.getMatchNumbersAsInt trước sample, log /tmp/hw05-load-java17.log. Đọc log và xác minh field chính xác của JSONPostProcessor JMeter5.6.3 từ installed jar javap/source, không đoán hay chạy lại test để xác nhận lỗi. Sửa cấu hình extractor token/user.id/orderId đúng native keys/delimiters; giữ workflow/params. Không chạy JMeter, Manager giao sonic sau. Nếu CSV main mỗi iteration hiện vẫn tiêu thụ dòng nhưng giữ account cố định, có thể để reviewer nêu ở bước5, không thêm abstraction. Append AI_LOG entry riêng () với bằng chứng lỗi và sửa, không sửa/xóa entry cũ. Append report/02a_load_smoke.md mô tả nguyên nhân/sửa (chưa claim pass); append report/00_environment.md hướng dẫn dùng JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64, version thực 17.0.21.0.3 được sonic quan sát. Không sửa hardware report lịch sử. Dùng edit mọi file cũ.
- **AI output:**
  > Đọc log Java 17: lỗi ArrayIndexOutOfBoundsException tại getMatchNumbersAsInt khi xử lý 01 Login, summary 0 sample. Đối chiếu javap JMeter 5.6.3: defaultValues được split bằng dấu chấm phẩy, giá trị cũ `;` tạo mảng rỗng trong khi match_numbers có hai phần tử. Sửa default của extractor login thành `NOT_FOUND;NOT_FOUND` và checkout thành `NOT_FOUND`, giữ native keys, JSONPath, match và workflow. Append nguyên nhân vào report/02a_load_smoke.md và hướng dẫn Java 17 vào report/00_environment.md. Chưa chạy lại JMeter, chưa xác nhận pass.
- **Human review:** _(để trống – người dùng tự điền)_

## #8 – 2026-11-17 23:21 (giờ VN)
- **AI tool:** omp – Reviewer (anthropic/claude-sonnet-5-5)
- **Bước:** Task 1 – Bước 5 – Review độc lập test plan Load
- **Prompt:**
  > Bước 5 – Review độc lập test plan LOAD (test-plans/23120190_Load_*.jmx). Đối chiếu với report/02_test_design.md và eshop-sut/backend/server.js.
  > Kiểm tra và liệt kê từng lỗi theo mẫu: [mức độ] vị trí – vấn đề – cách sửa. Cần kiểm tra:
  >   - Ramp-up và think-time có thực tế không; số thread có hợp lý không.
  >   - Assertion có yếu không (chỉ kiểm tra 200 là yếu). Có xử lý được price string/number không.
  >   - Xử lý lockout có đúng không: tài khoản sai có tách riêng không, 401/403 có được coi là đúng không.
  >   - Extractor và header có đúng không; Authorization có bị thiếu ở request nào không.
  >   - Đường dẫn CSV, Sharing mode, Recycle.
  >   - total_amount có bị cộng dồn sai không.
  >   - Listener có đúng duy nhất Summary Report không.
  > Ghi vào report/03_review_load.md. KHÔNG sửa file .jmx.
  > Xong khi: mỗi lỗi có vị trí cụ thể và cách sửa; có kết luận PASS hoặc NEEDS FIX.
  > Điểm đã biết cần xét: CSV main tiêu thụ mỗi iteration nhưng account_email cố định; pool fallback đọc file. Kiểm tra việc này gây consumer-visible lỗi thực hay chỉ lệch thiết kế, tránh đòi abstraction dư. Xem response assertions, stop dependencies, token default NOT_FOUND. Không sửa JMX; mỗi finding phải có dòng/cách sửa và evidence. Có quyền viết thì chỉ report/03_review_load.md và append AI_LOG; không có thì trả nguyên nội dung để Manager ghi.
- **AI output:**
  > Đọc JMX, 02_test_design.md, 02a_load_smoke.md và server.js; tạo report/03_review_load.md, kết luận NEEDS FIX. 3 lỗi Medium: (1) thiếu HTTPSampler.use_keepalive nên mọi request gửi Connection: close (đối chiếu javap ApacheJMeter_http.jar 5.6.3: mặc định false); (2) assertion 05 Get cart khớp phần tử cũ vì giỏ không bị xóa, nên dùng phần tử cuối; (3) login thất bại thì vòng lặp quay lại không có think-time. Thêm 2 lỗi Low (switch assertion không có default; assertion không đối chiếu biến extractor), các mục Info. Pool account: không phải lỗi người dùng nhìn thấy, chỉ lệch thiết kế, không đòi abstraction. Không sửa JMX/SUT, không chạy test, không tạo .jtl; chưa chạy 50 VU nên các nhận định tải đánh dấu [INFERENCE].
- **Human review:** _(để trống – người dùng tự điền)_

## #9 – 2026-11-17 23:22 (giờ VN)
- **AI tool:** omp – CorrectLoad (openai-codex/gpt-6.1-terra)
- **Bước:** Task 1 – Bước 6 – Sửa test plan Load
- **Prompt:**
  > Bước 6 – Sửa test plan LOAD theo report/03_review_load.md.
  > Với mỗi lỗi: sửa xong thì ghi vào cuối report/03_review_load.md, mục "Đã sửa": lỗi gì – đã sửa thế nào – vì sao AI (bước 4) bỏ sót (do prompt / giới hạn model / đặc điểm endpoint).
  > Sau khi sửa: chạy lại smoke test 1 thread 1 vòng.
  > Xong khi: mọi lỗi mức độ cao đã được sửa, smoke test pass.
  > Sửa mọi Medium và Low cụ thể trong report/03_review_load.md: keepalive tất cả8 sampler, kiểm tra cart phần tử cuối với exclusive per-user, pause khi login thất bại không tạo HTTP sample, default switch fail, đối chiếu token/user_id/order_id extractor. Đừng biến pool tài khoản thành abstraction mới; reviewer kết luận đây chỉ lệch thiết kế không consumer-visible. Append mục Đã sửa có lý do AI bỏ sót, không sửa các finding gốc; ghi rõ cwd hw05 và Java17 cho command. Không chạy smoke trong coding agent: Manager giao sonic chạy sau. Append report/02a_load_smoke.md nói /tmp/hw05-load-fixed.jtl và negative.jtl đã được xóa sau trích bằng chứng theo yêu cầu bước4, giữ nguyên kết quả cũ. Không claim pass cho bản mới trước runtime.
- **AI output:**
  > Sửa test-plans/23120190_Load_20261117.jmx theo các lỗi Medium và Low; append mục Đã sửa và lệnh smoke Java 17 vào report/03_review_load.md, bổ sung thông tin xóa JTL cũ vào report/02a_load_smoke.md. Không thay pool, không chạy smoke trong coding agent; chưa xác nhận plan mới pass.
- **Human review:** _(để trống – người dùng tự điền)_

## #10 – 2026-11-17 23:30 (giờ VN)
- **AI tool:** omp – Manager (openai-codex/gpt-6.1-sol); task workers StressSpike và BuildStressSpike chưa tạo file
- **Bước:** Task 1 – Bước 7 – Sinh Stress và Spike
- **Prompt:**
  > Bước 7 – Tạo test plan STRESS và SPIKE, dùng Load plan đã sửa làm gốc.
  > - test-plans/23120190_Stress_<YYYYMMDD>.jmx: tăng tải theo bậc, đúng như report/02_test_design.md (dùng nhiều Thread Group nối tiếp, hoặc tham số -J). Listener DUY NHẤT: Aggregate Report.
  > - test-plans/23120190_Spike_<YYYYMMDD>.jmx: tải nền thấp → tăng vọt trong vài giây → hạ về mức nền. Listener DUY NHẤT: Response Time Graph.
  > - Giữ nguyên workflow, CSV, extractor, assertion và cách xử lý lockout của Load plan.
  > - Smoke test mỗi plan với 1 thread 1 vòng.
  > Xong khi: có 2 file .jmx đúng tên, smoke test pass, 3 plan dùng 3 listener khác nhau.
- **AI output:**
  > Hai worker không tạo được file; Manager tái sử dụng cây XML của Load đã sửa, ghi hai JMX Stress/Spike đúng ngày date. Stress có 4 nhóm nối tiếp, gate nội bộ không ghi sample đánh giá error/p95 trước bậc tiếp, pool tài khoản riêng từng bậc và summary; Spike có nhóm nền/burst đồng thời chia sẻ pool. Giữ workflow, assertion, keepalive và lockout. Giao sonic chạy smoke 1VU, toàn bậc Stress và compressed Spike. Chưa xác nhận runtime pass, chưa chạy tải thật.
- **Human review:** _(để trống – người dùng tự điền)_

## #11 – 2026-11-17 23:45 (giờ VN)
- **AI tool:** omp – Reviewer (anthropic/claude-sonnet-5-5)
- **Bước:** Task 1 – Bước 8 – Review độc lập test plan Stress và Spike
- **Prompt:**
  > Bước 8 – Review độc lập test plan STRESS và SPIKE, dùng cùng checklist với report/03_review_load.md. Kiểm tra thêm:
  >   - Các bậc tải Stress có đủ cao để chạm điểm gãy không.
  >   - Spike có thật sự tăng vọt không: ramp-up phải vài giây, không phải vài phút.
  >   - Tổng thời gian chạy của mỗi plan có hợp lý không.
  >   - Khi tải cao, lockout có làm hỏng luồng chính không.
  > Ghi vào report/04_review_stress_spike.md. KHÔNG sửa file .jmx.
  > Xong khi: mỗi plan có danh sách lỗi và kết luận riêng.
  > Đọc report/04a_stress_spike_initial_smoke.md: smoke7/7 mỗiplan, Stress4stage28samples, Spike compressed low/high/low, stopgate Java17 đã quan sát. Đọc các plan và Load đã sửa, thiết kế, server code. Kiểm tra property runtime JMeter (__groovy, num_threads=0 smoke, scheduler/delay/duration), pool namespaces Stress riêngstage/Spikechung, failure gate assertion state, one ResultCollector listener each. Nêu lỗi observable với evidence, không scope creep. Report/04_review_stress_spike.md, AI_LOG append only, kết luận mỗiplan riêng. Không sửa plans, không kiểm tra lại runtime.
- **AI output:**
  > Đọc hai JMX, Load đã sửa, 02_test_design.md, 04a, 03_review_load.md, server.js, database.js, JTL/log smoke có sẵn; chỉ phân tích tĩnh, không chạy JMeter, không sửa JMX/SUT/JTL. Stress: NEEDS FIX. Lỗi High #S1: `props.get('threads','N')` ở stage 2–4 là `DefaultGroovyMethods.get(Map,K,V)` (đối chiếu javap Groovy 3.0.20) nên ghi default vào props; chạy mặc định (không `-Jthreads`) bậc 3 và 4 chỉ 100 VU thay vì 200/290, smoke không thấy vì luôn truyền `-Jthreads=1` (đánh dấu [INFERENCE], chưa chạy). Lỗi Low #S2: tên timer "500–1500 ms" nhưng giá trị 250–750 ms. Info: chưa có số đo để kết luận có chạm điểm gãy, tổng 600 s hợp lý, gate đếm lỗi đúng (`finally` + AssertionResult), `STRESS_STAGE_SUMMARY` không chạy khi gate dừng test (log stop-gate). Spike: PASS; ramp 5 s, 120/120/120 s, pool chung 200 ≤ 290, một listener; ghi chú Low `props.get` cùng mẫu (vô hại) và Info đỉnh ~230 req/s thấp hơn Stress. Lockout không làm hỏng luồng chính (main account chỉ gửi mật khẩu đúng, khóa theo từng user). Ghi nhận: công cụ ghi file (write/edit) không có trong phiên này nên báo cáo và entry log này được soạn ở local://04_review_stress_spike.md và local://AI_LOG_entry_11.md để Manager sao chép vào report/ và append vào report/AI_LOG.md.
- **Human review:** _(để trống – người dùng tự điền)_

## #12 – 2026-11-17 23:45 (giờ VN)
- **AI tool:** omp – FixStressSpike (openai-codex/gpt-6.1-terra)
- **Bước:** Task 1 – Bước 9 – Sửa Stress và Spike
- **Prompt:**
  >  Bước 9 – Sửa STRESS và SPIKE theo report/04_review_stress_spike.md. Ghi mục "Đã sửa" giống bước 6. Chạy smoke test lại cho cả 2 plan.
  > Xong khi: mọi lỗi mức độ cao đã được sửa, smoke test pass.
  > Sửa #S1 High, #S2 Low và #P1 Low theo review trong2JMX Stress/Spike. Đổi mọi props.get(key,default) (hai args) sang props.getProperty, giữ props.get(key) cho object state. Sửa Stress timer testname250–750ms. Cùng pattern có ở Load ThreadGroup.scheduler dùngprops.get('loops','-1'): sửa cùng một dòng này trong Load đểkhông đểpatternlỗi còn caller. Không thay workflow/lịch/count. Append report/04_review_stress_spike.md mục Đã sửa: lỗi/sửa/lýdo AI bỏsót (Manager sinh sai do hiểu nhầm Groovy Map.get overload; smoke chỉoverride threads). Ghi rõ bản mới chưa smoke. Runtime Manager giao sonic sau, không chạy JMeter. Không sửa review finding gốc. Append AI_LOG đúng format và timestamp thực.
- **AI output:**
  > Sửa #S1, #S2 và #P1 trong Stress/Spike, sửa scheduler Load cùng mẫu và append mục Đã sửa vào report/04_review_stress_spike.md. Không chạy JMeter; bản mới chưa được smoke, chưa xác nhận pass.
- **Human review:** _(để trống – người dùng tự điền)_
## #13 – 2026-11-17 23:52 (giờ VN)
- **AI tool:** omp – FinalSmoke (openai-codex/gpt-6-luna)
- **Bước:** Task 1 – Bước 10 – Smoke test cả 3 plan
- **Prompt:**
  > Bước 10 – Smoke test cả 3 plan với tải nhỏ (5 thread, 2 vòng). Chạy reset_sut.sh trước MỖI plan.
  > Lệnh: jmeter -n -t <plan> -Jthreads=5 -l results/smoke/<tên>.jtl
  > Báo cáo: số sample, % lỗi, và lỗi theo từng request (đọc từ .jtl). KHÔNG sửa plan. Nếu có lỗi thì báo lại cho Manager.
  > Xong khi: cả 3 plan chạy hết; % lỗi của luồng chính = 0 (không tính request login sai cố ý).
  > Bổ sung -Jloops=2 -Jrampup=1 để chạy đúng 2 vòng thay vì lịch tải; file results/smoke/23120190_{Load|Stress|Spike}_20261117.jtl, đặt -j results/smoke/<tên>_jmeter.log riêng để có runtime log chứ không chỉ console. Reset trước mỗi plan, chạy tuần tự, timeout120s mỗi plan. Đọc samples/errors per label từ JTL thật; kỳvọng70 main samples/plan (5*2*7), negative cóthể0 theo controller rounding. Nếu lỗi báo Manager và không sửa plan; cóthể chạy cácplan còn lại vì từngrun độc lập sau reset. Tạo report/05a_all_plans_smoke.md với command table/per-label main count/errors và negative counts/codes riêng; đọc parse/scripting errors JMeter runtime logs. Append AI_LOG entry bước10 đúngtimestamp, prompt nguyênvăn bỏ Ghi vào log, Human review trống; không viết entry bước12 vì do người dùng. Không chạy tải thật, không HTML reports bước13.
- **AI output:**
  > Chạy tuần tự Load, Stress, Spike; reset SUT trước mỗi plan, không sửa JMX. Mỗi JTL có 70 samples, 0 errors (0%); 7 workflow label đều 10 samples/0 errors, negative login 0 sample. Runtime logs không cho thấy lỗi parsing/scripting. Tạo report/05a_all_plans_smoke.md; cả ba smoke pass.
- **Human review:** _(để trống – người dùng tự điền)_

## #14 – 2026-11-18 00:46 (giờ VN)
- **AI tool:** omp – RunLoad (openai-codex/gpt-6-luna)
- **Bước:** Task 1 – Bước 13 – Chạy thật plan LOAD
- **Prompt:**
  > Bước 13 – Chạy thật plan LOAD (mỗi lần giao chỉ chạy 1 plan).
  > 1. Chạy scripts/reset_sut.sh. Ghi các bước reset vào report/07_run_log.md, kèm thời điểm thực hiện.
  > 2. Chạy song song: scripts/monitor_backend.sh results/monitor/<tên>.csv
  > 3. Chạy: jmeter -n -t test-plans/23120190_Load_20261117.jmx -l results/jtl/<tên>.jtl -e -o results/html/<tên>/
  > 4. Dừng monitor. Ghi vào report/07_run_log.md: thời gian bắt đầu/kết thúc, lệnh đã chạy, số sample, % lỗi, avg/p90/p95/p99, throughput, CPU và RAM tối đa của backend.
  > Mọi số phải lấy từ results/html/<tên>/statistics.json và file monitor CSV. Không ước lượng.
  > 5. Nếu có lockout xảy ra: ghi lại mã lỗi và số lần, rồi ghi cách đã reset.
  > Xong khi: có .jtl, thư mục HTML và CSV monitor của plan; run log có số liệu kèm nguồn trích.
  > Chi tiết thực thi: jmx test-plans/23120190_Load_20261117.jmx (không đổi ngày tên plan đãtạo). Kếtquả basename23120190_Load_$(date +%Y%m%d), nếu outputđãtồn tại dùng timestamp suffix đừng xóa/ghiđè kếtquả trước. Trước bất kỳrun: ghi thời gian dateVN và reset_sut. Tạo dirs results/jtl,results/html,results/monitor. Chạy monitor output CSV basename tươngứng, giữ PID, trap dừngmonitor khi JMeter kếtthúc/lỗi. Chạy JMeter KHÔNG override threads/rampup/duration/loops: mặcđịnh50VU ramp50s tổng600s, -l -e -o đúngyêu cầu, -j results/<basename>_jmeter.log, console tee results/23120190_Load_console.log (log là outputprogram, shell redirect đượcphép khôngcodeedit). Timeout đủ khoảng900s, không tự rútngắn. Bắt stdout/progress thật, đừng đểpipeline tee làm mất exitcode setpipefail. Sau test dừngmonitor, đọcthậtJTL vàHTML statistics.json, count primary/negative riêng, mã401/403, negative success, mainerrors; tínhcpu/rSS max từCSV và nóiCPU ps là lifetime average sampled không phải instantaneouspeak. Mọiavg/p90/p95/p99/throughput lấy statistics.json exactfields, nêu units. Source report/07_run_log.md có start/end/reset times/commands/errors vàcácmetricsnguồn. Append AI_LOG bước13Load đúngtimestamp/prompt(đãthayLOAD), modelactual, Humanreviewtrống. Khôngtựđiềnreview hoặc commitusersfiles. Nếu HTML generation lỗi, giữJTL/CSV vàbáoerror thật không claimđủ; không chạy lại tải chỉđểтạoHTML (cóthể dùngjmeter -g existingJTL đểgenerateHTML saufixruntime nếu khôngсửaJTL). Cuối lượt báođủartifact paths vàtrạngthái, дừngчờManager yêu cầungười dùngchụpảnh. Khôngч chạyplan thứ2.
- **AI output:**
  > Đã reset SUT, chạy duy nhất LOAD plan với monitor đồng hành; hoàn tất thành công, sinh JTL, HTML report và CSV monitor. Báo cáo số liệu thực trong report/07_run_log.md, phân tách main/negative login và mã HTTP, kèm nguồn statistics.json/CSV. Không sửa plan/SUT, không chạy plan khác.
- **Human review:** 

## #15 – 2026-11-18 01:11 (giờ VN)
- **AI tool:** omp – FinishStressReport (openai-codex/gpt-6-luna)
- **Bước:** Task 1 – Bước 13 – Chạy thật plan STRESS
- **Prompt:**
  > Bước 13 – Chạy thật plan STRESS (mỗi lần giao chỉ chạy 1 plan).
  > 1. Chạy scripts/reset_sut.sh. Ghi các bước reset vào report/07_run_log.md, kèm thời điểm thực hiện.
  > 2. Chạy song song: scripts/monitor_backend.sh results/monitor/<tên>.csv
  > 3. Chạy: jmeter -n -t test-plans/23120190_Stress_20261117.jmx -l results/jtl/<tên>.jtl -e -o results/html/<tên>/
  > 4. Dừng monitor. Ghi vào report/07_run_log.md: thời gian bắt đầu/kết thúc, số sample, % lỗi, avg/p90/p95/p99, throughput, CPU/RAM backend; metrics không ước lượng.
  > 5. Ghi lockout nếu có. Xong khi có JTL, HTML, monitor CSV và run log có nguồn.
  > Run thực tế đã reset 00:58:12+07, bắt đầu 00:58:19, kết thúc 01:08:21. Không chạy lại Stress hoặc Load. HTML báo outputdir already exists là ground truth; không ghi đè/xóa HTML cũ, inspect trạng thái cũ. Generate offline `jmeter -g <existingJTL> -o results/html/23120190_Stress_20261118_recovered/` với `-j` log mới (suffix nếu cần), không mkdir leaf trước; report-only, không reset SUT/monitor. Đọc statistics Total, CSV giám sát và JTL labels/codes. Tính per-stage VU50/100/200/290, thời gian thực, main samples/errors/p95/RPS; bỏ 30s ramp, nêu gate all-stage khác stable window. Tìm highest stable VU đạt error<=5%, p95<=2000ms; phân biệt max observed stable và breakpoint chưa đạt. Append run log mục Stress, không chạm Load; exact commands/time/env/reset/output failure/recovery/sources. Append AI_LOG Bước 13 Stress theo TASK1_PROMPTS Phần B+C, bỏ cụm Ghi vào log; nêu Report Recovery thực tế, model actual, timestamp dateVN, không đổi Human review. CPU ps lifetime sampled, không instantaneous peak; RSS MiB. Báo evidence/artifacts/higher stable load. Không chạy Spike/Soak.
- **AI output:**
  > Bảo toàn HTML output cũ sau lỗi directory tồn tại; tạo report offline thành công từ JTL hiện có. Append report/07_run_log.md mục Stress với statistics, phân loại sample/codes, monitor và từng stable stage; tất cả bốn bậc tới 290 VU đạt gate, max observed 290 VU nhưng breakpoint chưa chạm. Append prompt chính xác vào TASK1_PROMPTS.md và entry này; không rerun tải, không chạy Load/Spike/Soak.
- **Human review:** 
