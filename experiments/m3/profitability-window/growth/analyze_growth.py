"""Finite price/fee sensitivity of the prior exploratory profitability screen.

No equilibrium or demand forecast. Each actor acts independently. All results
use October main-text MFS with fixed stake, cuts, score, cost and ownership.
"""
import csv
import importlib.util
import json
from decimal import Decimal as D
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('ex05', ROOT/'experiments/m2/october-reconciliation/build.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
snapshot, observed, pools = engine.inputs()
pools = sorted(pools, key=lambda p: (-p['stake_lpt'], p['address']))
F0 = observed['fees_usd_indexed']
E = observed['scheduled_mint_ceiling_lpt']
P0 = D(snapshot['prices']['lpt_usd_spot'])
S = sum(p['stake_lpt'] for p in pools)
PRICE_FACTORS = ['0.5', '1', '1.5', '2', '4']
FEE_FACTORS = ['1', '1.5', '2', '4', '10']
MODES = ['proportional', 'stake_proportional_additions']
scenarios, details, checked = [], [], 0
for mode in MODES:
    for h_text in PRICE_FACTORS:
        h = D(h_text)
        for g_text in FEE_FACTORS:
            g = D(g_text)
            ps = [dict(p, fee_usdc=p['fee_usdc']*g if mode=='proportional' else
                       p['fee_usdc']+(g-1)*F0*p['stake_lpt']/S) for p in pools]
            F = sum(p['fee_usdc'] for p in ps)
            assert abs(F-g*F0) < D('1e-45')
            P, V = P0*h, D('.94')*E*P0*h
            base, _ = engine.account(ps, E, P)
            base = {r['address']: r for r in base}
            rows = []
            for rank, p in enumerate(ps, 1):
                a, s = p['fee_usdc']/F, p['stake_lpt']/S
                t, z = engine.retention(p['reward_cut'], p['delegator_fee_share'], p['own_fraction'])
                L = 1-D('.5')*z+D('.3')
                cap = max(D(0), (s*F-p['fee_usdc'])/(1-s))
                incentive = V*t*(1-a)/(F*L) if a<s else D(0)
                star = max(D(0), min(cap, (V*t*(F-p['fee_usdc'])/L).sqrt()-F))
                def profit(x):
                    return V*t*(min((p['fee_usdc']+x)/(F+x),s)-min(a,s))-L*x
                peak = profit(star)
                # Full 100-pool ledger check of every selected optimum.
                changed, _ = engine.account(ps, E, P, additions={p['address']:star})
                after = next(r for r in changed if r['address']==p['address'])
                actual = engine.job_delta(base[p['address']], after, D(1), star, D('.3'), P)
                assert abs(actual-peak)<D('1e-18'), (mode,h,g,rank)
                assert (incentive>1)==(peak>0)
                checked += 1
                root = D(0)
                if peak>0:
                    raw_root = V*t*(1-a)/L-F
                    root = raw_root if raw_root<=cap else V*t*(s-a)/L
                    assert abs(profit(root))<D('1e-18')
                row = dict(mode=mode,price_factor=h_text,fee_factor=g_text,rank=rank,
                           stake_share=s,fee_share=a,incentive_ratio=incentive,
                           cap_invoice_usdc=cap,optimum_invoice_usdc=star,
                           peak_value_usdc=peak,break_even_invoice_usdc=root)
                rows.append(row)
                details.append(row)
            positive = [r for r in rows if r['peak_value_usdc']>0]
            scenarios.append(dict(mode=mode,price_factor=h_text,fee_factor=g_text,
                                  price_usdc_per_lpt=P,fees_usdc=F,
                                  allowance_value_to_fees=V/F,
                                  profitable_pools=len(positive),
                                  profitable_stake_share=sum((r['stake_share'] for r in positive),D(0)),
                                  above_10_pools=sum(r['peak_value_usdc']>10 for r in rows),
                                  median_peak_all_100=median(r['peak_value_usdc'] for r in rows),
                                  rank1=rows[0]))

lookup={(r['mode'],r['price_factor'],r['fee_factor'],r['rank']):r for r in details}
prior=json.loads((OUT.parent/'results.json').read_text())
for rank, old in enumerate(prior['rows'],1):
    b=lookup['proportional','1','1',rank]
    assert abs(b['peak_value_usdc']-D(old['peak_value_usdc']))<D('1e-18')
    for scale in ['1.5','2','4']:
        same=lookup['proportional',scale,scale,rank]
        for key in ['optimum_invoice_usdc','peak_value_usdc','break_even_invoice_usdc']:
            assert abs(same[key]-D(scale)*b[key])<D('1e-18'),(rank,scale,key)
        assert abs(same['incentive_ratio']-b['incentive_ratio'])<D('1e-18')

report=dict(status='Exploratory 2026-11-02 sensitivity; not accepted M2 research or measured prevalence',
            snapshot_id=snapshot['snapshot_id'],snapshot_sha256=snapshot['integrity']['content_sha256'],
            round_id=observed['round_id'],start_utc=observed['start_utc'],end_utc_exclusive=observed['end_utc_exclusive'],
            F0=F0,P0=P0,E0=E,price_factors=PRICE_FACTORS,fee_factors=FEE_FACTORS,
            assumptions=prior['assumptions'],
            growth_definitions=dict(proportional='Scale all baseline fees by g; preserve each fee share.',
                stake_proportional_additions='Keep baseline fees; allocate only the added (g-1)*F0 across pools by fixed stake shares. This is a diagnostic allocation, not a routing recommendation.'),
            interpretation='Hypothetical external-fee growth; baseline receipts do not establish independent demand. Traffic growth changes this model only through paid fee value or explicitly changed costs. Current fees are the chosen scenario floor, not a proven future lower bound.',
            validation=dict(independent_engine_optima=checked,baseline_reconciled=100,
                equal_growth_scaling='300 per-pool cases agree on invariant incentive ratios and proportionally scaled optimal spend, peak value and break-even spend'),
            scenarios=scenarios)
(OUT/'results.json').write_text(json.dumps(report,indent=2,default=str)+'\n')
with (OUT/'pool-scenarios.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(details[0]));w.writeheader();w.writerows(details)
with (OUT/'scenarios.csv').open('w') as f:
    summary=[{k:v for k,v in s.items() if k!='rank1'} for s in scenarios]
    w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
print(json.dumps(report['validation']))
for s in scenarios:
    if s['price_factor'] in ['1','1.5','2']:
        print(s['mode'],s['price_factor'],s['fee_factor'],s['profitable_pools'],s['above_10_pools'],round(s['median_peak_all_100'],2))
