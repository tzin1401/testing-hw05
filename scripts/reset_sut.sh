#!/bin/bash
# Reset SUT giữa các lần chạy: restart backend (database.js tự DROP + seed lại DB => xóa lockout, order, cart)
# rồi đăng ký lại các user test trong data/users.csv.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
pkill -f "^node server.js" || true
sleep 1
cd "$ROOT/eshop-sut/backend"
setsid node server.js > "$ROOT/results/server.log" 2>&1 &
until curl -s localhost:3000/api/products >/dev/null; do sleep 0.5; done
tail -n +2 "$ROOT/data/users.csv" | while IFS=, read -r name email pw; do
  curl -s -o /dev/null -XPOST localhost:3000/api/register -H 'Content-Type: application/json' \
    -d "{\"name\":\"$name\",\"email\":\"$email\",\"password\":\"$pw\"}"
done
echo "SUT reset. Backend PID: $(pgrep -f "^node server.js")  | users seeded: $(($(wc -l < "$ROOT/data/users.csv")-1))"
