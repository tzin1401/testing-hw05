"""Synthetic CSV fixtures are parser tests, not JMeter results."""
import csv
import fcntl
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.jtl_truth import LABELS
from scripts.perf_decide import decide
from scripts.perf_gate import FILTER, PLANS, PROFILES, digest

ROOT = Path(__file__).resolve().parent.parent


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        self.base = self.dir / 'baseline.json'

    def fixture(self, name, elapsed, count=500):
        path = self.dir / (name + '.csv')
        with path.open('w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timeStamp', 'elapsed', 'label', 'responseCode', 'success', 'threadName', 'Latency', 'Connect'])
            writer.writerow([1000, 1, 'Negative login', '401', 'true', 'thread', 1, 0])
            for label in LABELS:
                for i in range(count):
                    writer.writerow([16000 + i, elapsed, label, '200', 'true', 'thread', elapsed, 0])
        meta = {'source_jtl': str(path), 'source_sha256': digest(path), 'source_commit': 'test',
                'profile': {'name': 'smoke', **PROFILES['smoke']},
                'filter': FILTER, 'machine': {'hostname': 'test', 'platform': 'test', 'machine': 'test'},
                'plan': 'test-plans/' + PLANS['smoke'], 'plan_sha256': 'test', 'data_sha256': {'test.csv': 'test'}}
        Path(str(path) + '.meta.json').write_text(json.dumps(meta))
        return path

    def run_gate(self, *args):
        return subprocess.run([sys.executable, str(ROOT / 'scripts/perf_gate.py'), '--baseline', str(self.base), *map(str, args)], capture_output=True, text=True)

    def check_candidate(self, old, new, expected, count=500):
        baseline = self.fixture('base', old)
        self.assertEqual(self.run_gate('--make-baseline', baseline).returncode, 0)
        result = self.run_gate('--candidate', self.fixture('candidate', new, count))
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)

    def test_unchanged(self):
        self.check_candidate(20, 20, 0)

    def test_regression(self):
        self.check_candidate(30, 40, 1)

    def test_small_absolute_delta(self):
        self.check_candidate(10, 13, 0)

    def test_insufficient(self):
        self.check_candidate(20, 20, 2, 499)

    def test_failure_not_hidden_by_insufficient_label(self):
        from scripts.perf_gate import evaluate
        from scripts.jtl_truth import metrics
        labels = {label: metrics([(1, 200 if label == LABELS[0] else 1, label, '200', True, 't', 0, 0, None)] * (500 if label == LABELS[0] else 1)) for label in LABELS}
        candidate = {'labels': labels, 'all': metrics([(1, 1, 'x', '200', True, 't', 0, 0, None)]), 'main': {'count': 506}, 'error_windows': []}
        slo = json.loads((ROOT / 'results/cpt/slo.json').read_text())
        self.assertEqual(evaluate(candidate, None, slo, 500)[0], 'FAIL')

    def test_incompatible_profile(self):
        self.assertEqual(self.run_gate('--make-baseline', self.fixture('base', 20)).returncode, 0)
        candidate = self.fixture('candidate', 20)
        sidecar = Path(str(candidate) + '.meta.json')
        meta = json.loads(sidecar.read_text())
        meta['profile']['threads'] = 50
        sidecar.write_text(json.dumps(meta))
        self.assertEqual(self.run_gate('--candidate', candidate).returncode, 2)

    def append_errors(self, path, times):
        with path.open('a', newline='') as f:
            writer = csv.writer(f)
            for timestamp in times:
                writer.writerow([timestamp, 1, 'Negative login', '500', 'false', 'thread', 1, 0])
        sidecar = Path(str(path) + '.meta.json')
        meta = json.loads(sidecar.read_text())
        meta['source_sha256'] = digest(path)
        sidecar.write_text(json.dumps(meta))

    def test_ramp_errors_count_in_whole_run(self):
        self.assertEqual(self.run_gate('--make-baseline', self.fixture('base', 20)).returncode, 0)
        candidate = self.fixture('candidate', 20)
        self.append_errors(candidate, [1001, 1002, 1003, 1004])
        result = self.run_gate('--candidate', candidate)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        report = json.loads((self.dir / 'candidate_gate.json').read_text())
        self.assertTrue(any('whole-run' in f for f in report['failures']))

    def test_localized_window_errors(self):
        self.assertEqual(self.run_gate('--make-baseline', self.fixture('base', 20)).returncode, 0)
        candidate = self.fixture('candidate', 20)
        self.append_errors(candidate, [140000])
        result = self.run_gate('--candidate', candidate)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        report = json.loads((self.dir / 'candidate_gate.json').read_text())
        self.assertLess(report['metrics']['all']['error_pct'], 0.1)
        self.assertTrue(any('error window' in f for f in report['failures']))
        self.assertEqual(self.run_gate('--candidate', candidate).returncode, 1)

    def test_baseline_update_is_explicit(self):
        candidate = self.fixture('base', 20)
        self.assertEqual(self.run_gate('--make-baseline', candidate).returncode, 0)
        self.assertEqual(self.run_gate('--make-baseline', candidate).returncode, 0)

    def test_policy_hash_mismatch_is_inconclusive_but_absolute_failure_survives(self):
        self.assertEqual(self.run_gate('--make-baseline', self.fixture('base', 20)).returncode, 0)
        policy = self.dir / 'policy.json'
        policy.write_text((ROOT / 'results/cpt/slo.json').read_text() + '\n')
        result = self.run_gate('--slo', policy, '--candidate', self.fixture('candidate', 20))
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        report = json.loads((self.dir / 'candidate_gate.json').read_text())
        self.assertIn('baseline SLO policy hash mismatch', report['inconclusive'])
        result = self.run_gate('--slo', policy, '--candidate', self.fixture('slow', 200))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_check_policy_rejects_missing_baseline_and_policy_mismatch(self):
        with self.subTest('missing baseline'):
            result = self.run_gate('--check-policy', '--profile', 'smoke')
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn('INCONCLUSIVE', result.stderr)
            self.assertIn('baseline.json', result.stderr)
        self.assertEqual(self.run_gate('--make-baseline', self.fixture('base', 20)).returncode, 0)
        policy = self.dir / 'policy.json'
        policy.write_text((ROOT / 'results/cpt/slo.json').read_text() + '\n')
        with self.subTest('policy hash mismatch'):
            result = self.run_gate('--check-policy', '--profile', 'smoke', '--slo', policy)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn('SLO hash mismatch', result.stderr)

    def test_relative_requires_main_count_but_slo_still_checked(self):
        from scripts.perf_gate import evaluate
        from scripts.jtl_truth import metrics
        def result(value, count):
            m = metrics([(1, value, 'x', '200', True, 't', 0, 0, None)] * 500)
            return {'labels': {label: m for label in LABELS}, 'all': m, 'main': {'count': count},
                    'error_windows': [{'start_ms': 0, 'end_ms': 1, 'metrics': m}]}
        slo = json.loads((ROOT / 'results/cpt/slo.json').read_text())
        self.assertEqual(evaluate(result(40, 999), result(30, 1000), slo, 500)[0], 'INCONCLUSIVE')
        self.assertEqual(evaluate(result(200, 1000), result(30, 999), slo, 500)[0], 'FAIL')


class DecisionTests(unittest.TestCase):
    def test_docs(self):
        self.assertEqual(decide(['README.md'], 'docs')[0], 'skip')

    def test_backend(self):
        self.assertEqual(decide(['backend/server.js'], 'change')[0], 'run')

    def test_marker_precedence(self):
        self.assertEqual(decide(['README.md'], '[perf] [skip perf]')[0], 'run')
        self.assertEqual(decide(['backend/server.js'], '[skip perf]')[0], 'skip')

    def test_unknown(self):
        self.assertEqual(decide(['backend/database.sqlite'], 'change')[0], 'run')


class PipelineLockTests(unittest.TestCase):
    def test_backend_does_not_keep_pipeline_lock(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'scripts').mkdir()
            (root / 'results/cpt').mkdir(parents=True)
            (root / 'eshop-sut').mkdir()
            bins = root / 'bin'
            bins.mkdir()
            shutil.copy(ROOT / 'scripts/cpt_pipeline.sh', root / 'scripts/cpt_pipeline.sh')
            (root / 'scripts/perf_decide.py').write_text("print('{\"decision\":\"run\"}')\n")
            (root / 'scripts/perf_gate.py').write_text('raise SystemExit(0)\n')
            (root / 'scripts/reset_sut.sh').write_text(
                '#!/bin/bash\nsleep 60 >/dev/null 2>&1 &\necho $! > backend.pid\n')
            git = bins / 'git'
            git.write_text('#!/bin/bash\ncase "$3" in rev-parse) echo abc123 ;; esac\n')
            git.chmod(0o755)
            jmeter = bins / 'jmeter'
            jmeter.write_text('#!/bin/bash\nexit 1\n')
            jmeter.chmod(0o755)
            env = os.environ.copy()
            env.update(PATH=str(bins) + os.pathsep + env['PATH'], CPT_TIER='smoke', CPT_FORCE='0')
            env.pop('CPT_RUN_ID', None)
            pidfile = root / 'backend.pid'
            try:
                result = subprocess.run(['bash', str(root / 'scripts/cpt_pipeline.sh'), 'base', 'head'],
                                        cwd=root, env=env, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                pid = int(pidfile.read_text())
                os.kill(pid, 0)
                with (root / 'results/cpt/.sut.lock').open('w') as lock:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    fcntl.flock(lock, fcntl.LOCK_UN)
            finally:
                if pidfile.exists():
                    try:
                        os.kill(int(pidfile.read_text()), signal.SIGTERM)
                    except ProcessLookupError:
                        pass

    def test_deep_profile_without_policy_stops_before_reset(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'scripts').mkdir()
            (root / 'results/cpt').mkdir(parents=True)
            (root / 'eshop-sut').mkdir()
            bins = root / 'bin'
            bins.mkdir()
            shutil.copy(ROOT / 'scripts/cpt_pipeline.sh', root / 'scripts/cpt_pipeline.sh')
            (root / 'scripts/perf_decide.py').write_text("print('{\"decision\":\"run\"}')\n")
            (root / 'scripts/reset_sut.sh').write_text('touch reset-called\n')
            git = bins / 'git'
            git.write_text('#!/bin/bash\ncase "$3" in rev-parse) echo abc123 ;; esac\n')
            git.chmod(0o755)
            jmeter = bins / 'jmeter'
            jmeter.write_text('#!/bin/bash\ntouch jmeter-called\nexit 1\n')
            jmeter.chmod(0o755)
            env = os.environ.copy()
            env.update(PATH=str(bins) + os.pathsep + env['PATH'], CPT_TIER='stress', CPT_FORCE='0')
            env.pop('CPT_SLO', None)
            result = subprocess.run(['bash', str(root / 'scripts/cpt_pipeline.sh'), 'base', 'head'],
                                    cwd=root, env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn('CPT_SLO', result.stderr)
            self.assertFalse((root / 'reset-called').exists())
            self.assertFalse((root / 'jmeter-called').exists())
            self.assertFalse((root / 'results/cpt/abc123_stress_1').exists())


if __name__ == '__main__':
    unittest.main()
