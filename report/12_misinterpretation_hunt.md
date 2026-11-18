# Bước 24 – Truy tìm chỗ AI đọc sai / hiểu sai (đối chiếu `11_ai_analysis.md` bước 20–21 với JTL thô)

## 1. Kết luận

- Đã đối chiếu mọi con số và nhận định trong `report/11_ai_analysis.md` **dòng 1–122** (bước 20–21). Dòng 123–195 là bước 22 (đề xuất tối ưu), ngoài phạm vi.
- **Số lỗi số liệu cứng tìm được: 0.** Chi tiết ở §2 và Phụ lục A.
  - 4 bảng tổng; số mẫu và 4 phép tính Checkout cho từng run; label có max toàn lần; mã 401/403 của `Negative login`.
  - 4 hàng Stress; 4 cửa sổ Spike cùng thời điểm đầu/cuối của burst; 6 hàng Soak.
  - Các nhóm SLO Auth/Read/Transactional; số học throughput, error và regression.
  - Mọi số này khớp raw JTL khi chạy lại bằng đúng phương pháp mà analyst đã công bố.
- Không bịa lỗi: mọi khác biệt chỉ do filter hoặc mẫu số khác với `ground_truth.json` mặc định được ghi riêng ở §4 và **không** tính là lỗi.
- Nguồn tính toán là `scripts/jtl_truth.py` (bước 23): `load_jtl`, `metrics`, `percentile`, `LABELS`, `ROOT`. Không dùng số Task 1 hay `summarize.py` cũ.

Ghi chú về `metrics()`: `duration_ms=None` nghĩa là span thực = `max(timeStamp+elapsed) − min(timeStamp)`. Cửa sổ cố định truyền `duration_ms=(b−a)*1000`, tức RPS = số sample bắt đầu trong cửa sổ / độ rộng cố định. Cả hai đều đúng với công thức analyst đã công bố ở dòng 7 và dòng 9.

## 2. Bảng lỗi (AI đọc sai / hiểu sai / kết luận sai)

| # | AI nói (trích nguyên văn + vị trí) | Giá trị đúng từ .jtl (con số + file + cách lọc) | Loại sai | Vì sao AI sai |
|---|---|---|---|---|
| — | **Không có lỗi số liệu cứng nào.** Số của Phụ lục A đều khớp cmd CMD-1…CMD-7 chạy trên raw. | — | — | — |

Các mục dễ bị nhầm với lỗi nhưng không phải lỗi nằm ở §4. Chúng là hạn chế hoặc khuyến nghị, không tô thành "misreading".

## 3. Bảng AI đúng (rút gọn, để báo cáo cân bằng)

| # | Chỗ AI làm đúng | Vị trí `11` | Bằng chứng |
|---|---|---|---|
| D1 | Không gộp `*_writer.jtl`; đây là bản ghi trùng của cùng lần Soak. | L5, L81 | CMD-1: cùng 158.591 dòng, cùng min/max `timeStamp` (1794940254143 / 1794940973924). |
| D2 | Không coi 401/403 của `Negative login` là lỗi. | L6, L23, L38, L64, L90 | CMD-2: 5/236, 8/1.253, 22/183, 6/1.123, đều `success=true`; `success=false` = 0. |
| D3 | Tách `Negative login` khỏi latency Auth và khỏi 7 label chính. | L109 | CMD-6 chỉ lọc `01 Login` cho Auth; số khớp. |
| D4 | Tính throughput theo span thực, không theo thời lượng cấu hình. | L7, L19, L34, L60, L86 | CMD-1: 599.439 / 600.092 / 358.864 / 719.783 ms. |
| D5 | Phân biệt label chậm nhất theo mean với label có max toàn lần (Spike: 03 Product detail; Soak: 02 Products). | L8, L64, L90 | CMD-2. |
| D6 | Không nhầm mean với p95; p90 của Spike (24) thấp hơn mean (75,25) là đúng. | L62 | CMD-1. |
| D7 | Phân biệt cửa sổ throughput 200 req/s với việc vi phạm độ trễ (Soak 120–240 s: 204,59 req/s nhưng p95 Transactional 1.408). | L120 | CMD-5, CMD-6. |
| D8 | Không biến giả thuyết bottleneck thành nhân quả; không kết luận rò rỉ bộ nhớ. | L10, L25, L51, L77, L105 | Giả thuyết "Checkout là đường cần khảo sát" khớp CMD-7: Checkout có mean cao nhất trong cả ba cửa sổ chậm. |
| D9 | Ghi rõ ngưỡng đề xuất không phải số đã đo; nêu Stress vượt nhẹ p95 (51 và 52 ms). | L109, L113–L114, L119–L122 | CMD-6. |
| D10 | Nêu rõ cửa sổ 150 s và burst không trùng chính xác ranh giới nhóm. | L40, L49, L75 | CMD-3, CMD-4. |

## 4. Khác biệt đã kiểm nhưng KHÔNG phải lỗi analyst

| # | Điểm khác | Giải thích |
|---|---|---|
| N1 | `ground_truth.json` mặc định chia Stress theo `threadName` (stage), chia minute 60 s và Spike theo phase 0–120/120–180/180–240/240–360 s. Analyst dùng cửa sổ 150 s, Spike 60–300 s và Soak 120 s, theo thời điểm bắt đầu sample. | Analyst đã công bố filter này ở L9, L40, L66, L92. Không so các số khác phương pháp để kết lỗi. |
| N2 | Stress: cửa sổ 150 s lẫn ít sample của bậc kế (5, 6, 7 sample; `300–450 s` có 7 sample bậc 4). | Ảnh hưởng không đáng kể. Cửa sổ và stage có cùng p95 (12/17/48/905) và p99 (21/28/79/1152). Count và RPS lệch nhẹ: 66.877/445,85 so với stage 4 là 66.884/444,36 (khác tập và khác mẫu số). L49 đã nói "không diễn giải là steady-state thuần túy". |
| N3 | HTML Total có p90/p95/p99 khác JTL nearest-rank (CMD-9). Stress: HTML 843,9/1023,0/1194,99 so với JTL 143/496/1030. Spike: 12/17/32 so với 24/158/2115. Soak: 15/21/59 so với 17/29/753. | Analyst không dùng số HTML mà dùng raw nearest-rank, đúng theo L8. `ground_truth.md` cũng ghi nguyên nhân không được giả định. Không phải lỗi. |
| N4 | L7 "có thể ngắn hơn thời lượng cấu hình": Stress span 600,092 s. | Câu có "có thể" nên không sai. Load/Spike/Soak là 599,439 / 358,864 / 719,783 s. Thời lượng cấu hình không được kiểm lại ở bước này. |
| N5 | L70 "60–120 s, gần nền trước spike": p95 37 so với 13 ở 0–60 s. | Đây không phải do burst chen vào. Chỉ 32/721 sample thuộc burst; riêng baseline-thread p95 vẫn 37 (CMD-4); trong 60–119,22 s p95 = 37 (CMD-8). Analyst chỉ gọi cửa sổ là "gần nền" và không nêu nguyên nhân, nên không sai. Nguyên nhân tăng trong baseline chưa xác định. |
| N6 | L113–L114: Auth/Read p95 đề xuất 50 ms nhưng Stress 200 VU đo 51/52 ms; cụm "dành khoảng đệm cho đuôi" chỉ đúng so với Soak (19/20). | Là mục tiêu đề xuất, analyst đã tự nêu "Stress vượt nhẹ". Khuyến nghị: Bước 25 nên nói rõ ngưỡng 50 ms chặt hơn kết quả đo ở 200 VU. Không đếm là misreading. |

## 5. Lệnh kiểm tra (chạy từ gốc repo, chỉ đọc, không ghi file)

Mọi lệnh gọi `scripts/jtl_truth.py` (`load_jtl`, `metrics`) trên raw `results/jtl/23120190_{Load,Stress,Spike,Soak}_20261118.jtl`.

Cách tính thời lượng:
- **actual span** (`duration_ms=None`) cho toàn file và stage;
- **fixed-width** (`(b−a)*1000`) cho cửa sổ.

Cửa sổ là `[a,b)` giây tính từ sample đầu của file (min `timeStamp`), lọc theo thời điểm bắt đầu sample. Đã chạy cả 9 lệnh ngày 2026-11-18 và đối chiếu; kết quả là các số ở §6 và Phụ lục A.

### CMD-1 – tổng từng file (span thực) + tính độc lập bằng csv + writer trùng
```bash
cd /home/zinn/zinn/testing/hw05 && python3 - <<'PY'
import sys, math, csv, re, collections; sys.path.insert(0, "scripts"); import jtl_truth as T
R = T.ROOT / "results/jtl"; S = {n: T.load_jtl(R / f"23120190_{n}_20261118.jtl") for n in T.NAMES}
O = {n: min(x[0] for x in S[n]) for n in S}          # origin = min start of the file
def win(n, a, b, pred=lambda x: True):               # fixed-width window [a,b) s by sample start; RPS = count/(b-a)
    return T.metrics([x for x in S[n] if a*1000 <= x[0]-O[n] < b*1000 and pred(x)], (b-a)*1000)
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
Kết quả:
- Load: 33775 / span 599439 / 56.344 rps / mean 3.216 / p90-95-99 = 10/11/18 / max 95.
- Stress: 175882 / 600092 / 293.092 / 67.012 / 143/496/1030 / 1690.
- Spike: 27965 / 358864 / 77.926 / 75.252 / 24/158/2115 / 4633.
- Soak: 158591 / 719783 / 220.332 / 32.449 / 17/29/753 / 6344.
- `success!=true` = 0 ở cả 4 run; `wc -l` = số dòng + 1 header; writer trùng dòng và timestamp.

### CMD-2 – theo label, label chậm nhất theo mean, label giữ max, mã Negative login
```bash
cd /home/zinn/zinn/testing/hw05 && python3 - <<'PY'
import sys, math, csv, re, collections; sys.path.insert(0, "scripts"); import jtl_truth as T
R = T.ROOT / "results/jtl"; S = {n: T.load_jtl(R / f"23120190_{n}_20261118.jtl") for n in T.NAMES}
for n in T.NAMES:
    s = S[n]; ms = {l: T.metrics([x for x in s if x[2] == l]) for l in sorted({x[2] for x in s})}
    print(n)
    for l, m in ms.items(): print("  ", l, "n=%s mean=%.2f p95=%s max=%s err=%s" % (m["count"], m["mean_ms"], m["p95_ms"], m["max_ms"], m["error_count"]))
    print("   slowest by mean:", max(ms, key=lambda l: ms[l]["mean_ms"]), "| label(s) holding global max:", [l for l, m in ms.items() if m["max_ms"] == max(x[1] for x in s)])
    print("   Negative login:", dict(collections.Counter((x[3], x[4]) for x in s if x[2] == "Negative login")), "| non-200 on other labels:", sum(x[3] != "200" for x in s if x[2] != "Negative login"))
PY
```
Kết quả:
- Checkout có mean cao nhất ở cả 4 run.
  - Load: n=4772, mean 11.41, p95 18, max 95.
  - Stress: n=24735, mean 175.94, p95 977, max 1690.
  - Spike: n=3896, mean 195.92, p95 1798, max 4502.
  - Soak: n=22418, mean 89.14, p95 74, max 6282.
- Label giữ max toàn lần: Load = Checkout, Stress = Checkout, Spike = 03 Product detail (4633), Soak = 02 Products (6344).
- Negative login (401, 403): Load (5, 236); Stress (8, 1253); Spike (22, 183); Soak (6, 1123). Tất cả `success=True`; label khác không có mã non-200.
- `err=0` ở mọi label.

### CMD-3 – Stress cửa sổ 150 s (analyst) so với stage theo threadName (ground_truth)
```bash
cd /home/zinn/zinn/testing/hw05 && python3 - <<'PY'
import sys, math, csv, re, collections; sys.path.insert(0, "scripts"); import jtl_truth as T
R = T.ROOT / "results/jtl"; S = {n: T.load_jtl(R / f"23120190_{n}_20261118.jtl") for n in T.NAMES}
O = {n: min(x[0] for x in S[n]) for n in S}          # origin = min start of the file
def win(n, a, b, pred=lambda x: True):               # fixed-width window [a,b) s by sample start; RPS = count/(b-a)
    return T.metrics([x for x in S[n] if a*1000 <= x[0]-O[n] < b*1000 and pred(x)], (b-a)*1000)
def row(tag, m): print(tag, "n=%s rps=%s mean=%s p90=%s p95=%s p99=%s max=%s err=%s" % (m["count"], None if m["rps"] is None else round(m["rps"],2), None if m["mean_ms"] is None else round(m["mean_ms"],2), m["p90_ms"], m["p95_ms"], m["p99_ms"], m["max_ms"], m["error_count"]))
for a in (0, 150, 300, 450): row(f"Stress {a}-{a+150}s", win("Stress", a, a+150))
for a in (0, 150, 300, 450): print(f"  window {a}-{a+150}", dict(sorted(collections.Counter(int(re.search(r"stage (\d+)", x[5]).group(1)) for x in S["Stress"] if a*1000 <= x[0]-O["Stress"] < (a+150)*1000).items())))
st = collections.defaultdict(list)
for x in S["Stress"]: st[int(re.search(r"stage (\d+)", x[5]).group(1))].append(x)
for k, v in sorted(st.items()):
    m = T.metrics(v); print("stage", k, "first start %.3f last end %.3f" % ((min(x[0] for x in v)-O["Stress"])/1000, (max(x[0]+x[1] for x in v)-O["Stress"])/1000), "n=%s rps(actual span)=%.2f mean=%.2f p95=%s p99=%s" % (m["count"], m["rps"], m["mean_ms"], m["p95_ms"], m["p99_ms"]))
PY
jq -c '.runs.Stress.variants.all.stages | to_entries[] | [.key, .value.count, .value.rps, .value.p95_ms]' results/analysis/ground_truth.json
```
Kết quả (fixed-width 150 s):

| Cửa sổ | n | rps | mean | p90 | p95 | p99 | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0–150 s | 15886 | 105.91 | 3.35 | 10 | 12 | 21 | 38 |
| 150–300 s | 31503 | 210.02 | 4.37 | 11 | 17 | 28 | 86 |
| 300–450 s | 61616 | 410.77 | 12.91 | 34 | 48 | 79 | 175 |
| 450–600 s | 66877 | 445.85 | 161.49 | 643 | 905 | 1152 | 1690 |

Cả 4 cửa sổ có `err=0`.

Thành phần theo stage: `{1:15881, 2:5}`, `{2:31497, 3:6}`, `{3:61609, 4:7}`, `{4:66877}`.

Stage theo threadName (span thực):

| Stage | start đầu (s) | kết thúc cuối (s) | n | rps | mean | p95 | p99 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.000 | 149.268 | 15881 | 106.39 | 3.35 | 12 | 21 |
| 2 | 149.361 | 299.316 | 31502 | 210.08 | 4.37 | 17 | 28 |
| 3 | 299.417 | 449.473 | 61615 | 410.61 | 12.91 | 48 | 79 |
| 4 | 449.575 | 600.092 | 66884 | 444.36 | 161.48 | 905 | 1152 |

Dòng `jq` khớp stage ở trên (count, rps, p95).

### CMD-4 – Spike 60 s cửa sổ 0–360, burst đầu/cuối, thành phần 60–120
```bash
cd /home/zinn/zinn/testing/hw05 && python3 - <<'PY'
import sys, math, csv, re, collections; sys.path.insert(0, "scripts"); import jtl_truth as T
R = T.ROOT / "results/jtl"; S = {n: T.load_jtl(R / f"23120190_{n}_20261118.jtl") for n in T.NAMES}
O = {n: min(x[0] for x in S[n]) for n in S}          # origin = min start of the file
def win(n, a, b, pred=lambda x: True):               # fixed-width window [a,b) s by sample start; RPS = count/(b-a)
    return T.metrics([x for x in S[n] if a*1000 <= x[0]-O[n] < b*1000 and pred(x)], (b-a)*1000)
def row(tag, m): print(tag, "n=%s rps=%s mean=%s p90=%s p95=%s p99=%s max=%s err=%s" % (m["count"], None if m["rps"] is None else round(m["rps"],2), None if m["mean_ms"] is None else round(m["mean_ms"],2), m["p90_ms"], m["p95_ms"], m["p99_ms"], m["max_ms"], m["error_count"]))
for a in (0, 60, 120, 180, 240, 300): row(f"Spike {a}-{a+60}s", win("Spike", a, a+60))
b = [x for x in S["Spike"] if x[5].startswith("Spike burst")]
print("burst first start %.3f s, last end %.3f s" % ((min(x[0] for x in b)-O["Spike"])/1000, (max(x[0]+x[1] for x in b)-O["Spike"])/1000))
print("60-120 window by group:", dict(collections.Counter(x[5].split(" ")[1] for x in S["Spike"] if 60000 <= x[0]-O["Spike"] < 120000)))
row("Spike 60-120s baseline-threads only", win("Spike", 60, 120, lambda x: x[5].startswith("Spike baseline")))
row("Spike 120-180s ", win("Spike", 120, 180))
PY
jq -c '.runs.Spike.variants.all.phases | to_entries[] | [.key, .value.count, .value.rps, .value.p95_ms]' results/analysis/ground_truth.json
```
Kết quả (fixed-width 60 s; analyst dùng 60–120, 120–180, 180–240, 240–300):

| Cửa sổ | n | rps | mean | p90 | p95 | p99 | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0–60 s | 668 | 11.13 | 4.25 | 12 | 13 | 22 | 52 |
| 60–120 s | 721 | 12.02 | 7.00 | 27 | 37 | 53 | 149 |
| 120–180 s | 11291 | 188.18 | 179.22 | 340 | 1497 | 3322 | 4633 |
| 180–240 s | 13890 | 231.50 | 4.94 | 13 | 17 | 29 | 90 |
| 240–300 s | 695 | 11.58 | 3.14 | 10 | 11 | 13 | 19 |
| 300–360 s | 700 | 11.67 | 3.06 | 10 | 11 | 13 | 16 |

Cả 6 cửa sổ có `err=0`.

- Burst: first start 119.220 s, last end 239.844 s.
- Cửa sổ 60–120 s gồm `{'baseline': 689, 'burst': 32}`; chỉ baseline-thread thì n=689, rps 11.48, mean 7.1, p95 37, p99 56.
- Phase của ground_truth (khác cửa sổ analyst, xem N1): `0-120s` 1389, `120-180s` 11291 (188.18, p95 1497), `180-240s` 13890 (231.5, p95 17), `240-360s` 1395.

### CMD-5 – Soak 120 s, số học throughput và quy tắc regression
```bash
cd /home/zinn/zinn/testing/hw05 && python3 - <<'PY'
import sys, math, csv, re, collections; sys.path.insert(0, "scripts"); import jtl_truth as T
R = T.ROOT / "results/jtl"; S = {n: T.load_jtl(R / f"23120190_{n}_20261118.jtl") for n in T.NAMES}
O = {n: min(x[0] for x in S[n]) for n in S}          # origin = min start of the file
def win(n, a, b, pred=lambda x: True):               # fixed-width window [a,b) s by sample start; RPS = count/(b-a)
    return T.metrics([x for x in S[n] if a*1000 <= x[0]-O[n] < b*1000 and pred(x)], (b-a)*1000)
def row(tag, m): print(tag, "n=%s rps=%s mean=%s p90=%s p95=%s p99=%s max=%s err=%s" % (m["count"], None if m["rps"] is None else round(m["rps"],2), None if m["mean_ms"] is None else round(m["mean_ms"],2), m["p90_ms"], m["p95_ms"], m["p99_ms"], m["max_ms"], m["error_count"]))
for a in range(0, 720, 120): row(f"Soak {a}-{a+120}s", win("Soak", a, a+120))
rps = [win("Soak", a, a+120)["rps"] for a in (240, 360, 480, 600)]; print("Soak rps 240-720 min/max: %.2f %.2f" % (min(rps), max(rps)))
print("max allThreads Soak:", max(x[8] for x in S["Soak"]), "| Stress stage 3 rps window 300-450: %.2f" % win("Stress", 300, 450)["rps"])
print("regression rule, baseline p95=20: smallest integer p95 with new>1.2*20 and new-20>=5 ->", min(v for v in range(21, 100) if v > 1.2*20 and v - 20 >= 5))
PY
```
Kết quả (fixed-width 120 s):

| Cửa sổ | n | rps | mean | p90 | p95 | p99 | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0–120 s | 21588 | 179.9 | 4.76 | 12 | 17 | 30 | 90 |
| 120–240 s | 24551 | 204.59 | 158.33 | 261 | 1013 | 3589 | 6344 |
| 240–360 s | 27364 | 228.03 | 24.06 | 15 | 24 | 145 | 5179 |
| 360–480 s | 28376 | 236.47 | 5.54 | 14 | 20 | 37 | 132 |
| 480–600 s | 28398 | 236.65 | 5.58 | 14 | 20 | 33 | 130 |
| 600–720 s | 28314 | 235.95 | 6.44 | 15 | 21 | 44 | 200 |

Cả 6 cửa sổ có `err=0`.

- rps 240–720 s: min 228.03, max 236.65.
- `max allThreads` Soak = 203; Stress 300–450 s rps = 410.77.
- Quy tắc regression với p95 baseline 20: giá trị nguyên nhỏ nhất kích hoạt = 25.

### CMD-6 – các nhóm SLO (Negative login bị loại)
```bash
cd /home/zinn/zinn/testing/hw05 && python3 - <<'PY'
import sys, math, csv, re, collections; sys.path.insert(0, "scripts"); import jtl_truth as T
R = T.ROOT / "results/jtl"; S = {n: T.load_jtl(R / f"23120190_{n}_20261118.jtl") for n in T.NAMES}
O = {n: min(x[0] for x in S[n]) for n in S}          # origin = min start of the file
def win(n, a, b, pred=lambda x: True):               # fixed-width window [a,b) s by sample start; RPS = count/(b-a)
    return T.metrics([x for x in S[n] if a*1000 <= x[0]-O[n] < b*1000 and pred(x)], (b-a)*1000)
G = {"Auth": ("01 Login",), "Read": ("02 Products", "03 Product detail"), "Trans": ("04 Add cart", "05 Get cart", "06 Checkout", "07 My orders")}
for n, a, b in (("Soak", 360, 600), ("Stress", 300, 450), ("Soak", 120, 240)):
    for g, ls in G.items(): m = win(n, a, b, lambda x: x[2] in ls); print(n, f"{a}-{b}s", g, "n=%s p95=%s p99=%s err=%s" % (m["count"], m["p95_ms"], m["p99_ms"], m["error_count"]))
PY
```
Kết quả:

| Run, cửa sổ | Nhóm | n | p95 | p99 | err |
|---|---|---:|---:|---:|---:|
| Soak 360–600 s | Auth | 8049 | 19 | 37 | 0 |
| Soak 360–600 s | Read | 16107 | 20 | 36 | 0 |
| Soak 360–600 s | Trans | 32216 | 20 | 34 | 0 |
| Stress 300–450 s | Auth | 8835 | 51 | 81 | 0 |
| Stress 300–450 s | Read | 17578 | 52 | 84 | 0 |
| Stress 300–450 s | Trans | 34761 | 45 | 76 | 0 |
| Soak 120–240 s | Auth | 3424 | 1054 | 2181 | 0 |
| Soak 120–240 s | Read | 6924 | 303 | 1594 | 0 |
| Soak 120–240 s | Trans | 14032 | 1408 | 3908 | 0 |

### CMD-7 – theo label trong các cửa sổ chậm (kiểm tra giả thuyết "Checkout")
```bash
cd /home/zinn/zinn/testing/hw05 && python3 - <<'PY'
import sys, math, csv, re, collections; sys.path.insert(0, "scripts"); import jtl_truth as T
R = T.ROOT / "results/jtl"; S = {n: T.load_jtl(R / f"23120190_{n}_20261118.jtl") for n in T.NAMES}
O = {n: min(x[0] for x in S[n]) for n in S}          # origin = min start of the file
def win(n, a, b, pred=lambda x: True):               # fixed-width window [a,b) s by sample start; RPS = count/(b-a)
    return T.metrics([x for x in S[n] if a*1000 <= x[0]-O[n] < b*1000 and pred(x)], (b-a)*1000)
for n, a, b in (("Stress", 450, 600), ("Spike", 120, 180), ("Soak", 120, 240)):
    print(n, a, b)
    for l in T.LABELS: m = win(n, a, b, lambda x: x[2] == l); print("  ", l, "n=%s mean=%.1f p95=%s p99=%s" % (m["count"], m["mean_ms"], m["p95_ms"], m["p99_ms"]))
PY
```
Kết quả: trong cả ba cửa sổ, `06 Checkout` có mean cao nhất.

| Cửa sổ | 06 Checkout (mean, p95) | 07 My orders (mean, p95) | 01 Login (mean, p95) |
|---|---|---|---|
| Stress 450–600 s | 433.4, 1128 | 361.7, 1061 | 202.6, 854 |
| Spike 120–180 s | 474.0, 3163 | 357.2, 2404 | 180.0, 1556 |
| Soak 120–240 s | 440.9, 3435 | 282.4, 1746 | 142.4, 1054 |

Các label còn lại có mean thấp hơn hẳn (≤ 86,3 ms). Giả thuyết "Checkout là đường cần khảo sát" của analyst nhất quán với số đo; không xác định được nhân quả.

### CMD-8 – Spike 60–120 s: chậm trước hay sau khi burst bắt đầu
```bash
cd /home/zinn/zinn/testing/hw05 && python3 - <<'PY'
import sys; sys.path.insert(0,'scripts'); import jtl_truth as T
S=T.load_jtl(T.ROOT/'results/jtl/23120190_Spike_20261118.jtl'); o=min(x[0] for x in S)
for a,b in ((0,60),(60,119.22),(119.22,120),(60,100),(100,119.22)):
    g=[x for x in S if a*1000<=x[0]-o<b*1000]; m=T.metrics(g,1000)
    print(a,b,m['count'],round(m['mean_ms'],2),m['p95_ms'],m['p99_ms'],m['max_ms'])
PY
```
Kết quả (n, mean, p95, p99, max): 0–60 s: 668, 4.25, 13, 22, 52; 60–119,22 s: 682, 7.07, 37, 53, 149; 119,22–120 s: 39, 5.82, 44, 56, 56; 60–100 s: 459, 6.84, 33, 48, 149; 100–119,22 s: 223, 7.53, 42, 53, 65.

### CMD-9 – HTML statistics.json Total (chỉ để so, không phải số analyst dùng)
```bash
cd /home/zinn/zinn/testing/hw05 && for n in Load Stress Spike Soak; do echo -n "$n "; jq -c '.Total|[.sampleCount,.errorCount,.meanResTime,.pct1ResTime,.pct2ResTime,.pct3ResTime,.maxResTime,.throughput]' results/html/23120190_${n}_20261118/statistics.json; done
```
Kết quả `[count, err, mean, p90, p95, p99, max, throughput]`:
- Load: `[33775,0,3.216,10,11,18,95,56.344]`.
- Stress: `[175882,0,67.012,843.9,1023,1194.99,1690,293.092]`.
- Spike: `[27965,0,75.252,12,17,32,4633,77.926]`.
- Soak: `[158591,0,32.449,15,21,59,6344,220.332]`.

Count, error, mean, max và throughput trùng JTL. Chỉ p90/p95/p99 khác nearest-rank (xem N3).

## 6. Phụ lục A – Bảng coverage mọi con số/nhận định trong dòng 1–122
Cột "Kết quả": ✔ = khớp raw. Số trong `11` viết dấu phẩy thập phân; ở đây giữ nguyên.

### A1. Phương pháp (L5–L10)

| Dòng | Trích | Lọc / cmd | Kết quả |
|---|---|---|---|
| L5 | "bốn file `…{Load,Stress,Spike,Soak}_20261118.jtl`; mỗi dòng là một sample, kể cả `Negative login`" | CMD-1 `wc -l` | ✔ 33.776 / 175.883 / 27.966 / 158.592 dòng = dữ liệu + header; count `Negative login` nằm trong tổng. |
| L5 | "`…Soak_20261118_writer.jtl` … bản ghi trùng" | CMD-1 (`.soak_writer_comparison`) | ✔ cùng 158.591 dòng, cùng min/max `timeStamp`. |
| L6 | "error % = 100 × số dòng `success=false` / tổng dòng"; 401/403 không mặc nhiên là lỗi | CMD-1 `success!=true`; CMD-2 | ✔ 0 lỗi ở cả 4 run; 401/403 đều `success=true`. |
| L7 | "Throughput toàn lần = tổng số dòng / (… `timeStamp + elapsed` − `timeStamp` bắt đầu sớm nhất)" | CMD-1 span thực | ✔ công thức đúng; xem N4 về "có thể ngắn hơn". |
| L8 | "Mean là trung bình `elapsed`; p90/p95/p99 dùng nearest-rank … `ceil(p × N)`"; "Label chậm nhất … theo **mean**, không phải theo max" | CMD-1 (tính độc lập), CMD-2 | ✔ nearest-rank độc lập trùng `metrics()`; label chậm nhất theo mean đúng. |
| L9 | "cận trái đóng và cận phải mở"; "RPS cửa sổ = số sample bắt đầu trong cửa sổ / độ rộng cửa sổ"; "sample vượt qua ranh giới vẫn thuộc cửa sổ nó bắt đầu"; "có thể lệch nhẹ" | CMD-3/4/5 (`win(...)`) | ✔ đúng mô tả; lệch nhẹ có thật (N2). |
| L10 | Nhận định nguyên nhân là giả thuyết, không có đo CPU/bộ nhớ/I/O | — | Phát biểu giới hạn, không phải số; thuộc D8. |

### A2. Load (L12–L25)

| Dòng | Trích | Lọc / cmd | Kết quả |
|---|---|---|---|
| L14 | "toàn bộ sample trong `…Load_20261118.jtl`" | CMD-1 | ✔ |
| L18 | "Tổng request 33.775" | CMD-1 | ✔ 33775 |
| L19 | "599,439 s; 56,34 request/s" | CMD-1 span thực | ✔ 599439 ms; 56.344 |
| L20 | "`success=false`; error %: 0; 0,000%" | CMD-1 | ✔ 0 / 0.000 |
| L21 | "3,22 / 10 / 11 / 18 / 95 ms" (mean/p90/p95/p99/max) | CMD-1 | ✔ 3.216 / 10 / 11 / 18 / 95 |
| L23 | "06 Checkout chậm nhất theo mean: 11,41 ms; p95 18 ms, max 95 ms (4.772 sample)" | CMD-2 (`label==06 Checkout`) | ✔ 11.41 / 18 / 95 / 4772 |
| L23 | "Không có label nào có `success=false`" | CMD-2 | ✔ `err=0` ở 8 label |
| L23 | "`Negative login` có 5 response 401 và 236 response 403, đều `success=true`" | CMD-2 | ✔ (401,5), (403,236) |
| L25 | "Checkout là ứng viên … vì mean cao nhất"; "độ trễ thấp … chưa thể khẳng định có nút thắt" | CMD-2 | ✔ Checkout mean cao nhất; nhận định có điều kiện. |

### A3. Stress (L27–L51)

| Dòng | Trích | Lọc / cmd | Kết quả |
|---|---|---|---|
| L29 | "toàn bộ sample trong `…Stress_20261118.jtl`" | CMD-1 | ✔ |
| L33 | "Tổng request 175.882" | CMD-1 | ✔ |
| L34 | "600,092 s; 293,09 request/s" | CMD-1 | ✔ 600092 ms; 293.092 |
| L35 | "0; 0,000%" | CMD-1 | ✔ |
| L36 | "67,01 / 143 / 496 / 1.030 / 1.690 ms" | CMD-1 | ✔ 67.012 / 143 / 496 / 1030 / 1690 |
| L38 | "06 Checkout … 175,94 ms; p95 977 ms, max 1.690 ms (24.735 sample)" | CMD-2 | ✔ |
| L38 | "`Negative login`: 8 response 401 và 1.253 response 403, tất cả `success=true`" | CMD-2 | ✔ |
| L38 | "Không có label nào có `success=false`" | CMD-2 | ✔ |
| L40 | "các cửa sổ 150 s … các bậc cấu hình 50/100/200/290 VU, mỗi bậc có ramp" | CMD-3; `allThreads` max mỗi cửa sổ = 50/100/200/290 | Phần 50/100/200/290 khớp. Ramp là cấu hình plan, không kiểm ở bước này. |
| L44 | "0–150 s, 50 VU \| 15.886 \| 105,91 \| 3,35 / 12 / 21 \| 0" | CMD-3 | ✔ n=15886; 105.91; 3.35/12/21; err 0 |
| L45 | "150–300 s, 100 VU \| 31.503 \| 210,02 \| 4,37 / 17 / 28 \| 0" | CMD-3 | ✔ |
| L46 | "300–450 s, 200 VU \| 61.616 \| 410,77 \| 12,91 / 48 / 79 \| 0" | CMD-3 | ✔ |
| L47 | "450–600 s, 290 VU \| 66.877 \| 445,85 \| 161,49 / 905 / 1.152 \| 0" | CMD-3 | ✔ |
| L49 | "Độ trễ đã tăng … ở bậc 200 VU so với 100 VU … suy giảm nghiêm trọng nhất bắt đầu ở 290 VU: p95 tăng từ 48 lên 905 ms … RPS chỉ tăng từ 410,77 lên 445,85" | CMD-3 | ✔ mean/p95: 4.37/17 → 12.91/48 → 161.49/905; rps 410.77 → 445.85 (+8,5% khi VU tăng 45%). |
| L49 | "Ranh giới cửa sổ gần nhưng không trùng chính xác ranh giới nhóm" | CMD-3 | ✔ stage 3 bắt đầu 299.417 s, stage 4 bắt đầu 449.575 s; xem N2. |
| L51 | "nhiều label cùng chậm và throughput gần bão hòa" (giả thuyết) | CMD-7, CMD-3 | Phù hợp số đo: Login 202.6, My orders 361.7, Checkout 433.4 (mean, 450–600 s); rps +8,5%. Không phải nhân quả cứng. |

### A4. Spike (L53–L77)

| Dòng | Trích | Lọc / cmd | Kết quả |
|---|---|---|---|
| L55 | "toàn bộ sample trong `…Spike_20261118.jtl`" | CMD-1 | ✔ |
| L59 | "Tổng request 27.965" | CMD-1 | ✔ |
| L60 | "358,864 s; 77,93 request/s" | CMD-1 | ✔ 358864 ms; 77.926 |
| L61 | "0; 0,000%" | CMD-1 | ✔ |
| L62 | "75,25 / 24 / 158 / 2.115 / 4.633 ms" | CMD-1 | ✔ 75.252 / 24 / 158 / 2115 / 4633 |
| L64 | "06 Checkout … 195,92 ms; p95 1.798 ms, max 4.502 ms (3.896 sample)" | CMD-2 | ✔ |
| L64 | "Max toàn lần thuộc **03 Product detail**, không phải Checkout" | CMD-2 | ✔ max 4633 ở 03 Product detail; Checkout max 4502. |
| L64 | "Lọc `Negative login`: 22 response 401 và 183 response 403" | CMD-2 | ✔ |
| L70 | "60–120 s … 721 \| 12,02 \| 7,00 / 37 / 53 \| 0" | CMD-4 | ✔ |
| L71 | "120–180 s … 11.291 \| 188,18 \| 179,22 / 1.497 / 3.322 \| 0" | CMD-4 | ✔ |
| L72 | "180–240 s … 13.890 \| 231,50 \| 4,94 / 17 / 29 \| 0" | CMD-4 | ✔ |
| L73 | "240–300 s … 695 \| 11,58 \| 3,14 / 11 / 13 \| 0" | CMD-4 | ✔ |
| L70 | Nhãn "gần nền trước spike" | CMD-4, CMD-8 | Nhãn không sai: 32 sample burst, baseline-only p95 vẫn 37 (N5). |
| L75 | "nhóm burst bắt đầu sample đầu ở 119,220 s và sample cuối kết thúc ở 239,844 s" | CMD-4 (`threadName` bắt đầu bằng "Spike burst") | ✔ 119.220 / 239.844 |
| L75 | "độ trễ đuôi tăng mạnh trong cửa sổ đầu; … p95 và p99 phục hồi ngay cả khi tải burst còn hiện diện, và sau burst trở lại mức nền" | CMD-4 | ✔ p95/p99: 1497/3322 → 17/29 (n=13890); 240–300 s: 11/13. |
| L75 | "Không quan sát được `success=false`" | CMD-4 | ✔ err=0 ở mọi cửa sổ |
| L77 | "tranh chấp/hàng đợi tạm thời … có thể ảnh hưởng mạnh đến Checkout" (giả thuyết) | CMD-7 | Nhất quán: Checkout mean 474.0 và p95 3163 cao nhất ở 120–180 s. Không xác định nhân quả. |

### A5. Soak (L79–L105)

| Dòng | Trích | Lọc / cmd | Kết quả |
|---|---|---|---|
| L81 | "toàn bộ sample trong `…Soak_20261118.jtl`, không cộng file writer trùng" | CMD-1 | ✔ |
| L85 | "Tổng request 158.591" | CMD-1 | ✔ |
| L86 | "719,783 s; 220,33 request/s" | CMD-1 | ✔ 719783 ms; 220.332 |
| L87 | "0; 0,000%" | CMD-1 | ✔ |
| L88 | "32,45 / 17 / 29 / 753 / 6.344 ms" | CMD-1 | ✔ 32.449 / 17 / 29 / 753 / 6344 |
| L90 | "06 Checkout … 89,14 ms; p95 74 ms, max 6.282 ms (22.418 sample)" | CMD-2 | ✔ |
| L90 | "Max toàn lần thuộc **02 Products**, không phải Checkout" | CMD-2 | ✔ 6344 ở 02 Products; Checkout max 6282. |
| L90 | "6 response 401 và 1.123 response 403, tất cả `success=true`" | CMD-2 | ✔ |
| L96 | "0–120 s \| 21.588 \| 179,90 \| 4,76 / 17 / 30 \| 0" | CMD-5 | ✔ |
| L97 | "120–240 s \| 24.551 \| 204,59 \| 158,33 / 1.013 / 3.589 \| 0" | CMD-5 | ✔ |
| L98 | "240–360 s \| 27.364 \| 228,03 \| 24,06 / 24 / 145 \| 0" | CMD-5 | ✔ |
| L99 | "360–480 s \| 28.376 \| 236,47 \| 5,54 / 20 / 37 \| 0" | CMD-5 | ✔ |
| L100 | "480–600 s \| 28.398 \| 236,65 \| 5,58 / 20 / 33 \| 0" | CMD-5 | ✔ |
| L101 | "600–720 s \| 28.314 \| 235,95 \| 6,44 / 21 / 44 \| 0" | CMD-5 | ✔ |
| L103 | "đợt chậm lớn trong khoảng 120–240 s, sau đó độ trễ giảm và throughput ổn định hơn" | CMD-5 | ✔ mean 158.33, p95 1013; rps 204.59 → 228.03 → ~236. |
| L103 | "Cuối lần chạy p95/p99 cao hơn nhẹ so với hai cửa sổ trước" | CMD-5 | ✔ 600–720 s: p95 21 so với 20/20; p99 44 so với 37/33. |
| L103 | "không có xu hướng suy giảm liên tục rõ ràng" | CMD-5 | Phù hợp: p95 20→20→21, mean 5.54→5.58→6.44. Chênh nhỏ; kết luận đã nêu giới hạn. |
| L103 | "Cửa sổ đầu gồm ramp, cửa sổ cuối có kết thúc thread" | CMD-5 (`allThreads` min) | Phù hợp: 0–120 s min allThreads=5, 600–720 s min=1. |
| L105 | "Checkout là đường cần khảo sát; … không đủ để … kết luận rò rỉ bộ nhớ/tài nguyên" | CMD-7 | ✔ Checkout mean 440.9 và p95 3435 cao nhất ở 120–240 s; không gán rò rỉ bộ nhớ (D8). |

### A6. Đề xuất ngưỡng (L107–L122)

| Dòng | Trích | Lọc / cmd | Kết quả |
|---|---|---|---|
| L109 | Auth = `01 Login`; Read = 02+03; Transactional = 04–07; `Negative login` tách riêng; mức đề xuất 200 VU | CMD-6 | ✔ phân nhóm đúng như code CMD-6; "đề xuất" không phải số đo. |
| L113 | "Soak 360–600 s, 8.049 login: p95/p99 là 19/37 ms" | CMD-6 | ✔ |
| L113 | "Stress 300–450 s, 8.835 login: 51/81 ms" | CMD-6 | ✔ |
| L113 | "50 ms / 100 ms"; "51 ms cho thấy lần Stress đã vượt nhẹ mục tiêu p95" | CMD-6 | ✔ 51 > 50 là đúng; "khoảng đệm cho đuôi" xem N6. |
| L114 | "Soak 360–600 s có 16.107 sample, p95/p99 20/36 ms; Stress 300–450 s có 17.578 sample, 52/84 ms" | CMD-6 | ✔ |
| L114 | "Stress vượt nhẹ p95" | CMD-6 | ✔ 52 > 50 |
| L115 | "Soak 360–600 s có 32.216 sample, p95/p99 20/34 ms; Stress 300–450 s có 34.761 sample, 45/76 ms" | CMD-6 | ✔ |
| L117 | "chọn sample theo `timeStamp` trong cửa sổ tương đối từ sample đầu, cận trái đóng và cận phải mở; các cửa sổ Stress gồm cả ramp" | CMD-6 (`win`, `[a,b)`) | ✔ đúng phương pháp. |
| L117 | "Soak 120–240 s cho p95/p99 Auth 1.054/2.181 ms, Read 303/1.594 ms và Transactional 1.408/3.908 ms, đều vượt mục tiêu đề xuất" | CMD-6 | ✔ 1054/2181; 303/1594; 1408/3908; đều > 50/100. |
| L117 | "không coi lần Soak này đã đạt SLO liên tục" | CMD-5, CMD-6 | ✔ nhất quán với số đo. |
| L119 | "Error tối đa: 0,1% … Trong bốn JTL ở Bước 20, quan sát là 0%" | CMD-1 | ✔ error đo = 0%; 0,1% là mức đề xuất, không phải số đo. |
| L119 | "`Negative login` có 401/403 được đánh dấu `success=true`, không được coi là đăng nhập thành công" | CMD-2 | ✔ |
| L120 | "Throughput tối thiểu: 200 request/s … số sample bắt đầu / 120 s" | CMD-5 | Công thức khớp `win(...)` fixed-width 120 s. |
| L120 | "Soak đạt 204,59 request/s ở 120–240 s và 228,03–236,65 request/s ở các cửa sổ 240–720 s; Stress 300–450 s đạt 410,77 request/s" | CMD-5 | ✔ min/max 240–720 s = 228.03 / 236.65; Stress 410.77. |
| L120 | "cửa sổ Soak 120–240 s đạt throughput nhưng vi phạm độ trễ" | CMD-5, CMD-6 | ✔ 204.59 ≥ 200 nhưng p95 Auth 1054, Read 303, Trans 1408. |
| L121 | "Soak có tối đa 203 thread" | CMD-5 (`max allThreads`) | ✔ 203 |
| L121 | "Stress bậc 200 VU chỉ kéo dài khoảng 150 s và có ramp" | CMD-3 | Khoảng 150 s khớp: 299.417 → 449.473 s (150.06 s). Ramp là cấu hình, không kiểm lại. |
| L121 | "200 VU … 200 request/s" là điểm thử tiếp, không phải giới hạn đã chứng minh | — | Khuyến nghị, không phải số đo. |
| L122 | "p95 mới vừa lớn hơn 1,20 lần p95 baseline **và** tăng ít nhất 5 ms … ít nhất 1.000 sample" | CMD-5 | Quy tắc đề xuất, không phải số đo. |
| L122 | "baseline p95 Read 20 ms ở Soak 360–600 s sẽ kích hoạt từ 25 ms" | CMD-5 (dòng `regression rule`), CMD-6 | ✔ p95 Read = 20; ngưỡng nguyên nhỏ nhất thỏa `>1.2×20` và `≥+5` là 25. |
| L122 | "cửa sổ Stress 300–450 s có tải/thời đoạn khác nên không dùng trực tiếp làm cặp so sánh" | CMD-3, CMD-6 | Lập luận hợp lệ: Stress 300–450 s = 200 VU, 150 s (Soak 203 VU, 720 s). |

## 7. Phạm vi và chưa kiểm tra

- Đã kiểm: mọi số và nhận định định lượng ở `11_ai_analysis.md` dòng 1–122 so với 4 JTL thô qua `scripts/jtl_truth.py`.
- Chưa kiểm:
  - Bước 22 (dòng 123–195) và các đề xuất tối ưu: ngoài phạm vi bước 24.
  - Cấu hình plan `.jmx` (ramp-up, số VU danh định): chỉ so gián tiếp qua `allThreads` và `threadName`.
  - Nhận định nguyên nhân (CPU, DB, queue, rò rỉ): JTL không đủ bằng chứng; analyst không khẳng định những điều này.
  - HTML report: chỉ dùng CMD-9 để tham chiếu, không đối chiếu từng label.
- Không đọc `AI_LOG.md`, `TASK1_REPORT.md`, `endurance.json`. Không sửa JTL, SUT, plan, script, ground_truth hay report 11.
