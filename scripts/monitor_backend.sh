#!/usr/bin/env bash
set -eu

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <output.csv>" >&2
    exit 1
fi
pid=$(pgrep -f '^node server.js' | head -n 1) || {
    echo 'Backend node server.js not found' >&2
    exit 1
}
trap 'exit 0' INT TERM
printf 'timestamp,cpu_percent,rss_mb\n' > "$1"
while :; do
    stats=$(ps -o %cpu=,rss= -p "$pid") || break
    [ -n "$stats" ] || break
    printf '%s %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$stats" |
        awk '{printf "%s,%s,%.2f\n", $1, $2, $3 / 1024}' >> "$1"
    sleep 1
done
