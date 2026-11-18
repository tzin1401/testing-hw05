# HW05 – Kiểm thử hiệu năng EShop

Báo cáo này tổng hợp Task 1 và Task 2; Task 3 và Agent Skill không được xác nhận hoàn thành ở bước này. Xem [báo cáo Task 1](report/TASK1_REPORT.md), [AI log](report/AI_LOG.md) và [snapshot Git log](report/GIT_LOG.md).

## Tự đánh giá

Thang điểm theo [Mục 15 của đề](2026.HW05.Performance%20Testing_En.pdf); sinh viên tự điền điểm.

| Tiêu chí | Điểm tối đa | Tự chấm |
|---|---:|---:|
| Task 1 – Load testing | 30 | |
| Task 1 – Stress testing | 20 | |
| Task 1 – Spike testing | 20 | |
| Task 2 – AI analysis và misinterpretation hunt | 10 | |
| Task 3 – Continuous Performance Testing | 10 | |
| Agent Skill | 10 | |
| Tổng | 100 | |

## Tóm tắt kiểm thử

Workflow bao phủ **Auth** (`POST /api/login`), **Read** (list/detail products) và **Transactional** (cart, checkout, my-orders), chi tiết tại [phân tích API](report/01_api_analysis.md). Nguồn số liệu tổng hợp là entry `Total` trong statistics JSON của từng run, gồm negative login được chấp nhận; số liệu luồng chính riêng được giải thích ở [run log](report/07_run_log.md).

| Kịch bản | Tổng samples | p95 ms | RPS | Lỗi tổng | Kết quả và dữ liệu |
|---|---:|---:|---:|---:|---|
| Load | 33,775 | 11 | 56.344 | 0% | [JSON](results/html/23120190_Load_20261118/statistics.json) · [HTML](results/html/23120190_Load_20261118/index.html) · [JTL](results/jtl/23120190_Load_20261118.jtl) |
| Stress | 175,882 | 1,023 | 293.092 | 0% | [JSON](results/html/23120190_Stress_20261118/statistics.json) · [HTML](results/html/23120190_Stress_20261118/index.html) · [JTL](results/jtl/23120190_Stress_20261118.jtl) |
| Spike | 27,965 | 17 | 77.926 | 0% | [JSON](results/html/23120190_Spike_20261118/statistics.json) · [HTML](results/html/23120190_Spike_20261118/index.html) · [JTL](results/jtl/23120190_Spike_20261118.jtl) |
| Soak | 158,591 | 21 | 220.332 | 0% | [JSON](results/html/23120190_Soak_20261118/statistics.json) · [HTML](results/html/23120190_Soak_20261118/index.html) · [JTL](results/jtl/23120190_Soak_20261118.jtl) |

Theo [endurance JSON](results/analysis/endurance.json) và [phân tích](report/08_endurance.md), bậc Stress cao nhất quan sát ổn định sau ramp là 290 VU, 468.556 RPS, p95 947 ms; chưa tìm thấy điểm vượt trong phạm vi này. Đây không chứng minh sức chịu tải liên tục 12 phút. Soak 203 VU có phút index 3 đạt p95 2.244 ms, 171.183 RPS, 0% lỗi, vượt ngưỡng 2.000 ms dù p95 tổng là 21 ms. RSS max quan sát Stress 171.64 MiB, Soak 127.80 MiB; slope Soak 1.470 MiB/phút không chứng minh trần RAM hay leak.

[Bug report](report/09_bugs.md): 4 bug có bằng chứng (3 theo FR-02/FR-08, 1 mật khẩu plaintext theo SEC-01 tham khảo), thêm 1 finding Low về kiểu giá với spec chưa rõ; episode hiệu năng là quan sát riêng. [API GitHub Issues](https://api.github.com/repos/tzin1401/testing-hw05/issues?state=all&per_page=100) trả `[]` lúc Manager kiểm tra: 0 issue quan sát, không khẳng định trạng thái về sau. Sinh viên tự đăng tại [GitHub Issues](https://github.com/tzin1401/testing-hw05/issues) và bổ sung ảnh/URL.

**Video YouTube:** sinh viên bổ sung URL unlisted; chưa có URL. Cần video ít nhất 6 phút, thuyết minh tiếng Việt của sinh viên, theo [đề](2026.HW05.Performance%20Testing_En.pdf).

## Task 2 – Phân tích AI

[Báo cáo Task 2](report/TASK2_REPORT.md) tổng hợp phân tích AI, đối chiếu [ground truth](results/analysis/ground_truth.md) tính bằng [script](scripts/jtl_truth.py) và [human review](report/14_human_review_task2.md), cùng đánh giá các đề xuất tối ưu.

## Bắt đầu và tái lập

Chạy từ thư mục gốc `hw05`, cần JMeter 5.6.3, Java 17, Node.js và Python; cần tự lấy [SUT EShop upstream](https://github.com/ttbhanh/eshop-sut) vào `eshop-sut/`: thư mục này bị Git ignore, không được bao gồm trong repo bài làm ([môi trường](report/00_environment.md)). Các prerequisite dự án gồm [reset](scripts/reset_sut.sh), [gen_users.py](scripts/gen_users.py), [users.csv](data/users.csv) và các [CSV đầu vào](data/README.md). Reset sẽ restart backend và xóa trạng thái dữ liệu/giỏ/lockout; chạy trước **mỗi** lần đo.

```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"
scripts/reset_sut.sh
jmeter -n -t test-plans/23120190_Load_20261117.jmx -l results/jtl/load_new.jtl -e -o results/html/load_new/
```

Đổi tên JTL và thư mục HTML chưa tồn tại cho từng lần chạy; không ghi đè dữ liệu cũ. Lệnh đầy đủ cho từng plan, monitor và metadata thực tế ở [run log](report/07_run_log.md); Soak phải dùng `-Jwriter_file` trỏ tới một JTL mới **khác** `-l`, tránh cộng trùng hai bản ghi. Lệnh phân tích lại từ JTL canonical và monitor ở [endurance report](report/08_endurance.md); cần đường dẫn output mới nếu muốn giữ nguyên phân tích hiện tại.

## Việc sinh viên còn làm

Review AI log và các kết quả, tự điền cột Human review và điểm, tự đăng Issues và bổ sung ảnh, bổ sung URL video, hoàn thành Task 3 và Agent Skill, xuất PDF theo đề và tự push repo công khai. Những mục này chưa được báo cáo là hoàn thành.
