"""Capture chain cases and a labelled synthetic missing-target semantic control.
Usage: python3 tools/generate_job_samples.py runs/phase-28/fixture-TIMESTAMP
Signing seeds are read only in memory from existing fixture files, never copied.
"""
import pathlib,json,sys,copy,hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
R=pathlib.Path(sys.argv[1]);S=pathlib.Path('samples/evidence')
def load(label):
 d=R/label/'client';return [json.loads((d/'package.json').read_text()),(d/'request.http').read_bytes(),(d/'response.http').read_bytes(),json.loads((d/'trust.json').read_text())]
def save(name,data,result,link=None):
 d=S/name;d.mkdir(exist_ok=True)
 package,req,res,trust=copy.deepcopy(data)
 package['provenance']=dict(run=str(R),build_identity=json.loads((R/'build-identity.json').read_text()))
 profile=package['chain'][-1]['receipt']['verdict'].get('profile','credential-sequence') if result=='PASS' or link in ('job_link','result_digest') else None
 for n,v in [('package.json',package),('trust.json',trust),('expected.json',dict(result=result,link=link,profile=profile))]:(d/n).write_text(json.dumps(v,indent=2)+'\n')
 (d/'request.http').write_bytes(req);(d/'response.http').write_bytes(res)
a=load('normal-a');b=load('normal-b')
save('job-complete',a,'PASS');save('job-pending-done',load('pending'),'PASS');save('job-cut',load('cut'),'UNVERIFIED')
bad=load('bad-digest');save('job-bad-digest-unverified',bad,'UNVERIFIED')
# The honest router refused verification. Reassemble its genuine authenticated
# exchanges with a synthetic unsigned verified envelope to exercise the checker.
bad[0]['state']='verified'
bad[0]['chain']=json.loads((R/'receipts'/bad[0]['receipt_id']/'rejected-chain.json').read_text())
bad[0]['test_only']='Unsigned verified envelope around genuine witnessed corrupt fixture result; router published UNVERIFIED.'
save('job-result-digest',bad,'FAIL','result_digest')
c=copy.deepcopy(a);c[0]['chain'][1]=copy.deepcopy(b[0]['chain'][1]);save('job-other-poll',c,'FAIL','job_link')
c=copy.deepcopy(a);c[0]['chain'][-1]=copy.deepcopy(b[0]['chain'][-1]);c[2]=b[2];save('job-other-fetch',c,'FAIL','job_link')
# A real record with valid fixture signatures, rewritten deliberately to isolate
# target semantics. It is NOT a new TLSNotary observation. Both attestations are
# explicitly test signed; the unchanged real fixture seed files remain ignored.
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def sign(value,path):
 value.pop('sig',None)
 seed=bytes.fromhex(pathlib.Path(path).read_text().strip())
 value['sig']=Ed25519PrivateKey.from_private_bytes(seed).sign(canonical(value)).hex()
def target_control(name,index,bad):
 c=copy.deepcopy(a);step=c[0]['chain'][index];target=step['receipt']['record']['request']['path']
 step['request_hex']=bytes.fromhex(step['request_hex']).replace(target.encode(),bad.encode(),1).hex()
 statement=step['operator_statement'];statement['path']=bad;sign(statement,'runs/phase-22/operator.key')
 record=step['receipt']['record'];record['request']['path']=bad;record['operator_statement_sha256']=hashlib.sha256(canonical(statement)).hexdigest()
 verdict=step['receipt']['verdict'];assert verdict['exchanges']==1 and step['receipt']['path']==[]
 verdict['root']=hashlib.sha256(canonical(record)).hexdigest();sign(verdict,'runs/phase-22/witness-b.key')
 c[0]['test_only']='Synthetic fixture signatures for target semantics with unchanged receipt id; not a TLSNotary observation.'
 save(name,c,'FAIL','job_link')

target_control('job-missing-id',1,'/jobs/poll')
target_control('job-other-id-poll',1,b[0]['chain'][1]['receipt']['record']['request']['path'])
target_control('job-other-id-fetch',-1,b[0]['chain'][-1]['receipt']['record']['request']['path'])
c=copy.deepcopy(a);c[0].pop('chain');save('job-kind-without-chain',c,'FAIL','evidence')
c=copy.deepcopy(a);c[0].pop('kind');save('job-chain-without-kind',c,'FAIL','inclusion')
c=copy.deepcopy(a);c[0]['chain'][1]=copy.deepcopy(b[0]['chain'][1])
c[0]['chain'][-1]['receipt']['record']['response']['body_bytes']+=1
c[0]['test_only']='Synthetic compound failure: step 2 receipt-id job_link precedes step 3 tampered-record inclusion.'
save('job-interleaved-order',c,'FAIL','job_link')
print('13 chain samples created')
