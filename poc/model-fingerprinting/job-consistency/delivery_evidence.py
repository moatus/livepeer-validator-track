"""Private saved-artifact delivery evidence; no additional inference."""
import pathlib,json
from PIL import Image
from common import *
P=pathlib.Path(__file__).resolve().parent
J=json.loads((P/'private/requests.json').read_text());R=[json.loads(p.read_text()) for p in (P/'runs').glob('*.json')]
j=next(j for j in J if j['family']==5 and j['variant']=='A' and j['seed']==6303)
d=next(j for j in J if j['family']==5 and j['variant']=='C' and j['seed']==6303)
def image(job):
 r=next(r for r in R if r['id']==job['id'] and r['role']=='candidate')
 return P/'images'/f"{r['key']}.png"
expected=image(j);delivered=image(d)
with Image.open(expected) as im:ec=commit('output',bytes.fromhex(j['output_blind']),pixels(im))
with Image.open(delivered) as im:dc=commit('output',bytes.fromhex(j['output_blind']),pixels(im))
assert ec!=dc
T={t['case_id']:t for t in json.loads((P/'private/ground-truth.json').read_text())};cases=json.loads((P/'bundle/cases.json').read_text())
rows=[]
for c in cases:
 kind=T[c['case_id']]['kind']
 if kind not in ['signed_wrong_output','wrong_delivery_with_observer','wrong_delivery_no_observer','copied_reference_no_fresh_execution']:continue
 assert c['expected']['output_commitment']==ec
 if kind=='signed_wrong_output':assert c['candidate']['receipt']['output_commitment']==dc
 if kind=='wrong_delivery_with_observer':assert c['observed_output_commitment']==dc
 if kind in ['wrong_delivery_no_observer','copied_reference_no_fresh_execution']:assert 'observed_output_commitment' not in c
 rows.append(dict(case_id=c['case_id'],kind=kind,expected_image=str(expected),delivery_image=str(delivered if kind!='copied_reference_no_fresh_execution' else expected),expected_output_commitment=ec,delivery_output_commitment=dc if kind!='copied_reference_no_fresh_execution' else ec,observer_supplied='observed_output_commitment' in c,new_inference=False))
dump(P/'private/delivery-evidence.json',rows)
print('Verified four saved-artifact delivery/replay controls; no inference')
