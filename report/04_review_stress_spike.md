# Bước 8 – Review độc lập test plan Stress và Spike

Đối tượng: `test-plans/23120190_Stress_20261117.jmx`, `test-plans/23120190_Spike_20261117.jmx`. Đối chiếu `report/03_review_load.md` (checklist + mục "Đã sửa"), plan Load đã sửa, `report/02_test_design.md`, `report/04a_stress_spike_initial_smoke.md`, `eshop-sut/backend/server.js`, `eshop-sut/backend/database.js`. Số dòng là số dòng của file `.jmx`.

Giới hạn bằng chứng: **không sửa JMX, không chạy lại runtime**. Bằng chứng runtime duy nhất là smoke ở `report/04a_stress_spike_initial_smoke.md` (1 VU) cùng JTL/log trong `results/smoke/`, tôi chỉ đọc lại các file đó. Chưa có lần chạy nào ở 50/100/200/290 VU hay 10→200 VU. Nhận định về hành vi dưới tải là suy luận từ code, đánh dấu `[INFERENCE]`. Có một kiểm tra tĩnh mới (đọc bytecode `javap`, không chạy plan) dùng cho lỗi #S1.

## Kết luận

| Plan | Kết luận | Lý do ngắn |
|---|---|---|
| Stress | **NEEDS FIX** | 1 lỗi High (#S1): chạy mặc định (không `-Jthreads`) bậc 3 và 4 chỉ có 100 VU thay vì 200 và 290. 1 lỗi Low (#S2). |
| Spike | **PASS** | Không có lỗi Medium trở lên. Ramp 5 s, lịch thấp→cao→thấp đúng thiết kế, pool và listener đúng. Chỉ có ghi chú Low/Info (#P1–#P3). |

## Checklist chung (cùng checklist với `03_review_load.md`)

| Hạng mục | Stress | Spike | Bằng chứng |
|---|---|---|---|
| Workflow 7 bước, đúng thứ tự | Đúng | Đúng | `01 Login` → `02 Products` → `03 Product detail` → `04 Add cart` → `05 Get cart` → `06 Checkout` → `07 My orders`. Smoke: 7/7 mỗi plan, HTTP 200, `success=true` (04a). Stress: bốn khối nhóm giống hệt nhau, chỉ khác tên nhóm, namespace pool và `num_threads` (so khối dòng 40–376 với 377–713, 714–1050, 1051–1385 sau khi thay tên). |
| Các sửa của Load đã mang sang | Đủ | Đủ | `HTTPSampler.use_keepalive=true`: 32/32 sampler (Stress), 16/16 (Spike). `Login failed` + `Pause after failed login` (không tạo HTTP sample): 4 (Stress), 2 (Spike). `default: assert false`: 4 và 2. `json[-1]` (cart phần tử cuối): 4 và 2. Đối chiếu `token`/`user_id`/`order_id` với response: có trong cả hai assertion. |
| Assertion không chỉ kiểm tra 200 | Đúng | Đúng | Cùng script với Load (parse JSON, price string/number bằng `BigDecimal`, `orderId` số nguyên dương, my-orders khớp `id`/`user_id`/`total_amount`). |
| Lockout tách riêng, 401/403 coi là đúng | Đúng | Đúng | `lock_email` chỉ xuất hiện trong sampler `Negative login` (Stress dòng 188, 525, 862, 1199) và đến từ `data/users_lock.csv` (perf291–300). Assertion `Negative login` chỉ chấp nhận 401/403. |
| Throughput Controller 5% | Đúng | Đúng | `style=1`, `percentThroughput=${__P(lock_percent,5)}`, `perThread=false`. |
| CSV: đường dẫn, sharing mode, recycle | Đúng | Đúng | Đường dẫn tương đối `data/...`, `shareMode.all`, `recycle=true`, `ignoreFirstLine=true`. File CSV dùng CRLF (`od -c`); CSVDataSet và `File.readLines` của fallback đều bỏ `\r`. |
| `total_amount` không cộng dồn | Đúng | Đúng | `price × qty` của vòng hiện tại (assertion `03`), xóa biến mỗi vòng ở PreProcessor `01 Login`. Checkout không dùng giỏ (`server.js:297-309`). |
| Listener: đúng một `ResultCollector`, khác nhau | Đúng | Đúng | Load `SummaryReport` (Load dòng 108), Stress `StatVisualizer` = Aggregate Report (dòng 1414), Spike `RespTimeGraphVisualizer` (dòng 606). `grep -c 'testclass="ResultCollector"'` = 1 ở cả ba file. |
| Pool tài khoản | Đúng | Đúng | Xem mục "Pool tài khoản" bên dưới. |
| `__groovy` và property runtime | Đúng khi có `-Jloops`; **lỗi khi không có `-Jthreads`** (#S1) | Đúng | Xem mục "Property runtime". |

## Property runtime (`__groovy`, `num_threads=0`, scheduler, delay, duration)

- **`__groovy` + Java.** Các plan đặt Groovy ngay trong thuộc tính thread group (`scheduler`, `num_threads`, `delay`), nên nếu Groovy không chạy thì lỗi ngay lúc khởi động. `04a` ghi lần chạy Java 25 lỗi `Unsupported class file major version 69`; lần chạy Java 17 pass. Shell hiện tại vẫn mặc định Java 25 (`java -version` → `25.0.5.0.3`), nên phải đặt `JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64` trong cùng lệnh chạy JMeter (đã có trong `00_environment.md`).
- **`num_threads=0` khi smoke (`loops>0`).** Stage 2–4 và burst nhận `'0'`. Smoke `-Jloops=1` cho Stress và Spike cùng exit 0 với đúng 7 sample mỗi plan, nên nhóm 0 thread không làm treo hay lỗi (04a). Nhánh bật lại bằng `stage_smoke=true`/`timeline_smoke=true` có bằng chứng: 28 sample (7 × 4 nhóm) và 37 sample.
- **Scheduler / delay / duration.** Timeline smoke (`loops=-1 duration=24 spike_delay=8 spike_duration=8`): JTL cho `Spike burst 2-1` có mẫu từ 7.69 s đến 15.61 s (so với sample đầu), tức xấp xỉ `delay`=8 và `delay+duration`=16. `Spike baseline 1-1` có mẫu từ 0 đến 23.2 s trong khi burst hoạt động. Các nhóm Spike chạy song song (`serialize_threadgroups=false`, Spike dòng 20). Stress `serialize_threadgroups=true` (Stress dòng 20): log stage smoke cho thấy mỗi nhóm bắt đầu sau khi nhóm trước kết thúc (`Waiting for thread group: Stress stage N to finish before starting next group`).
- **Khoảng trống smoke:** mọi lượt smoke đều truyền `-Jloops` tường minh (`1` hoặc `-1`). Nhánh mặc định (không có property `loops`, không có `threads`), đúng là lệnh chạy đo trong `CLAUDE.md`, chưa được chạy. Lỗi #S1 nằm đúng ở nhánh này.

## Pool tài khoản

- Stress dùng namespace riêng mỗi bậc: `stress.accounts.1`…`stress.accounts.4` (dòng 150, 487, 824, 1161). Hợp lý vì bậc N chỉ bắt đầu sau khi bậc N−1 kết thúc hết thread (serialize), nên bậc sau có thể dùng lại perf001..290 mà không va chạm đang chạy. Bậc 4 với 290 VU dùng vừa đủ 290 tài khoản; thêm một VU sẽ ném `IllegalStateException('Not enough main accounts...')` trong PreProcessor.
- Spike dùng chung `spike.accounts` cho baseline (dòng 109) và burst (dòng 392). Đúng vì hai nhóm chạy cùng lúc: 10 + 190 = 200 ≤ 290, không tài khoản nào bị hai VU giữ. Khi dòng CSV của VU burst trùng tài khoản baseline đã giữ thì fallback đọc `data/users_main.csv` và chọn dòng chưa dùng.
- Như Load #7: CSV vẫn tiêu thụ mỗi iteration nhưng chỉ vòng đầu của VU quyết định tài khoản; fallback đọc file chạy trong khối `synchronized` mỗi khi va chạm (đa số VU của bậc 4 và burst). Chi phí là đọc 290 dòng một lần mỗi VU; không phải lỗi người dùng nhìn thấy.

## Lockout khi tải cao: có làm hỏng luồng chính không?

**Không**, với plan như đã viết. Bằng chứng:

1. Chỉ tài khoản gửi sai mật khẩu mới bị cộng `login_attempts` và bị khóa (`server.js:46-60`). Luồng chính luôn gửi mật khẩu đúng của đúng tài khoản (`account_email`/`account_password` lấy từ cùng một dòng CSV hoặc cùng dòng fallback), và login đúng còn đặt lại `login_attempts=0`.
2. Khóa kiểm tra theo từng dòng `users` (`server.js:40-44`), không có khóa toàn cục hay giới hạn tốc độ, nên 10 tài khoản perf291–300 bị khóa không ảnh hưởng perf001–290.
3. Mẫu `Negative login`: lần sai thứ 1 → 401 (attempts=2), lần thứ 2 → 401 và khóa 180 s (attempts=4), sau đó 403 đến hết khóa; hết khóa thì lần sai kế khóa lại. `[INFERENCE]` ở mức 5% của khoảng 32–94 vòng/s thì phần lớn mẫu là 403, đi nhánh SELECT rẻ trước khi so mật khẩu (`server.js:40-44`), không phải tải đáng kể.
4. Rủi ro còn lại do trạng thái, không do plan: nếu quên chạy `scripts/reset_sut.sh` và một tài khoản chính đã bị khóa từ trước (ví dụ test thủ công), VU giữ tài khoản đó nhận 403 ở mọi vòng, ngủ 1 s rồi thử lại cùng tài khoản. Các mẫu lỗi đó vào số liệu gate và có thể dừng Stress vì lỗi > 5% chứ không phải do SUT hỏng. 04a đã chứng minh chính tình huống này (stop-gate, 403 → `continue=false`). Cách phòng: reset trước mỗi lần chạy, đã có trong quy trình.

---

# Stress – `23120190_Stress_20261117.jmx`

## Danh sách lỗi

### #S1 [High] Stage 2, 3, 4 (dòng 383, 720, 1057) – `props.get('threads', N)` ghi `N` vào props nên chạy mặc định là 50/100/**100/100** thay vì 50/100/200/290

- **Vấn đề:** `num_threads` của stage 2–4 là `${__groovy((props.get('loops','-1')=='-1' || …) ? props.get('threads','100'|'200'|'290') : '0')}`. Trong `__groovy`, `props` là `java.util.Properties` (đọc `ApacheJMeter_functions.jar`: `Groovy.execute` gọi `JMeterUtils.getJMeterProperties()` rồi bind tên `props`). `Properties` chỉ có `get(Object)` một tham số, nên `props.get(key, default)` được Groovy chuyển sang `DefaultGroovyMethods.get(Map, K, V)`. Bytecode bản Groovy 3.0.20 kèm JMeter 5.6.3 (`javap -c`):

  ```
  public static <K, V> V get(java.util.Map<K, V>, K, V);
     0: aload_0 / aload_1   invokeinterface Map.containsKey
     7: ifne 19
    10: aload_0 / aload_1 / aload_2   invokeinterface Map.put   // ghi default vào map
    19: aload_0 / aload_1   invokeinterface Map.get ; areturn
  ```

  Tức khi key chưa có, default bị **ghi vào props** rồi trả về. Stage 2 được tính trước: `threads` chưa có nên trả 100 và ghi `threads=100`. Stage 3 tính sau đó: key đã có, `props.get('threads','200')` trả `'100'`. Stage 4 cũng trả `'100'`. Stage 1 dùng `__P(threads,50)` (không ghi) nên vẫn là 50. Thứ tự này không phụ thuộc thời điểm JMeter tính thuộc tính (đầu test hay đầu từng nhóm), vì stage 2 luôn được tính trước 3 và 4.
- **Vì sao smoke không thấy:** smoke bậc dùng `-Jthreads=1`, nên key đã tồn tại và mọi bậc đều là 1 VU (log `Starting thread group... threads=1` cho bốn nhóm). Không lượt smoke nào chạy nhánh không có `-Jthreads`.
- **Hệ quả `[INFERENCE]`, chưa chạy lại theo yêu cầu:** lệnh chuẩn không có `-J` sinh bậc 50 → 100 → 100 → 100 VU. Không bao giờ chạm 200 và 290 VU, nên điểm gãy ở tải cao không được tìm; bậc 3 và 4 chỉ lặp lại bậc 2 nhưng giỏ hàng và đơn hàng đã tích lũy thêm, nên số đo của bậc 3/4 không phải "tải cao hơn" mà là "cùng tải, trạng thái nặng hơn". Báo cáo Stress sẽ ghi sai tên bậc.
- **Cách sửa:** dùng `Properties.getProperty(key, default)` (hàm Java thật, không ghi gì) cho mọi lần đọc property có default: dòng 383, 720, 1057 đổi `props.get('threads'\,'N')` thành `props.getProperty('threads'\,'N')`. Cho đồng nhất, đổi luôn `props.get('loops'\,'-1')`, `props.get('stage_smoke'\,'false')` ở dòng 48, 383, 385, 720, 722, 1057, 1059 (sau sửa các key này chỉ đọc, không bị ghi). Không đụng `props.get('stress.run')` một tham số (không phải DGM). Giá trị `-J` là chuỗi nên `getProperty` đọc được.
- **Kiểm tra sau sửa (giao Manager, chưa chạy):** reset SUT, Java 17, chạy `jmeter -n -t test-plans/23120190_Stress_20261117.jmx -Jduration=5 -Jrampup=1 -l /tmp/x.jtl -j /tmp/x.log` (không `-Jthreads`, không `-Jloops`) rồi `grep 'Starting thread group' /tmp/x.log`: phải thấy `threads=50`, `100`, `200`, `290`. Reset lại SUT sau lượt thử trước khi chạy đo chính thức.

### #S2 [Low] Think-time timer (dòng 224, 561, 898, 1235) – tên "Think time 500–1500 ms" nhưng giá trị là 250–750 ms

- **Vấn đề:** `ConstantTimer.delay=250`, `RandomTimer.range=500` (khoảng 250–750 ms, đúng thiết kế Stress). Tên element sao chép từ Load. Tên đó hiện trong GUI và dễ làm người đọc báo cáo ghi sai think-time Stress.
- **Cách sửa:** đổi `testname` thành `Think time 250–750 ms` ở bốn timer. Không đổi giá trị.

### #S3 [Info] Bậc tải có đủ cao để chạm điểm gãy không?

- **Cấu hình thiết kế:** 50/100/200/290 VU, think-time 250–750 ms (trung bình 0,5 s, 6 lần chờ mỗi vòng), ngưỡng dừng lỗi > 5% hoặc p95 > 2000 ms. Trần 290 do số tài khoản, không phải năng lực SUT.
- **Chưa có số đo nào để kết luận.** Smoke chỉ có 1 VU, p95 11–31 ms (log `STRESS_STAGE_SUMMARY`). Không có lần chạy nhiều VU nên không biết điểm gãy nằm ở đâu.
- **Suy luận từ code `[INFERENCE]`:** mỗi vòng ≈ 3,0 s chờ + 7 request vài chục ms, nên 290 VU cho khoảng 90 vòng/s ≈ 650 request/s (100 VU, mức mà #S1 đang cho, chỉ khoảng 225 request/s). SUT không băm mật khẩu (`server.js:46`, so chuỗi), mọi truy vấn là SELECT/INSERT đơn giản, nên chi phí mỗi request thấp. Hai chỗ tăng chi phí theo thời gian, không theo VU: `GET /api/cart` trả cả giỏ không bao giờ bị xóa (`server.js:289-295`, mỗi vòng +1 phần tử/người dùng) và `GET /api/orders/my-orders` quét bảng `orders` (không có chỉ mục; `database.js:74-81` chỉ có khóa chính) rồi sắp xếp, trong khi bảng `orders` không bị xóa trong cả lần chạy (cỡ hàng chục nghìn đơn khi hết bậc 4). Vì vậy suy giảm nếu có nhiều khả năng đến từ tích lũy qua các bậc chứ không chỉ từ VU, và các bậc không so sánh "sạch" với nhau.
- **Máy dùng chung:** JMeter chạy JSR223 assertion (`JsonSlurper` mỗi sample, có `json.any` trên products/my-orders) cùng máy với SUT (6 nhân/12 luồng). Ở vài trăm request/s, CPU phía JMeter có thể làm tăng `elapsed` khi SUT chưa quá tải. Cần theo dõi CPU của cả `jmeter` và `node` khi chạy (`monitor_backend.sh` hiện chỉ theo dõi `node`).
- **Kết luận cho mục này:** không phải lỗi plan. Cấu hình đúng thiết kế là mức cao nhất khả thi với 290 tài khoản. Nếu 290 VU không vượt ngưỡng thì báo cáo ghi "chưa tìm được điểm gãy trong phạm vi thiết kế", đúng như `02_test_design.md`. Phải sửa #S1 trước, vì hiện tại plan không bao giờ lên đến 290.

### #S4 [Info] Tổng thời gian chạy hợp lý

- 4 × 150 s = 600 s (dòng 49 `duration=150` tính cả ramp 30 s; nhóm kết thúc theo thời điểm tuyệt đối, thread chỉ dừng giữa các sampler). Cộng vài giây chuyển nhóm; ở smoke các nhóm nối nhau trong khoảng 0,01–0,1 s. Trường hợp SUT treo: `response_timeout=30000` (dòng 28) có thể kéo dài mỗi bậc thêm tối đa khoảng 30 s do sampler đang chờ, nên dự trù khoảng 10–12 phút. Gate fail thì dừng sớm.
- 120 s ổn định mỗi bậc: ở 290 VU khoảng 94 vòng/s × 120 s ≈ 11 000 vòng `[INFERENCE]`; đủ mẫu cho p95 của TOTAL và theo nhãn. Bậc 1 (50 VU, khoảng 16 vòng/s) cũng đủ.
- JTL ở bậc cuối khoảng 100 000 dòng, cả bốn bậc cỡ vài trăm nghìn dòng `[INFERENCE]`; HTML report vẫn sinh được, nên dùng `-e -o` vào thư mục mới.

### #S5 [Info] Failure gate: trạng thái assertion và giới hạn

Đã kiểm tra, **không có lỗi**:

- Điều kiện đếm lỗi: `!prev.isSuccessful() || AssertionResult.isFailure() || AssertionResult.isError()` trong khối `finally`, nên chạy cả khi assertion ném lỗi (catch gán `setFailure(true)`) lẫn khi `return` sớm. Sampler lỗi HTTP (403, 5xx) có `prev.isSuccessful()=false`; HTTP 200 nhưng sai nội dung bị bắt bởi `AssertionResult`. `elapsed.add` và `fail++` nằm trong `synchronized(props)`, cổng đọc cũng trong `synchronized(props)`: không đua.
- Bằng chứng runtime: stop-gate Java 17: login 403 → JTL một sample `success=false`, log `STRESS_GATE previous=1 samples=1 errors=100.0 p95_ms=23 continue=false`, stage 2 `allowed=false`, rồi `Test stopped - no more thread groups will be started`; không có HTTP sample của bậc 2. Stage smoke: ba lần `continue=true`, p95 31/14/11 ms, lỗi 0%.
- Mẫu `Negative login` bị loại khỏi `elapsed`/`fail` (`if label != 'Negative login'`). Chỉ kiểm tra tĩnh: không smoke nào chạy nhánh này trong Stress (stage smoke dùng `lock_percent` mặc định 5% với một vòng mỗi nhóm nên không chọn trúng).

Giới hạn cần biết khi đọc kết quả:

1. **Gate chỉ ở ranh giới bậc.** Bậc 4 không có bậc sau nên không bị gate đánh giá; lỗi ở bậc 4 chỉ thấy ở JTL và `STRESS_STAGE_SUMMARY`. Đây là thiết kế.
2. **`STRESS_STAGE_SUMMARY` không chạy khi gate dừng test.** Log stop-gate có `Starting tearDown thread groups` nhưng không có `Thread started: Stress final summary` và không có `STRESS_STAGE_SUMMARY`; plan không có `TestPlan.tearDown_on_shutdown` (`grep` = 0), mặc định tắt. Không mất dữ liệu: `STRESS_GATE` đã ghi samples/lỗi/p95 của bậc vừa bị đánh giá, `STRESS_STAGE_START` có mốc thời gian, JTL có đủ mẫu. Chỉ cần biết để không tìm summary trong log của lần chạy bị dừng.
3. **Mẫu số của error%.** Các `IfController` bỏ bước phụ thuộc khi bước trước lỗi, nên tỷ lệ lỗi của gate tính trên các sample đã gửi. Giống Load #9: khi báo cáo nêu số sample từng nhãn.
4. **p95 tính cả 30 s ramp**, đúng thiết kế (gate toàn bậc); phân tích ổn định sau ramp cần JTL riêng.

## Kiểm tra bổ sung Stress

| Câu hỏi | Kết quả |
|---|---|
| Các bậc đủ cao để chạm điểm gãy? | Chưa biết (#S3); và chạy mặc định hiện chỉ lên 100 VU (#S1). |
| Tổng thời gian hợp lý? | Có: 600 s nếu không dừng sớm (#S4). |
| Lockout làm hỏng luồng chính? | Không (mục Lockout ở trên). |
| Một listener? | Có, Aggregate Report. |

---

# Spike – `23120190_Spike_20261117.jmx`

## Danh sách lỗi

Không có lỗi Medium/High. Ba ghi chú Low/Info:

### #P1 [Low] Dòng 48, 329, 331, 333 – cùng mẫu `props.get(key, default)` như #S1 (hiện vô hại)

- **Vấn đề:** `props.get('loops'\,'-1')`, `props.get('timeline_smoke'\,'false')`, `props.get('spike_threads'\,'190')`, `props.get('spike_delay'\,'120')` ghi default vào props (cơ chế ở #S1). Ở Spike không gây sai số: giá trị được ghi chính là default đang dùng (`loops=-1`, `spike_threads=190`, `spike_delay=120`) và không chỗ nào khác đọc cùng key với default khác. Không quan sát được hậu quả.
- **Cách sửa:** đổi sang `props.getProperty(...)` cùng đợt với #S1 để không sao chép mẫu này. Không bắt buộc.

### #P2 [Info] Spike có thật sự tăng vọt, ramp vài giây?

- **Ramp:** burst `num_threads=190` với `ramp_time=${__P(spike_rampup,5)}` = 5 s (dòng 330) ≈ 38 VU/s. Baseline 10 VU, ramp 10 s. Tổng 200 VU sau 5 s so với 10 VU trước đó: tăng 20 lần số VU. `delay=120` s (dòng 333, giá trị khi `loops=-1`), `duration=120` s (dòng 332) nên burst kết thúc ở ~240 s; baseline tiếp tục đến 360 s: **120 s thấp, 120 s cao, 120 s phục hồi**. Ramp tính bằng giây, không phải phút.
- **Bằng chứng runtime (compressed, 1 VU mỗi nhóm):** burst bắt đầu ở 7.69 s (delay 8 s) và kết thúc ở 15.61 s (delay + duration = 16 s), baseline có mẫu suốt 0–23.2 s (thấp → cao → thấp theo `threadName`). Smoke này kiểm tra lịch và cơ chế, **không** phải bằng chứng cho 190 VU trong 5 s.
- **Độ cao tuyệt đối `[INFERENCE]`:** think-time 500–1500 ms như Load (đúng thiết kế): mỗi vòng ≈ 6 s, nên 200 VU ≈ 32 vòng/s ≈ 230 request/s, baseline 10 VU ≈ 11 request/s. Đỉnh tuyệt đối thấp hơn khoảng 650 request/s của Stress bậc 4, nên Spike có thể không làm SUT suy giảm dù tăng 20 lần trong 5 s. Đây là kết quả thiết kế, không phải lỗi; nếu không thấy suy giảm thì nêu rõ khi phân tích: spike kiểm tra tốc độ thay đổi, không phải trần tải.

### #P3 [Info] Tổng thời gian, pool, listener

- 360 s đúng thiết kế (dòng 49): hợp lý cho ba pha 120 s. Request đang chạy có thể hoàn tất muộn vài giây sau 240 s.
- Pool chung `spike.accounts` đúng (mục Pool). `spike_threads` > 280 sẽ ném `IllegalStateException` vì baseline đã giữ 10 tài khoản.
- Một `ResultCollector` Response Time Graph (dòng 606), khác Load và Stress. Plan không có gate hay summary (đúng thiết kế).
- Login là request đầu của vòng và không có think-time trước nó, nên 190 VU burst gửi login ngay khi khởi chạy: đỉnh ≈ 38 login/s trong 5 s đầu `[INFERENCE]`. SUT không băm mật khẩu nên không ảnh hưởng đáng kể.

## Kiểm tra bổ sung Spike

| Câu hỏi | Kết quả |
|---|---|
| Có tăng vọt thật, ramp vài giây? | Có: 5 s (#P2). |
| Tổng thời gian hợp lý? | Có: 360 s (120/120/120). |
| Lockout làm hỏng luồng chính? | Không (mục Lockout ở trên). |
| Pool dùng chung, không trùng tài khoản? | Có (200 ≤ 290). |
| Một listener? | Có, Response Time Graph. |

---

## Việc cần làm theo thứ tự

1. Sửa #S1 trong Stress JMX (người/agent được giao sửa; reviewer không sửa). Nên kèm #P1 và #S2.
2. Reset SUT, đặt Java 17, rồi kiểm tra thread count mặc định như mô tả ở #S1 trước khi chạy đo chính thức; reset lại sau lượt kiểm tra.
3. Spike không cần sửa để chạy đo. Chạy từ thư mục `hw05`, Java 17, `scripts/reset_sut.sh` trước mỗi lượt.

Chưa kiểm tra: hành vi nhiều VU của cả hai plan (chưa có lần chạy nào), nhánh `Negative login` trong số liệu gate, và kích thước JTL/HTML thực tế.

## Đã sửa

Nguyên nhân bỏ sót là nhận định `[INFERENCE]` từ plan và smoke, không phải kết luận về quá trình nội bộ của model.

| Lỗi | Đã sửa | Vì sao AI có thể bỏ sót |
|---|---|---|
| #S1 High – default thread bị ghi vào props | Dùng `getProperty(key, default)` cho các property có default trong Stress; giữ `props.get(key)` cho object state. Sửa cùng mẫu scheduler trong Load. | Manager sinh plan hiểu nhầm overload `Groovy Map.get`: tưởng chỉ đọc default, không biết nó ghi default; smoke override `threads` nên không phơi bày lỗi default. |
| #S2 Low – tên timer sai | Đổi tên cả bốn timer Stress thành `Think time 250–750 ms`, không đổi giá trị timer. | Manager sao chép tên từ Load nhưng bỏ sót đối chiếu với giá trị timer Stress. |
| #P1 Low – đọc default có tác dụng phụ | Dùng `getProperty(key, default)` cho các property có default trong Spike. | Cùng hiểu nhầm overload `Groovy Map.get`; smoke override `threads` và không kiểm tra tác dụng phụ của default. |

Chưa chạy smoke cho bản mới; kết quả smoke cũ không xác nhận bản sửa. Cần reset SUT trước mỗi lượt smoke Stress và Spike, dùng Java 17; kiểm tra thêm thread count mặc định Stress như #S1, không truyền `-Jthreads` hoặc `-Jloops`.
