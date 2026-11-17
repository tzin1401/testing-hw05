# Bước 10 – Smoke test cả 3 plan

Chạy tuần tự, mỗi plan sau `scripts/reset_sut.sh`, JMeter 5.6.3 với Java 17; mỗi lần chạy kết thúc thành công. JTL là nguồn số liệu.

| Plan | Lệnh JMeter (sau reset) | JTL samples | Errors | Error % |
|---|---|---:|---:|---:|
| Load | `jmeter -n -t test-plans/23120190_Load_20261117.jmx -Jthreads=5 -Jloops=2 -Jrampup=1 -l results/smoke/23120190_Load_20261117.jtl -j results/smoke/23120190_Load_20261117_jmeter.log` | 70 | 0 | 0% |
| Stress | `jmeter -n -t test-plans/23120190_Stress_20261117.jmx -Jthreads=5 -Jloops=2 -Jrampup=1 -l results/smoke/23120190_Stress_20261117.jtl -j results/smoke/23120190_Stress_20261117_jmeter.log` | 70 | 0 | 0% |
| Spike | `jmeter -n -t test-plans/23120190_Spike_20261117.jmx -Jthreads=5 -Jloops=2 -Jrampup=1 -l results/smoke/23120190_Spike_20261117.jtl -j results/smoke/23120190_Spike_20261117_jmeter.log` | 70 | 0 | 0% |

## Samples/errors theo label

| Label | Load samples/errors | Stress samples/errors | Spike samples/errors |
|---|---:|---:|---:|
| 01 Login | 10/0 | 10/0 | 10/0 |
| 02 Products | 10/0 | 10/0 | 10/0 |
| 03 Product detail | 10/0 | 10/0 | 10/0 |
| 04 Add cart | 10/0 | 10/0 | 10/0 |
| 05 Get cart | 10/0 | 10/0 | 10/0 |
| 06 Checkout | 10/0 | 10/0 | 10/0 |
| 07 My orders | 10/0 | 10/0 | 10/0 |

Negative login: 0 samples for all three plans; no negative response codes to report. No JTL sample errors. Main workflow: 70 samples and 0% errors for each plan (expected 70). Runtime logs show plan loading and normal completion; searched for ERROR/Exception/parse/script failures and found none. The log lines containing `Parser for ...` are normal INFO parser registration, and `Thread will continue on error` is INFO thread-group configuration, not a runtime error.
