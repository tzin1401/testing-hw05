# AI Audit Report – HW05 Performance Testing

Sinh viên: 23120190 · Flow 1 · Repo: https://github.com/tzin1401/testing-hw05

## Tuyên bố

**I use AI tools for the following tasks:** thiết kế và review test plan JMeter, chạy và giám sát các kịch bản Load/Stress/Spike/Soak, phân tích file `.jtl`, săn lỗi đọc sai metric, đánh giá đề xuất tối ưu, thiết kế pipeline Continuous Performance Testing, viết Agent Skill và soạn nháp tài liệu. Mọi file `.jtl`, HTML report, ảnh chụp, hardware report và video đều sinh ra từ lần chạy thật trên máy của sinh viên, không do AI tạo.

## Công cụ AI đã dùng

| Công cụ | Model | Vai trò |
|---|---|---|
| omp multi-agent – Manager | openai-codex/gpt-6.1-sol | Điều phối, giao bước, commit |
| omp – task workers | openai-codex/gpt-6.1-terra | Viết test plan, script, báo cáo, AI analyst Task 2 |
| omp – sonic / scout | openai-codex/gpt-6-luna | Chạy JMeter, đọc code SUT, tái hiện bug |
| omp – reviewer | anthropic/claude-sonnet-5-5 | Review plan, săn lỗi metric, phân loại feasible/hallucinated, rà soát cuối |
| Claude Code | claude-opus-5-5 | Soạn bộ prompt giao cho Manager, hướng dẫn quay video, đăng Issue, viết Agent Skill (theo hướng dẫn của giảng viên, phiên này không ghi từng entry) |

Cách ghi log: quy tắc trong [`agent.md`](../agent.md). Mỗi prompt có cụm "ghi vào log" thì agent tự append một entry gồm tên công cụ, ngày giờ (lấy từ lệnh `date`), prompt nguyên văn và tóm tắt output. Mục **Human review** do sinh viên tự điền.

## Danh sách tương tác (41 entry)

Prompt nguyên văn, AI output và Human review của từng entry nằm trong [AI_LOG.md](AI_LOG.md). Bản PDF có kèm toàn văn log ở phụ lục.

| # | Thời gian (giờ VN) | Bước | Công cụ AI |
|---:|---|---|---|
| 1 | 2026-11-17 23:00 | Task 1 – Bước 0 – Khởi tạo môi trường | omp – sonic (openai-codex/gpt-6-luna); Manager (openai-codex/gpt-6.1-sol) |
| 2 | 2026-11-17 23:04 | Task 1 – Bước 1 | omp – scout; Manager (openai-codex/gpt-6.1-sol) |
| 3 | 2026-11-17 23:04 | Task 1 – Bước 11 | omp – sonic; Manager (openai-codex/gpt-6.1-sol) |
| 4 | 2026-11-17 23:04 | Task 1 – Bước 2 – Thiết kế kịch bản | omp – Design (openai-codex/gpt-6.1-terra) |
| 5 | 2026-11-17 23:06 | Task 1 – Bước 3 – Chuẩn bị dữ liệu và script giám sát tài nguyên | omp – DataMonitor (openai-codex/gpt-6.1-terra) |
| 6 | 2026-11-17 23:11 | Task 1 – Bước 4 – Tạo test plan Load | omp – LoadPlan (openai-codex/gpt-6.1-terra) |
| 7 | 2026-11-17 23:14 | Task 1 – Bước 4 – Sửa test plan Load | omp – FixExtractor (openai-codex/gpt-6.1-terra) |
| 8 | 2026-11-17 23:21 | Task 1 – Bước 5 – Review độc lập test plan Load | omp – Reviewer (anthropic/claude-sonnet-5-5) |
| 9 | 2026-11-17 23:22 | Task 1 – Bước 6 – Sửa test plan Load | omp – CorrectLoad (openai-codex/gpt-6.1-terra) |
| 10 | 2026-11-17 23:30 | Task 1 – Bước 7 – Sinh Stress và Spike | omp – Manager (openai-codex/gpt-6.1-sol); task workers StressSpike và BuildStressSpike chưa tạo file |
| 11 | 2026-11-17 23:45 | Task 1 – Bước 8 – Review độc lập test plan Stress và Spike | omp – Reviewer (anthropic/claude-sonnet-5-5) |
| 12 | 2026-11-17 23:45 | Task 1 – Bước 9 – Sửa Stress và Spike | omp – FixStressSpike (openai-codex/gpt-6.1-terra) |
| 13 | 2026-11-17 23:52 | Task 1 – Bước 10 – Smoke test cả 3 plan | omp – FinalSmoke (openai-codex/gpt-6-luna) |
| 14 | 2026-11-18 00:46 | Task 1 – Bước 13 – Chạy thật plan LOAD | omp – RunLoad (openai-codex/gpt-6-luna) |
| 15 | 2026-11-18 01:11 | Task 1 – Bước 13 – Chạy thật plan STRESS | omp – FinishStressReport (openai-codex/gpt-6-luna) |
| 16 | 2026-11-18 01:21 | Task 1 – Bước 13 – Chạy thật plan SPIKE | omp – RunSpike (openai-codex/gpt-6-luna) |
| 17 | 2026-11-18 01:26 | Task 1 – Bước 14 – Tạo test plan Soak | omp – SoakPlan (openai-codex/gpt-6.1-terra) |
| 18 | 2026-11-18 01:43 | Task 1 – Bước 15 – Chạy soak 12 phút | omp – RunSoak (openai-codex/gpt-6-luna) |
| 19 | 2026-11-18 01:52 | Task 2 – Bước 16 – Script phân tích endurance | omp – EnduranceScript (openai-codex/gpt-6.1-terra) |
| 20 | 2026-11-18 01:58 | Task 1 – Bước 16 – Xác minh và diễn giải output | omp – ComputeEndurance (sonic); Manager (openai-codex/gpt-6.1-sol) |
| 21 | 2026-11-18 02:04 | Task 2 – Bước 17 – Bản nháp bug report Flow 1 | omp – ReproduceBugs (openai-codex/gpt-6-luna) |
| 22 | 2026-11-18 02:09 | Task 1 – Bước 17 – Sửa kết luận thiếu bằng chứng | omp – Manager (openai-codex/gpt-6.1-sol) |
| 23 | 2026-11-18 02:12 | Task 1 – Bước 18 – Tổng hợp báo cáo | omp – TaskOneReport (openai-codex/gpt-6.1-terra) |
| 24 | 2026-11-18 02:22 | Task 1 – Bước 19 – Rà soát cuối | omp – FinalCheck (anthropic/claude-sonnet-5-5) |
| 25 | 2026-11-18 02:31 | Task 1 – Bước 19 – Xử lý rà soát cuối | omp – Manager (openai-codex/gpt-6.1-sol) |
| 26 | 2026-11-18 14:52 | Task 2 – Bước 20 | omp – TaskTwoAnalyst (openai-codex/gpt-6.1-terra) |
| 27 | 2026-11-18 14:56 | Task 2 – Bước 21 | omp – TaskTwoAnalyst (openai-codex/gpt-6.1-terra) |
| 28 | 2026-11-18 14:58 | Task 2 – Bước 23 | omp – TaskTwoTruthScript (openai-codex/gpt-6.1-terra); TaskTwoTruthRun (sonic, runtime không cung cấp model ID) |
| 29 | 2026-11-18 14:59 | Task 2 – Bước 22 | omp – TaskTwoAnalyst (openai-codex/gpt-6.1-terra) |
| 30 | 2026-11-18 15:07 | Task 2 – Bước 24 | omp – TaskTwoMetricReview (anthropic/claude-sonnet-5-5) |
| 31 | 2026-11-18 15:28 | Task 2 – Bước 25 | omp – TaskTwoOptimizationReview (anthropic/claude-sonnet-5-5); Manager (openai-codex/gpt-6.1-sol) |
| 32 | 2026-11-18 16:15 | Task 2 – Bước 27 | omp – TaskTwoReport (openai-codex/gpt-6.1-terra); Manager (openai-codex/gpt-6.1-sol) |
| 33 | 2026-11-18 20:04 | Task 2 – Bước 28 | omp – Manager (openai-codex/gpt-6.1-sol); TaskTwoFinalFallback (openai-codex/gpt-6.1-terra, thực thi kiểm chứng trước lỗi dịch vụ) |
| 34 | 2026-11-18 22:19 | Task 2 – Bước 28 (review độc lập chạy lại sau lỗi 429) | omp – TaskTwoFinalReview (anthropic/claude-sonnet-5-5); Manager ghi log |
| 35 | 2026-11-18 22:29 | Task 3 – Bước 29 | omp – TaskThreeChangeMap (gpt-6-luna); Manager (openai-codex/gpt-6.1-sol) |
| 36 | 2026-11-18 22:39 | Task 3 – Bước 30 | omp – TaskThreeProposal (gpt-6.1-terra); TaskThreeRenderCheck (gpt-6-luna); Manager (openai-codex/gpt-6.1-sol) |
| 37 | 2026-11-18 22:42 | Task 3 – Bước 31 | omp – TaskThreePipeline (openai-codex/gpt-6.1-terra); TaskThreeRenderCheck (gpt-6-luna); Manager (openai-codex/gpt-6.1-sol) |
| 38 | 2026-11-18 23:13 | Task 3 – Bước 32 | omp – TaskThreeDemoRun (gpt-6-luna); TaskThreePipeline (openai-codex/gpt-6.1-terra, fix lock/test); TaskThreeRenderCheck (gpt-6-luna, verify fix); Manager (openai-codex/gpt-6.1-sol) |
| 39 | 2026-11-18 23:37 | Task 3 – Bước 33 | omp – TaskThreeReview (anthropic/claude-sonnet-5-5); TaskThreePipeline (openai-codex/gpt-6.1-terra); TaskThreeReviewRender + TaskThreeRenderCheck (gpt-6-luna); Manager (openai-codex/gpt-6.1-sol) |
| 40 | 2026-11-19 00:07 | Task 3 – Bước 35 | omp – TaskThreeFinalReport (openai-codex/gpt-6.1-terra); Manager (openai-codex/gpt-6.1-sol) |
| 41 | 2026-11-19 00:22 | Task 3 – Bước 35 | omp – Manager (openai-codex/gpt-6.1-sol) |
