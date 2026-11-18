# AI Critique

**AI sai, thiên lệch hoặc thiếu ở đâu?**

AI hiếm khi viết sai số. Nó sai khi diễn giải số và khi thiết kế công cụ đo.

- **Ngưỡng không khớp dữ liệu.** Ở Task 2, AI đọc đúng mọi số từ `.jtl` nhưng đề xuất SLO p95 50 ms theo nhóm. Trong khi đó, Stress 200 VU đã đo được Login 51 ms, Products 52 ms, Checkout 60 ms. p95 gộp Transactional là 45 ms, che mất Checkout.
- **Công cụ đo có lỗi.** Plan Soak có thêm listener ghi trùng mọi sample. Monitor dùng `ps %cpu`, là CPU trung bình từ lúc tiến trình khởi động, không phải CPU tức thời. Lời thoại video AI soạn ghi CPU 80%, còn htop chỉ hiện 45,7%.
- **Đề xuất tối ưu không áp dụng được.** "Rút ngắn transaction Checkout" không áp dụng, vì Checkout chỉ có một `INSERT`. "Connection pool" không hợp với SQLite, vì SQLite chỉ có một writer.

**Vì sao AI không tự phát hiện?**

- AI trả lời theo mẫu quen thuộc nhưng không đối chiếu với dữ liệu và mã nguồn thật.
- AI không thấy runtime.
- Agent reviewer có cùng điểm mù với agent viết.
- Số gộp trông đẹp nên che mất phần đuôi chậm.

**Nguyên tắc em rút ra**

- Tách phần đo và phần diễn giải: mọi con số phải do script tính lại được từ `.jtl` thô.
- Không để AI tự review AI. Phải có bước kiểm bằng script hoặc người, như `jtl_truth.py`, gate A/A và `check_claims.py`.
- Người giữ các quyết định có hậu quả: SLO, baseline, đóng cảnh báo.
