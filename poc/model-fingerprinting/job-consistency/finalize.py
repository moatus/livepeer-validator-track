import pathlib,json,hashlib,sys,datetime,statistics
from common import dump
P=pathlib.Path(__file__).resolve().parent;OLD=P.parents[1]/'image-fingerprinting-poc/2026-10-25'
rows=json.loads((P/'decision-rows.json').read_text());summary={}
for split in ['calibration','heldout']:
 summary[split]={}
 for kind in ['correct','reload','close','distant']:
  rr=[r for r in rows if r['split']==split and r['kind']==kind]
  summary[split][kind]=dict(n=len(rr),**{k:sum(r[k] for r in rr) for k in ['fingerprint_only','signature_valid','receipt_valid','commitment_receipt_only','combined']})
  assert all(r['signature_valid'] and r['receipt_valid'] and r['commitment_receipt_only'] for r in rr)
  assert all(r['fingerprint_only']==(kind in ['correct','reload']) and r['combined']==r['fingerprint_only'] for r in rr)
controls={r['kind']:r for r in rows if r['split']=='control' or r['kind'] in ['identical_effective_input','receipt_unchanged','signed_wrong_fingerprint','signed_wrong_output','wrong_delivery_with_observer','wrong_delivery_no_observer','copied_reference_no_fresh_execution']}
for kind,r in controls.items():
 if kind.startswith('unsigned_edit_'):assert not r['signature_valid'] and not r['combined']
for kind in ['receipt_unchanged','copied_reference_no_fresh_execution','wrong_delivery_no_observer','identical_effective_input']:assert controls[kind]['combined']
for kind in ['signed_wrong_fingerprint','signed_wrong_output','wrong_delivery_with_observer','stale_other_job_receipt']:assert not controls[kind]['combined']
assert controls['signed_wrong_fingerprint']['signature_valid'] and controls['signed_wrong_fingerprint']['commitment_receipt_only'] and not controls['signed_wrong_fingerprint']['fingerprint_only']
for kind in ['signed_wrong_output','wrong_delivery_with_observer']:assert controls[kind]['fingerprint_only'] and not controls[kind]['commitment_receipt_only']
# Compare audited run decisions excluding timing only.
a=json.loads((P/'audit-decisions.json').read_text());d=json.loads((P/'decisions.json').read_text())
assert [{k:v for k,v in r.items() if k!='cpu_ns'} for r in a]==[{k:v for k,v in r.items() if k!='cpu_ns'} for r in d]
assert all((P/'bundle'/n).read_bytes()==(P/n).read_bytes() for n in ['verifier.py','common.py'])
assert {p.name for p in (P/'bundle').iterdir()}=={'cases.json','rule.json','public-key.hex','verifier.py','common.py'}
assert not json.loads((P/'cleanup.json').read_text())['remaining_experiment_generation_processes']
dump(P/'binding-main-scorecard.json',summary)
dump(P/'model-identity.json',json.loads((OLD/'identity-sd15.json').read_text()))
(P/'generation-requirements.lock').write_bytes((OLD/'requirements.lock').read_bytes())
dump(P/'test-verifier-runtime.json',dict(python=sys.version,cryptography=__import__('cryptography').__version__,standard_library_numeric=True))
dump(P/'final-checks.json',dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),main_scorecards_expected=True,all_controls_expected=True,audited_decisions_equal=True,exported_code_matches_frozen_source=True,bundle_exactly_five_files=True,no_remaining_generation_processes=True))
print('All main/negative-control expectations and audited reproduction match')
