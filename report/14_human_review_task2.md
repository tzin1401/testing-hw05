# Bước 26 – Human review Task 2

## 1. Phạm vi và cách kiểm chứng

Mình đọc `report/11_ai_analysis.md` (dòng 1–122 là phân tích + ngưỡng, dòng 123–195 là đề xuất tối ưu), `report/12_misinterpretation_hunt.md` và `report/13_optimization_review.md`. Sau đó mình chạy lại ba lệnh trọng tâm trong report 12 là **CMD-1**, **CMD-5**, **CMD-6**, cộng thêm hai lệnh kiểm tra per-label và cửa sổ Soak. Mọi số dưới đây lấy từ output lệnh hoặc từ `results/analysis/ground_truth.json`; mình không sửa `report/11`, `12`, `13`, không sửa `.jtl`, không sửa SUT và không bịa số. Các lệnh dưới đây chạy ngày **2026-11-18**, từ gốc repo `/home/zinn/zinn/testing/hw05`.

## 2. Kết quả chạy lại

### 2.1 CMD-1 – tổng bốn lần chạy

```bash
cd /home/zinn/zinn/testing/hw05 && python3 - <<'PY'
import sys, math, csv; sys.path.insert(0, "scripts"); import jtl_truth as T
R = T.ROOT / "results/jtl"; S = {n: T.load_jtl(R / f"23120190_{n}_20261118.jtl") for n in T.NAMES}
def row(tag, m): print(tag, "n=%s rps=%s mean=%s p90=%s p95=%s p99=%s max=%s err=%s" % (m["count"], None if m["rps"] is None else round(m["rps"],2), None if m["mean_ms"] is None else round(m["mean_ms"],2), m["p90_ms"], m["p95_ms"], m["p99_ms"], m["max_ms"], m["error_count"]))
for n in T.NAMES:
    m = T.metrics(S[n]); row(n, m); print("   span_ms", m["duration_ms"], "rps", round(m["rps"],3), "401/403 accepted", m["accepted_401_403"])
    rows = list(csv.DictReader((R / f"23120190_{n}_20261118.jtl").open()))
    el = sorted(int(r["elapsed"]) for r in rows); N = len(el)
    span = max(int(r["timeStamp"])+int(r["elapsed"]) for r in rows) - min(int(r["timeStamp"]) for r in rows)
    print("   indep: rows", N, "success!=true", sum(r["success"] != "true" for r in rows), "mean", round(sum(el)/N,3), "p90/95/99", el[math.ceil(.9*N)-1], el[math.ceil(.95*N)-1], el[math.ceil(.99*N)-1], "max", el[-1], "span", span, "rps", round(N*1000/span,3))
PY
wc -l results/jtl/*.jtl
jq -c '.soak_writer_comparison' results/analysis/ground_truth.json
```

| Run | Count | Span (ms) | RPS | Error | Mean | p90 | p95 | p99 | Max | 401/403 `success=true` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Load | 33.775 | 599.439 | 56,34 | 0 | 3,22 | 10 | 11 | 18 | 95 | 241 |
| Stress | 175.882 | 600.092 | 293,09 | 0 | 67,01 | 143 | 496 | 1.030 | 1.690 | 1.261 |
| Spike | 27.965 | 358.864 | 77,93 | 0 | 75,25 | 24 | 158 | 2.115 | 4.633 | 205 |
| Soak | 158.591 | 719.783 | 220,33 | 0 | 32,45 | 17 | 29 | 753 | 6.344 | 1.129 |

Kết quả tính độc lập bằng `csv` (không dùng `jtl_truth.py`) trùng hoàn toàn: cùng count, mean, p90/p95/p99, max, span và RPS. `wc -l` cho đúng count + 1 header. File `*_writer.jtl` có cùng 158.591 dòng và cùng min/max `timeStamp` với Soak, đúng là bản ghi trùng, không phải run thứ hai.

→ Khớp `report/11` dòng 18–21, 33–36, 59–62, 85–88 và `report/12` CMD-1. Không có lỗi số liệu ở phần tổng.

### 2.2 CMD-5 – cửa sổ Soak 120 s

```bash
cd /home/zinn/zinn/testing/hw05 && python3 - <<'PY'
import sys; sys.path.insert(0, "scripts"); import jtl_truth as T
R = T.ROOT / "results/jtl"; S = {n: T.load_jtl(R / f"23120190_{n}_20261118.jtl") for n in T.NAMES}
O = {n: min(x[0] for x in S[n]) for n in S}
def win(n, a, b, pred=lambda x: True):
    return T.metrics([x for x in S[n] if a*1000 <= x[0]-O[n] < b*1000 and pred(x)], (b-a)*1000)
def row(tag, m): print(tag, "n=%s rps=%s mean=%s p90=%s p95=%s p99=%s max=%s err=%s" % (m["count"], None if m["rps"] is None else round(m["rps"],2), None if m["mean_ms"] is None else round(m["mean_ms"],2), m["p90_ms"], m["p95_ms"], m["p99_ms"], m["max_ms"], m["error_count"]))
for a in range(0, 720, 120): row(f"Soak {a}-{a+120}s", win("Soak", a, a+120))
rps = [win("Soak", a, a+120)["rps"] for a in (240, 360, 480, 600)]
print("Soak rps 240-720 min/max: %.2f %.2f" % (min(rps), max(rps)))
print("max allThreads Soak:", max(x[8] for x in S["Soak"]))
print("regression rule, baseline p95=20: giá trị nguyên nhỏ nhất =", min(v for v in range(21, 100) if v > 1.2*20 and v - 20 >= 5))
PY
```

| Cửa sổ | n | RPS | Mean | p90 | p95 | p99 | Max | Error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0–120 s | 21.588 | 179,90 | 4,76 | 12 | 17 | 30 | 90 | 0 |
| 120–240 s | 24.551 | 204,59 | 158,33 | 261 | 1.013 | 3.589 | 6.344 | 0 |
| 240–360 s | 27.364 | 228,03 | 24,06 | 15 | 24 | 145 | 5.179 | 0 |
| 360–480 s | 28.376 | 236,47 | 5,54 | 14 | 20 | 37 | 132 | 0 |
| 480–600 s | 28.398 | 236,65 | 5,58 | 14 | 20 | 33 | 130 | 0 |
| 600–720 s | 28.314 | 235,95 | 6,44 | 15 | 21 | 44 | 200 | 0 |

`max allThreads` = 203; RPS 240–720 s nằm trong 228,03–236,65; quy tắc regression với baseline p95 20 kích hoạt từ 25 ms. Tất cả khớp `report/11` dòng 96–101 và `report/12` CMD-5.

### 2.3 CMD-6 – các nhóm SLO

```bash
cd /home/zinn/zinn/testing/hw05 && python3 - <<'PY'
import sys; sys.path.insert(0, "scripts"); import jtl_truth as T
R = T.ROOT / "results/jtl"; S = {n: T.load_jtl(R / f"23120190_{n}_20261118.jtl") for n in T.NAMES}
O = {n: min(x[0] for x in S[n]) for n in S}
def win(n, a, b, pred=lambda x: True):
    return T.metrics([x for x in S[n] if a*1000 <= x[0]-O[n] < b*1000 and pred(x)], (b-a)*1000)
G = {"Auth": ("01 Login",), "Read": ("02 Products", "03 Product detail"), "Trans": ("04 Add cart", "05 Get cart", "06 Checkout", "07 My orders")}
for n, a, b in (("Soak", 360, 600), ("Stress", 300, 450), ("Soak", 120, 240)):
    for g, ls in G.items():
        m = win(n, a, b, lambda x: x[2] in ls)
        print(n, f"{a}-{b}s", g, "n=%s p95=%s p99=%s err=%s" % (m["count"], m["p95_ms"], m["p99_ms"], m["error_count"]))
PY
```

| Run, cửa sổ | Nhóm | n | p95 | p99 | Error |
|---|---|---:|---:|---:|---:|
| Soak 360–600 s | Auth | 8.049 | 19 | 37 | 0 |
| Soak 360–600 s | Read | 16.107 | 20 | 36 | 0 |
| Soak 360–600 s | Trans | 32.216 | 20 | 34 | 0 |
| Stress 300–450 s | Auth | 8.835 | **51** | 81 | 0 |
| Stress 300–450 s | Read | 17.578 | **52** | 84 | 0 |
| Stress 300–450 s | Trans | 34.761 | **45** | 76 | 0 |
| Soak 120–240 s | Auth | 3.424 | 1.054 | 2.181 | 0 |
| Soak 120–240 s | Read | 6.924 | 303 | 1.594 | 0 |
| Soak 120–240 s | Trans | 14.032 | 1.408 | 3.908 | 0 |

Khớp `report/11` dòng 113–117. Điểm cần chú ý: ở 200 VU, p95 của Auth và Read đã là 51/52 ms, tức **vượt** ngưỡng 50 ms mà analyst đề xuất.

### 2.4 Kiểm tra thêm – p95/p99 từng label trong chính cửa sổ SLO

Lệnh này mình chạy thêm vì CMD-6 chỉ gộp nhóm; gộp nhóm có thể che endpoint chậm.

```bash
cd /home/zinn/zinn/testing/hw05 && python3 - <<'PY'
import sys; sys.path.insert(0,'scripts'); import jtl_truth as T
S={n:T.load_jtl(T.ROOT/f'results/jtl/23120190_{n}_20261118.jtl') for n in T.NAMES}
O={n:min(x[0] for x in S[n]) for n in S}
def win(n,a,b,pred=lambda x:True):
    return T.metrics([x for x in S[n] if a*1000<=x[0]-O[n]<b*1000 and pred(x)],(b-a)*1000)
for nm,a,b in (('Stress',300,450),('Soak',360,600)):
    print(nm,a,b)
    for l in T.LABELS:
        m=win(nm,a,b,lambda x:x[2]==l)
        print(' ',l,'n=%s mean=%.2f p95=%s p99=%s max=%s'%(m['count'],m['mean_ms'],m['p95_ms'],m['p99_ms'],m['max_ms']))
PY
```

**Stress 300–450 s (200 VU):**

| Label | n | Mean | p95 | p99 | Max |
|---|---:|---:|---:|---:|---:|
| 01 Login | 8.835 | 13,45 | 51 | 81 | 167 |
| 02 Products | 8.803 | 13,87 | 52 | 82 | 154 |
| 03 Product detail | 8.775 | 14,77 | 53 | 87 | 160 |
| 04 Add cart | 8.746 | 5,34 | 22 | 38 | 91 |
| 05 Get cart | 8.710 | 5,21 | 23 | 38 | 99 |
| 06 Checkout | 8.671 | 22,83 | **60** | 93 | 162 |
| 07 My orders | 8.634 | 15,09 | 53 | 85 | 175 |

**Soak 360–600 s:**

| Label | n | Mean | p95 | p99 | Max |
|---|---:|---:|---:|---:|---:|
| 01 Login | 8.049 | 4,63 | 19 | 37 | 132 |
| 02 Products | 8.054 | 5,01 | 19 | 35 | 116 |
| 03 Product detail | 8.053 | 5,39 | 21 | 37 | 130 |
| 04 Add cart | 8.054 | 1,96 | 7 | 17 | 81 |
| 05 Get cart | 8.055 | 1,89 | 6 | 16 | 86 |
| 06 Checkout | 8.057 | 14,00 | 28 | 43 | 110 |
| 07 My orders | 8.050 | 6,17 | 20 | 35 | 116 |

→ Ở 200 VU, **Checkout p95 = 60 ms**, cũng vượt 50 ms. Nhóm Transactional có p95 45 ms vì p95 gộp là phân vị trên toàn bộ mẫu, không phải trung bình các p95 endpoint; 04/05 có đuôi ngắn (22/23 ms) nên phân vị 95% của mẫu gộp thấp hơn p95 riêng của Checkout. Đây là chỗ CMD-6 không thấy.

### 2.5 Kiểm tra thêm – độ phân giải cửa sổ Soak

```bash
cd /home/zinn/zinn/testing/hw05 && python3 - <<'PY'
import sys; sys.path.insert(0,'scripts'); import jtl_truth as T
S=T.load_jtl(T.ROOT/'results/jtl/23120190_Soak_20261118.jtl'); o=min(x[0] for x in S)
def win(a,b,pred=lambda x:True):
    return T.metrics([x for x in S if a*1000<=x[0]-o<b*1000 and pred(x)],(b-a)*1000)
for a in range(180,260,10):
    m=win(a,a+10); print(a,a+10,'n=%s mean=%.1f rps=%.2f p95=%s'%(m['count'],m['mean_ms'],m['rps'],m['p95_ms']))
PY
```

| Cửa sổ | n | Mean | RPS | p95 |
|---|---:|---:|---:|---:|
| 180–190 s | 2.365 | 4,9 | 236,50 | 19 |
| 190–200 s | 2.071 | 139,8 | 207,10 | 485 |
| 200–210 s | 1.721 | 380,0 | 172,10 | 1.743 |
| 210–220 s | 1.418 | 680,8 | 141,80 | 2.975 |
| 220–230 s | 1.409 | 716,1 | 140,90 | 3.833 |
| 230–240 s | 1.357 | 649,6 | 135,70 | 4.263 |
| 240–250 s | 1.239 | 397,7 | 123,90 | 3.885 |
| 250–260 s | 2.420 | 11,2 | 242,00 | 71 |

Đợt chậm thật nằm khoảng **190–245 s**, mạnh nhất 220–230 s (mean 716 ms, p95 3.833 ms). Cửa sổ 120–240 s mà analyst dùng có mean 158,33 và p95 1.013, tức đã pha loãng đợt chậm với khoảng 70 s khỏe phía trước. Con số không sai, nhưng mức độ sự cố bị mô tả nhẹ đi.

## 3. Đồng ý / không đồng ý với reviewer

### 3.1 Những điểm mình đồng ý

- **Reviewer đúng khi nói 0 lỗi số liệu cứng.** Mình đã tự chạy lại CMD-1, CMD-5, CMD-6, tính độc lập bằng `csv`, và kiểm tra thêm per-label. Các số mình kiểm tra đều khớp; reviewer đã coverage toàn bộ dòng 1–122: count, span, RPS, error, mean, p90/p95/p99, max, số 401/403, số sample Checkout, các cửa sổ Stress/Spike/Soak, số nhóm SLO và số học quy tắc regression.
- **Không gộp file `*_writer.jtl`:** đúng. Cùng 158.591 dòng, cùng min/max timestamp. Nếu cộng thêm bản ghi trùng thì số sample và RPS tăng gấp đôi, nhưng mean, p95 và error % không đổi.
- **Không coi 401/403 của Negative login là lỗi:** đúng. Cả bốn run có `success=false` = 0; 401/403 đều `success=true`. Đây là login sai có chủ đích, không phải lỗi JMeter.
- **Không coi p90 < mean là lỗi:** đúng. Spike p90 24 < mean 75,25 và Soak Checkout p95 74 < mean 89,14 là hệ quả của đuôi rất dài, không phải nhầm percentile.
- **Không coi chênh lệch percentile giữa HTML và JTL là lỗi:** đúng. Analyst công bố dùng nearest-rank trên raw; HTML dùng cách tính khác. Đây là khác estimator, không phải đọc sai.
- **Reviewer đúng khi tách N1–N5 ra khỏi bảng lỗi:** các khác biệt cửa sổ 150 s/60 s/120 s, stage theo `threadName`, HTML report và nhãn "gần nền" đều đã được analyst công bố hoặc không phải claim số. Mình không tính là lỗi.
- **Reviewer đúng khi không gán nhân quả cho bottleneck:** report 11 chỉ nói "có khả năng", "giả thuyết", không khẳng định rò rỉ bộ nhớ hay CPU. Mình đồng ý giữ nguyên mức bất định đó.

### 3.2 Không đồng ý: N6 phải là một lỗi, không chỉ là ghi chú

`report/12` xếp N6 vào mục "khác biệt đã kiểm nhưng KHÔNG phải lỗi" và chỉ khuyến nghị bước 25 nói rõ. Mình không đồng ý. Danh sách loại sai của chính bước 24 có dòng **"ngưỡng đề xuất mâu thuẫn với số đo"**. N6 thỏa đúng định nghĩa đó:

- `report/11` dòng 113–115 đặt p95 tối đa **50 ms** cho cả Auth, Read và Transactional, ở mức đề xuất **200 VU**.
- Ở 200 VU (Stress 300–450 s), đo được: Auth p95 **51 ms**, Read p95 **52 ms** — cả hai vượt ngưỡng nhóm 50 ms; Checkout p95 **60 ms** — vượt 50 ms nếu đánh giá theo endpoint, dù p95 nhóm Transactional chỉ 45 ms. Như vậy ngưỡng 50 ms không có khoảng đệm ở đúng mức tải đề xuất, trước khi nói tới regression.
- Câu "dành khoảng đệm cho đuôi" chỉ đúng nếu so với Soak 360–600 s (19–20 ms), không đúng ở 200 VU. Việc analyst tự ghi "Stress vượt nhẹ" không sửa được mâu thuẫn: một ngưỡng mà lần đo ở chính mức tải mục tiêu đã đỏ thì không dùng làm gate được.

Vì vậy mình đếm **1 lỗi thiết kế ngưỡng**, không phải 0. Đây không phải lỗi đọc số, nhưng là lỗi của kết luận/đề xuất, đúng phạm vi bước 24.

**Hướng sửa mình đề xuất:** dùng ngưỡng theo endpoint, không chỉ theo nhóm. Bảng dưới là đề xuất của mình cho bước 27, dựa trên số đo 200 VU và lấy khoảng đệm 1,4–2,6 lần:

| Nhóm / endpoint | p95 tối đa | p99 tối đa | Số đo 200 VU (p95/p99) | Ghi chú |
|---|---:|---:|---|---|
| Auth – 01 Login | 75 ms | 125 ms | 51 / 81 | Trước là 50/100, nay nới p95 |
| Read – 02 Products | 75 ms | 125 ms | 52 / 82 | Trước là 50/100 |
| Read – 03 Product detail | 75 ms | 125 ms | 53 / 87 | Trước là 50/100 |
| Transactional – 04 Add cart | 50 ms | 100 ms | 22 / 38 | Giữ nguyên, đang đạt |
| Transactional – 05 Get cart | 50 ms | 100 ms | 23 / 38 | Giữ nguyên, đang đạt |
| Transactional – 06 Checkout | 100 ms | 150 ms | 60 / 93 | Trước là 50/100, đây là endpoint sát ngưỡng nhất |
| Transactional – 07 My orders | 75 ms | 125 ms | 53 / 85 | Trước là 50/100 |
| Error toàn run / từng cửa sổ | ≤ 0,1% | — | 0% | Giữ nguyên |
| Throughput – Stress 200 VU | ≥ 200 req/s | — | 410,77 req/s | Giữ nguyên |
| Throughput – Soak 203 VU (tham chiếu) | — | — | 228–237 req/s | Không dùng thay số 200 VU |

Nếu nhóm muốn giữ đúng bảng 50/100 ms thì phải hạ mức tải mục tiêu xuống **100 VU** (Stress 150–300 s có p95 17 ms), và khi đó không được gọi 200 VU là endurance threshold. Mình chọn cách ngưỡng theo endpoint ở 200 VU vì nó phản ánh đúng điểm đã đo và không che Checkout.

### 3.3 Về phân loại trong report 13

Mình đồng ý 6/7 phân loại:

- **#1 Index – FEASIBLE, nhưng chỉ với ứng viên cụ thể.** Ứng viên thật là `orders(user_id)` cho `07 My orders` (`server.js:313`); `users(email)` đúng câu query nhưng bảng chỉ 302 dòng; `products` 5 dòng, `LIKE '%…%'` không dùng được index thường. Đồng ý với reviewer rằng đề xuất generic của analyst chưa dùng được ngay.
- **#2 Pool – PARTIALLY FEASIBLE.** Đồng ý: mở nhiều kết nối tới cùng file là hợp lệ, nhưng rollback journal + `busy_timeout` 1000 ms + một writer khiến `SQLITE_BUSY` thành 500. Phải có WAL trước.
- **#3 WAL – FEASIBLE.** Đồng ý. Một dòng `PRAGMA journal_mode=WAL`, hoàn tác dễ. Lợi ích thật có thể là giảm fsync mỗi commit, không phải "đọc song song với ghi" như analyst hình dung, vì hiện chỉ có một kết nối.
- **#4 Cache – FEASIBLE nhưng giá trị thấp.** Đồng ý. Chỉ 5 sản phẩm, p50 1–2 ms; không đáng ưu tiên.
- **#5 Cluster – PARTIALLY FEASIBLE.** Đồng ý. `userCarts` nằm trong RAM từng process, `initDatabase()` chạy `DROP TABLE` mỗi worker, SQLite vẫn một writer. Đây là lỗi correctness, không chỉ là chậm.
- **#7 Event loop – FEASIBLE phần đo.** Đồng ý. `monitorEventLoopDelay` có sẵn; phần chuyển worker thread chưa có đối tượng vì route không có CPU nặng.

Riêng **#6 Rút ngắn transaction Checkout**, mình đồng ý với dữ kiện của reviewer (không có `BEGIN/COMMIT`, không có tồn kho, Checkout chỉ là một `INSERT` tự commit) nhưng **không đồng ý cách đọc chữ HALLUCINATED như một cáo buộc bịa đặt**. Analyst đã viết "nếu thực tế có"; SQLite vẫn có transaction ngầm của `INSERT`. Nhãn đúng nghĩa là "không áp dụng được cho code hiện tại", không phải "analyst bịa ra transaction". Mình giữ nhãn HALLUCINATED vì đề chỉ cho hai lựa chọn feasible/hallucinated và hành động này không có đối tượng để làm; nhưng trong `TASK2_REPORT.md` sẽ ghi rõ **"HALLUCINATED (không áp dụng), không phải bịa đặt"**. Nếu người chấm hiểu HALLUCINATED là "tiền đề sai" thì nhãn này quá mạnh; nếu hiểu là "không dùng được" thì đúng.

Toàn bộ phân loại ở report 13 là **đánh giá tĩnh trên code**, không phải benchmark. Mình không đọc "FEASIBLE" thành "chắc chắn cải thiện" và không dùng bảng đó để hứa % nào.

## 4. Reviewer bỏ sót gì

### 4.1 Checkout p95 60 ms ở 200 VU

Đây là lỗ hổng cùng loại với N6 nhưng reviewer chưa nêu, không phải lỗi số của analyst. `report/12` CMD-6 chỉ tính p95 nhóm Transactional = 45 ms và kết luận nhóm này đạt 50 ms. Nhưng p95 từng label ở Stress 300–450 s là **Checkout 60 ms**, trong khi 04/05 chỉ 22/23 ms. p95 gộp không phải trung bình có trọng số của các p95 theo endpoint; nó là phân vị trên phân phối mẫu gộp, nên p95 nhóm 45 ms có thể thấp hơn p95 riêng của Checkout (60 ms). Analyst có ghi ở dòng 117 là nên báo thêm p95/p99 từng label, đặc biệt Checkout; nhưng reviewer 12 không chạy con số đó, nên bảng lỗi vẫn thiếu. Vì vậy:

- Nếu đánh giá theo nhóm, Transactional "đạt" 50 ms.
- Nếu đánh giá theo endpoint, Checkout "trượt" 50 ms.
- Cách đánh giá đúng cho SLO là theo endpoint, hoặc ít nhất phải công bố cả hai.

Mình đã ghi số này vào bảng 3.2. Đây là chỗ reviewer bỏ sót vì chỉ chạy CMD-6 gộp nhóm, chưa chạy per-label trong cùng cửa sổ.

### 4.2 Cửa sổ Soak 120–240 s làm nhẹ đợt chậm

Reviewer 12 không nêu; reviewer 13 có nêu ở §3 ("Lưu ý đối chiếu với report 11") nhưng không đưa vào bảng lỗi. Mình cho rằng đây là hạn chế phân tích, không phải lỗi số:

- Analyst dùng cửa sổ 120–240 s, mean 158,33 / p95 1.013.
- Đợt chậm thật khoảng 190–245 s; riêng 180–240 s là mean 368,54 / p95 2.213 / p99 4.121 (report 13 M4), còn bucket 10 s cao nhất 220–230 s là mean 716,1 / p95 3.833.
- Kết luận "SLO không đạt" vẫn đúng, nhưng nếu chỉ nhìn 120–240 s thì mức độ sự cố bị giảm khoảng 2–4 lần. Trong `TASK2_REPORT.md` nên trích cả cửa sổ 120–240 s (theo analyst) và 180–240 s / bucket 10 s (theo ground truth) để người đọc thấy đỉnh thật.

### 4.3 Không có lỗi số liệu nào khác

Mình đã kiểm tra thêm và không tìm thấy lỗi số cứng nào khác:

- `Latency` và `Connect`: analyst dùng `elapsed`, không trộn với `Latency`; ground truth có tách mean Latency/Connect nhưng các số trong report 11 đều là elapsed. Không có nhầm đơn vị ms/s.
- `Negative login`: 401/403 đều `success=true`; số 5/236, 8/1.253, 22/183, 6/1.123 khớp.
- Stress: các cửa sổ 150 s lẫn 5–7 sample của bậc kế, nhưng p95/p99 của cửa sổ và stage trùng nhau; analyst đã ghi "không phải steady-state thuần túy". Không phải lỗi.
- Spike: burst bắt đầu 119,220 s, kết thúc 239,844 s; cửa sổ 120–180 và 180–240 gần đúng, analyst đã ghi rõ. Không phải lỗi.
- Soak: 6 cửa sổ 120 s khớp; `max allThreads` 203 khớp; p95 20/20/21 ở ba cửa sổ cuối đúng là "cao hơn nhẹ", không phải suy giảm liên tục.
- SLO: các count 8.049/16.107/32.216, 8.835/17.578/34.761, 3.424/6.924/14.032 khớp; p95/p99 khớp; error 0.
- Quy tắc regression: baseline 20 → ngưỡng nguyên nhỏ nhất 25, đúng.

Mình không thêm lỗi nào chỉ để tỏ ra đã kiểm tra. Kết luận của mình là: **0 lỗi số liệu cứng, 1 lỗi thiết kế ngưỡng (N6, mở rộng cho Checkout), 1 hạn chế độ phân giải cửa sổ Soak.**

## 5. Đề xuất tối ưu đáng làm nhất

### 5.1 Dữ liệu nói gì

- Checkout là label chậm nhất theo mean ở cả bốn run: Load 11,41; Stress 175,94; Spike 195,92; Soak 89,14 ms (report 13 M1).
- Ở Soak khỏe, Checkout p50 = **11 ms** rất ổn định từ phút 0 đến 720 (trừ 180–240 s); các route không ghi chỉ 1–4 ms. Đây là dấu hiệu chi phí commit/fsync cố định, khớp giả thuyết WAL.
- Nhưng trong đợt chậm, cả `04 Add cart` và `05 Get cart` — hai route **không chạm DB** — cũng chậm: Soak 120–240 s Add cart mean 30,51 / p95 160; Get cart mean 70,23 / p95 413 (report 13 D2, mình đã chạy lại và khớp). Vì vậy không thể quy toàn bộ đợt chậm cho SQLite/index/pool.
- Ở Stress stage 4 (290 VU), `07 My orders` p50 = 221 ms trong khi `02 Products` p50 = 2 ms; `orders` cuối Stress khoảng 24,7k dòng và không có index `user_id`, không có LIMIT.
- CPU ước tính của Node thấp hơn trong đợt chậm Soak (12–22% một core) và chỉ 42–55% ở stage 4 (report 13 D5). Đây là ước tính từ `ps %cpu`, không phải ground truth, nên không dùng một mình để loại trừ CPU/event loop.

### 5.2 Thứ tự mình chọn

1. **Đo trước, chưa sửa (ưu tiên 0).** Bật `monitorEventLoopDelay`, đo thời gian từng `db.run` ở Login/Checkout/My orders, đo CPU tức thời bằng `pidstat`/`top`, và kiểm tra phía JMeter (vì JMeter chạy cùng máy). Mục đích là phân biệt: chờ I/O/khóa, event loop, hay chính load generator. Nếu bỏ bước này, mọi đề xuất DB đều là đoán.
2. **WAL (#3) – việc đáng làm nhất trong các thay đổi code.** Một dòng `PRAGMA journal_mode=WAL`, hoàn tác dễ, không đổi schema/API. Nó kiểm tra đúng giả thuyết "mỗi INSERT của Checkout tốn một commit/fsync" — giả thuyết có bằng chứng từ p50 11 ms ổn định và Checkout chậm nhất theo mean ở cả bốn run. Đây là thí nghiệm falsifiable: nếu WAL không làm Checkout p50/p95 giảm, giả thuyết commit sai và phải quay lại event loop/client.
3. **Index `orders(user_id)` (#1) – làm sau WAL.** Nhắm `07 My orders` (p50 221 ms ở 290 VU). Rủi ro: thêm b-tree phải cập nhật mỗi lần Checkout `INSERT`, đúng route đang chậm nhất; và `SELECT` không có LIMIT nên response vẫn lớn dần theo số đơn. Phải đo cả thời gian ghi trước/sau, không chỉ đọc.
4. **Hoãn #2 pool, #4 cache, #5 cluster. Bỏ #6.**

### 5.3 Vì sao không chọn các cái khác

- **Cache sản phẩm (#4):** chỉ 5 sản phẩm, p50 1–2 ms ngay cả ở 290 VU. Không có bottleneck đọc để giải quyết; cache chỉ thêm rủi ro dữ liệu cũ ở 4 chỗ ghi.
- **Pool (#2):** hiện một kết nối, rollback journal, `busy_timeout` 1000 ms. Mở nhiều kết nối có thể biến độ trễ thành lỗi `SQLITE_BUSY` (500 ở Checkout/Login) trước khi có WAL. Lợi ích chưa chứng minh vì `02 Products` p50 chỉ 2 ms.
- **Cluster (#5):** `userCarts` trong RAM từng process sẽ làm `05 Get cart` trả `[]` khi trúng worker khác; `initDatabase()` chạy `DROP TABLE` mỗi worker; SQLite vẫn một writer. Đây là rủi ro correctness, không phải tối ưu hiệu năng.
- **Rút ngắn transaction (#6):** không có transaction tường minh để rút ngắn. Chỉ có transaction ngầm của một `INSERT`; muốn giảm chi phí commit thì làm WAL, không phải "rút ngắn transaction".

### 5.4 Tiêu chí đánh giá sau khi thử WAL

Chạy lại cùng plan, cùng thời lượng, cùng cửa sổ; so Checkout p50/p95/p99 và My orders p50/p95, không so cả run với cửa sổ khác. Nếu Checkout p50 giảm rõ nhưng đợt chậm 190–245 s vẫn còn, WAL chỉ giải quyết chi phí commit chứ không phải nguyên nhân đợt chậm. Nếu cả hai không đổi, chuyển sang đo event loop và phía JMeter. Không cộng các cải thiện giả định và không hứa % nào khi chưa đo.

## 6. Kết luận

- **Số lỗi số liệu cứng: 0.** Mình đã chạy lại CMD-1, CMD-5, CMD-6, tính độc lập bằng `csv`, kiểm tra per-label và cửa sổ Soak; các số mình kiểm tra đều khớp, và reviewer đã coverage toàn bộ `report/11` dòng 1–122.
- **Không đồng ý với reviewer ở N6:** đây là 1 lỗi "ngưỡng đề xuất mâu thuẫn với số đo", không phải ghi chú. Cụ thể: ở 200 VU, Auth p95 51 và Read p95 52 đã vượt ngưỡng nhóm 50 ms; Checkout p95 60 vượt 50 ms nếu tính theo endpoint. Mình đề xuất ngưỡng theo endpoint ở mục 3.2.
- **Reviewer bỏ sót Checkout p95 60 ms** vì CMD-6 chỉ gộp nhóm; đây là lỗ hổng kiểm tra, không phải lỗi số của analyst. Reviewer 12 cũng chưa nêu đủ việc cửa sổ Soak 120–240 s làm nhẹ đợt chậm 190–245 s.
- **Không có lỗi số nào khác.** Mình không bịa thêm lỗi; các điểm N1–N5 và D1–D10 mình đồng ý.
- **Đề xuất đáng làm nhất:** đo event-loop/SQL/phía JMeter trước; sau đó WAL là thay đổi code đầu tiên vì một dòng, hoàn tác dễ và kiểm tra được giả thuyết commit của Checkout. Index `orders(user_id)` làm sau; bỏ #6, hoãn pool/cache/cluster.
- **#6:** giữ nhãn HALLUCINATED nhưng ghi rõ nghĩa "không áp dụng được", không phải "analyst bịa đặt".

Đã cập nhật Human review cho các entry #26–#34 trong `report/AI_LOG.md`. Không sửa `report/11`, `12`, `13`; không sửa `.jtl`/SUT; chưa commit.

**Xong bước 26.**
