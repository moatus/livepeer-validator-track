"""Diagnostic levers, not recommended settings or forecasts of participant response."""
import csv
import importlib.util
import json
from decimal import Decimal as D
from pathlib import Path
from statistics import median

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ex05',ROOT/'experiments/m2/october-reconciliation/build.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
snapshot,observed,pools=engine.inputs()
pools=sorted(pools,key=lambda p:(-p['stake_lpt'],p['address']))
F=observed['fees_usd_indexed'];E=observed['scheduled_mint_ceiling_lpt'];P=D(snapshot['prices']['lpt_usd_spot'])
S=sum(p['stake_lpt'] for p in pools)
configs=[
 ('Baseline','1','.5','1','0'),
 ('Node allowance -50%','.5','.5','1','0'),
 ('Node allowance -90%','.1','.5','1','0'),
 ('Network fee 75%','1','.75','1','0'),
 ('Network fee 100%','1','1','1','0'),
 ('Headroom reduced 90%','1','.5','.1','0'),
 ('Exact fee/stake alignment','1','.5','0','0'),
 ('50% chance of action-triggered reward denial','1','.5','1','.5'),
 ('90% chance of action-triggered reward denial','1','.5','1','.9'),
]
summaries=[];details=[];checks=0
for label,em,beta,alpha,q in configs:
 em,beta,alpha,q=map(D,(em,beta,alpha,q))
 ps=[]
 for p in pools:
  a=p['fee_usdc']/F;s=p['stake_lpt']/S
  ps.append(dict(p,stake_lpt=S*(a+alpha*(s-a))))
 assert abs(sum(p['stake_lpt'] for p in ps)-S)<D('1e-40')
 before,_=engine.account(ps,E*em,P)
 before={r['address']:r for r in before}
 gains=[];active_stake=D(0)
 for rank,p in enumerate(ps,1):
  a=p['fee_usdc']/F;s=p['stake_lpt']/S
  t,z=engine.retention(p['reward_cut'],p['delegator_fee_share'],p['own_fraction'])
  V=D('.94')*E*em*P;L=1-(1-beta)*z+D('.3')
  cap=max(D(0),(s-a)*F/(1-s)) if alpha else D(0)
  x=max(D(0),min(cap,(V*(1-q)*t*F*(1-a)/L).sqrt()-F))
  # No action incurs no penalty. Any positive action risks losing the entire
  # modeled earning-cohort node reward; honest no-action baseline scores 1.
  if x:
   value=(1-q)*V*t*min((a*F+x)/(F+x),s)-V*t*min(a,s)-L*x
  else:value=D(0)
  if value<=0:x=D(0);value=D(0)
  after,_=engine.account(ps,E*em,P,additions={p['address']:x})
  after=next(r for r in after if r['address']==p['address'])
  # Original engine checks both reward levels. Explicitly replace only its
  # hardcoded fee split, and apply the stated expected whole-cohort score.
  check=(after['operator_reward_lpt']*(1-q if x else 1)-before[p['address']]['operator_reward_lpt'])*P+(1-beta)*z*x-x-D('.3')*x
  assert abs(check-value)<D('1e-18'),(label,rank)
  checks+=1;gains.append(value)
  if value>0:active_stake+=s
  details.append(dict(case=label,rank=rank,optimum_invoice_usdc=x,peak_value_usdc=value))
 summaries.append(dict(case=label,allowance_factor=em,network_fee=beta,remaining_headroom_factor=alpha,denial_probability=q,
                       profitable_pools=sum(g>0 for g in gains),above_10_pools=sum(g>10 for g in gains),
                       median_peak_all_100=median(gains),active_stake_share=active_stake))
report=dict(status='Exploratory lever sensitivity; hypothetical extremes are not recommendations',
            snapshot_id=snapshot['snapshot_id'],snapshot_sha256=snapshot['integrity']['content_sha256'],round_id=4364,
            inherited_assumptions=json.loads((OUT.parent/'results.json').read_text())['assumptions'],
            headroom_definition='Artificially replace all stake shares with a+alpha*(s-a), conserving total stake. Retention fractions are held fixed to isolate cap geometry. No feasible delegation path, ownership reconstruction, migration cost or actual stake decision is modeled.',
            denial_definition='Conditional on a positive controlled purchase, probability q of score zero on the entire modeled earning-cohort node reward; otherwise score one. No-action baseline retains score one. No fee recovery, principal slash, future punishment or measured detection ability is assumed. Legitimate internal work has no automatic adverse judgment.',
            scope='All pools act independently. Costs .30 per $1 invoice, fixed price and fees, no cash or capacity cap, no setup cost. Node allowance reduction does not specify reallocation of foregone rewards.',
            validation=f'{checks} optima checked against original full-network reward ledger with explicit fee-split and action-contingent score adjustments',
            scenarios=summaries)
(OUT/'results.json').write_text(json.dumps(report,indent=2,default=str)+'\n')
with (OUT/'scenarios.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(summaries[0]));w.writeheader();w.writerows(summaries)
print(report['validation'])
for r in summaries:print(r['case'],r['profitable_pools'],r['above_10_pools'],round(r['median_peak_all_100'],3))
