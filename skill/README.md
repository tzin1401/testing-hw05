# Agent Skill: `perf-endpoint-group`

Skill này đóng gói quy trình kiểm thử hiệu năng và phân tích log của HW05, để dùng lại cho các nhóm endpoint khác. Chỉ cần gõ một lệnh, skill chạy từ đầu đến cuối:

```
/perf-endpoint-group <auth|read|transactional|đường/dẫn/group.json> [smoke|load]
```

| Bước | Ai làm | Việc |
|---|---|---|
| 1 | `scripts/gen_plan.py` | Sinh file `.jmx` từ định nghĩa nhóm (JSON) |
| 2 | `scripts/run.sh` | Reset SUT, chạy JMeter non-GUI và theo dõi RAM backend |
| 3 | `scripts/analyze.py` | Tính số liệu từ `.jtl` thô (nearest-rank), kiểm SLO → PASS/FAIL |
| 4 | AI | Viết `report.md`, phần phân tích ghi là "giả thuyết" |
| 5 | `scripts/check_claims.py` | Kiểm tra mọi con số AI viết đều có trong `summary.json`, chặn số bịa |
| 6 | Sinh viên | Kiểm theo checklist mục C của report |

**Thêm endpoint mới:** chép một file trong `perf-endpoint-group/groups/` rồi sửa path, body và SLO. Không cần sửa code. Schema ở `perf-endpoint-group/references/group-schema.md`.

**Đăng ký slash command cho Claude Code:** `.claude/skills/perf-endpoint-group` là symlink trỏ tới thư mục này.

## Đã kiểm thử (2026-11-19, chạy thật trên SUT)

| Lần chạy | Kết quả | Thư mục |
|---|---|---|
| `read`, `auth`, `transactional`, mỗi nhóm 5 VU × 30 s | Cả 3 PASS, 0 lỗi | `results/skill/*_20261119-0050*`, `*-005149` |
| Nhóm cố ý sai path (`/api/nope`) | FAIL đúng: lỗi 100%, mã 404 | Đã xóa sau khi kiểm |
| Agent mới làm theo SKILL.md: `/perf-endpoint-group transactional` | PASS. `check_claims` bắt được 1 số không có nguồn, agent đã sửa | `results/skill/transactional_20261119-005420` |
| Video demo trên omp (gpt-6.1-sol): `/skill:perf-endpoint-group transactional`, 20 VU × 120 s | PASS: 2260 request, 0% lỗi, Checkout p95 14 ms; `check_claims` OK. Video: https://youtu.be/1NvKtbFaqGs | `results/skill/transactional_20261119-114919` |
