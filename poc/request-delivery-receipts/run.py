"""Offline fixture replay; expectations are outside verifier and joined after verification."""
import json,pathlib,time,statistics,platform,sys
from verifier import verify,sha
ROOT=pathlib.Path(__file__).parent
EXPECTED={'honest_json':'EXACT_EXCHANGE_BOUND','honest_sse':'EXACT_EXCHANGE_BOUND','honest_media':'EXACT_EXCHANGE_BOUND','changed_user_input':'REQUEST_MISMATCH','changed_instruction_settings':'REQUEST_MISMATCH','changed_delivery':'DELIVERY_MISMATCH','old_nonce_new_job':'JOB_CHALLENGE_MISMATCH','duplicate_job_replay':'JOB_ALREADY_CONSUMED','expensive_provider_decoy_substitute':'DELIVERY_MISMATCH','truncated_sse':'DELIVERY_MISMATCH','gateway_signature_as_upstream':'SIGNATURE_INVALID','missing_signature':'MISSING_SIGNATURE','trusted_signer_wrong_hidden_backend':'EXACT_EXCHANGE_BOUND','replay_no_independent_freshness':'NO_INDEPENDENT_FRESHNESS','missing_independent_delivery':'NO_INDEPENDENT_DELIVERY','attacker_chosen_issuer_key':'UNTRUSTED_ISSUER'}
def main():
    trust=json.loads((ROOT/'trust.json').read_text());cases=json.loads((ROOT/'cases.json').read_text());rows=[];loaded=[]
    for case in cases:
        d=ROOT/'fixtures'/case['id'];e=json.loads((d/'receipt.json').read_text());c=json.loads((d/'customer.json').read_text());loaded.append((case,e,c))
        state=set()
        if case['preconsume']:
            first=verify(e,c,trust,state)
            assert first['scope']=='exchange_verified'
        start=time.perf_counter_ns();result=verify(e,c,trust,state);ns=time.perf_counter_ns()-start
        passed=result['reason']==EXPECTED[case['id']]
        rows.append(dict(id=case['id'],group=case['group'],**result,expected_reason=EXPECTED[case['id']],passed=passed,verification_ns=ns,receipt_file_bytes=(d/'receipt.json').stat().st_size,customer_file_bytes=(d/'customer.json').stat().st_size,intended_request_bytes=len(bytes.fromhex(c['intended_request_hex'])),delivered_response_bytes=len(bytes.fromhex(c.get('delivered_response_hex',''))),delivered_asset_bytes=sum(len(bytes.fromhex(v)) for v in c.get('delivered_assets',{}).values())))
    out=dict(protocol_sha256=sha((ROOT/'PROTOCOL.json').read_bytes()),core=dict(total=12,honest_accepted=sum(r['scope']=='exchange_verified' for r in rows[:3]),invalid_accepted=sum(r['scope']=='exchange_verified' for r in rows[3:12]),passed=sum(r['passed'] for r in rows[:12])),boundary=dict(total=4,passed=sum(r['passed'] for r in rows[12:])),failures=sum(not r['passed'] for r in rows),spend_usd=0,actual_model_executions=0,benchmark=dict(status='not_rerun',historical_source='original-results.json',note='Original v1 benchmark is historical, not measured for v2'),environment=dict(python=sys.version,platform=platform.platform()),outcomes=rows)
    (ROOT/'results.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ('core','boundary','failures','benchmark')}));return bool(out['failures'])
if __name__=='__main__': raise SystemExit(main())
