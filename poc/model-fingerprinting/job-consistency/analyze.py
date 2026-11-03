import pathlib,json,csv,collections,statistics,hashlib,datetime,os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import dump
P=pathlib.Path(__file__).resolve().parent
D=json.loads((P/'decisions.json').read_text());T={x['case_id']:x for x in json.loads((P/'private/ground-truth.json').read_text())}
rows=[dict(**r,**{k:v for k,v in T[r['case_id']].items() if k!='case_id'}) for r in D]
dump(P/'decision-rows.json',rows)
fields=sorted(set().union(*(r.keys() for r in rows)))
with (P/'decision-rows.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
score={}
for split in ['calibration','heldout']:
 score[split]={}
 for kind in ['correct','close','distant','reload']:
  rr=[r for r in rows if r['split']==split and r['kind']==kind]
  distances=[r['distance'] for r in rr]
  score[split][kind]=dict(n=len(rr),accepted=sum(r['fingerprint_only'] for r in rr),false_rejections=sum(not r['fingerprint_only'] for r in rr) if kind in ['correct','reload'] else None,false_acceptances=sum(r['fingerprint_only'] for r in rr) if kind in ['close','distant'] else None,distance_min=min(distances),distance_median=statistics.median(distances),distance_max=max(distances))
controls={}
for kind in sorted({r['kind'] for r in rows if r['kind'] not in ['correct','close','distant','reload']}):
 rr=[r for r in rows if r['kind']==kind]
 controls[kind]={k:sum(r[k] is True for r in rr) for k in ['fingerprint_only','signature_valid','receipt_valid','output_claim_matches','observed_output_matches','commitment_receipt_only','combined']};controls[kind]['n']=len(rr)
R=[json.loads(p.read_text()) for p in (P/'runs').glob('*.json')];refs={r['id']:r for r in R if r['role']=='reference'}
repeat={}
for role in ['candidate','reload']:
 rr=[r for r in R if r['role']==role]
 repeat[role]=dict(n=len(rr),equal_vectors=sum((P/'vectors'/f"{r['key']}.f32").read_bytes()==(P/'vectors'/f"{refs[r['id']]['key']}.f32").read_bytes() for r in rr),equal_pixels=sum(r['pixel_digest']==refs[r['id']]['pixel_digest'] for r in rr))
timing={}
for role in ['reference','candidate','reload','control']:
 rr=[r for r in R if r['role']==role];v=[r['seconds'] for r in rr]
 timing[role]=dict(n=len(rr),total_seconds=sum(v),median_seconds=statistics.median(v),min_seconds=min(v),max_seconds=max(v))
nsfw=[r['key'] for r in R if any(r['nsfw'] or [])]
summary=dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),numerical=score,controls=controls,repeats=repeat,generation_timing=timing,saved_generations=len(R),safety_replacements=nsfw,payload_bytes=216,bundle_bytes=sum(p.stat().st_size for p in (P/'bundle').iterdir() if p.is_file()),images_bytes=sum(p.stat().st_size for p in (P/'images').glob('*.png')),vectors_bytes=sum(p.stat().st_size for p in (P/'vectors').glob('*.f32')),verifier_cpu_us=dict(median=statistics.median(r['cpu_ns']/1000 for r in rows),p95=float(np.percentile([r['cpu_ns']/1000 for r in rows],95)),total=sum(r['cpu_ns'] for r in rows)/1e9))
dump(P/'results.json',summary);dump(P/'numerical-scorecard.json',score);dump(P/'binding-scorecard.json',controls)
fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
for ax,split in zip(axes,['calibration','heldout']):
 for i,kind in enumerate(['correct','reload','close','distant']):
  v=[r['distance'] for r in rows if r['split']==split and r['kind']==kind]
  ax.scatter([i]*len(v),np.maximum(v,1e-8),s=20,alpha=.5)
 ax.axhline(json.loads((P/'frozen-rule.json').read_text())['tolerance'],color='red',ls='--',label='frozen tolerance')
 ax.set(xticks=range(4),xticklabels=['correct','reload','close swap','distant swap'],yscale='log',ylabel='standardized RMS (zeros drawn at 1e-8)',title=split);ax.legend()
fig.savefig(P/'distances.png',dpi=160);plt.close(fig)
fig,ax=plt.subplots(figsize=(8,4),layout='constrained')
labels=['correct FR','reload FR','close FA','distant FA'];h=score['heldout'];counts=[h[k]['false_rejections'] if k in ['correct','reload'] else h[k]['false_acceptances'] for k in ['correct','reload','close','distant']]
ax.bar(labels,counts);ax.set(ylim=(0,max(1,max(counts)+1)),ylabel='observed errors',title='Held-out errors; correlated samples, one GPU')
for i,k in enumerate(['correct','reload','close','distant']):ax.text(i,counts[i]+.03,f"{counts[i]}/{h[k]['n']}",ha='center')
fig.savefig(P/'errors.png',dpi=160);plt.close(fig)
print(json.dumps(summary,indent=2))
