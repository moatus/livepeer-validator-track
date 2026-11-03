"""Local, serial credential-hidden diagnosis. Invoke under the measurement flock.

Uses existing binary records, fixture credentials only, no provider access.
Systemd scopes cap each role; affinity reserves four operator P cores, two disjoint witness P cores,
and one E core for support. Keys stay in a fresh /tmp directory, never in records.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import signal
import socket
import subprocess
import time

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('output', type=Path)
parser.add_argument('--suite', choices=['smoke', 'matrix', 'threads', 'reuse', 'correction', 'controls'], default='matrix')
parser.add_argument('--sent-sizes', type=int, nargs='+', default=[4096, 16384, 32768])
parser.add_argument('--repeats', type=int, default=3)
args = parser.parse_args()
root = Path.cwd()
binary = root / 'target/release/witness'
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
scratch = Path('/tmp/tlsw-ch-diagnose-' + secrets.token_hex(8))
scratch.mkdir(mode=0o700)
# Six distinct P cores (cpu_core PMU), with support on an E core.
operator_cpus, witness_cpus, support_cpus = [0, 1, 6, 8], [3, 10], [12]
cpus = operator_cpus + witness_cpus + support_cpus
assert set(cpus) <= os.sched_getaffinity(0)
siblings = [set((Path('/sys/devices/system/cpu') / f'cpu{c}' / 'topology/thread_siblings_list')
                .read_text().strip().replace('-', ',').split(',')) for c in cpus]
assert all(not a.intersection(b) for i, a in enumerate(siblings) for b in siblings[i+1:])
os.sched_setaffinity(0, set(support_cpus))
base = dict(os.environ)
base["PYTHONDONTWRITEBYTECODE"] = "1"
for name in ['OPENROUTER_API_KEY', 'OPENROUTER_MANAGEMENT_KEY',
             'WITNESS_UPSTREAM_CREDENTIAL', 'WITNESS_FIXTURE_CREDENTIAL']:
    base.pop(name, None)
ca = root / 'target/tlsn-src/crates/server-fixture/certs/src/tls/root_ca.crt'
path = '/api/v1/chat/completions'
results = []
credentials = []
children = []


def save(file, value):
    file.write_text(json.dumps(value, indent=2) + '\n')


def wait_for(predicate, proc, timeout=180):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        if proc.poll() is not None:
            raise RuntimeError('child exited: ' + str(proc.returncode))
        time.sleep(.05)
    raise TimeoutError('readiness or record deadline')


# The small in-scope supervisor records final counters even if the binary is
# OOM-killed. It is included in cgroup memory.peak; binary CPU records exclude it.
SUPERVISOR = r"""
import json, os, signal, subprocess, sys, time
from pathlib import Path
cg = Path('/sys/fs/cgroup') / Path('/proc/self/cgroup').read_text().split('0::', 1)[1].strip().lstrip('/')
p = subprocess.Popen(sys.argv[2:])
def capture():
    data = {'child_returncode': p.poll(), 'cgroup': str(cg),
            'supervisor_affinity': sorted(os.sched_getaffinity(0))}
    for name in ['memory.peak', 'memory.events', 'memory.swap.peak', 'memory.max',
                 'memory.swap.max', 'cpu.max', 'cpuset.cpus.effective']:
        f = cg / name
        data[name] = f.read_text().strip() if f.exists() else None
    dest = Path(sys.argv[1])
    temp = dest.with_suffix('.tmp')
    temp.write_text(json.dumps(data, indent=2) + '\n')
    temp.replace(dest)
def finish(signum, frame):
    capture()
    p.terminate()
signal.signal(signal.SIGTERM, finish)
while p.poll() is None:
    capture()
    time.sleep(.1)
rc = p.wait()
capture()
sys.exit(rc if rc >= 0 else 128-rc)
"""


def start(command, log, env, role=None):
    if role:
        affinity = operator_cpus if role == 'operator' else witness_cpus
        quota = 400 if role == 'operator' else 200
        command = ['systemd-run', '--user', '--scope', '--quiet',
                   '--unit=tlsw-diagnose-' + secrets.token_hex(6),
                   '-p', f'CPUQuota={quota}%', '-p', 'MemoryMax=2200M',
                   '-p', 'MemorySwapMax=0', '-p', 'AllowedCPUs=' + ','.join(map(str, affinity)),
                   'taskset', '-c', ','.join(map(str, affinity)),
                   'python3', '-B', '-c', SUPERVISOR, str(log.with_suffix('.cgroup.json'))] + command
    with log.open('wb') as handle:
        proc = subprocess.Popen(command, env=env, stdout=handle, stderr=subprocess.STDOUT,
                                start_new_session=True)
    children.append(proc)
    return proc


def stop(proc):
    if proc.poll() is None:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=5)


def request(raw):
    with socket.create_connection(('127.0.0.1', 19002), timeout=300) as sock:
        sock.sendall(raw)
        parts = []
        while True:
            part = sock.recv(65536)
            if not part:
                return b''.join(parts)
            parts.append(part)


def check(command, directory, name):
    result = subprocess.run(command, env=base, capture_output=True, timeout=30)
    (directory / name).write_bytes(result.stdout + result.stderr)
    return result.returncode


def run_case(label, sent, recv, bb=4, rayon=4, wt=2, tlsn=1, count=1, router=True):
    case = out / label
    case.mkdir()
    temp = scratch / label
    temp.mkdir()
    credential = 'tlsw-fixture-' + secrets.token_hex(24)
    credentials.append(credential.encode())
    operator_env = {**base, 'WITNESS_UPSTREAM_CREDENTIAL': credential,
                    'HARDWARE_CONCURRENCY': str(bb), 'RAYON_NUM_THREADS': str(rayon)}
    fixture_env = {**base, 'WITNESS_FIXTURE_CREDENTIAL': credential}
    opkey = temp / 'operator.key'
    seed = secrets.token_bytes(32)
    opkey.write_text(seed.hex())
    opkey.chmod(0o600)
    pub = Ed25519PrivateKey.from_private_bytes(seed).public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
    opkey.with_suffix('.pub').write_text(pub)
    common = ['--profile', 'credential-hidden', '--max-sent', str(sent + 2048),
              '--max-recv', str(recv + 2048)]
    fixture = start(['python3', 'tools/router_fixture.py', str(case / 'fixture'), '19000',
                     '--response-bytes', str(recv)], case / 'fixture.log', fixture_env)
    wait_for(lambda: 'fixture ready' in (case / 'fixture.log').read_text(), fixture)
    witness = start([str(binary), 'verifier'] + common + [
        '--listen', '127.0.0.1:19001', '--key', str(temp / 'witness.key'),
        '--roots', str(ca), '--allow-server', 'test-server.io',
        '--operator-pub', str(opkey.with_suffix('.pub')), '--record-dir', str(case / 'witness'),
        '--resolve', 'test-server.io=127.0.0.1:19000', '--threads', str(wt),
        '--cpus', ','.join(map(str, witness_cpus[:wt]))], case / 'witness.log', base, 'witness')
    wait_for(lambda: (case / 'witness/startup.json').exists(), witness)
    settings = {'sent_body_bytes': sent, 'response_body_bytes': recv, 'bb_threads': bb,
                'rayon_threads': rayon, 'witness_threads_per_pool': wt, 'tlsn_threads': tlsn,
                'operator_cpus': operator_cpus, 'witness_cpus': witness_cpus,
                'witness_pool_cpus': witness_cpus[:wt], 'support_cpus': support_cpus,
                'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
                'build': 'cargo build --release --offline -j 8; default release profile',
                'environment_names': ['WITNESS_UPSTREAM_CREDENTIAL', 'WITNESS_FIXTURE_CREDENTIAL',
                                      'HARDWARE_CONCURRENCY', 'RAYON_NUM_THREADS'],
                'provider_calls': 0, 'dollars': 0, 'router': router, 'count': count}
    save(case / 'settings.json', settings)
    if router:
        operator = start([str(binary), 'router'] + common + [
            '--listen', '127.0.0.1:19002', '--witness', '127.0.0.1:19001',
            '--operator-key', str(opkey), '--host', 'test-server.io', '--path', path,
            '--ca-cert', str(ca), '--record-dir', str(case / 'operator'),
            '--session-timeout', '240', '--evidence-deadline', '300'],
            case / 'operator.log', operator_env, 'operator')
        wait_for(lambda: 'router listening' in (case / 'operator.log').read_text(), operator)
        for i in range(count):
            client = case / f'client-{i + 1}'
            client.mkdir()
            body = b'a' * sent
            raw = (f'POST {path} HTTP/1.1\r\nHost: local-router\r\nContent-Type: application/octet-stream\r\n'
                   f'X-Client-Require-Witness: true\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n').encode() + body
            (client / 'request.http').write_bytes(raw)
            before = time.monotonic()
            response = request(raw)
            response_ms = (time.monotonic() - before) * 1000
            (client / 'response.http').write_bytes(response)
            head, delivered = response.split(b'\r\n\r\n', 1)
            assert head.startswith(b'HTTP/1.1 200'), head
            assert delivered == b'x' * recv
            receipt = next(line.split(b':', 1)[1].strip().decode() for line in head.split(b'\r\n')
                           if line.lower().startswith(b'x-witness-receipt:'))
            while time.monotonic() - before < 300:
                evidence_response = request((f'GET /evidence/{receipt} HTTP/1.1\r\nHost: local-router\r\nConnection: close\r\n\r\n').encode())
                evidence = json.loads(evidence_response.split(b'\r\n\r\n', 1)[1])
                if evidence['state'] != 'pending':
                    break
                time.sleep(.025)
            evidence_ms = (time.monotonic() - before) * 1000
            save(client / 'package.json', evidence)
            assert evidence['state'] == 'verified', evidence.get('reason')
            wait_for(lambda: (case / 'operator' / receipt / 'operator.resources.json').exists(), operator, 10)
            trust = {'v': 1, 'witnesses': [{'label': 'local witness', 'public_key':
                     (temp / 'witness.pub').read_text().strip(), 'profiles': ['credential-hidden']}],
                     'operators': [pub], 'server_name': 'test-server.io', 'path': path}
            save(client / 'trust.json', trust)
            check_args = ['--evidence', str(client / 'package.json'), '--client-request', str(client / 'request.http'),
                          '--client-response', str(client / 'response.http'), '--trust-list', str(client / 'trust.json')]
            checks = [check([str(binary), 'check'] + check_args, client, 'rust-check.json'),
                      check(['python3', 'tools/cleanroom_check.py', 'check'] + check_args,
                            client, 'python-check.json')]
            save(client / 'timings.json', {'response_ms': response_ms, 'evidence_ms': evidence_ms,
                                         'receipt_id': receipt, 'checks_exit': checks})
            assert checks == [0, 0], checks
        stop(operator)
    else:
        for i in range(1, count + 1):
            reqdir = case / f'input-{i}'
            reqdir.mkdir()
            save(reqdir / 'request.json', {'method': 'POST', 'host': 'test-server.io', 'path': path,
                                          'headers': {'Content-Type': 'application/json'}, 'body': 'a' * sent})
            rc = check([str(binary), 'seal', '--key', str(temp / 'customer.key'), '--request',
                        str(reqdir / 'request.json'), '--job-id', f'local-{i}', '--out', str(reqdir / 'seal.json')], reqdir, 'seal.log')
            assert rc == 0
        operator = start([str(binary), 'prover'] + common + [
            '--verifier', '127.0.0.1:19001', '--mode', 'proxy', '--ca-cert', str(ca),
            '--request', str(case / 'input-{s}/request.json'), '--seal', str(case / 'input-{s}/seal.json'),
            '--out-dir', str(case / 'operator-{s}'), '--prewarm', 'test-server.io',
            '--sessions', str(count), '--tlsn-threads', str(tlsn), '--timeout', '240'],
            case / 'operator.log', operator_env, 'operator')
        operator.wait(timeout=600)
        assert operator.returncode == 0
    wait_for(lambda: len(list((case / 'witness').glob('*.record.json'))) >= count, witness, 15)
    stop(witness)
    stop(fixture)
    save(case / 'shutdown.json', {'all_children_exited': all(p.poll() is not None for p in [fixture, witness, operator])})
    results.append({'label': label, **settings})
    save(out / 'results.json', results)
    print(label + ' verified', flush=True)


started = time.monotonic()
save(out / 'runner.json', {'scratch': str(scratch), 'affinity': cpus,
     'measurement_lock': '/tmp/tlsw-measure.lock (caller holds exclusive flock)',
     'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
try:
    save(out / 'loadavg.json', {'before_batch': Path('/proc/loadavg').read_text().strip()})
    topology = {}
    for p in sorted(Path('/sys/devices/system/cpu').glob('cpu[0-9]*')):
        topology[p.name] = {name: (p / name).read_text().strip() if (p / name).exists() else None
            for name in ['topology/thread_siblings_list', 'topology/core_cpus_list',
                         'topology/core_type', 'cpufreq/cpuinfo_max_freq', 'cpufreq/base_frequency']}
    save(out / 'topology.json', {'cpus': topology, 'cpu_core_P': Path('/sys/bus/event_source/devices/cpu_core/cpus').read_text().strip(),
         'cpu_atom_E_or_LPE': Path('/sys/bus/event_source/devices/cpu_atom/cpus').read_text().strip(),
         'assignment': {'operator_P': operator_cpus, 'witness_P': witness_cpus, 'support_E': support_cpus},
         'type_evidence': 'PMU cpu_core identifies P; single-thread atom CPUs 12-19 max 3.8 GHz are E, 20-21 max 2.5 GHz are LP-E (155H topology inference).'})
    if args.suite == 'correction':
        for size in args.sent_sizes:
            for n in range(args.repeats):
                first = len(children)
                try:
                    run_case(f'send-{size}-r{n+1}', size, 1024)
                except Exception as e:
                    save(out / f'send-{size}-r{n+1}' / 'failure.json', {'cause': str(e), 'type': type(e).__name__})
                    print(f'send-{size}-r{n+1} aborted: {e}', flush=True)
                finally:
                    for child in reversed(children[first:]):
                        stop(child)
                    save(out / f'send-{size}-r{n+1}' / 'shutdown.json',
                         {'all_children_exited': all(c.poll() is not None for c in children[first:])})
    elif args.suite == 'controls':
        for n in range(args.repeats):
            for label, bb, rayon, wt in [('reference',4,4,2), ('bb1',1,4,2),
                                         ('reference-rayon',4,4,2), ('rayon1',4,1,2),
                                         ('reference-witness',4,4,2), ('witness1',4,4,1)]:
                run_case(f'{label}-r{n+1}', 16384, 1024, bb, rayon, wt, count=2)
    elif args.suite == 'smoke':
        run_case('tiny', 100, 1024)
    elif args.suite == 'matrix':
        for size in [100, 4096, 16384, 65536, 131072]:
            run_case(f'send-{size}', size, 1024, count=2 if size == 100 else 1)
        run_case('receive-1048576', 100, 1048576)
        run_case('receive-4194304', 100, 4194304)
    elif args.suite == 'threads':
        for bb, rayon, wt in [(4, 4, 2), (1, 4, 2), (4, 1, 2), (4, 4, 1)]:
            run_case(f'bb{bb}-rayon{rayon}-witness{wt}', 16384, 1024, bb, rayon, wt, count=2)
        for n in [1, 2, 4]:
            run_case(f'tlsn-{n}', 16384, 1024, tlsn=n, count=2, router=False)
    else:
        run_case('persistent-prover', 100, 1024, count=3, router=False)
finally:
    for child in reversed(children):
        stop(child)
    hits = []
    scanned = 0
    for file in list(out.rglob('*')) + [root / p for p in subprocess.check_output(['git', 'ls-files'], env=base, text=True).splitlines()]:
        if file.is_file() and file.suffix not in ['.key']:
            data = file.read_bytes()
            scanned += 1
            if any(c in data for c in credentials):
                hits.append(str(file))
    save(out / 'credential-sweep.json', {'credentials': len(credentials), 'files': scanned,
         'unexpected_hits': hits, 'real_key_prefix_scan': 'NOT RUN: .env access forbidden; provider variables unset'})
    save(out / 'elapsed.json', {'measurement_seconds': time.monotonic() - started,
                               'all_children_exited': all(c.poll() is not None for c in children)})
