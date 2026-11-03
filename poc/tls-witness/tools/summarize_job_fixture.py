"""Reproduce summary.json and connections.json from retained job run records.
Usage: python3 tools/summarize_job_fixture.py runs/phase-28/fixture-TIMESTAMP
"""
import json, pathlib, sys

run = pathlib.Path(sys.argv[1])
def read(path):
    return json.loads(path.read_text())
def save(name, value):
    (run/name).write_text(json.dumps(value, indent=2)+'\n')

measurements = read(run/'measurements.json')
rows = read(run/'results.json')
chains, connections = [], []
for row, measured in zip(rows, measurements['chains']):
    assert row['case'] == measured['case']
    times = read(run/row['case']/'client'/'timestamps.json')
    sessions = measured['sessions']
    chains.append(dict(case=row['case'],
        client_total_delivery_ms=(times['response_end_unix_ns']-times['start_unix_ns'])/1e6,
        credential_lifetimes_ms=[s['credential_lifetime_ms'] for s in sessions],
        obtain_ms_total=sum(s['obtain_ms'] or 0 for s in sessions),
        disable_ms_total=sum(s['revoke_ms'] or 0 for s in sessions),
        dead_check_windows_ms=[s['dead_check_window_ms'] for s in sessions],
        evidence_delay_after_last_upstream_response_ms=measured['evidence_delay_after_last_upstream_response_ms'],
        router_peak_rss_mib=measured['router_peak_rss_mib'],retention=measured['retention']))
    steps = []
    for path in sorted((run/'witness').glob('*.record.json')):
        record = read(path)
        if record.get('job_id') != row['receipt_id'] or not record.get('detail',{}).get('upstream'):
            continue
        steps.append(dict(session_id=record['detail']['session_id'],
            upstream=record['detail']['upstream'],tls=record['detail'].get('tls'),record=str(path)))
    addresses = {s['upstream']['local_addr'] for s in steps}
    connections.append(dict(case=row['case'],distinct_upstream_tcp_connections=len(addresses),steps=steps))

save('connections.json', connections)
save('summary.json',dict(final_fixture=str(run),source_commit=read(run/'build-identity.json')['source_commit'],
    witness_peak_rss_mib=measurements['witness_peak_rss_mib'],chains=chains,
    reconciliation=read(run/'reconciliation.json'),provider_requests=0,spend_usd=0))
