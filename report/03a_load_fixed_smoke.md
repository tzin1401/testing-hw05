# Bước 6 – Load smoke sau khi sửa

**Kết quả: PASS.** Cả lượt thường và lượt negative đều kết thúc bình thường; JMeter summary lần lượt báo 14/14 và 8/8 samples, `Err: 0 (0.00%)`. Mỗi lượt đều reset SUT trước khi chạy (backend lần lượt PID `385476`, `387324`; 300 users seeded). Java: `JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64`, JMeter 5.6.3. Timeout cho mỗi lệnh chạy JMeter: 90 giây.

## Lượt thường

```sh
jmeter -n -t test-plans/23120190_Load_20261117.jmx -Jthreads=1 -Jrampup=1 -Jloops=2 -l results/smoke/step6_load_20261117.jtl -j results/smoke/step6_load_20261117.log
```

Có 14 samples, hai lần cho mỗi sampler chính. Mọi sample có `success=true`, `failureMessage` rỗng; cả 14 đều trả HTTP 200:

| Label | Samples | Code | Success | failureMessage |
|---|---:|---:|---|---|
| 01 Login | 2 | 200 | true | rỗng |
| 02 Products | 2 | 200 | true | rỗng |
| 03 Product detail | 2 | 200 | true | rỗng |
| 04 Add cart | 2 | 200 | true | rỗng |
| 05 Get cart | 2 | 200 | true | rỗng |
| 06 Checkout | 2 | 200 | true | rỗng |
| 07 My orders | 2 | 200 | true | rỗng |

Controller mặc định chọn negative login 0 lần trong lượt này; không có negative sample/failure cần tách riêng. Không phát hiện sampler fail.

## Lượt negative

Chạy sau reset SUT, một vòng với `lock_percent=100`:

```sh
jmeter -n -t test-plans/23120190_Load_20261117.jmx -Jthreads=1 -Jrampup=1 -Jloops=1 -Jlock_percent=100 -l results/smoke/step6_negative_20261117.jtl -j results/smoke/step6_negative_20261117.log
```

Có 8 samples, `Err: 0 (0.00%)`. Bảy sampler chính pass (code 200, `success=true`, `failureMessage` rỗng); Negative login trả 401 và cũng `success=true`, `failureMessage` rỗng, đúng assertion chấp nhận 401/403:

| Label | Code | Success | failureMessage |
|---|---:|---|---|
| 01 Login | 200 | true | rỗng |
| Negative login | 401 | true | rỗng |
| 02 Products | 200 | true | rỗng |
| 03 Product detail | 200 | true | rỗng |
| 04 Add cart | 200 | true | rỗng |
| 05 Get cart | 200 | true | rỗng |
| 06 Checkout | 200 | true | rỗng |
| 07 My orders | 200 | true | rỗng |

**Nguồn bằng chứng:** `results/smoke/step6_load_20261117.jtl` và `results/smoke/step6_negative_20261117.jtl` (đọc sample fields `label`, `responseCode`, `success`, `failureMessage`); JMeter logs tương ứng `results/smoke/step6_load_20261117.log` và `results/smoke/step6_negative_20261117.log` (lệnh, summary và lỗi). JTL được giữ nguyên, không chỉnh sửa. Không cập nhật AI_LOG.
