# Bước 29 – Bản đồ thay đổi SUT cho Continuous Performance Testing

Khảo sát chỉ đọc ngày 2026-11-18: metadata Git lấy lúc 22:24, tổng hợp lúc 22:26 (giờ VN, bằng `date`). Scout `TaskThreeChangeMap` (`gpt-6-luna`) đọc source/JMX; do scout không có shell, Manager (`openai-codex/gpt-6.1-sol`) thu thập metadata bắt buộc và hoàn tất báo cáo. Không chạy JMeter, reset hay sửa SUT.

## 1. Nguồn và cách kiểm tra

- Metadata: `git -C eshop-sut ls-files`, `git -C eshop-sut log --oneline`, `git -C eshop-sut status --short`, `git -C eshop-sut branch --show-current`, `git -C eshop-sut rev-parse HEAD`; thêm `git status --short` của HW05 để phân biệt hai repo.
- Thời gian: `TZ=Asia/Ho_Chi_Minh date '+%Y-%m-%d %H:%M'`.
- Route và số dòng: [server.js](../eshop-sut/backend/server.js); đối chiếu trực tiếp các registration `app.get/post/put/delete` trong source. Có **31** registration, không phải 29 như câu mở đầu nhầm của scout.
- Workflow/label: [Load plan](../test-plans/23120190_Load_20261117.jmx), được scout đọc; các nhãn Flow 1 trong đề bài. [database.js](../eshop-sut/backend/database.js), [test_profile.js](../eshop-sut/backend/test_profile.js), [run_servers.sh](../eshop-sut/run_servers.sh) được đọc để phân loại.
- Các link SUT là nguồn local trong repo riêng đã bị ignore, không cam kết hoạt động trong bản HW05 không kèm SUT. Commit đầy đủ bên dưới cho phép đối chiếu nguồn.

## 2. Chính sách phân loại file

B = **ảnh hưởng backend**; N = **không ảnh hưởng hiệu năng API trong workload JMeter cố định**; U = **chưa rõ**, cần chạy theo hướng an toàn. Áp dụng từ trên xuống, mỗi path đúng một loại:

| Ưu tiên | Pattern / path | Loại | Lý do |
|---:|---|---|---|
| 1 | `backend/**/*.js` | B | Source, schema/seed, hoặc script thử backend. `test_profile.js` là client thử API chứ không phải production handler; vẫn chạy theo luật bảo thủ bao phủ JS backend, chấp nhận chạy dư. |
| 2 | `backend/package.json`, `backend/package-lock.json` | B | Dependency/runtime có thể đổi hành vi hoặc chi phí API. |
| 3 | `run_servers.sh` | B | Cấu hình khởi chạy SUT. Bản hiện tại dùng đường dẫn macOS và `killall node`; chỉ đọc, không thực thi. Đây là phân loại bảo thủ dù CPT dùng reset script riêng. |
| 4 | `frontend-admin/**`, `frontend-mobile/**`, `frontend-web/**` | N | UI, asset và dependency frontend không đổi backend chạy riêng trong test API với Flow 1 cố định. |
| 5 | `**/*.md` và Markdown ở gốc | N | Tài liệu, không được chạy trong workload này. |
| 6 | Mọi path còn lại | U | Không suy diễn an toàn khi chưa biết vai trò; quyết định chạy. |

`backend/database.sqlite` là **U**: dữ liệu/schema/state có thể ảnh hưởng API, nhưng [database.js](../eshop-sut/backend/database.js) dòng 13–20, 83–117 khởi tạo lại bảng và seed khi backend khởi động. Không coi thay file DB là docs-only, cũng không kết luận diff binary chắc chắn tồn tại sau reset.

Giới hạn: N chỉ có nghĩa không đổi hiệu năng backend trong **workload cố định**, không chứng minh trải nghiệm frontend hoặc request mix thực tế không đổi. Seed hiện nằm trong `backend/database.js` nên thuộc B. File seed mới ngoài các nhóm biết trước thuộc U; seed/environment/dữ liệu test thay bên ngoài repo SUT không được phát hiện chỉ bằng diff repo này. Đổi hợp đồng API hoặc route ngoài Flow 1 có thể được quyết định chạy nhưng vẫn không được workflow đo phủ.

### Inventory đầy đủ từ `git ls-files`

| Tracked path | Loại |
|---|---|
| `README.md` | N |
| `api_specification.md` | N |
| `backend/database.js` | B |
| `backend/database.sqlite` | U |
| `backend/package-lock.json` | B |
| `backend/package.json` | B |
| `backend/server.js` | B |
| `backend/test_profile.js` | B |
| `frontend-admin/.gitignore` | N |
| `frontend-admin/README.md` | N |
| `frontend-admin/eslint.config.js` | N |
| `frontend-admin/index.html` | N |
| `frontend-admin/package-lock.json` | N |
| `frontend-admin/package.json` | N |
| `frontend-admin/postcss.config.js` | N |
| `frontend-admin/public/favicon.svg` | N |
| `frontend-admin/public/icons.svg` | N |
| `frontend-admin/src/App.css` | N |
| `frontend-admin/src/App.jsx` | N |
| `frontend-admin/src/assets/hero.png` | N |
| `frontend-admin/src/assets/react.svg` | N |
| `frontend-admin/src/assets/vite.svg` | N |
| `frontend-admin/src/index.css` | N |
| `frontend-admin/src/main.jsx` | N |
| `frontend-admin/tailwind.config.js` | N |
| `frontend-admin/vite.config.js` | N |
| `frontend-mobile/.gitignore` | N |
| `frontend-mobile/App.js` | N |
| `frontend-mobile/app.json` | N |
| `frontend-mobile/assets/adaptive-icon.png` | N |
| `frontend-mobile/assets/favicon.png` | N |
| `frontend-mobile/assets/icon.png` | N |
| `frontend-mobile/assets/splash-icon.png` | N |
| `frontend-mobile/index.js` | N |
| `frontend-mobile/package-lock.json` | N |
| `frontend-mobile/package.json` | N |
| `frontend-web/.gitignore` | N |
| `frontend-web/README.md` | N |
| `frontend-web/eslint.config.js` | N |
| `frontend-web/index.html` | N |
| `frontend-web/package-lock.json` | N |
| `frontend-web/package.json` | N |
| `frontend-web/postcss.config.js` | N |
| `frontend-web/public/favicon.svg` | N |
| `frontend-web/public/icons.svg` | N |
| `frontend-web/src/App.css` | N |
| `frontend-web/src/App.jsx` | N |
| `frontend-web/src/assets/hero.png` | N |
| `frontend-web/src/assets/react.svg` | N |
| `frontend-web/src/assets/vite.svg` | N |
| `frontend-web/src/context/AuthContext.jsx` | N |
| `frontend-web/src/context/CartContext.jsx` | N |
| `frontend-web/src/index.css` | N |
| `frontend-web/src/main.jsx` | N |
| `frontend-web/src/pages/Cart.jsx` | N |
| `frontend-web/src/pages/Checkout.jsx` | N |
| `frontend-web/src/pages/ForgotPassword.jsx` | N |
| `frontend-web/src/pages/Home.jsx` | N |
| `frontend-web/src/pages/Login.jsx` | N |
| `frontend-web/src/pages/ProductDetail.jsx` | N |
| `frontend-web/src/pages/Profile.jsx` | N |
| `frontend-web/src/pages/Register.jsx` | N |
| `frontend-web/tailwind.config.js` | N |
| `frontend-web/vite.config.js` | N |
| `run_servers.sh` | B |
| `setup_guide.md` | N |

**Đối soát:** 66 path duy nhất = **6 B + 59 N + 1 U**. Mỗi path trong output `git ls-files` được liệt kê đúng một lần; không lấy `node_modules/` untracked làm tracked input. Đây là trạng thái hiện tại, không phải allowlist đóng: path mới phải đi qua luật ưu tiên và fallback U.

## 3. Route → nhóm → label JMeter

Nhóm theo mục đích workflow: Auth gồm vòng đời tài khoản/quản trị tài khoản; Read gồm đọc catalog; Transactional gồm cart/order/promotion và các thao tác ghi catalog ngoài Auth. Nhóm ngoài Flow 1 là phân loại phục vụ bản đồ, **không** hàm ý đã có coverage. Các route ghi sản phẩm/danh mục không được gọi là Read chỉ vì cùng domain catalog.

| Dòng server.js | Method | Path | Nhóm | Label Flow 1 |
|---:|---|---|---|---|
| 20 | POST | `/api/register` | Auth | không phủ |
| 32 | POST | `/api/login` | Auth | 01 Login; Negative login |
| 68 | POST | `/api/forgot-password` | Auth | không phủ |
| 87 | POST | `/api/reset-password` | Auth | không phủ |
| 112 | GET | `/api/users/me` | Auth | không phủ |
| 118 | PUT | `/api/users/me` | Auth | không phủ |
| 141 | GET | `/api/products` | Read | 02 Products |
| 159 | GET | `/api/products/:id` | Read | 03 Product detail |
| 167 | POST | `/api/products` | Transactional | không phủ |
| 179 | PUT | `/api/products/:id` | Transactional | không phủ |
| 191 | DELETE | `/api/products/:id` | Transactional | không phủ |
| 199 | POST | `/api/admin/import-products` | Transactional | không phủ |
| 243 | GET | `/api/categories` | Read | không phủ |
| 249 | POST | `/api/categories` | Transactional | không phủ |
| 257 | PUT | `/api/categories/:id` | Transactional | không phủ |
| 269 | DELETE | `/api/categories/:id` | Transactional | không phủ |
| 284 | GET | `/api/cart` | Transactional | 05 Get cart |
| 290 | POST | `/api/cart` | Transactional | 04 Add cart |
| 297 | POST | `/api/checkout` | Transactional | 06 Checkout |
| 311 | GET | `/api/orders/my-orders` | Transactional | 07 My orders |
| 321 | PUT | `/api/orders/:id/cancel` | Transactional | không phủ |
| 344 | GET | `/api/orders/:id` | Transactional | không phủ |
| 356 | GET | `/api/coupons` | Transactional | không phủ |
| 363 | POST | `/api/apply-coupon` | Transactional | không phủ |
| 444 | POST | `/api/coupon-usage` | Transactional | không phủ |
| 457 | POST | `/api/admin/coupons` | Transactional | không phủ |
| 483 | DELETE | `/api/admin/coupons/:id` | Transactional | không phủ |
| 494 | GET | `/api/admin/users` | Auth | không phủ |
| 504 | DELETE | `/api/admin/users/:id` | Auth | không phủ |
| 510 | GET | `/api/admin/orders` | Transactional | không phủ |
| 525 | PUT | `/api/admin/orders/:id/status` | Transactional | không phủ |

**Đối soát:** 31 route method/path duy nhất; Flow 1 phủ **7 route**, còn **24 không phủ**. Có 8 label sampler vì `01 Login` và `Negative login` dùng chung `POST /api/login`; Negative là đầu vào sai có chủ đích, không phải route thứ tám. Nhóm Transactional có cả endpoint GET như cart/my-orders vì đó là nhóm workflow, không đồng nghĩa mọi endpoint trong nhóm đều ghi DB.

## 4. Git history và working tree – snapshot trước khi tạo báo cáo

Repo SUT: nhánh **main**, HEAD **`85af3ba875c88283615e22cb108f13e2fccaf0e9`**.

```text
$ git -C eshop-sut log --oneline
85af3ba first upload
2f9bf2b Initial commit

$ git -C eshop-sut status --short
 M backend/database.sqlite
?? backend/node_modules/
```

**SUT không sạch ngay trước demo**: có DB tracked đã thay đổi và dependency untracked. Không tự restore/xóa/stage hai mục này; bước 32 phải ghi nhận trạng thái ban đầu, chỉ commit đúng thay đổi demo được duyệt, rồi trở về đúng main ban đầu. Không hứa working tree sạch toàn bộ khi snapshot đầu vào vốn không sạch. Không thực thi `run_servers.sh` để kiểm tra vì script dừng mọi tiến trình node.

Snapshot repo **HW05**, không phải repo SUT:

```text
$ git status --short
 M report/14_human_review_task2.md
 M report/15_task2_check.md
 M report/AI_LOG.md
?? .github/
?? "03 - github_bug_management.pptx.pdf"
?? CLAUDE.md
?? HW05_CHON_WORKFLOW.pdf
?? TASK1_PROMPTS.md
?? TASK2_PROMPTS.md
?? TASK3_PROMPTS.md
?? VIDEO_SCRIPT.md
?? agent.md
?? report/issues/
```

Các thay đổi trên đã tồn tại khi bắt đầu bước này, thuộc người dùng; không gộp vào commit bước 29. AI_LOG chỉ được Manager nối entry mới, giữ nguyên entry/human review đã có.

## 5. Tiêu chí hoàn thành

- Đủ 66 tracked file, phân loại một-một và tổng bảo toàn 66.
- Đủ 31 route với method/path và số dòng được đối chiếu source; đủ 7 route workflow, 24 route không phủ ghi rõ.
- Có lịch sử commit, nhánh/HEAD, working tree SUT và snapshot HW05; không che trạng thái bẩn ban đầu.
- Bước khảo sát không sửa SUT, không sinh/chỉnh JTL, không push và không tạo Issue.
