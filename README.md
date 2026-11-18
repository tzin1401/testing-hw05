# HW05 – Kiểm thử hiệu năng EShop

Sinh viên 23120190, Flow 1. [Báo cáo chính](report/MAIN_REPORT.md) gộp Task 1–3, Agent Skill và AI Critique. Ngoài ra có [AI Audit Report](report/AI_AUDIT_REPORT.md), [AI Critique](report/AI_CRITIQUE.md) và [Git log](report/GIT_LOG.md).

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

[Bug report](report/09_bugs.md): 4 bug có bằng chứng (3 theo FR-02/FR-08, 1 mật khẩu plaintext theo SEC-01 tham khảo), 1 finding Low về kiểu giá và 1 vấn đề hiệu năng (Spike). Cả 6 đã đăng tại [GitHub Issues](https://github.com/tzin1401/testing-hw05/issues) (#1–#6), ảnh chụp ở [evidence/issues/](evidence/issues/).

**Video demo (YouTube, unlisted):**

| Kịch bản | Link |
|---|---|
| Load | https://youtu.be/gI2pvrCkcQg |
| Stress | https://youtu.be/1ZFqomMaMFU |
| Spike | https://youtu.be/qH1VOzb8fZU |
| Soak | https://youtu.be/ADsnkwwEeRE |
| Agent Skill | _(bổ sung sau khi quay)_ |

## Task 2 – Phân tích AI

[Báo cáo Task 2](report/TASK2_REPORT.md) tổng hợp phân tích AI, đối chiếu [ground truth](results/analysis/ground_truth.md) tính bằng [script](scripts/jtl_truth.py) và [human review](report/14_human_review_task2.md), cùng đánh giá các đề xuất tối ưu.

## Task 3 – Continuous Performance Testing

[Báo cáo Task 3](report/TASK3_REPORT.md) tổng hợp mô hình theo dõi commit, luật gate, flow chart và trade-off; [demo trên commit thật](report/17_cpt_demo.md), [rà soát độc lập](report/18_task3_check.md) và [nhận định của sinh viên](report/19_human_review_task3.md) ghi bằng chứng và giới hạn. CI chưa triển khai; baseline vận hành và policy các tầng sâu chưa được duyệt.

## Agent Skill

[`skill/perf-endpoint-group`](skill/README.md): một lệnh `/perf-endpoint-group <auth|read|transactional|group.json> [smoke|load]` chạy trọn quy trình: sinh plan → reset SUT → JMeter non-GUI + monitor → số liệu tính từ JTL → SLO PASS/FAIL → AI phân tích → script kiểm mọi con số AI viết. Thêm endpoint mới chỉ cần một file JSON. Kết quả kiểm thử thật ở [skill/README.md](skill/README.md).

## Bắt đầu và tái lập

Chạy từ thư mục gốc `hw05`, cần JMeter 5.6.3, Java 17, Node.js và Python; cần tự lấy [SUT EShop upstream](https://github.com/ttbhanh/eshop-sut) vào `eshop-sut/`: thư mục này bị Git ignore, không được bao gồm trong repo bài làm ([môi trường](report/00_environment.md)). Các prerequisite dự án gồm [reset](scripts/reset_sut.sh), [gen_users.py](scripts/gen_users.py), [users.csv](data/users.csv) và các [CSV đầu vào](data/README.md). Reset sẽ restart backend và xóa trạng thái dữ liệu/giỏ/lockout; chạy trước **mỗi** lần đo.

```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"
scripts/reset_sut.sh
jmeter -n -t test-plans/23120190_Load_20261117.jmx -l results/jtl/load_new.jtl -e -o results/html/load_new/
```

Đổi tên JTL và thư mục HTML chưa tồn tại cho từng lần chạy; không ghi đè dữ liệu cũ. Lệnh đầy đủ cho từng plan, monitor và metadata thực tế ở [run log](report/07_run_log.md); Soak phải dùng `-Jwriter_file` trỏ tới một JTL mới **khác** `-l`, tránh cộng trùng hai bản ghi. Lệnh phân tích lại từ JTL canonical và monitor ở [endurance report](report/08_endurance.md); cần đường dẫn output mới nếu muốn giữ nguyên phân tích hiện tại.
