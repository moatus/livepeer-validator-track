"""Artifact-only verifier. Reads only the supplied bundle directory.
No torch, tokenizer, model, image decoder, prompt, secret, private path or ground truth.
"""
import argparse,pathlib,json,math,struct,time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from common import canonical,digest,framed
FIELDS={'version','job_id','input_commitment','model_profile','settings_commitment','output_commitment','fingerprint_digest','measurement_version'}
def vector_bytes(v):
 if len(v)!=54 or not all(isinstance(x,(float,int)) and math.isfinite(x) for x in v):raise ValueError('invalid fingerprint')
 return struct.pack('<54f',*v)
def numeric(reference,candidate,scale,tolerance):
 # ONLY these 4 numerical inputs enter scoring; no envelope metadata is accessible here.
 vector_bytes(reference);vector_bytes(candidate)
 if len(scale)!=54 or not all(math.isfinite(s) and s>0 for s in scale):raise ValueError('invalid scale')
 score=math.sqrt(sum(((float(a)-float(b))/s)**2 for a,b,s in zip(reference,candidate,scale))/54)
 return score,score<=tolerance

def verify(case,public_key,rule):
 start=time.perf_counter_ns();e=case['expected'];c=case['candidate'];r=c['receipt']
 score,fp=numeric(e['reference'],c['fingerprint'],rule['scale'],rule['tolerance'])
 signature=False
 try:
  public_key.verify(bytes.fromhex(c['signature']),framed('receipt',canonical(r)));signature=True
 except Exception:pass
 identity=set(r)==FIELDS and all(r.get(k)==e[k] for k in ['version','job_id','input_commitment','model_profile','settings_commitment','measurement_version'])
 fd=r.get('fingerprint_digest')==digest('fingerprint-f32le',vector_bytes(c['fingerprint']))
 receipt=bool(signature and identity and fd)
 output_claim=r.get('output_commitment')==e['output_commitment']
 # trusted observer is a separately supplied commitment over delivered pixel bytes.
 observer=(case.get('observed_output_commitment')==e['output_commitment']) if 'observed_output_commitment' in case else None
 binding=receipt and output_claim and observer is not False
 return dict(case_id=case['case_id'],distance=score,fingerprint_only=fp,signature_valid=signature,identity_valid=identity,fingerprint_digest_valid=fd,receipt_valid=receipt,output_claim_matches=output_claim,observed_output_matches=observer,commitment_receipt_only=binding,combined=fp and binding,cpu_ns=time.perf_counter_ns()-start)

def main():
 a=argparse.ArgumentParser();a.add_argument('bundle',type=pathlib.Path);a.add_argument('--output',type=pathlib.Path);args=a.parse_args()
 b=args.bundle
 rule=json.loads((b/'rule.json').read_text());cases=json.loads((b/'cases.json').read_text());key=Ed25519PublicKey.from_public_bytes(bytes.fromhex((b/'public-key.hex').read_text().strip()))
 rows=[verify(c,key,rule) for c in cases]
 s=json.dumps(rows,indent=2,allow_nan=False)+'\n'
 if args.output:args.output.write_text(s)
 else:print(s,end='')
if __name__=='__main__':main()
