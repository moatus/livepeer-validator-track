"""Offline RECEIPT-005. Trust/customer inputs must originate independently of gateway."""
import argparse, hashlib, json, struct, pathlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
VERSION='receipt005-v1'
FIELDS=set('version job_id challenge provider canonical_model model_version request_sha256 response_sha256 terminal_status format assets'.split())
def canonical(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')
def framed(domain,*parts):
    return b''.join(struct.pack('>Q',len(p))+p for p in [VERSION.encode(),domain.encode(),*parts])
def sha(b): return hashlib.sha256(b).hexdigest()
def raw(s): return bytes.fromhex(s)
def reject_constant(value):
    raise ValueError('Non-JSON numeric constant: '+value)
def strict_json(data):
    # Artifact v2 profile: body/event bytes are strict UTF-8, finite JSON only.
    return json.loads(data.decode('utf-8'),parse_constant=reject_constant)
def verify(envelope,customer,trust,consumed):
    def fail(reason,status='rejected'): return dict(scope=status,reason=reason)
    try:
        r=envelope['payload']
        if set(r)!=FIELDS or any(not isinstance(r[k],str) for k in FIELDS-{'assets'}) or not isinstance(r['assets'],dict) or any(not isinstance(k,str) or not isinstance(v,str) for k,v in r['assets'].items()): return fail('SCHEMA')
        if r['version']!=VERSION: return fail('VERSION')
        if envelope.get('issuer')!=trust['issuer']: return fail('UNTRUSTED_ISSUER')
        if not envelope.get('signature'): return fail('MISSING_SIGNATURE','unverified')
        try: Ed25519PublicKey.from_public_bytes(raw(trust['public_key_hex'])).verify(raw(envelope['signature']),framed('receipt',canonical(r)))
        except Exception: return fail('SIGNATURE_INVALID')
        if customer.get('fresh_challenge_issued') is not True: return fail('NO_INDEPENDENT_FRESHNESS','unverified')
        if (r['job_id'],r['challenge'])!=(customer['job_id'],customer['challenge']): return fail('JOB_CHALLENGE_MISMATCH')
        if r['job_id'] in consumed: return fail('JOB_ALREADY_CONSUMED')
        if any(r[k]!=trust[k] for k in ('provider','canonical_model','model_version')): return fail('PROVIDER_MODEL_MISMATCH')
        if sha(raw(customer['intended_request_hex']))!=r['request_sha256']: return fail('REQUEST_MISMATCH')
        if 'delivered_response_hex' not in customer: return fail('NO_INDEPENDENT_DELIVERY','unverified')
        delivery=raw(customer['delivered_response_hex'])
        if sha(delivery)!=r['response_sha256']: return fail('DELIVERY_MISMATCH')
        if r['terminal_status']!='complete': return fail('NONTERMINAL')
        if r['format']=='sse':
            delivery.decode('utf-8')  # Validate entire stream before byte-exact framing.
            events=delivery.split(b'\n\n')
            if len(events)<3 or events[-1]!=b'' or events[-2]!=b'data: [DONE]': return fail('SSE_INCOMPLETE')
            for event in events[:-2]:
                if not event.startswith(b'data: ') or not isinstance(strict_json(event[6:]),dict): return fail('SSE_GRAMMAR')
            if r['assets']: return fail('UNEXPECTED_ASSETS')
        elif r['format'] in ('json','media'):
            obj=strict_json(delivery)
            if not isinstance(obj,dict): return fail('JSON_OBJECT_REQUIRED')
            if r['format']=='media':
                if set(obj)!={'asset_url'} or not isinstance(obj['asset_url'],str) or not obj['asset_url'].startswith('mock://') or set(r['assets'])!={obj['asset_url']}: return fail('MEDIA_RECORD')
                asset=customer.get('delivered_assets',{}).get(obj['asset_url'])
                if asset is None: return fail('NO_INDEPENDENT_ASSET','unverified')
                if sha(raw(asset))!=r['assets'][obj['asset_url']]: return fail('ASSET_MISMATCH')
            elif r['assets']: return fail('UNEXPECTED_ASSETS')
        else: return fail('UNSUPPORTED_FORMAT')
        consumed.add(r['job_id'])
        return dict(scope='exchange_verified',reason='EXACT_EXCHANGE_BOUND')
    except (ValueError,TypeError,KeyError,UnicodeError): return fail('MALFORMED_EVIDENCE')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',required=True,type=pathlib.Path);p.add_argument('--customer',required=True,type=pathlib.Path);p.add_argument('--trust',required=True,type=pathlib.Path);p.add_argument('--consumed',required=True,type=pathlib.Path,help='Caller-owned local JSON list; initialized [] if absent; no concurrent writers');a=p.parse_args()
    consumed=set(json.loads(a.consumed.read_text())) if a.consumed.exists() else set()
    result=verify(json.loads(a.receipt.read_text()),json.loads(a.customer.read_text()),json.loads(a.trust.read_text()),consumed)
    if result['scope']=='exchange_verified': a.consumed.write_text(json.dumps(sorted(consumed))+'\n')
    print(json.dumps(result));return 0 if result['scope']=='exchange_verified' else 1
if __name__=='__main__': raise SystemExit(main())
