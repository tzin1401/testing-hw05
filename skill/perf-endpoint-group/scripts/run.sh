#!/usr/bin/env bash
# End-to-end performance test for ONE endpoint group:
#   generate plan -> reset SUT -> JMeter non-GUI (+ RAM monitor) -> analyze JTL -> SLO verdict.
# Usage (from the project root, the folder that holds data/):
#   run.sh <group-name|path/to/group.json> [smoke|load]
# Env overrides: THREADS RAMPUP DURATION STUDENT_ID SUT_RESET SUT_URL JMETER
set -euo pipefail
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
GROUP_ARG="${1:?usage: run.sh <group|group.json> [smoke|load]}"
PROFILE="${2:-smoke}"
GROUP_JSON="$GROUP_ARG"; [ -f "$GROUP_JSON" ] || GROUP_JSON="$SKILL/groups/$GROUP_ARG.json"
[ -f "$GROUP_JSON" ] || { echo "Không tìm thấy nhóm '$GROUP_ARG' (có: $(ls "$SKILL/groups" | sed 's/.json//' | tr '\n' ' '))"; exit 2; }
GROUP=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['name'])" "$GROUP_JSON")

case "$PROFILE" in
  smoke) T=20; R=10; D=120 ;;
  load)  T=50; R=50; D=600 ;;
  *) echo "profile phải là smoke hoặc load"; exit 2 ;;
esac
T="${THREADS:-$T}"; R="${RAMPUP:-$R}"; D="${DURATION:-$D}"
SID="${STUDENT_ID:-23120190}"
SUT_URL="${SUT_URL:-http://localhost:3000}"
JMETER="${JMETER:-jmeter}"

echo "== [1/6] Kiểm tra môi trường"
for f in $(python3 -c "import json,sys;print(' '.join(c['file'] for c in json.load(open(sys.argv[1])).get('csv',[])))" "$GROUP_JSON"); do
  [ -f "$f" ] || { echo "Thiếu file dữ liệu $f (chạy từ thư mục gốc project)"; exit 2; }
done
command -v "$JMETER" >/dev/null || { echo "Không thấy jmeter trong PATH"; exit 2; }
# JMeter 5.6.3 + Groovy fails on Java >= 21 here; prefer JDK 17 when it is installed.
if [ -z "${JAVA_HOME:-}" ] && [ -d /usr/lib/jvm/java-17-openjdk-amd64 ]; then export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64; fi
echo "group=$GROUP profile=$PROFILE threads=$T rampup=${R}s duration=${D}s JAVA_HOME=${JAVA_HOME:-system}"

STAMP=$(date +%Y%m%d-%H%M%S); DAY=$(date +%Y%m%d)
OUT="results/skill/${GROUP}_${STAMP}"; mkdir -p "$OUT"
PLAN="$OUT/${SID}_Load_${DAY}.jmx"

echo "== [2/6] Sinh test plan từ $GROUP_JSON"
python3 "$SKILL/scripts/gen_plan.py" "$GROUP_JSON" "$PLAN"

echo "== [3/6] Reset SUT"
RESET="${SUT_RESET:-scripts/reset_sut.sh}"
if [ -x "$RESET" ]; then "$RESET"; else echo "Không có $RESET → bỏ qua reset, chỉ kiểm tra SUT đang chạy"; fi
curl -sf "$SUT_URL/api/products" >/dev/null || { echo "SUT không phản hồi tại $SUT_URL"; exit 2; }

echo "== [4/6] Bật monitor RAM backend (1 s/mẫu)"
PID=$(pgrep -f '^node server.js' | head -n1 || true)
MON="$OUT/monitor.csv"; MON_PID=""
if [ -n "$PID" ]; then
  ( printf 'timestamp,cpu_percent,rss_mb\n'
    while s=$(ps -o %cpu=,rss= -p "$PID"); do
      echo "$(date +%H:%M:%S) $s" | awk '{printf "%s,%s,%.2f\n",$1,$2,$3/1024}'; sleep 1; done ) > "$MON" &
  MON_PID=$!
  trap '[ -n "$MON_PID" ] && kill "$MON_PID" 2>/dev/null || true' EXIT
else echo "Không tìm thấy tiến trình node server.js → bỏ monitor"; fi

echo "== [5/6] Chạy JMeter non-GUI (~$((D + 15)) s)"
HOST=$(echo "$SUT_URL" | sed -E 's#https?://([^:/]+).*#\1#'); PORT=$(echo "$SUT_URL" | sed -nE 's#.*:([0-9]+).*#\1#p'); PORT="${PORT:-80}"
"$JMETER" -n -t "$PLAN" -l "$OUT/run.jtl" -e -o "$OUT/html" -j "$OUT/jmeter.log" \
  -Jthreads="$T" -Jrampup="$R" -Jduration="$D" -Jhost="$HOST" -Jport="$PORT" \
  -Jjmeter.save.saveservice.output_format=csv -Jjmeter.save.saveservice.print_field_names=true \
  -Jsummariser.interval=30
[ -n "$MON_PID" ] && kill "$MON_PID" 2>/dev/null || true; MON_PID=""

echo "== [6/6] Phân tích JTL + SLO"
set +e
python3 "$SKILL/scripts/analyze.py" "$OUT/run.jtl" "$GROUP_JSON" "$OUT" "$MON"
RC=$?
set -e
echo
echo "RUN_DIR=$OUT"
echo "Plan: $PLAN | JTL: $OUT/run.jtl | HTML: $OUT/html/index.html | Summary: $OUT/summary.md"
exit $RC
