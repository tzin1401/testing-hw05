# Bước 25 – Đánh giá các đề xuất tối ưu trong `11_ai_analysis.md`

## 1. Phạm vi và giới hạn

- Đối tượng: 7 đề xuất ở mục "Đề xuất tối ưu" của `report/11_ai_analysis.md` (§1–§7). Analyst đã ghi: "tôi không đọc mã hoặc schema", mọi `<...>` là chỗ trống phải thay bằng schema thật, và mọi cải thiện đều "chưa định lượng". Vì vậy không đề xuất nào bị coi là hallucinated chỉ vì thiếu số hay thiếu tên bảng. Chỉ phân loại HALLUCINATED khi tiền đề của đề xuất sai với code thật.
- Đối chiếu với: `eshop-sut/backend/server.js`, `database.js`, `package.json`, `node_modules/sqlite3` (driver thực), `scripts/reset_sut.sh`, `scripts/monitor_backend.sh`, JMX Soak.
- **Chưa chạy gì để kiểm tra hiệu quả.** Không benchmark, không `EXPLAIN QUERY PLAN`, không `PRAGMA`, không sửa SUT, không chạy JMeter. "Khả thi tĩnh" (áp dụng được vào code) không chứng minh có bottleneck, và không chứng minh có cải thiện.
- Ba mức khác nhau được tách riêng trong từng mục:
  - (a) áp dụng được cho code hiện tại không;
  - (b) khả thi nếu đổi kiến trúc;
  - (c) có nhắm đúng bottleneck đã đo không. Latency theo thời gian không chứng minh quan hệ nhân quả.
- Ba mức phân loại dùng ở đây:
  - FEASIBLE: áp dụng được cho code này, rủi ro nêu rõ.
  - PARTIALLY FEASIBLE: làm được nhưng gây lỗi khác nếu không xử lý thêm.
  - HALLUCINATED: tiền đề sai với hệ thống thật.

## 2. Hiện trạng SUT (đọc trực tiếp, không suy diễn)

| Hạng mục | Sự thật từ code | Dẫn chứng |
|---|---|---|
| Loại DB | **File** `eshop-sut/backend/database.sqlite`, không phải in-memory | `database.js:4-5` (không có `:memory:`) |
| Số kết nối | **1** đối tượng `new sqlite3.Database`, export và dùng chung cho mọi route | `database.js:5`, `:119`, `server.js:4` |
| Driver | `sqlite3@6.0.1` (node-sqlite3, bản build kèm SQLite 3.52.0) | `package.json:18`; `node_modules/sqlite3/package.json` (version); `deps/common-sqlite.gypi:3` (`3520000`) |
| Cơ chế driver | Mặc định không `serialize` thì lệnh gửi song song sang threadpool, nhưng build `SQLITE_THREADSAFE=1` nên mọi lệnh qua một mutex của kết nối; `busy_timeout` mặc định **1000 ms** | `src/database.cc:111`; `deps/sqlite3.gyp:85`; `src/database.cc:175` |
| Journal mode | Không có PRAGMA nào trong code (`grep PRAGMA\|INDEX\|BEGIN\|COMMIT` trong `server.js`/`database.js` không có kết quả liên quan). Header file `database.sqlite` byte 18–19 = `1,1` (rollback journal, chưa phải WAL). Không có file `-wal`/`-shm` | đọc 2 byte bằng `od`; `ls` thư mục backend |
| Seed/drop | Mỗi lần `require('./database')`, `initDatabase()` chạy `DROP TABLE` + `CREATE TABLE` + seed. `reset_sut.sh` restart backend rồi đăng ký lại 300 user | `database.js:14-20`, `:117`; `reset_sut.sh:6-14` |
| Schema | `categories`, `coupons`, `coupon_usage`, `users`, `products`, `orders`. **Không có `CREATE INDEX`.** Chỉ có PK `id` (rowid) và `coupons.code UNIQUE`. `products` không có cột tồn kho/số lượng | `database.js:23-81`, `:31` |
| Số dòng | `products` 5; `users` 2 seed + 300 đăng ký (`data/users.csv` 301 dòng gồm header); `orders` tăng theo checkout: Load 4.772, Stress 24.735, Soak 22.418 (`06 Checkout` count trong `ground_truth.json`) | `database.js:97-103`; `ground_truth.json` `runs.<Run>.variants.all.labels["06 Checkout"].count` |
| Giỏ hàng | `userCarts` là object **trong RAM của từng process**, không xóa khi checkout | `server.js:14`, `:284-295`, `:297-309` |
| Checkout | **Một `INSERT INTO orders` tự commit**, không có `BEGIN/COMMIT`, không kiểm tra tồn kho, không đọc giỏ hàng (`total_amount` lấy từ body) | `server.js:297-309` (`:299`, `:301-303`) |
| Port, xác thực | Port cứng 3000; JWT stateless với `SECRET_KEY` hằng; lockout nằm trong DB (`login_attempts`, `locked_until`) | `server.js:8`, `:9`, `:35-62`, `:105` |
| Dependencies | `body-parser`, `cors`, `express`, `jsonwebtoken`, `sqlite3`. **Không có** thư viện pool, cache, cluster/pm2 (cũng không có trong `node_modules`) | `package.json:13-19` |
| Máy test | JMeter và SUT cùng máy (`localhost:3000`), 6 core/12 luồng, Node v22.22.1 | `report/05_hardware.md`; JMX |

**SQL thật của Flow 1** (đối chiếu index):

| Request | SQL thật | Dòng | Index sẵn có |
|---|---|---|---|
| 01 Login | `SELECT * FROM users WHERE email = ?`; thành công thì `UPDATE users SET login_attempts=0, locked_until=NULL WHERE id=?` (không chờ callback) | `server.js:35`, `:47-50` | `email`: **không có** (302 dòng); `id`: PK |
| 02 Products | `SELECT * FROM products` (không WHERE, Flow không dùng `?search=`) | `:153` | không cần |
| 03 Product detail | `SELECT * FROM products WHERE id = ?` | `:160` | PK |
| 04 Add cart / 05 Get cart | **không có truy vấn DB**, chỉ đọc/ghi `userCarts` | `:284-295` | n/a |
| 06 Checkout | `INSERT INTO orders (user_id, total_amount, status, shipping_address) VALUES (?,?,?,?)` | `:301-303` | n/a (INSERT) |
| 07 My orders | `SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC` | `:313` | `user_id`: **không có**; `id`: PK |
| Negative login | như 01, nhánh sai mật khẩu: `UPDATE users SET login_attempts=?, locked_until=? WHERE id=?` | `:59-62` | PK |

Các route ngoài Flow: `LIKE '%${searchQuery}%'` (`:144`, dấu `%` đầu nên index b-tree thường không dùng được), `coupon_usage WHERE coupon_id=? AND user_id=?` (`:388`, không index), JOIN `orders`/`users` (`:510-517`).

## 3. Bằng chứng đo tái sử dụng (nguồn và bộ lọc)

Tất cả từ lần chạy thật 2026-11-18. Mục "ground_truth" là đường dẫn trong `results/analysis/ground_truth.json`. Mục "dẫn xuất" do tôi tính chỉ-đọc bằng `scripts/jtl_truth.py` (`load_jtl`, `metrics`), chưa có trong `ground_truth.json`. Bộ lọc: `label` đúng tên, và `timeStamp − min(timeStamp của file)` trong cửa sổ `[a,b)` (hoặc `threadName` chứa `Stress stage N`).

| Mã | Giá trị | Nguồn / bộ lọc |
|---|---|---|
| M1 | `06 Checkout` mean: Load 11,41; Stress 175,94; Spike 195,92; Soak 89,14 ms | ground_truth `runs.<Run>.variants.all.labels["06 Checkout"].mean_ms` |
| M2 | Stress stage 3: mean 12,91, p95 48. Stage 4: mean 161,48, p95 905, rps 444,36 | ground_truth `runs.Stress.variants.all.stages["3"|"4"]` |
| M3 | Spike 120–180 s: p95 1.497, p99 3.322, rps 188,18. 180–240 s: p95 17, p99 29, rps 231,5 | ground_truth `runs.Spike.variants.all.phases[...]` |
| M4 | Soak 120–180 s: mean 5,36, p95 19. **180–240 s: mean 368,54, p95 2.213, p99 4.121, rps 172,35** | ground_truth `runs.Soak.variants.all.minutes[2]`, `[3]` |
| D1 | Stress stage 4, p50 theo label: Login 110, Products 2, Product detail 1, Add cart 1, Get cart 7, **Checkout 338, My orders 221**. Mean: Checkout 433,40; My orders 361,72; Login 202,44; Products 49,83. Stage 3, p50: Products 7, My orders 8, Checkout 16 | dẫn xuất: `threadName` chứa `Stress stage 4` / `3`, theo label |
| D2 | **Route không chạm DB cũng chậm trong đợt chậm.** Soak 120–240 s: Add cart mean 30,51 / p95 160 / max 2.860; Get cart mean 70,23 / p95 413 / max 5.127. Spike 120–180 s: Add cart mean 37,61 / max 1.473; Get cart mean 86,33 / max 2.632. Khỏe (Soak 360–600 s): Add cart 1,96 / p95 7; Get cart 1,89 / p95 6 | dẫn xuất: label `04 Add cart`, `05 Get cart`; cửa sổ như ghi |
| D3 | Soak, bucket 10 s: 180–190 s mean 4,9 (cart 1,6); **190–200 s mean 139,8 (cart 60,8)**; 210–220 s mean 680,8 (cart 246,5); 240–250 s mean 397,7; 250–260 s mean 11,2. Đợt chậm khoảng **190–245 s**, rps tụt 124–207, `allThreads` max 203 (đã đủ tải trước 90 s). Spike, bucket 5 s: chậm khoảng **122–145 s**, hết khi tải 200 VU vẫn còn | dẫn xuất: bucket theo `timeStamp − origin` |
| D4 | Soak khỏe, p50 theo phút: Checkout **11 ms hằng định** từ ~1k đến ~22k order tích lũy; Products 2; My orders tăng nhẹ 2→3→4 ms khi orders tăng | dẫn xuất: phút 0–660, label `06`, `02`, `07` |
| D5 | **CPU ước tính theo khoảng** (từ `results/monitor/*.csv`): Soak 192–244 s ≈ **12–22% một core**, so với 31–37% trước (151–182 s) và 28–34% sau (244–264 s). Spike 121–136 s ≈ 6–29%, sau đó 33–43%. Stress stage 4 ≈ 42–55%. RSS Soak 118→126 MB trong đợt chậm rồi tụt ~100 MB lúc kết thúc | dẫn xuất từ `monitor_backend.sh:8-…` (`ps -o %cpu`) |

**Cách tính D5 (cần đọc kỹ):** `ps -o %cpu` là CPU time / thời gian process đã chạy (trung bình từ lúc khởi động), không phải tức thời. Cột `cpu_percent` trong CSV không dùng trực tiếp được. Tôi dựng CPU time = `%cpu × (E0 + t)` rồi lấy hiệu giữa hai mốc, với E0 (tuổi process lúc bắt đầu ghi) chưa biết, thử 5/10/20 s. Kết quả đổi ≤ ~2 điểm phần trăm. Làm tròn 0,1% của `ps` thêm sai số cỡ ±2–3 điểm phần trăm. Đây là **ước tính [INFERENCE]**, gồm tất cả luồng của process.

**Quan sát chung (giả thuyết, không phải nguyên nhân gốc):**
1. Trong đợt chậm của Soak và Spike, các route **không chạm DB** (`04`, `05`, `server.js:284-295`) cũng chậm cùng lúc (D2, D3). Chỉ riêng DB (index, pool, WAL) không giải thích được việc này.
2. Ở Soak, CPU ước tính của process **thấp hơn** trong đợt chậm (D5), không có dấu hiệu một core bị bão hòa. Ở Stress stage 4, CPU ước tính chỉ ≈ 42–55% một core dù p95 là 905 ms.
3. Mẫu nhận diện được: đợt chậm của Soak (~190–245 s) bắt đầu và kết thúc đột ngột khi tải đã ổn định (D3). Không thể quy cho "đủ tải" vì 203 VU khỏe ở các phút sau và ở Spike 180–240 s.
4. Ở lúc khỏe, **Checkout có p50 11 ms cố định** so với 1–2 ms của route không ghi (D4). Phù hợp với giả thuyết commit/ghi DB tốn kém cố định, nhưng chưa được đo trực tiếp trong code.
5. Ở Stress stage 4, `07 My orders` p50 221 ms trong khi `02 Products` p50 2 ms. Ở stage 3 hai route gần nhau (p50 8 và 7). Phù hợp với giả thuyết chi phí phụ thuộc bảng `orders` đang lớn (D1, D4), nhưng cũng phù hợp với tranh chấp ghi.
6. Chưa kiểm tra phía load generator (JMeter chạy cùng máy). Chưa có phép đo event-loop delay, thời gian từng câu SQL, hay I/O disk.

**Lưu ý đối chiếu với report 11:** cửa sổ Soak 120–240 s của analyst gộp ~70 s khỏe (120–~190 s, `minutes[2]` mean 5,36) với đợt chậm thật (~190–245 s). Điều này không làm sai các số analyst nêu, nhưng khi gắn bottleneck nên dùng `minutes[3]` hoặc bucket 10 s ở D3.

## 4. Bảng tổng hợp

| # | Đề xuất | Phân loại | Lý do (dẫn file:dòng) | Có nhắm đúng bottleneck đo được? |
|---|---|---|---|---|
| 1 | Index cho truy vấn tốn kém (generic, chưa nêu index cụ thể) | **FEASIBLE** (chỉ với ứng viên cụ thể bên dưới; generic thì chưa dùng được) | Không có index nào ngoài PK/`coupons.code` UNIQUE (`database.js:23-81`, `:31`). `07 My orders` lọc `WHERE user_id = ? ORDER BY id DESC` (`server.js:313`), `orders.user_id` chưa có index. Login lọc `email` (`:35`), `users.email` chưa có index nhưng chỉ 302 dòng. Products 5 dòng, `LIKE '%…%'` (`:144`) không dùng index. `INSERT` của Checkout (`:301`) sẽ chậm hơn khi thêm index | **Một phần.** Ứng viên `orders(user_id)` khớp với `07 My orders` (D1, D4) chứ không khớp Checkout, và không giải thích route không chạm DB chậm (D2). Chưa chứng minh |
| 2 | Pool kết nối SQLite giới hạn | **PARTIALLY FEASIBLE** | Có thể mở nhiều kết nối tới **cùng file** `database.sqlite` (`database.js:4-5`); không phải đề xuất chỉ dành cho MySQL. Nhưng chưa có thư viện/mã pool (`package.json:13-19`), phải tự viết hoặc thêm dependency. Journal mode hiện là rollback (header byte 18–19=`1,1`), không `busy_timeout` tùy chỉnh ngoài 1000 ms mặc định (`src/database.cc:175`): ghi/đọc đồng thời trên kết nối khác nhau có thể trả `SQLITE_BUSY`, route Checkout/Login trả 500 (`server.js:305`, `:36`). Vẫn một writer; không tăng năng lực ghi | **Một phần/chưa chứng minh.** Chỉ giúp nếu nút thắt là xếp hàng đọc trên mutex của kết nối (`deps/sqlite3.gyp:85`). `02 Products` p50 chỉ 2 ms ở stage 4 (D1), nên đọc rẻ không bị chặn đồng loạt. Không giải thích route không chạm DB chậm |
| 3 | Thử SQLite WAL | **FEASIBLE** (lợi ích có thể khác cơ chế analyst nêu) | DB là file (`database.js:4`), SQLite 3.52.0 hỗ trợ WAL; header hiện là rollback journal. Một dòng PRAGMA sau `database.js:5` hoặc trong `db.serialize` (`:14`). Chế độ WAL lưu bền trong file, `DROP/CREATE TABLE` (`:15-81`) và `reset_sut.sh:6-9` (chỉ restart) không đổi nó. **Một kết nối thì "đọc song song với ghi" không có ý nghĩa**; lợi ích có thể là ít `fsync` mỗi commit (tài liệu SQLite WAL, `wal.html`), không phải nhiều writer | **Giả thuyết, chưa chứng minh.** Có thể liên quan đến Checkout p50 hằng định 11 ms (D4) và Checkout luôn chậm nhất theo mean (M1). Không giải thích route không chạm DB chậm (D2) |
| 4 | Cache dữ liệu sản phẩm công khai | **FEASIBLE** (giá trị thấp) | Áp dụng cho `server.js:141-165`. Chỉ 5 sản phẩm (`database.js:97-103`), nên đọc DB rẻ. Cần invalidation ở **4 chỗ ghi, không cần xác thực**: `server.js:167-177`, `:179-189`, `:191-196`, `:199-241`. Route chi tiết đổi kiểu `price` theo chẵn/lẻ id (`:162`), cache phải giữ nguyên hành vi đó. Không có thư viện cache trong `package.json:13-19`, nhưng `Map` có sẵn | **Không.** Products p50 1–2 ms ngay cả ở stage 4 (D1); latency cao ở Products là đuôi theo đợt (D2), không do đọc 5 dòng |
| 5 | Chạy nhiều tiến trình Node (cluster) | **PARTIALLY FEASIBLE** | `node:cluster` có sẵn (Node v22.22.1). Nhưng `userCarts` ở RAM từng process (`server.js:14`, `:284-295`): `GET /api/cart` trúng worker khác sẽ trả `[]`; `JMX:94-95` (`json[-1].id == id`) sẽ fail. `database.js:117` chạy `DROP TABLE` + seed (`:15-20`) trong **mỗi** worker nên xóa dữ liệu đang chạy và có thể đụng `SQLITE_BUSY`. SQLite vẫn khóa ghi theo file. `monitor_backend.sh:8` lấy `head -n 1` PID nên chỉ theo dõi process chính. `server.js:570` không export nên cần file entry mới bọc `require('./server')` | **Không có bằng chứng.** CPU ước tính dưới 1 core ở cả stage 4 (42–55%) và trong đợt chậm Soak (12–22%) (D5), không thấy bão hòa CPU của Node |
| 6 | Rút ngắn transaction Checkout | **HALLUCINATED** (tiền đề sai với hiện trạng; analyst có ghi "nếu thực tế có") | Không có transaction nào để rút ngắn: Checkout là một `INSERT` tự commit (`server.js:301-308`), không `BEGIN/COMMIT/ROLLBACK` (grep). Không có tồn kho: `products` không có cột số lượng (`database.js:64-71`), mã Checkout không đọc giỏ hàng hay sản phẩm (`:297-309`). Phần "giữ kiểm tra tồn kho" của analyst không có đối tượng trong code | **Không áp dụng.** Điểm nghi liên quan Checkout (D4) nằm ở chi phí commit mỗi `INSERT` (xem #3), không ở độ dài transaction |
| 7 | Giảm xử lý chặn event loop (đo rồi mới sửa) | **FEASIBLE** (chỉ phần đo; phần "chuyển sang worker thread/I/O async" chưa có đối tượng trong code) | `monitorEventLoopDelay` từ `node:perf_hooks` có sẵn, không cần thư viện mới. Đọc các route của Flow (`server.js:32-66`, `:100-110`, `:141-165`, `:284-319`) không thấy xử lý CPU nặng hay I/O đồng bộ; chỉ có `jwt.sign/verify` (`:51`, `:105`) và `res.json` | **Đề xuất khớp nhất với quan sát**: route không chạm DB cũng chậm đồng thời (D2, D3). Nhưng CPU ước tính thấp trong đợt chậm (D5) nên chưa chắc là event loop; phía JMeter chưa kiểm tra |

## 5. Chi tiết từng đề xuất

### 5.1 Index

- **Analyst viết (nguyên văn điều kiện):** "thêm index phù hợp với điều kiện lọc, join hoặc sắp xếp của các truy vấn đang quét nhiều dòng; không thêm index mù cho mọi cột"; "Các placeholder phải được thay bằng schema thật, không chạy nguyên mẫu". Đề xuất generic, chưa nêu index cụ thể. Mục này là ý kiến reviewer, không sửa report 11.
- **Ứng viên thật theo SQL ở Mục 2:**
  - `CREATE INDEX idx_orders_user_id ON orders(user_id);` Entry index SQLite có rowid ở cuối khóa nên `ORDER BY id DESC` có thể đọc ngược index; không cần cột `(user_id, id)`. Chỗ đặt: ngay sau `CREATE TABLE orders` ở `database.js:81`. `DROP TABLE orders` (`database.js:20`) xóa luôn index, nên reset vẫn sạch.
  - `users(email)`: đúng với `server.js:35` nhưng chỉ 302 dòng. Cần để khớp điều kiện lọc, nhưng khó là nguồn của latency đo được. Không gợi ý ưu tiên.
  - `products`, `categories`, `coupons`: không có điều kiện lọc trong Flow cần index (`products WHERE id` đã là PK).
- **Rủi ro:** thêm một b-tree phải cập nhật mỗi lần `INSERT INTO orders` (`server.js:301`), đúng route Checkout đang chậm nhất theo mean (M1). Không có LIMIT ở `:313` nên response My orders vẫn tăng theo số đơn của user; index không giải quyết phần này. Orders cuối Stress ≈ 24,7k dòng.
- **Bottleneck fit:** `07 My orders` ở stage 4 p50 221 ms vs Products 2 ms, ở stage 3 gần bằng nhau (D1). Trong Soak khỏe, My orders p50 tăng nhẹ 2→4 ms khi orders tăng (D4). Cả hai phù hợp với "quét bảng lớn dần", nhưng cũng phù hợp với tranh chấp ghi. Không giải thích đợt chậm ảnh hưởng `04`/`05` (D2).

### 5.2 Pool kết nối

- **Analyst viết:** "giữ mỗi transaction trên một kết nối riêng từ BEGIN đến COMMIT/ROLLBACK"; "Nếu database là in-memory hoặc có trạng thái theo kết nối, phải giải quyết tính chia sẻ và isolation trước khi áp dụng"; "`pool` và `runTransaction` là giao diện minh họa cần hiện thực theo code thực tế, không khẳng định package đã cài".
- **Đối chiếu:** điều kiện in-memory không xảy ra (DB là file, `database.js:4`). Không có transaction nào trong code (`BEGIN/COMMIT` không có), nên mẫu `runTransaction` chưa có đối tượng. `pool`, `acquire`, `release` không phải package đã cài (`package.json:13-19`): phải tự viết hoặc thêm dependency mới.
- **Có làm được không:** có. Mở N kết nối tới cùng `database.sqlite` là hợp lệ với SQLite. Phải đảm bảo `initDatabase()` (`database.js:117`) chỉ chạy một lần, không chạy ở mọi kết nối (vì nó `DROP TABLE`).
- **Lỗi khác có thể sinh ra:** với rollback journal hiện tại, writer cần khóa độc quyền và reader giữ khóa chia sẻ; xung đột chờ tối đa 1000 ms (`src/database.cc:175`) rồi trả `SQLITE_BUSY`. Lỗi này trả 500 ở Checkout (`server.js:305`) và Login (`:36`); `GET /api/products` không xử lý `err` (`:153-155`). Hiện tại JTL có 0 lỗi (ground_truth `error_count`); pool có thể đổi độ trễ thành lỗi. Vì vậy nếu thử pool, cần WAL trước (xem 5.3).
- **Giới hạn cơ chế:** mặc định driver không `serialize` (chỉ `database.js:14` dùng `db.serialize` cho init), lệnh gửi sang threadpool rồi qua mutex của kết nối (`database.cc:111`; `sqlite3.gyp:85`). "Một hàng đợi trên kết nối chung" là giả thuyết, không phải FIFO đã được xác nhận trong code.
- **Bottleneck fit:** Spike 120–180 s p95 1.497 ms (M3). Nhưng route không chạm DB cũng chậm cùng lúc (D2), và `02 Products` p50 chỉ 2 ms ở stage 4 (D1). Chưa có bằng chứng nút thắt là hàng đợi đọc.

### 5.3 WAL

- **Analyst viết:** "nếu database là file và cấu hình phù hợp"; "không loại bỏ giới hạn một writer và không chắc có lợi khi chỉ dùng một kết nối"; "Không giả định WAL khả dụng hoặc có ý nghĩa cho database in-memory".
- **Đối chiếu:** điều kiện file thỏa. SQLite 3.52.0 (`deps/common-sqlite.gypi:3`) hỗ trợ WAL. Header file hiện là rollback journal. Lệnh `PRAGMA journal_mode=WAL` lưu bền trong file DB (tài liệu `wal.html`), nên `DROP TABLE` ở `database.js:15-20` và restart ở `reset_sut.sh:6-9` không đổi lại. Chỗ đặt: `database.js:14` (đầu `db.serialize`) hoặc ngay sau `:11`.
- **Cơ chế:** analyst nêu "reader và writer chờ nhau" nhưng với **một kết nối** thì không có khóa file giữa các lệnh của chính kết nối đó, nên cơ chế này không áp dụng ở hiện trạng. Phần có thể có lợi theo tài liệu SQLite là "WAL uses many fewer fsync() operations" mỗi commit. Mỗi Login thành công (`server.js:47-50`) và mỗi Checkout (`:301`) là một commit riêng. Chưa đo cái này trong SUT.
- **Rủi ro:** thêm file `database.sqlite-wal` và `-shm` cạnh file DB (khi backup/copy phải kèm đủ); WAL cần cùng một host, không dùng được trên network filesystem (tài liệu `wal.html`); checkpoint có thể tạo đỉnh ghi định kỳ. `synchronous` mặc định không đổi, nên không có rủi ro mất bền vững mới (đổi `synchronous` là quyết định riêng, analyst không đề xuất).
- **Bottleneck fit:** Checkout p50 11 ms hằng định khi khỏe (D4) so với 1–2 ms ở route không ghi; Checkout chậm nhất theo mean ở cả bốn run (M1). Giả thuyết thử được và dễ hoàn tác. Không giải thích route không chạm DB chậm (D2).

### 5.4 Cache sản phẩm

- **Analyst viết:** "sau khi xác nhận dữ liệu được phép công khai"; "invalidate khi sản phẩm thay đổi, không cache lỗi hoặc dữ liệu cá nhân"; "Nếu nhiều process, thiết kế invalidation chung trước khi coi cache nhất quán".
- **Đối chiếu:** áp dụng cho `GET /api/products` (`server.js:141-157`) và `GET /api/products/:id` (`:159-165`). Dữ liệu này không phải riêng tư và là công khai (không có `authenticateToken` ở các route này). Không cần thư viện mới (`Map` đủ). Nơi cần invalidation, vì sản phẩm sửa bằng route không xác thực: `POST` (`:167-177`), `PUT` (`:179-189`), `DELETE` (`:191-196`), import (`:199-241`). Khóa cache `?search=` phải chứa chuỗi gốc (`:144`), đó là SQL nối chuỗi nên key do người dùng điều khiển, cần giới hạn kích thước. Route chi tiết đổi `price` thành chuỗi khi id chẵn (`:162`), cache phải giữ đúng kiểu.
- **Rủi ro:** dữ liệu cũ nếu quên một trong bốn chỗ ghi.
- **Bottleneck fit:** Không. `products` chỉ 5 dòng (`database.js:97-103`), Products p50 1–2 ms ngay cả ở stage 4 (D1). Đợt chậm Products (D2, p95 277 ms ở Soak 120–240 s) xuất hiện cả ở route không chạm DB nên không do chi phí đọc.

### 5.5 Cluster

- **Analyst viết:** "sau khi bảo đảm khởi tạo database, session, lockout và cache an toàn giữa process"; "Kiểm tra entrypoint chỉ listen trong worker và không reset DB mỗi worker; không dùng nếu mỗi worker tạo database in-memory riêng hoặc trạng thái xác thực/lockout riêng gây sai nghiệp vụ".
- **Đối chiếu từng điều kiện (với code thật):**
  - *Database in-memory:* không (file, `database.js:4`), nên điều kiện đó không xảy ra.
  - *Reset DB mỗi worker:* **có**. `database.js:117` gọi `initDatabase()` khi `require`, nên mỗi worker `DROP TABLE` + `CREATE` + seed (`:15-111`). Worker khởi động sau sẽ xóa user mà `reset_sut.sh:11-14` đã đăng ký và các order đang có. `CREATE TABLE` không có `IF NOT EXISTS` (`:23`...), hai process chạy song song có thể va nhau.
  - *Session/lockout:* JWT stateless (`server.js:9`, `:105`) nên an toàn qua process. Lockout nằm trong DB (`:35-62`) nên chia sẻ được, nhưng read-modify-write không nguyên tử (đọc ở `:35`, ghi ở `:59-62` không chờ). Race này đã có ở một process và nặng hơn khi có nhiều process.
  - *Giỏ hàng:* **không chia sẻ.** `userCarts` (`:14`) ở RAM từng process. `GET /api/cart` trúng worker khác trả `[]` (`:286-287`); assertion `05 Get cart` (`JMX:94-95`, `json[-1].id == id`) sẽ fail. Với `keep-alive` trong JMX, mỗi VU thường bám một worker nên lỗi có thể **không hiện** trong test dù sai với client đóng/mở lại kết nối [INFERENCE].
  - *Entrypoint:* `server.js:570` gọi `app.listen` ở cấp module và không export, nên cần file entry mới bọc `require('./server')`; mẫu `require('<entrypoint-khoi-dong-server>')` của analyst dùng được theo hướng đó. Port 3000 cứng (`:8`) vẫn dùng được trong worker (cluster chia sẻ cổng).
  - *SQLite khóa ghi theo file:* mọi worker ghi cùng một file nên vẫn một writer, `SQLITE_BUSY` sau 1000 ms (`src/database.cc:175`) → 500 ở `server.js:305`, `:36`.
  - *Công cụ:* `monitor_backend.sh:8` lấy `pgrep ... | head -n 1`, chỉ theo dõi process đầu tiên; `reset_sut.sh:6` (`pkill -f "^node server.js"`) vẫn dọn được nếu worker cũng chạy cùng dòng lệnh.
- **Làm được nếu đổi kiến trúc:** đưa giỏ hàng vào DB hoặc store chung, tách bước seed khỏi mỗi worker, cấu hình WAL và `busy_timeout`. Ở hiện trạng thì đây không phải thay đổi một dòng.
- **Bottleneck fit:** chỉ có ý nghĩa nếu Node bão hòa CPU. Ước tính CPU của process (D5) dưới 1 core cả ở stage 4 và trong đợt chậm Soak, và thấp hơn trong đợt chậm. Số này gồm mọi luồng nên không loại trừ main thread bận từng đợt ngắn, nhưng không có dấu hiệu bão hòa.

### 5.6 Rút ngắn transaction Checkout

- **Analyst viết:** "chỉ giữ khóa transaction trong phần truy vấn và cập nhật cần tính nguyên tử; giảm công việc lặp hoặc thao tác ngoài database bên trong transaction, nếu thực tế có"; "giữ kiểm tra tồn kho, cập nhật và tạo đơn liên quan trong cùng transaction".
- **Đối chiếu:** không có transaction trong code: Checkout là đúng một `db.run("INSERT INTO orders …")` (`server.js:301-308`), không `BEGIN/COMMIT/ROLLBACK`. Không có thao tác ngoài DB bên trong transaction. Không có tồn kho: `products` không có cột số lượng (`database.js:64-71`) và Checkout không đọc sản phẩm hay giỏ hàng (`:297-309`; `total_amount` lấy từ body ở `:299`). Cụm "giữ kiểm tra tồn kho, cập nhật và tạo đơn liên quan" mô tả cấu trúc không tồn tại.
- **Phân loại:** HALLUCINATED theo nghĩa tiền đề sai với hiện trạng, **không** phải bịa số hay thư viện (analyst đã ghi điều kiện "nếu thực tế có"). Đề xuất không áp dụng được vì không có gì để "rút ngắn".
- **Hướng liên quan còn lại:** chi phí commit mỗi `INSERT` (xem 5.3) và index `orders` (xem 5.1).
- **Bottleneck fit:** Checkout là label chậm nhất (M1), nhưng nguyên nhân không nằm ở độ dài transaction.

### 5.7 Event loop

- **Analyst viết:** "xác định và thay xử lý CPU nặng hoặc I/O đồng bộ trong đường request bằng cách không chặn event loop, nếu có"; "Mẫu trên là phép đo đề xuất, không phải kết quả đã đo".
- **Đối chiếu:** `monitorEventLoopDelay` thuộc `node:perf_hooks` có sẵn; `h.percentile(99) / 1e6` đổi ns sang ms đúng. Không cần dependency mới. Đọc các route của Flow thì không thấy xử lý CPU nặng hay I/O đồng bộ (`server.js:32-66`, `:100-110`, `:141-165`, `:284-319`); chỉ `jwt.sign/verify` (`:51`, `:105`) và `res.json`. Nên điều kiện "nếu có" chưa thỏa theo đọc tĩnh; phần thay bằng worker thread chưa có đối tượng. Phần **đo** là hợp lệ.
- **Bottleneck fit:** đây là đề xuất khớp nhất với quan sát "route không chạm DB cũng chậm cùng lúc" (D2, D3). Nhưng D5 cho thấy CPU thấp hơn trong đợt chậm, nên không chắc nguyên nhân là event loop. Còn một khả năng khác chưa kiểm tra: JMeter chạy cùng máy (`report/05_hardware.md`) và có thể là nguồn trễ phía client.

## 6. Kiểm tra cụ thể theo yêu cầu

- **Index có trúng SQL thật không:** chỉ `orders(user_id)` trúng truy vấn thật (`server.js:313`). `users(email)` trúng (`:35`) nhưng bảng nhỏ. `products` không có điều kiện lọc cần index. Không có index nào ngoài PK/UNIQUE (`database.js:23-81`).
- **WAL có hợp với driver không:** `sqlite3@6.0.1` build SQLite 3.52.0, hỗ trợ `PRAGMA journal_mode=WAL`. Một kết nối thì WAL không tăng concurrency ghi. Chỉ có thể giảm `fsync` mỗi commit (giả thuyết). Header file hiện là rollback journal.
- **Thư viện giả định đã cài:** analyst không giả định thư viện cụ thể nào đã cài (đã ghi "không khẳng định package đã cài"). Nhưng `pool`/`acquire`/`release` (#2) và cache có TTL (#4) **không có** trong `package.json:13-19`; nếu muốn dùng thư viện thì cần cài mới. `node:cluster` (#5) và `node:perf_hooks` (#7) có sẵn trong Node, không cần cài.
- **Pool có phải chỉ của MySQL không:** không. Mở nhiều `sqlite3.Database` tới cùng file là hợp lệ, nhưng driver này không có pool dựng sẵn (không có trong `package.json`) và hệ quả phụ (`SQLITE_BUSY`) nêu ở 5.2.
- **Số "cải thiện X%":** không có đề xuất nào của analyst nêu % cải thiện; analyst ghi rõ "chưa định lượng". Reviewer cũng không đưa % nào.

## 7. Chưa kiểm tra / không chạy

- Không chạy: benchmark, JMeter, `PRAGMA`, `EXPLAIN QUERY PLAN`, sửa SUT/DB. Chỉ đọc: code, JTL qua `jtl_truth.py` (read-only), CSV monitor, 2 byte header `database.sqlite`, tài liệu SQLite `wal.html`.
- D5 (CPU tức thời) là ước tính dẫn xuất từ `ps %cpu` trung bình (E0 chưa biết, thử 5–20 s), không phải số đo trực tiếp. Số liệu D1–D4 được tính ngoài `ground_truth.json` (cùng nguồn JTL, bộ lọc ghi trong Mục 3).
- Chưa có: thời gian từng câu SQL, event-loop delay, I/O disk, CPU tức thời (`pidstat`/`top`), số liệu phía JMeter. Vì vậy **chưa chứng minh nguyên nhân gốc** cho đợt chậm (Soak ~190–245 s, Spike ~122–145 s, Stress stage 4).
- Phát hiện ngoài 7 đề xuất, không phải thay đổi đề xuất: `userCarts` (`server.js:14`) không bao giờ bị xóa (kể cả sau Checkout `:297-309`), nên Get cart trả danh sách ngày càng dài trong lần chạy; RSS Stress tăng 132→171 MB (D5), chưa quy được nguyên nhân.

## 8. Thứ tự ưu tiên đề xuất (dựa trên bằng chứng hiện có, chưa phải kết luận nguyên nhân)

1. **Đo trước, chưa sửa:** event-loop delay (#7), thời gian từng `db.run` ở Login/Checkout/My orders, CPU tức thời bằng `pidstat`/`top`, và kiểm tra phía JMeter. Mục đích: phân biệt chờ I/O/khóa, event loop, và nguồn trễ phía client, vì đợt chậm ảnh hưởng cả route không chạm DB (D2) và CPU Node dưới 1 core (D5).
2. **WAL (#3)** nếu phép đo ở bước 1 cho thấy thời gian commit ghi chiếm phần lớn. Thay đổi 1 dòng, hoàn tác dễ, kiểm tra được giả thuyết Checkout p50 ~11 ms. Phải chạy lại cùng plan và cùng cửa sổ để so sánh.
3. **Index `orders(user_id)` (#1)** nhắm `07 My orders`, kiểm bằng `EXPLAIN QUERY PLAN` trên bản sao DB; theo dõi thêm chi phí `INSERT` của Checkout.
4. **Hoãn:** pool (#2, cần WAL trước và vẫn có nguy cơ `SQLITE_BUSY`), cache (#4, giá trị thấp, 5 dòng), cluster (#5, phải sửa trạng thái giỏ hàng và seed trước). **Bỏ:** #6 (không có transaction để rút ngắn).

## 9. Lưu ý của Manager trước human review

- Bảng trên là kết luận của reviewer: 4 FEASIBLE, 2 PARTIALLY FEASIBLE, 1 HALLUCINATED. Đây là đánh giá áp dụng tĩnh, không phải kết quả benchmark hay tỷ lệ cải thiện đã đo.
- Với mục 6, cần đọc đủ điều kiện “nếu thực tế có” của analyst. Chính xác về SQLite: Checkout vẫn có **transaction ngầm của INSERT tự commit**; code không có transaction tường minh nhiều bước hoặc công việc ngoài DB trong transaction để rút ngắn. Nhãn HALLUCINATED ở đây đánh giá tính áp dụng của hành động vào hiện trạng, không chứng minh analyst đã khẳng định có một transaction dài. Sinh viên cần tự quyết định liệu nhãn này có quá mạnh hay nên đổi trong human review.
- D5 là mô hình ước tính CPU từ `%CPU` trung bình với tuổi process ban đầu giả định, không phải phép đo CPU tức thời và không phải ground truth JTL. Không dùng nó một mình để loại trừ CPU/event loop hoặc chứng minh nguyên nhân đợt chậm. Các kết luận chắc về pool/cluster/transaction dựa trên code và giới hạn trạng thái, không dựa vào các con số CPU ước tính.
- Không sửa output analyst ở `11_ai_analysis.md`; mọi bất đồng với reviewer cần ghi ở `14_human_review_task2.md`, không sửa lại bằng chứng phân tích ban đầu.
