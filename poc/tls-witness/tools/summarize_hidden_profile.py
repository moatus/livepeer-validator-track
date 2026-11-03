"""Reconcile CPU mark deltas and socket counters from profile_hidden.py.

No fitting is used for the accounting: stages are measured, disjoint CPU
intervals. Fits below are explicitly descriptive, not hardware forecasts.
"""
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])


def read(path):
    return json.loads(path.read_text())


def role_parts(record):
    marks = {m['at']: m['cpu_s'] for m in record['detail']['cpu_marks']}
    total = record['resources']['cpu_seconds']
    if record['role'] == 'prover':
        start = record['detail']['session']['process_cpu_seconds_at_start']
        parts = {
            'prepare_and_process_metadata': marks['setup_started'] - start,
            'srs_vk_roots': marks['ready'] - marks['setup_started'],
            'session_setup': marks['committed'] - marks['ready'],
            'online_tls_and_http': marks['connection_closed'] - marks['committed'],
            'prf_tags_finalize': marks['plaintext_auth_started'] - marks['connection_closed'],
            'plaintext_auth_and_hidden_hash': marks['tlsn_proved'] - marks['plaintext_auth_started'],
            'no_cr_lf': record['detail']['zk']['prove_cpu_s'],
        }
    else:
        parts = {
            'session_setup': marks['committed'] - marks['session_start'],
            'relay_prf_and_record_tags': marks['plaintext_auth_started'] - marks['committed'],
            'plaintext_auth_and_hidden_hash': marks['tlsn_verified'] - marks['plaintext_auth_started'],
            'no_cr_lf': record['detail']['zk']['verify_cpu_s'],
        }
    assigned = sum(parts.values())
    return {'total_cpu_s': total, 'components_cpu_s': parts,
            'assigned_cpu_s': assigned, 'residual_cpu_s': total - assigned,
            'accounted_percent': 100 * assigned / total,
            'residual_includes': 'record signing/serialization, receipt checks, scheduling and mark rounding',
            'peak_rss_mib': record['resources']['peak_rss_mb']}


def fit(points):
    xbar = sum(x for x, _ in points) / len(points)
    ybar = sum(y for _, y in points) / len(points)
    slope = sum((x - xbar) * (y - ybar) for x, y in points) / sum((x - xbar)**2 for x, _ in points)
    intercept = ybar - slope * xbar
    residuals = [y - intercept - slope * x for x, y in points]
    return {'intercept': intercept, 'slope_per_KiB': slope, 'points': points,
            'max_abs_residual': max(map(abs, residuals)),
            'scope': 'descriptive least squares for these serial local records; no capacity or extrapolation claim'}


rows = []
startups = []
for suite in ['matrix-final', 'threads', 'reuse']:
    directory = root / suite
    if not (directory / 'results.json').exists():
        continue
    for setting in read(directory / 'results.json'):
        case = directory / setting['label']
        startup = read(case / 'witness/startup.json')
        zk = startup['zk']
        components = {'srs_check_and_process_circuit_metadata': zk['srs']['srs_check_cpu_s'],
                      'srs_load': sum(c['srs_cpu_s'] for c in zk['circuits']),
                      'verification_keys': sum(c['vk_cpu_s'] for c in zk['circuits'])}
        startups.append({'case': str(case), 'cpu_s': startup['cpu_seconds'],
                         'peak_rss_mib': startup['peak_rss_mb'], 'components_cpu_s': components,
                         'accounted_percent': 100 * sum(components.values()) / startup['cpu_seconds'],
                         'setup_ms': zk['setup_ms'], 'caps': startup['cgroup_caps']})
        witness = [read(p) for p in (case / 'witness').glob('*.record.json')]
        if setting['router']:
            calls = sorted(case.glob('client-*/timings.json'))
            operators = [(read(p), next((case / 'operator' / read(p)['receipt_id']).rglob('*.record.json'))) for p in calls]
        else:
            operators = [(None, p) for p in sorted(case.glob('operator-*/*.record.json'))]
        for i, (client, filename) in enumerate(operators, 1):
            operator = read(filename)
            match = next(v for v in witness if v['job_id'] == operator['job_id'])
            assert operator['outcome'] == match['outcome'] == 'verified'
            assert operator['bytes']['to_verifier'] == match['bytes']['to_verifier']
            assert operator['bytes']['from_verifier'] == match['bytes']['from_verifier']
            op, wi = role_parts(operator), role_parts(match)
            # 1 ms quantization of marks can put a small call slightly over 100%.
            assert op['accounted_percent'] >= 90 and wi['accounted_percent'] >= 90
            upstream = match['detail']['upstream_tls_bytes']
            network = {'operator_to_witness_socket_bytes': operator['bytes']['to_verifier'],
                       'witness_to_operator_socket_bytes': operator['bytes']['from_verifier'],
                       'upstream_tls_to_server_socket_bytes': upstream['to_server'],
                       'upstream_tls_from_server_socket_bytes': upstream['from_server']}
            network['operator_to_witness_overhead_bytes'] = network['operator_to_witness_socket_bytes'] - upstream['to_server']
            network['witness_to_operator_overhead_bytes'] = network['witness_to_operator_socket_bytes'] - upstream['from_server']
            network['basis'] = 'four successful socket read/write counters; overhead = role socket total minus relayed TLS stream; includes disclosed transcript copies, framing, proofs and receipt; excludes TCP/IP headers'
            rows.append({'case': str(case), 'call': i, 'settings': setting,
                         'operator_record': str(filename),
                         'witness_record': str(next(p for p in (case / 'witness').glob('*.record.json') if read(p)['job_id'] == operator['job_id'])),
                         'operator': op, 'witness': wi, 'network': network,
                         'operator_caps': operator['detail']['cgroup_caps'], 'witness_caps': match['detail']['cgroup_caps'],
                         'client': client, 'operator_timings_ms': operator['timings_ms'],
                         'sent_transcript_bytes': operator['detail']['request_bytes_sent'],
                         'received_transcript_bytes': operator['detail']['response_bytes_received'],
                         'operator_cpu_marks': operator['detail']['cpu_marks'],
                         'witness_cpu_marks': match['detail']['cpu_marks']})

fits = {}
uploads = [r for r in rows if '/matrix-final/send-' in r['case'] and r['call'] == 1]
downloads = [r for r in rows if '/matrix-final/receive-' in r['case']] + [r for r in uploads if r['settings']['sent_body_bytes'] == 100]
for role in ['operator', 'witness']:
    fits[role + '_sent_total_cpu_s'] = fit([(r['sent_transcript_bytes'] / 1024, r[role]['total_cpu_s']) for r in uploads])
    fits[role + '_sent_auth_cpu_s'] = fit([(r['sent_transcript_bytes'] / 1024, r[role]['components_cpu_s']['plaintext_auth_and_hidden_hash']) for r in uploads])
    fits[role + '_received_total_cpu_s'] = fit([(r['received_transcript_bytes'] / 1024, r[role]['total_cpu_s']) for r in downloads])

for direction in ['operator_to_witness_socket_bytes', 'witness_to_operator_socket_bytes']:
    fits[direction + '_by_sent'] = fit([(r['sent_transcript_bytes'] / 1024, r['network'][direction]) for r in uploads])
    fits[direction + '_by_received'] = fit([(r['received_transcript_bytes'] / 1024, r['network'][direction]) for r in downloads])

for role in ['operator', 'witness']:
    fits[role + '_sent_auth_cpu_s']['cpu_ms_per_16_byte_block_normalization'] = fits[role + '_sent_auth_cpu_s']['slope_per_KiB'] * 1000 / 64
    # Control out the independent, fixed-shape predicate's run-to-run noise.
    keys = ['online_tls_and_http', 'prf_tags_finalize', 'plaintext_auth_and_hidden_hash'] if role == 'operator' else ['relay_prf_and_record_tags', 'plaintext_auth_and_hidden_hash']
    fits[role + '_received_auth_and_io_cpu_s'] = fit([
        (r['received_transcript_bytes'] / 1024, sum(r[role]['components_cpu_s'][k] for k in keys))
        for r in downloads])

data = {'rows': rows, 'witness_startups': startups, 'descriptive_fits': fits,
        'minimum_accounted_percent': {role: min(r[role]['accounted_percent'] for r in rows) for role in ['operator', 'witness']},
        'arithmetic': 'Each component is the later absolute whole-process getrusage CPU mark minus the earlier mark. Roles ran separately, serially, with no overlapping sessions. Predicate CPU has an independent unrounded bracket. Sum components / run record CPU * 100. Startup is separate, not allocated repeatedly to sessions.'}
(root / 'accounting.json').write_text(json.dumps(data, indent=2) + '\n')
for r in rows:
    print(Path(r['case']).name, r['call'], 'operator/witness CPU:', r['operator']['total_cpu_s'], r['witness']['total_cpu_s'],
          'accounted:', round(r['operator']['accounted_percent'], 2), round(r['witness']['accounted_percent'], 2))
