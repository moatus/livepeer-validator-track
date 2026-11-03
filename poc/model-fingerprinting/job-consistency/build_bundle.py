"""Private collector/exporter. Never included in artifact-only bundle."""
import pathlib,json,struct,os,copy,secrets,shutil,datetime
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from common import *
P=pathlib.Path(__file__).resolve().parent;B=P/'bundle'
J=json.loads((P/'private/requests.json').read_text());R=[json.loads(p.read_text()) for p in (P/'runs').glob('*.json')]
byid={j['id']:j for j in J};refs={r['id']:r for r in R if r['role']=='reference'};cands={r['id']:r for r in R if r['role']=='candidate'}
assert len(refs)==len(cands)==90
key=Ed25519PrivateKey.generate()
kp=P/'private/test-ed25519.pem';kp.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()));kp.chmod(0o600)
(B/'public-key.hex').write_text(key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw).hex()+'\n')
def vec(r):return list(struct.unpack('<54f',(P/'vectors'/f"{r['key']}.f32").read_bytes()))
def sign(r):return key.sign(framed('receipt',canonical(r))).hex()
cases=[];truth=[]
def case(j,source,kind,observed=True):
 e={k:j[k] for k in ['input_commitment','model_profile','settings_commitment']};e.update(version=VERSION,job_id=j['id'],measurement_version='IMG-002-54-v1',output_commitment=refs[j['id']]['output_commitment'],reference=vec(refs[j['id']]))
 v=vec(source)
 receipt={k:v for k,v in e.items() if k!='reference'};receipt['fingerprint_digest']=digest('fingerprint-f32le',struct.pack('<54f',*v))
 x=dict(case_id=secrets.token_hex(16),expected=e,candidate=dict(fingerprint=v,receipt=receipt,signature=sign(receipt)))
 if observed:x['observed_output_commitment']=e['output_commitment']
 cases.append(x);truth.append(dict(case_id=x['case_id'],kind=kind,split=j['split'],family=j['family'],seed=j['seed'],expected_variant=j['variant'],source_variant=source['variant'],source_key=source['key']))
 return x
for j in J:
 if j['split']=='collision':continue
 case(j,cands[j['id']],'correct')
for j in J:
 if j['variant'] not in ['A','B','C']:continue
 pairs={'A':[('B','close'),('C','distant')],'B':[('A','close')],'C':[('A','distant')]}[j['variant']]
 for variant,kind in pairs:
  donor=next(k for k in J if k['family']==j['family'] and k['seed']==j['seed'] and k['variant']==variant)
  # Deliberately preserve ALL ordinary expected metadata, including output claim/observer.
  # Only numerical measurement + its necessary authentic digest/signature change.
  case(j,cands[donor['id']],kind)
for r in R:
 if r['role']=='reload':case(byid[r['id']],r,'reload')
j=next(j for j in J if j['family']==5 and j['variant']=='A' and j['seed']==6303)
donor=next(k for k in J if k['family']==5 and k['variant']=='C' and k['seed']==6303)
base=case(j,cands[j['id']],'receipt_unchanged')
for field in ['version','job_id','input_commitment','model_profile','settings_commitment','output_commitment','fingerprint_digest','measurement_version']:
 x=copy.deepcopy(base);x['case_id']=secrets.token_hex(16);x['candidate']['receipt'][field]='edited-'+x['candidate']['receipt'][field]
 cases.append(x);truth.append(dict(case_id=x['case_id'],kind='unsigned_edit_'+field,split='control'))
# Authentic other-job receipt swapped wholesale; signature succeeds, identity checking must fail.
x=copy.deepcopy(base);x['case_id']=secrets.token_hex(16)
d=next(c for c in cases if c['expected']['job_id']==donor['id'] and c['candidate']['fingerprint']==vec(cands[donor['id']]))
x['candidate']=copy.deepcopy(d['candidate']);cases.append(x);truth.append(dict(case_id=x['case_id'],kind='stale_other_job_receipt',split='control'))
# Trusted observer hashes wrong delivered pixels with EXPECTED job's output blinding.
# Pillow isn't in system Python; use venv helper to compute canonical pixel commitments only.
import subprocess
other_image=P/'images'/f"{cands[donor['id']]['key']}.png"
helper='from PIL import Image; import sys,json; from common import *; j=json.load(open(sys.argv[1])); r=next(x for x in j if x["id"]==sys.argv[2]); print(commit("output",bytes.fromhex(r["output_blind"]),pixels(Image.open(sys.argv[3]))))'
wrong_oc=subprocess.check_output([str(P.parents[1]/'image-fingerprinting-poc/2026-10-25/.venv/bin/python'),'-c',helper,str(P/'private/requests.json'),j['id'],str(other_image)],cwd=P,text=True).strip()
assert wrong_oc!=base['expected']['output_commitment']
x=case(j,cands[j['id']],'signed_wrong_output')
x['candidate']['receipt']['output_commitment']=wrong_oc;x['candidate']['signature']=sign(x['candidate']['receipt']);x['observed_output_commitment']=wrong_oc
# Output delivery swap with honest expected fingerprint and claimed output; observer catches it.
x=case(j,cands[j['id']],'wrong_delivery_with_observer');x['observed_output_commitment']=wrong_oc
# The same attack passes without trusted delivered-byte measurement.
x=case(j,cands[j['id']],'wrong_delivery_no_observer',False)
# Copy a known reference, claim its expected output, re-sign: no new execution.
x=case(j,refs[j['id']],'copied_reference_no_fresh_execution',False)
x=case(j,refs[j['id']],'signed_wrong_fingerprint');x['candidate']['fingerprint']=vec(cands[donor['id']]);x['candidate']['receipt']['fingerprint_digest']=digest('fingerprint-f32le',struct.pack('<54f',*x['candidate']['fingerprint']));x['candidate']['signature']=sign(x['candidate']['receipt'])
# Identical-effective-token control: raw commitments differ; numerical path cannot distinguish.
controls=[r for r in R if r['split']=='collision'];assert len(controls)==2
jx=next(k for k in J if k['id']==controls[0]['id']);jy=next(k for k in J if k['id']==controls[1]['id'])
assert jx['input_commitment']!=jy['input_commitment']
# Adapt only internal collector mapping; bundle sees opaque expected IDs as always.
refs[jx['id']]=controls[0]
case(jx,controls[1],'identical_effective_input')
rule=json.loads((P/'frozen-rule.json').read_text());dump(B/'rule.json',{k:rule[k] for k in ['measurement_version','scale','tolerance','score']})
# Shuffle opaque cases; ground truth is NOT exported and is joined after scoring.
secrets.SystemRandom().shuffle(cases);dump(B/'cases.json',cases);dump(P/'private/ground-truth.json',truth)
for name in ['common.py','verifier.py']:shutil.copyfile(P/name,B/name)
dump(P/'export.json',dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),cases=len(cases),files=sorted(p.name for p in B.iterdir()),notes='No prompt, seed, tokenizer IDs, images, embeddings, secret blinding, private key, manifest path, ground truth, family or variant exported. Opaque job ID selects expected reference.'))
print('Exported',len(cases),'artifact-only cases')
