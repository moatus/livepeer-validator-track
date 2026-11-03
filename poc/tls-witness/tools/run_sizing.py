#!/usr/bin/env python3
"""Plain-client sizing through the real router. One exclusive lock per batch.

Required inputs deliberately include binary, profile, ports base and records.
The same matrix can be run against another build without editing this file.
Role accounting uses only each scope's cgroup files, never process listings.
"""
import argparse
import concurrent.futures
import hashlib
import http.client
import json
import os
import pathlib
import secrets
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')

def read_json(path):
    return json.loads(path.read_text())

def cgroup_base():
    membership = pathlib.Path('/proc/self/cgroup').read_text()
    rel = next(s[3:] for s in membership.splitlines() if s.startswith('0::'))
    return pathlib.Path('/sys/fs/cgroup') / rel.lstrip('/')

def snapshot(base):
    out = {'path': str(base)}
    for name in ('cpu.max', 'cpu.stat', 'memory.max', 'memory.swap.max', 'memory.swap.current', 'memory.swap.peak', 'cpuset.cpus.effective', 'memory.peak', 'memory.current', 'memory.events'):
        try:
            value = (base / name).read_text().strip()
            out[name] = dict(line.split() for line in value.splitlines()) if name in ('cpu.stat', 'memory.events') else value
        except FileNotFoundError:
            out[name] = None
    return out

def role(record, command):
    # This process is inside the measured scope, so it reads its own caps.
    base = cgroup_base()
    save(record, {'initial': snapshot(base), 'affinity': sorted(os.sched_getaffinity(0)), 'command': command, 'pid': os.getpid()})
    child = subprocess.Popen(command)
    def stop(*_):
        child.terminate()
    signal.signal(signal.SIGTERM, stop)
    code = child.wait()
    save(record, {'initial': read_json(record)['initial'], 'affinity': sorted(os.sched_getaffinity(0)), 'final': snapshot(base), 'command': command, 'exit': code})
    return code

def environment():
    env = {k: v for k, v in os.environ.items() if not k.startswith('OPENROUTER_') and k not in (
        'OPENROUTER_API_KEY', 'OPENROUTER_MANAGEMENT_KEY',
        'WITNESS_UPSTREAM_CREDENTIAL', 'WITNESS_FIXTURE_CREDENTIAL')}
    env.update(RUST_LOG='warn', MALLOC_ARENA_MAX='2', RAYON_NUM_THREADS='1', HARDWARE_CONCURRENCY='1')
    return env

def ready(proc, logfile, token, seconds=120):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if logfile.exists() and token in logfile.read_text():
            return
        if proc.poll() is not None:
            raise RuntimeError('startup exited: ' + str(logfile))
        time.sleep(.05)
    raise TimeoutError('startup timeout: ' + str(logfile))

def cpu_placement(cap):
    def expand(text):
        out = []
        for part in text.split(','):
            ends = part.split('-')
            out.extend(range(int(ends[0]), int(ends[-1]) + 1))
        return out
    rows = []
    for cpu in sorted(os.sched_getaffinity(0)):
        base = pathlib.Path(f'/sys/devices/system/cpu/cpu{cpu}')
        def read(name):
            try:
                return (base / name).read_text().strip()
            except FileNotFoundError:
                return None
        siblings = read('topology/thread_siblings_list')
        freq = int(read('cpufreq/cpuinfo_max_freq') or 0)
        rows.append(dict(cpu=cpu, thread_siblings_list=siblings,
            core_cpus_list=read('topology/core_cpus_list'), max_frequency_khz=freq,
            core_type='P (inferred: SMT siblings)' if len(expand(siblings)) > 1 else
                      'E (inferred: non-SMT, higher maximum)' if freq > 2500000 else 'LP-E (inferred: non-SMT, lower maximum)'))
    physical = []
    for row in rows:
        if row['core_type'].startswith('P') and row['cpu'] == min(expand(row['thread_siblings_list'])):
            physical.append(row['cpu'])
    if len(physical) < 2 * cap:
        raise RuntimeError('not enough disjoint physical P-cores for this cap point')
    operator, witness = physical[:cap], physical[cap:2*cap]
    used = set()
    for cpu in operator + witness:
        used.update(expand(next(r['thread_siblings_list'] for r in rows if r['cpu'] == cpu)))
    clients = [r['cpu'] for r in rows if r['cpu'] not in used and r['core_type'].startswith('E')][:2]
    if not clients:
        raise RuntimeError('no separate fixture/client cores')
    return rows, dict(operator=operator, witness=witness, clients=clients,
                      operator_core_type='P', witness_core_type='P', clients_core_type='E')

def body_for(workload, upload_kib=16):
    sizes = {'small': 4096, 'stream': 4096, 'upload-slope': upload_kib * 1024,
             'upload-1m': 1024**2, 'upload-10m': 10 * 1024**2,
             'upload-32m': 32 * 1024**2, 'download-1m': 4096, 'download-10m': 4096}
    response = 65536 if workload == 'stream' else 10 * 1024**2 if workload == 'download-10m' else 1024**2 if workload == 'download-1m' else 1024
    obj = {'response_bytes': response, 'stream': workload == 'stream', 'padding': ''}
    base = json.dumps(obj, separators=(',', ':')).encode()
    obj['padding'] = 'p' * (sizes[workload] - len(base))
    return json.dumps(obj, separators=(',', ':')).encode(), response

def request(port, method, target, body=b'', deadline=None):
    raw = (f'{method} {target} HTTP/1.1\r\nHost: router\r\nContent-Type: application/json\r\n'
           f'X-Client-Require-Witness: true\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n').encode() + body
    chunks = []
    first = last = None
    sent = received = 0
    with socket.create_connection(('127.0.0.1', port), 10) as s:
        s.settimeout(max(.01, deadline-time.monotonic()) if deadline else 900)
        view = memoryview(raw)
        while sent < len(raw):
            sent += s.send(view[sent:])
        # Count socket returns, including HTTP heads and chunk framing.
        total = 0
        head_end = None
        for_data = b''
        while True:
            data = s.recv(65536)
            if not data:
                break
            received += len(data)
            last = time.monotonic()
            chunks.append(data)
            if first is None:
                for_data += data
                if head_end is None:
                    split = for_data.find(b'\r\n\r\n')
                    if split >= 0:
                        head_end = split + 4
                if head_end is not None:
                    chunked = b'transfer-encoding: chunked' in for_data[:head_end].lower()
                    if chunked:
                        end = for_data.find(b'\r\n', head_end)
                        if end >= 0:
                            size = int(for_data[head_end:end].split(b';', 1)[0], 16)
                            if size > 0 and len(for_data) > end + 2:
                                first = last
                    elif len(for_data) > head_end:
                        first = last
    return b''.join(chunks), sent, received, first, last

def client(a, directory, body, expected, barrier, deadline):
    directory.mkdir(parents=True)
    barrier.wait()
    start = time.monotonic()
    row = {'started_monotonic': start}
    try:
        raw = (f'POST /api/v1/chat/completions HTTP/1.1\r\nHost: router\r\nContent-Type: application/json\r\n'
               f'X-Client-Require-Witness: true\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n').encode() + body
        (directory / 'request.http').write_bytes(raw)
        response, sent, recv, first, last = request(a.ports_base + 2, 'POST', '/api/v1/chat/completions', body, deadline)
        response_at = last or time.monotonic()
        (directory / 'response.http').write_bytes(response)
        head = response.split(b'\r\n\r\n', 1)[0]
        status = int(head.split(b' ', 2)[1])
        row.update(status=status, time_to_response_ms=(response_at-start)*1000,
                   first_body_ms=(first-start)*1000 if first else None,
                   client_to_router=sent, router_to_client=recv,
                   evidence_get_to_router=0, evidence_get_from_router=0)
        rid = next((l.split(b':', 1)[1].strip().decode() for l in head.split(b'\r\n') if l.lower().startswith(b'x-witness-receipt:')), None)
        if not rid:
            raise RuntimeError('HTTP ' + str(status) + '; no receipt')
        row['receipt_id'] = rid
        while time.monotonic() < deadline:
            response, sent, recv, _, _ = request(a.ports_base + 2, 'GET', '/evidence/' + rid, deadline=deadline)
            row['evidence_get_to_router'] += sent
            row['evidence_get_from_router'] += recv
            package = json.loads(response.split(b'\r\n\r\n', 1)[1])
            if package['state'] != 'pending':
                row['time_to_evidence_ms'] = (time.monotonic() - start) * 1000
                break
            time.sleep(.05)
        else:
            raise TimeoutError('15 minute cap-point workload deadline')
        save(directory / 'package.json', package)
        row['state'] = package['state']
        row['pass'] = status == 200 and package['state'] == 'verified'
        if not row['pass']:
            row['error'] = package.get('reason', 'evidence not verified')
    except Exception as e:
        row.update(pass_=False, error=str(e))
        row['pass'] = False
    row['finished_monotonic'] = time.monotonic()
    save(directory / 'result.json', row)
    return row

def check_client(a, directory, row):
    if not (directory / 'package.json').exists():
        return
    for label, command in (
        ('rust', [a.binary]),
        ('cleanroom', [sys.executable, str(ROOT / 'tools/cleanroom_check.py')])):
        command += ['check', '--evidence', str(directory / 'package.json'),
                    '--client-request', str(directory / 'request.http'),
                    '--client-response', str(directory / 'response.http'),
                    '--trust-list', str(directory.parent.parent / 'trust.json')]
        check = subprocess.run(command, env=environment(), capture_output=True, text=True, timeout=60)
        row[label] = json.loads(check.stdout)
    row['pass'] = row['pass'] and all(row[k]['result'] == 'PASS' for k in ('rust', 'cleanroom'))
    if not row['pass']:
        row.setdefault('error', 'offline check did not pass')
    save(directory / 'result.json', row)

def key(path):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption
    k = Ed25519PrivateKey.generate()
    path.write_text(k.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()).hex() + '\n')
    path.chmod(0o600)
    path.with_suffix('.pub').write_text(k.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex() + '\n')

def batch(a):
    d = a.records.resolve()
    d.mkdir(parents=True, exist_ok=False)
    if any((parent / 'STOP').exists() for parent in d.parents):
        save(d / 'result.json', dict(verdict='NOT RUN', cause='superseded batch; STOP marker', workload=a.workload, cap=a.cap, concurrency=a.concurrency))
        return 0
    if a.cap not in (1, 2):
        save(d / 'result.json', dict(verdict='NOT RUN', cause='symmetric 4 vCPU / 8 GiB roles exceed the combined 10 GB budget; use a separately scoped asymmetric experiment', workload=a.workload, cap=a.cap, concurrency=a.concurrency))
        return 0
    scratch = pathlib.Path(tempfile.mkdtemp(prefix=a.scratch_prefix, dir='/tmp'))
    env = environment()
    credential = 'tlsw-fixture-' + secrets.token_hex(16)
    role_env = env | {('WITNESS_FIXTURE_CREDENTIAL' if a.profile == 'full-disclosure-fixture' else 'WITNESS_UPSTREAM_CREDENTIAL'): credential}
    topology, placement = cpu_placement(a.cap)
    overrides = [a.operator_cpus, a.witness_cpus, a.client_cpus]
    if any(overrides):
        if not all(overrides):
            raise RuntimeError('all three CPU placement overrides are required together')
        for role_name, value in zip(('operator', 'witness', 'clients'), overrides):
            placement[role_name] = [int(cpu) for cpu in value.split(',')]
        by_cpu = {row['cpu']: row for row in topology}
        physical_sets = []
        for role_name in ('operator', 'witness', 'clients'):
            selected = placement[role_name]
            if len(selected) != len(set(selected)) or not selected:
                raise RuntimeError('invalid CPU placement')
            if role_name != 'clients' and len(selected) != a.cap:
                raise RuntimeError('role CPU placement differs from cap')
            siblings = set()
            for cpu in selected:
                row = by_cpu[cpu]
                expected = 'E' if role_name == 'clients' else 'P'
                if not row['core_type'].startswith(expected):
                    raise RuntimeError('CPU core type differs from requested role')
                for part in row['thread_siblings_list'].split(','):
                    ends = part.split('-')
                    siblings.update(range(int(ends[0]), int(ends[-1]) + 1))
            if any(siblings & other for other in physical_sets):
                raise RuntimeError('roles share a physical core')
            physical_sets.append(siblings)
    os.sched_setaffinity(0, placement['clients'])
    units, procs = [], []
    body, expected = body_for(a.workload, a.upload_kib)
    # 32 MiB body is a known refusal point: headers also count toward 2^25.
    max_sent = min(2**25, len(body) + 4096)
    max_recv = expected + 8192
    helper_base = cgroup_base()
    helper_before = snapshot(helper_base)
    start = time.monotonic()
    deadline = start + 900
    save(d / 'identity.json', dict(binary=a.binary, binary_sha256=hashlib.sha256(pathlib.Path(a.binary).read_bytes()).hexdigest(),
        head_at_run_time=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        binary_source_commit=a.binary_source_commit, router_max_sessions=a.router_sessions or 4,
        source_diff=subprocess.check_output(['git', 'diff', 'HEAD', '--', 'src', 'tools/run_sizing.py', 'tools/sizing_fixture.py'], text=True),
        cpu_model=next(l.split(':',1)[1].strip() for l in pathlib.Path('/proc/cpuinfo').read_text().splitlines() if l.startswith('model name')),
        kernel=os.uname().release, host=socket.gethostname(), profile=a.profile, credential_header=a.credential_header, cap=a.cap,
        build_settings='cargo build --release --offline -j 8; default release profile',
        cargo_lock_sha256=hashlib.sha256((ROOT / 'Cargo.lock').read_bytes()).hexdigest(),
        patches={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / 'patch').glob('*.diff')},
        scratch=str(scratch), provider_calls=0, spend_usd=0, max_sent=max_sent, max_recv=max_recv,
        first_body_rule='first payload byte after HTTP head and chunk-size line', topology=topology, placement=placement, idle_loadavg=pathlib.Path('/proc/loadavg').read_text().strip(), request_body_bytes=len(body), response_body_bytes=expected, workload=a.workload, concurrency=a.concurrency, rounds=a.rounds,
        sustained_seconds=a.sustained_seconds, started_unix=time.time()))
    if a.profile == 'credential-hidden' and not (ROOT / 'target/srs/g1.dat').is_file():
        raise RuntimeError('local pinned SRS missing; network fetch forbidden')
    key(scratch / 'operator.key'); key(scratch / 'witness.key')
    save(d / 'trust.json', dict(v=1, witnesses=[dict(label='local sizing; ordinary host; no enclave', public_key=(scratch / 'witness.pub').read_text().strip(), profiles=[a.profile])],
         operators=[(scratch / 'operator.pub').read_text().strip()], server_name='test-server.io', path='/api/v1/chat/completions'))
    def launch(name, command, child_env, cap=False):
        if cap:
            unit = 'tlsw-sizing-' + secrets.token_hex(8)
            units.append(unit + '.scope')
            command = ['systemd-run', '--user', '--scope', '--quiet', '--unit=' + unit,
                       '-p', f'CPUQuota={a.cap * 100}%', '-p', f'MemoryMax={a.cap * 2}G', '-p', 'MemorySwapMax=0',
                       '-p', 'AllowedCPUs=' + ','.join(map(str, placement[name])),
                       'taskset', '-c', ','.join(map(str, placement[name])), sys.executable, '-B', str(pathlib.Path(__file__).resolve()), '--role-record', str(d / (name + '.scope.json')), '--', *command]
        log = d / (name + '.log')
        p = subprocess.Popen(command, env=child_env, stdout=log.open('w'), stderr=subprocess.STDOUT)
        procs.append(p)
        save(d / (name + '.launch.json'), dict(command=command, environment_names=sorted(child_env), unit=units[-1] if cap else None))
        return p, log
    rows = []
    resources = {}
    try:
        f, log = launch('fixture', [sys.executable, '-u', str(ROOT / 'tools/sizing_fixture.py'), '--port', str(a.ports_base), '--records', str(d / 'fixture'), '--cert-dir', str(a.cert_dir), *(['--credential-header', a.credential_header] if a.credential_header != 'authorization' else [])], env | {'WITNESS_FIXTURE_CREDENTIAL': credential})
        ready(f, log, 'fixture ready')
        w, log = launch('witness', [a.binary, 'verifier', '--profile', a.profile, '--listen', f'127.0.0.1:{a.ports_base+1}', '--key', str(scratch / 'witness.key'), '--roots', str(a.cert_dir / 'root_ca.crt'), '--operator-pub', str(scratch / 'operator.pub'), '--allow-server', 'test-server.io', '--resolve', f'test-server.io=127.0.0.1:{a.ports_base}', '--threads', str(a.cap), '--max-sessions', '16', '--max-sent', str(max_sent), '--max-recv', str(max_recv), '--record-dir', str(d / 'witness')], role_env if a.profile == 'full-disclosure-fixture' else env, True)
        ready(w, log, 'epoch: ')
        r, log = launch('operator', [a.binary, 'router', '--profile', a.profile, '--listen', f'127.0.0.1:{a.ports_base+2}', '--operator-key', str(scratch / 'operator.key'), '--host', 'test-server.io', '--witness', f'127.0.0.1:{a.ports_base+1}', '--ca-cert', str(a.cert_dir / 'root_ca.crt'), '--max-sent', str(max_sent), '--max-recv', str(max_recv), '--session-timeout', '870', '--evidence-deadline', '880', '--record-dir', str(d / 'router'), *(['--credential-header', a.credential_header] if a.credential_header != 'authorization' else []), *(['--max-sessions', str(a.router_sessions)] if a.router_sessions else [])], role_env, True)
        ready(r, log, 'router listening')
        bases = {name: pathlib.Path(read_json(d / (name + '.scope.json'))['initial']['path']) for name in ('operator', 'witness')}
        for name in bases:
            own = read_json(d / (name + '.scope.json'))
            caps = own['initial']
            quota, period = map(int, caps['cpu.max'].split())
            if quota != a.cap * period or int(caps['memory.max']) != a.cap * 2 * 1024**3 or caps['memory.swap.max'] != '0':
                raise RuntimeError(name + ': cgroup caps differ from requested no-swap cap point')
            actual = own['affinity']
            if actual != placement[name]:
                raise RuntimeError(name + ': CPU placement differs from requested cores')
        before = {name: snapshot(base) for name, base in bases.items()}
        time.sleep(.05)
        load_start = time.monotonic()
        round_number = 0
        while True:
            barrier = threading.Barrier(a.concurrency)
            with concurrent.futures.ThreadPoolExecutor(max_workers=a.concurrency) as pool:
                futures = [pool.submit(client, a, d / 'clients' / f'{round_number:04d}-{i:02d}', body, expected, barrier, deadline) for i in range(a.concurrency)]
                rows.extend(f.result() for f in futures)
            round_number += 1
            if any(not row['pass'] for row in rows) or time.monotonic() >= deadline:
                break
            if a.sustained_seconds:
                if time.monotonic() - load_start >= a.sustained_seconds:
                    break
            elif round_number >= a.rounds:
                break
        # Allow the record writer to finish after the final evidence response.
        time.sleep(.2)
        load_end = time.monotonic()
        after = {name: snapshot(base) for name, base in bases.items()}
        for name in bases:
            if any(after[name].get(field) is None for field in ('cpu.stat', 'memory.peak', 'memory.events')):
                saved = read_json(d / (name + '.scope.json'))
                if 'final' not in saved:
                    raise RuntimeError(name + ': scope disappeared without final accounting')
                after[name] = saved['final']
        for name in bases:
            cpu = (int(after[name]['cpu.stat']['usage_usec']) - int(before[name]['cpu.stat']['usage_usec'])) / 1e6
            initial = read_json(d / (name + '.scope.json'))['initial']
            startup_cpu = (int(before[name]['cpu.stat']['usage_usec']) - int(initial['cpu.stat']['usage_usec'])) / 1e6
            resources[name] = dict(startup_cpu_seconds=startup_cpu, core_type=placement[name + '_core_type'], cpus=placement[name], before=before[name], after=after[name], cpu_seconds=cpu,
                peak_memory_bytes=int(after[name]['memory.peak']), cpu_seconds_per_request=cpu/len(rows))
        for directory, row in zip(sorted((d / 'clients').iterdir()), rows):
            check_client(a, directory, row)
        cap_failures = []
        for name, value in resources.items():
            events = value['after']['memory.events']
            if any(int(events.get(key, 0)) for key in ('max', 'oom', 'oom_kill')):
                cap_failures.append(name + ': memory cap event ' + json.dumps(events))
        records = [read_json(p) for p in (d / 'witness').glob('*.record.json')]
        incomplete = sum('socket_bytes' not in rec.get('detail', {}) or 'bytes' not in rec for rec in records)
        traffic = {k: None if incomplete else sum(rec.get('detail', {}).get('socket_bytes', {}).get(k, 0) for rec in records) for k in (
            'upstream_sent', 'upstream_received', 'operator_to_witness', 'witness_to_operator',
            'operator_to_witness_non_relay', 'witness_to_operator_non_relay')}
        for k in ('client_to_router', 'router_to_client', 'evidence_get_to_router', 'evidence_get_from_router'):
            traffic[k] = sum(row.get(k, 0) for row in rows)
        traffic['post_connection_operator_to_witness'] = None if incomplete else sum(rec['bytes']['to_verifier'] - rec.get('detail',{}).get('transport_at_connection_close',{}).get('operator_to_witness', rec['bytes']['to_verifier']) for rec in records)
        traffic['post_connection_witness_to_operator'] = None if incomplete else sum(rec['bytes']['from_verifier'] - rec.get('detail',{}).get('transport_at_connection_close',{}).get('witness_to_operator', rec['bytes']['from_verifier']) for rec in records)
        if incomplete:
            operator_records = [read_json(p) for p in (d / 'router').glob('*/attempt-*/*.record.json')]
            if operator_records and all('bytes' in rec for rec in operator_records):
                traffic['operator_to_witness'] = sum(rec['bytes']['to_verifier'] for rec in operator_records)
                traffic['witness_to_operator'] = sum(rec['bytes']['from_verifier'] for rec in operator_records)
        helper_after = snapshot(helper_base)
        combined_peak = sum(v['peak_memory_bytes'] for v in resources.values()) + int(helper_after['memory.peak'])
        if combined_peak > 10_000_000_000:
            cap_failures.append('sum of independent cgroup peaks exceeds 10 GB')
        save(d / 'result.json', dict(verdict='PASS' if rows and all(row['pass'] for row in rows) and not cap_failures else 'FAIL',
             failure_causes=cap_failures + sorted(set(row.get('error', 'client failure') for row in rows if not row['pass'])),
             measured=True, completed=len(rows), passed=sum(row['pass'] for row in rows),
             workload=a.workload, profile=a.profile, cap=a.cap, concurrency=a.concurrency,
             elapsed_seconds=load_end-load_start, rate_scope='client POST through final evidence; offline checks after timed window; 200ms record drain included', requests_per_second=sum(row['pass'] for row in rows)/(load_end-load_start),
             resources=resources, helpers=dict(before=helper_before, after=helper_after, peak_memory_bytes=int(helper_after['memory.peak']), scope='uncapped fixture and plain clients; outside both roles'), combined_peak_memory_upper_bound_bytes=combined_peak, socket_bytes=traffic, clients=rows, record_count=len(records), incomplete_witness_records=incomplete))
    except Exception as e:
        save(d / 'result.json', dict(verdict='FAIL', cause=str(e), workload=a.workload, profile=a.profile, cap=a.cap, concurrency=a.concurrency, clients=rows))
    finally:
        for unit in units:
            subprocess.run(['systemctl', '--user', 'kill', '--signal=SIGTERM', unit], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for proc in reversed(procs):
            if proc.poll() is None:
                proc.terminate()
        for proc in procs:
            try:
                proc.wait(10)
            except subprocess.TimeoutExpired:
                proc.kill(); proc.wait()
        hits = []
        tracked = subprocess.check_output(['git', 'ls-files', '-z']).decode().split('\0')
        paths = list(d.rglob('*')) + [ROOT / p for p in tracked if p and p != '.env']
        for path in paths:
            if path.is_file() and credential.encode() in path.read_bytes():
                hits.append(str(path))
        save(d / 'credential-sweep.json', dict(files=sum(p.is_file() for p in paths), hits=hits, pass_sweep=not hits))
        save(d / 'shutdown.json', dict(scope_units=units, launcher_exits=[p.returncode for p in procs], helper_cgroup_final=snapshot(helper_base), elapsed_seconds=time.monotonic()-start))
    result = read_json(d / 'result.json')
    print(json.dumps(dict(directory=str(d), verdict=result['verdict'], cause=result.get('cause'), elapsed_seconds=result.get('elapsed_seconds'))), flush=True)
    return 0

def main():
    if '--role-record' in sys.argv:
        i = sys.argv.index('--')
        return role(pathlib.Path(sys.argv[sys.argv.index('--role-record')+1]), sys.argv[i+1:])
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binary', required=True, type=lambda x: str(pathlib.Path(x).resolve()))
    p.add_argument('--binary-source-commit', help='source commit of the selected binary, distinct from HEAD at run time')
    p.add_argument('--profile', required=True, choices=['full-disclosure-fixture', 'credential-hidden'])
    p.add_argument('--credential-header', choices=['authorization','x-api-key'], default='authorization')
    p.add_argument('--ports-base', required=True, type=int)
    p.add_argument('--records', required=True, type=pathlib.Path)
    p.add_argument('--scratch-prefix', default='tlsw-p31-')
    p.add_argument('--cert-dir', type=pathlib.Path, default=ROOT / 'target/tlsn-src/crates/server-fixture/certs/src/tls')
    p.add_argument('--caps', default='1,2')
    p.add_argument('--workloads', default='small,stream,upload-1m,upload-10m,download-1m,download-10m,upload-32m')
    p.add_argument('--rounds', type=int, default=3)
    p.add_argument('--upload-kib', type=int, default=16)
    p.add_argument('--sustained-seconds', type=int, default=0)
    p.add_argument('--batch', action='store_true')
    p.add_argument('--helper-scope', action='store_true', help=argparse.SUPPRESS)
    p.add_argument('--workload')
    p.add_argument('--router-sessions', type=int, choices=range(1,17), help='override router admission slots for concurrency validation')
    p.add_argument('--operator-cpus', help='explicit comma-separated CPU IDs; all roles required')
    p.add_argument('--witness-cpus')
    p.add_argument('--client-cpus')
    p.add_argument('--cap', type=int, default=1)
    p.add_argument('--concurrency', type=int, default=1)
    a = p.parse_args()
    if a.batch:
        if not a.helper_scope:
            # Account fixture/client memory separately, without a role cap.
            unit = 'tlsw-sizing-clients-' + secrets.token_hex(8)
            return subprocess.run(['systemd-run', '--user', '--scope', '--quiet', '--unit=' + unit,
                '-p', 'CPUAccounting=yes', '-p', 'MemoryAccounting=yes', '-p', 'MemoryMax=infinity',
                '-p', 'MemorySwapMax=0', sys.executable, '-B', str(pathlib.Path(__file__).resolve()),
                *sys.argv[1:], '--helper-scope']).returncode
        return batch(a)
    a.records.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    save(a.records / 'plan.json', vars(a) | {'records': str(a.records), 'cert_dir': str(a.cert_dir)})
    matrix = []
    for cap in map(int, a.caps.split(',')):
        for workload in a.workloads.split(','):
            concurrencies = [1, 2, 4, 8, 16] if workload == 'small' else [1, 8] if workload == 'stream' else [1] if workload in ('upload-slope', 'upload-32m') else [1, 4]
            for concurrency in concurrencies:
                name = f'{workload}-c{concurrency}-cpu{cap}'
                d = a.records / name
                if time.monotonic()-started > 3*3600:
                    save(d / 'result.json', dict(verdict='NOT RUN', cause='3 hour measurement budget'))
                    continue
                cmd = [sys.executable, str(pathlib.Path(__file__).resolve()), '--batch', '--binary', a.binary,
                       '--profile', a.profile, '--ports-base', str(a.ports_base), '--records', str(d),
                       '--scratch-prefix', a.scratch_prefix, '--cert-dir', str(a.cert_dir), '--workload', workload,
                       '--cap', str(cap), '--concurrency', str(concurrency), '--rounds', str(a.rounds),
                       '--sustained-seconds', str(a.sustained_seconds), '--upload-kib', str(a.upload_kib)]
                for option in ('binary_source_commit', 'router_sessions', 'operator_cpus', 'witness_cpus', 'client_cpus'):
                    value = getattr(a, option)
                    if value is not None:
                        cmd.extend(['--' + option.replace('_', '-'), str(value)])
                subprocess.run(['flock', '-x', '-w', '3600', '/tmp/tlsw-measure.lock', *cmd], check=True)
                matrix.append(dict(directory=str(d), **read_json(d / 'result.json')))
                save(a.records / 'matrix.json', matrix)
    return 0

if __name__ == '__main__':
    sys.exit(main())
