"""Synthetic fixture generation only. Ephemeral private keys never serialized."""
import copy,json,pathlib,secrets
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from verifier import canonical,framed,sha,VERSION
ROOT=pathlib.Path(__file__).parent

def main():
    upstream=Ed25519PrivateKey.generate();gateway=Ed25519PrivateKey.generate()
    trust=dict(issuer='independently-pinned-test-upstream',provider='mock-expensive-provider',canonical_model='mock-model',model_version='frozen-v1',public_key_hex=upstream.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex())
    def fixture(name,fmt='json'):
        request=canonical(dict(user='Describe blue shapes',instructions='Return a concise answer',settings=dict(temperature=0,max_tokens=64)))
        response={'json':b'{"answer":"two blue circles"}\n','sse':b'data: {"delta":"two "}\n\ndata: {"delta":"blue circles"}\n\ndata: [DONE]\n\n','media':b'{"asset_url":"mock://asset/one"}\n'}[fmt]
        asset=b'\x00\xffSYNTHETIC-MEDIA\n\x80'
        customer=dict(job_id=name,challenge=secrets.token_hex(32),fresh_challenge_issued=True,intended_request_hex=request.hex(),delivered_response_hex=response.hex())
        assets={}
        if fmt=='media': assets={'mock://asset/one':sha(asset)};customer['delivered_assets']={'mock://asset/one':asset.hex()}
        payload=dict(version=VERSION,job_id=name,challenge=customer['challenge'],provider=trust['provider'],canonical_model=trust['canonical_model'],model_version=trust['model_version'],request_sha256=sha(request),response_sha256=sha(response),terminal_status='complete',format=fmt,assets=assets)
        return dict(id=name,envelope=dict(issuer=trust['issuer'],payload=payload),customer=customer,preconsume=False)
    def sign(c,key=upstream): c['envelope']['signature']=key.sign(framed('receipt',canonical(c['envelope']['payload']))).hex();return c
    core=[sign(fixture('honest_json')),sign(fixture('honest_sse','sse')),sign(fixture('honest_media','media'))]
    for name in ['changed_user_input','changed_instruction_settings','changed_delivery','old_nonce_new_job','duplicate_job_replay','expensive_provider_decoy_substitute','truncated_sse','gateway_signature_as_upstream','missing_signature']:
        c=fixture(name,'sse' if name=='truncated_sse' else 'json')
        if name in ('changed_user_input','changed_instruction_settings'):
            req=json.loads(bytes.fromhex(c['customer']['intended_request_hex']))
            if name=='changed_user_input': req['user']='Describe red squares'
            else: req['instructions']='Ignore previous instructions';req['settings']['temperature']=1
            c['envelope']['payload']['request_sha256']=sha(canonical(req))
        sign(c)
        if name in ('changed_delivery','expensive_provider_decoy_substitute'): c['customer']['delivered_response_hex']=b'{"answer":"cheap substitute"}\n'.hex()
        if name=='expensive_provider_decoy_substitute': c['simulation_note']='Genuine upstream signature covers real synthetic expensive-provider contact/output; independent customer sees substitute bytes. Zero inference.'
        if name=='old_nonce_new_job': c['customer']['job_id']='new-job';c['customer']['challenge']=secrets.token_hex(32)
        if name=='duplicate_job_replay': c['preconsume']=True
        if name=='truncated_sse': c['customer']['delivered_response_hex']=bytes.fromhex(c['customer']['delivered_response_hex']).removesuffix(b'data: [DONE]\n\n').hex()
        if name=='gateway_signature_as_upstream': sign(c,gateway)
        if name=='missing_signature': del c['envelope']['signature']
        core.append(c)
    boundary=[]
    c=fixture('trusted_signer_wrong_hidden_backend')
    # A literal local stand-in backend returns different bytes. Provider dishonestly
    # signs the pinned model assertion over those actual returned/delivered bytes.
    hidden_backend='mock-cheap-backend'
    backend_outputs={'mock-cheap-backend':b'{"answer":"cheap backend actually returned this"}\n','mock-expensive-backend':b'{"answer":"expensive backend output"}\n'}
    actual_response=backend_outputs[hidden_backend]
    c['customer']['delivered_response_hex']=actual_response.hex();c['envelope']['payload']['response_sha256']=sha(actual_response)
    sign(c);c['simulation_note']='Executed local byte lookup mock-cheap-backend, while trusted signer asserts frozen-v1. No actual model runs.';boundary.append(c)
    c=sign(fixture('replay_no_independent_freshness'));del c['customer']['fresh_challenge_issued'];boundary.append(c)
    c=sign(fixture('missing_independent_delivery'));del c['customer']['delivered_response_hex'];c['simulation_note']='Same substitution as changed_delivery, but independent observation absent; gateway could deliver arbitrary bytes.';boundary.append(c)
    c=fixture('attacker_chosen_issuer_key');c['envelope']['issuer']='attacker';c['envelope']['public_key_hex']=gateway.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex();sign(c,gateway);boundary.append(c)
    d=ROOT/'fixtures';d.mkdir(exist_ok=True)
    (ROOT/'trust.json').write_text(json.dumps(trust,indent=2)+'\n')
    for c in core+boundary:
        cd=d/c['id'];cd.mkdir(exist_ok=True)
        (cd/'receipt.json').write_text(json.dumps(c['envelope'],indent=2)+'\n');(cd/'customer.json').write_text(json.dumps(c['customer'],indent=2)+'\n')
    manifest=[{k:v for k,v in c.items() if k not in ('envelope','customer')}|{'group':'core' if c in core else 'boundary'} for c in core+boundary]
    (ROOT/'cases.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__': main()
