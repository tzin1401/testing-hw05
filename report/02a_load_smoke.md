# Bước 4 – Load smoke verification

**Kết quả: FAIL; không chạy negative test.** Đã chạy `scripts/reset_sut.sh` trước lượt đầu; reset thành công, backend PID `345383`, 300 users seeded.

Command (timeout 90s):

```sh
jmeter -n -t test-plans/23120190_Load_20261117.jmx -Jthreads=1 -Jrampup=1 -Jloops=1 -l /tmp/hw05-load-check.jtl -j /tmp/hw05-load-check.log
```

JMeter loaded the plan but aborted while the `Load users 1-1` thread compiled `Script2.groovy`: `GroovyBugError: ... Unsupported class file major version 69` (Groovy 3.0.20; JMeter 5.6.3). Log cause: `java.lang.IllegalArgumentException: Unsupported class file major version 69`. Summary reported `0 in 00:00:00` samples and no errors; the JTL contains only its CSV header, no samples. Thus sample count is 0; labels, success values, and failureMessage values: none. The seven expected samplers (`01 Login`, `02 Products`, `03 Product detail`, `04 Add cart`, `05 Get cart`, `06 Checkout`, `07 My orders`) were not exercised. No negative run was attempted because the first run failed.

Failure log retained at `/tmp/hw05-load-check.log`; JTL retained for evidence. The JMeter/Groovy runtime class-file incompatibility prevented verification; no plan changes were made.

## Lượt Java 17 và sửa cấu hình extractor

Log `/tmp/hw05-load-java17.log` ghi JMeter 5.6.3 với Java `17.0.21.0.3`. Tại `01 Login`, `JSONPostProcessor.getMatchNumbersAsInt` ném `ArrayIndexOutOfBoundsException: Index 0 out of bounds for length 0`; summary ghi 0 sample. Đây là lỗi xử lý sau request login, không phải bằng chứng workflow pass.

Đối chiếu bytecode của `JSONPostProcessor` trong `ApacheJMeter_components.jar` bằng `javap -c -p`: các key native là `JSONPostProcessor.referenceNames`, `JSONPostProcessor.jsonPathExprs`, `JSONPostProcessor.match_numbers`, `JSONPostProcessor.defaultValues`; các danh sách dùng dấu `;`. `process()` tách default bằng `String.split(";")` và cấp phát mảng match theo số default. Giá trị cũ `;` chỉ gồm delimiter nên split trả mảng rỗng, trong khi match `1;1` có hai phần tử, gây lỗi truy cập mảng. Default rỗng của extractor checkout cũng không phù hợp để biểu diễn rõ một giá trị default.

Đã đổi default login thành `NOT_FOUND;NOT_FOUND` và checkout thành `NOT_FOUND`, giữ match `1;1`/`1`, tên biến và JSONPath tương ứng. Không thay workflow hay tham số. Chưa chạy lại JMeter sau sửa; chưa xác nhận pass.

## Java 17 smoke sau sửa extractor

Thiết lập `JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64`, prepend `$JAVA_HOME/bin` vào `PATH`. Cả hai lượt dùng JMeter 5.6.3; chạy `scripts/reset_sut.sh` thành công trước mỗi lượt (300 users seeded). Mỗi lệnh có timeout 90 giây.

### Lượt thường

Lệnh: `jmeter -n -t test-plans/23120190_Load_20261117.jmx -Jthreads=1 -Jrampup=1 -Jloops=1 -l /tmp/hw05-load-fixed.jtl -j /tmp/hw05-load-fixed.log`

Kết quả: 7 samples, `Err: 0 (0.00%)`. Cả bảy sampler chính đều pass:

| Label | Code | Success | failureMessage |
|---|---:|---|---|
| 01 Login | 200 | true | _(rỗng)_ |
| 02 Products | 200 | true | _(rỗng)_ |
| 03 Product detail | 200 | true | _(rỗng)_ |
| 04 Add cart | 200 | true | _(rỗng)_ |
| 05 Get cart | 200 | true | _(rỗng)_ |
| 06 Checkout | 200 | true | _(rỗng)_ |
| 07 My orders | 200 | true | _(rỗng)_ |

### Lượt negative (`lock_percent=100`)

Lệnh: `jmeter -n -t test-plans/23120190_Load_20261117.jmx -Jthreads=1 -Jrampup=1 -Jloops=1 -Jlock_percent=100 -l /tmp/hw05-load-fixed-negative.jtl -j /tmp/hw05-load-fixed-negative.log`

Kết quả: 8 samples, `Err: 0 (0.00%)`. Bảy sampler chính pass như lượt thường; negative login trả 401 và được kỳ vọng là thành công:

| Label | Code | Success | failureMessage |
|---|---:|---|---|
| 01 Login | 200 | true | _(rỗng)_ |
| Negative login | 401 | true | _(rỗng)_ |
| 02 Products | 200 | true | _(rỗng)_ |
| 03 Product detail | 200 | true | _(rỗng)_ |
| 04 Add cart | 200 | true | _(rỗng)_ |
| 05 Get cart | 200 | true | _(rỗng)_ |
| 06 Checkout | 200 | true | _(rỗng)_ |
| 07 My orders | 200 | true | _(rỗng)_ |

Nguồn: JTL `/tmp/hw05-load-fixed.jtl`, `/tmp/hw05-load-fixed-negative.jtl` và log tương ứng. Tạm giữ JTL để lưu bằng chứng; không chỉnh sửa JTL.

## Lưu ý bằng chứng bước 4

Hai file `/tmp/hw05-load-fixed.jtl` và `/tmp/hw05-load-fixed-negative.jtl` đã được xóa sau khi trích bằng chứng theo yêu cầu bước 4; các kết quả cũ ở trên được giữ nguyên. Chúng không xác nhận kết quả smoke của plan sau sửa bước 6.
