# AI Critique

Đọc lại log, mình thấy AI hiếm khi tính sai số. Cái sai chủ yếu nằm ở cách diễn giải số và thiết kế công cụ đo.

Lỗi rõ nhất là ngưỡng. Ở Task 2, AI đọc đúng mọi số từ `.jtl` nhưng vẫn đề xuất SLO p95 50 ms cho từng nhóm. Stress 200 VU đã đo được Login 51 ms, Products 52 ms, Checkout 60 ms. p95 gộp Transactional 45 ms trông đẹp nên che mất Checkout.

Công cụ đo cũng có lỗi. Plan Soak có thêm listener ghi trùng mọi sample. Monitor dùng `ps %cpu`, là CPU trung bình cả phiên, không phải CPU tức thời; lời thoại video AI soạn ghi 80%, htop chỉ 45,7%.

AI còn có thiên lệch làm phức tạp. Plan Stress có pool tài khoản `synchronized` và gate Groovy giữa các bậc; nhiều lỗi sinh ra từ đó. Đề xuất tối ưu cũng không áp dụng được: "rút ngắn transaction Checkout" vô nghĩa vì Checkout chỉ có một `INSERT`; "connection pool" không hợp với SQLite vì chỉ có một writer.

Vì sao AI không tự thấy? Vì nó trả lời theo mẫu quen thuộc, không đối chiếu dữ liệu và mã nguồn. Nó không thấy runtime. Reviewer do AI làm cũng mang cùng điểm mù.

Mình rút ra ba nguyên tắc. Một, tách đo và diễn giải: mọi số phải tính lại được từ `.jtl` thô. Hai, không để AI tự review AI; phải kiểm độc lập bằng script hoặc người, như `jtl_truth.py`, gate A/A, `check_claims.py`. Ba, người giữ quyết định có hậu quả: SLO, baseline, đóng cảnh báo. AI chỉ nên chỉ chỗ mình nhìn sót.
