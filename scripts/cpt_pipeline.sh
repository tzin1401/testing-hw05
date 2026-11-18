#!/bin/bash
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 2
if [ "$#" -ne 2 ]; then echo 'usage: cpt_pipeline.sh BASE HEAD' >&2; exit 2; fi
BASE=$1 HEAD=$2
SUT="$ROOT/eshop-sut"
resolved=$(git -C "$SUT" rev-parse --verify "$HEAD^{commit}") || exit 2
actual=$(git -C "$SUT" rev-parse HEAD) || exit 2
if [ "$resolved" != "$actual" ]; then echo 'INCONCLUSIVE: checkout HEAD first' >&2; exit 2; fi
# Database runtime state and installed dependencies are deliberately not cleaned.
if ! git -C "$SUT" diff --quiet --cached HEAD --; then echo 'INCONCLUSIVE: staged changes' >&2; exit 2; fi
if [ -n "$(git -C "$SUT" status --porcelain --untracked-files=all | grep -vE '^( M backend/database\.sqlite|\?\? backend/node_modules/)' || true)" ]; then
    echo 'INCONCLUSIVE: unexpected working tree changes' >&2; exit 2
fi
exec 9>"$ROOT/results/cpt/.sut.lock"
flock -n 9 || { echo 'INCONCLUSIVE: SUT already in use' >&2; exit 2; }
tier=${CPT_TIER:-smoke}
case "$tier" in
 smoke) plan=test-plans/23120190_Load_20261117.jmx; opts=(-Jthreads=30 -Jrampup=15 -Jduration=180 -Jlock_percent=5); baseline_name=baseline.json ;;
 nightly) plan=test-plans/23120190_Load_20261117.jmx; opts=(-Jthreads=50 -Jrampup=50 -Jduration=600 -Jlock_percent=5); baseline_name=nightly_baseline.json ;;
 stress) plan=test-plans/23120190_Stress_20261117.jmx; opts=(); baseline_name=stress_baseline.json ;;
 spike) plan=test-plans/23120190_Spike_20261117.jmx; opts=(); baseline_name=spike_baseline.json ;;
 soak) plan=test-plans/23120190_Soak_20261118.jmx; opts=(); baseline_name=soak_baseline.json ;;
 *) echo 'INCONCLUSIVE: unknown tier' >&2; exit 2 ;;
esac
baseline=${CPT_BASELINE:-"$ROOT/results/cpt/$baseline_name"}
short=$(git -C "$SUT" rev-parse --short=12 "$resolved") || exit 2
decision=$(python3 scripts/perf_decide.py "$BASE" "$HEAD") || exit 2
printf '%s\n' "$decision"
if [ "${CPT_FORCE:-0}" != 1 ] && [ "$(printf '%s' "$decision" | python3 -c 'import json,sys; print(json.load(sys.stdin)["decision"])')" = skip ]; then exit 0; fi
export JAVA_HOME=${JAVA_HOME:-/usr/lib/jvm/java-17-openjdk-amd64}
for attempt in 1 2; do
    suffix="${CPT_RUN_ID:+_${CPT_RUN_ID}}"
    if [ "$tier" = smoke ]; then dir="results/cpt/${short}${suffix}_${attempt}"; else dir="results/cpt/${short}_${tier}${suffix}_${attempt}"; fi
    mkdir "$dir" || { echo 'INCONCLUSIVE: artifact directory exists or cannot be created' >&2; exit 2; }
    bash scripts/reset_sut.sh 9>&- || { echo 'INCONCLUSIVE: reset failed' >&2; exit 2; }
    jmeter -n -t "$plan" -l "$dir/run.jtl" -e -o "$dir/html" "${opts[@]}" || { echo 'INCONCLUSIVE: JMeter failed' >&2; exit 2; }
    python3 scripts/perf_gate.py --baseline "$baseline" --write-metadata "$dir/run.jtl" --profile "$tier" || exit 2
    python3 scripts/perf_gate.py --baseline "$baseline" --candidate "$dir/run.jtl"
    status=$?
    if [ "$status" -eq 0 ]; then exit 0; fi
    if [ "$status" -ne 1 ]; then exit 2; fi
done
alert="results/cpt/${short}_${tier}${suffix}_alert.txt"
{
    echo 'Confirmed performance gate FAIL (two FAIL runs); human investigation required; no Issue created.'
    echo "SUT commit: $resolved; tier: $tier; baseline: $baseline"
    for attempt in 1 2; do
        if [ "$tier" = smoke ]; then dir="results/cpt/${short}${suffix}_${attempt}"; else dir="results/cpt/${short}_${tier}${suffix}_${attempt}"; fi
        echo "Evidence: $dir/run.jtl $dir/run_gate.json $dir/html"
        python3 -c 'import json,sys; print("Reasons:", "; ".join(json.load(open(sys.argv[1]))["failures"]))' "$dir/run_gate.json"
    done
} | tee "$alert" >&2
exit 1
