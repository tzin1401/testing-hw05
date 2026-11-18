# Agent rules – HW05 Performance Testing

Đây là quy tắc cho AI agent khi hỗ trợ làm HW05. Nguồn: `2026.HW05.Performance Testing_En.pdf`.

## 1. Ghi AI log (chỉ khi được yêu cầu)

- **Chỉ ghi log khi prompt (của người dùng hoặc của Manager giao xuống) có cụm "ghi vào log", không phân biệt hoa thường.** Prompt nào không có cụm này thì **không ghi**.
- Ghi bằng cách **nối thêm** (append) vào `report/AI_LOG.md`. Không sửa, không xóa các entry cũ.
- Mỗi entry đúng định dạng dưới đây (theo Mục 9 của đề):

```markdown
## #<số thứ tự> – <YYYY-MM-DD HH:MM> (giờ VN)
- **AI tool:** Claude Code (<model id>)
- **Bước:** <Task 1 – Load plan | Task 2 – Phân tích .jtl | ...>
- **Prompt:**
  > <nguyên văn prompt của người dùng, bỏ cụm "ghi vào log">
- **AI output:**
  > <tóm tắt output: AI đã làm gì, file nào được tạo/sửa, kết luận chính>
- **Human review:** _(để trống – người dùng tự điền)_
```

- Lấy thời gian bằng lệnh `date "+%Y-%m-%d %H:%M"`. Không được tự đoán giờ.
- Không bao giờ tự điền mục "Human review". Mục này là phần của sinh viên.

## 2. Quy tắc làm bài (bắt buộc tuân theo)

### AI-first, từng bước
- Hướng dẫn AI đi qua từng bước kỹ thuật. Không giải bằng một prompt chung chung kiểu "chạy load test rồi đánh giá".
- Mỗi lần trả lời chỉ làm một bước nhỏ, rồi dừng lại để người dùng review.

### Không được bịa (Anti-AI-Cheat, Mục 11)
- **Không** tạo hoặc sửa file `.jtl`. File `.jtl` chỉ được sinh ra từ lần chạy JMeter thật.
- **Không** bịa số liệu: RPS, p95, error %, RAM. Mọi số phải trích từ `.jtl`, từ HTML report hoặc từ output monitor thật.
- **Không** bịa hardware report, hostname hay nội dung video.

### Quy ước tên file
| Loại | Tên |
|---|---|
| Test plan | `{StudentID}_{Load\|Stress\|Spike}_{YYYYMMDD}.jmx` |
| File nộp | `<StudentID>_HW05_AI_Performance_<điểm 3 chữ số>.zip` |

### Yêu cầu của test plan
- Cả 3 plan dùng **cùng một workflow**, phủ đủ 3 nhóm endpoint: Auth, Read và Transactional. Flow đã chọn ghi trong `HW05_CHON_WORKFLOW.pdf`.
- Dữ liệu đầu vào lấy từ CSV trong `data/`.
- Mỗi plan dùng một loại listener/report **khác nhau**, không lặp lại.
- Chạy ở chế độ non-GUI để sinh `.jtl` và HTML report:

  ```bash
  jmeter -n -t <plan>.jmx -l results/jtl/<tên>.jtl -e -o results/html/<tên>/
  ```

- Chạy `scripts/reset_sut.sh` trước mỗi lần chạy test. Bước này gỡ lockout và reset DB.

### Đặc điểm SUT đã kiểm chứng
- Login sai **2 lần** là bị khóa trong **180 giây** (spec ghi 3 lần, 30 giây).
- Restart backend thì DB bị reset.

### Task 2 – Phân tích bằng AI
- Mỗi chỗ AI đọc sai metric phải **trích giá trị đúng từ `.jtl`**.
- Mỗi đề xuất tối ưu phải được phân loại là **feasible** hoặc **hallucinated**, kèm lý do, đối chiếu với `eshop-sut/backend/server.js`.

### Git
- Repo: https://github.com/tzin1401/testing-hw05 (remote `origin`, nhánh `main`). Bug log tại trang Issues của repo. Agent không tự push và không tự tạo issue.
- Mỗi bước là **một commit riêng**: từng test plan, phân tích AI, đề xuất Continuous Performance Testing.
- Chỉ commit khi người dùng yêu cầu.

### Tài liệu
- Mọi tài liệu viết bằng Markdown và để trong `report/`.
- Đề có quy định: copy giữa các sinh viên, **kể cả copy prompt**, thì cả hai bị 0 điểm. Không được dùng prompt hay file của thành viên khác.

## 3. Thư mục

| Thư mục | Chứa |
|---|---|
| `test-plans/` | File `.jmx` |
| `data/` | File CSV |
| `results/jtl/`, `results/html/` | Log thô và HTML report |
| `evidence/` | Ảnh chụp JMeter + htop, hardware report |
| `report/` | Báo cáo, `AI_LOG.md`, AI Critique |
| `skill/` | Agent Skill |
| `scripts/` | `reset_sut.sh` |
