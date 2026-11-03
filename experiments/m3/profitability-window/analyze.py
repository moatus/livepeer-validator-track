"""Exploratory all-pool extension of reviewed EX-05; no source/repo mutation.

Run from repository root: python3 experiments/m3/profitability-window/analyze.py
Every actor is evaluated independently, holding the other 99 pools fixed.
"""
import csv
import importlib.util
import json
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('ex05', ROOT/'experiments/m2/october-reconciliation/build.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
snapshot, observed, pools = engine.inputs()
F = observed['fees_usd_indexed']
E = observed['scheduled_mint_ceiling_lpt']
P = D(snapshot['prices']['lpt_usd_spot'])
V = D('.94') * E * P
S = sum(p['stake_lpt'] for p in pools)
baseline, _ = engine.account(pools, E, P)
baseline = {r['address']: r for r in baseline}
rows = []
for rank, p in enumerate(sorted(pools, key=lambda p: (-p['stake_lpt'], p['address'])), 1):
    a, s = p['fee_usdc']/F, p['stake_lpt']/S
    t, z = engine.retention(p['reward_cut'], p['delegator_fee_share'], p['own_fraction'])
    L = 1-D('.5')*z+D('.3')
    cap = max(D(0), (s*F-p['fee_usdc'])/(1-s))
    gain_rate = V*t*(1-a)/F if a < s else D(0)
    optimum = max(D(0), min(cap, (V*t*(F-p['fee_usdc'])/L).sqrt()-F))
    def profit(x):
        return V*t*(min((p['fee_usdc']+x)/(F+x), s)-min(a, s))-L*x
    peak = profit(optimum)
    break_even = D(0)
    if peak > 0:
        uncapped_root = V*t*(1-a)/L-F
        break_even = uncapped_root if uncapped_root <= cap else V*t*(s-a)/L
        assert abs(profit(break_even)) < D('1e-18')
        assert profit(break_even+D('.001')) < 0
    for x in (D(1), optimum):
        changed, _ = engine.account(pools, E, P, additions={p['address']: x})
        after = next(r for r in changed if r['address'] == p['address'])
        ledger_delta = engine.job_delta(baseline[p['address']], after, D(1), x, D('.3'), P)
        assert abs(ledger_delta-profit(x)) < D('1e-18'), (rank, x)
    assert (gain_rate > L) == (peak > 0)
    rows.append(dict(rank=rank, fee_share=a, stake_share=s, reward_retention=t,
                     node_fee_retention=z, leakage_per_invoice=L, marginal_reward_value=gain_rate,
                     headroom=s> a, marginally_profitable=gain_rate > L,
                     cap_invoice_usdc=cap, optimum_invoice_usdc=optimum,
                     peak_value_usdc=peak, break_even_invoice_usdc=break_even,
                     one_dollar_value_usdc=profit(D(1))))

# Reconcile all ten published standalone interventions, without changing outputs.
with (ROOT/'experiments/m2/october-reconciliation/generated/top-ten-standalone.csv').open() as f:
    old = list(csv.DictReader(f))
for r, prior in zip(rows[:10], old):
    assert r['rank'] == int(prior['round_stake_rank'])
    assert abs(r['one_dollar_value_usdc']-D(prior['self_funded_delta_usdc'])) < D('1e-18')

def tally(predicate):
    group = [r for r in rows if predicate(r)]
    return dict(pools=len(group), stake_share=sum((r['stake_share'] for r in group), D(0)),
                fee_share=sum((r['fee_share'] for r in group), D(0)))

summary = dict(
    headroom=tally(lambda r: r['headroom']),
    profitable=tally(lambda r: r['marginally_profitable']),
    profitable_one_dollar=tally(lambda r: r['one_dollar_value_usdc']>0),
    zero_recorded_fees=tally(lambda r: r['fee_share']==0),
    profitable_with_positive_recorded_fees=tally(lambda r: r['fee_share']>0 and r['marginally_profitable']),
    peak_above={v: tally(lambda r: r['peak_value_usdc']>D(v)) for v in ['1', '5', '10', '50', '100']},
    cost_sensitivity={c: sum(r['headroom'] and r['marginal_reward_value']>1-D('.5')*r['node_fee_retention']+D(c) for r in rows) for c in ['0','.3','1','3']},
)
report = dict(
    status='Exploratory extension calculated 2026-11-02; not an accepted M2 finding or live prevalence estimate',
    snapshot_id=snapshot['snapshot_id'], snapshot_sha256=snapshot['integrity']['content_sha256'],
    round_id=observed['round_id'], start_utc=observed['start_utc'], end_utc_exclusive=observed['end_utc_exclusive'],
    fee_series='Raw ETH fee proportions; indexed USD total replayed 1:1 as hypothetical USDC',
    assumptions=dict(rule='October main-text non-normalized MFS; 94% node allowance; 50% node fee share',
                     calibration='E0 set to measured round 4364 ceiling at hypothetical launch r=0',
                     invoice_per_job='1', execution_cost_per_job='.30', score='1, unchanged from baseline',
                     setup_cost='0', price_usdc_per_lpt=str(P), ownership='Capture-time operator-address stake proxy and round cuts; not beneficial ownership',
                     constraints='No cash/capacity limit, fractional work allowed; all other pools fixed',
                     exclusions='No financing, execution risk, claim discount, price impact, beneficial-owner consolidation or opportunity cost'),
    F=F, E=E, V=V, node_allowance_to_fee_ratio=V/F,
    validation='200 standalone payoffs checked against EX-05 engine; all ten published interventions matched; positive break-even roots checked',
    summary=summary, rows=rows,
)
(OUT/'results.json').write_text(json.dumps(report, indent=2, default=str)+'\n')
with (OUT/'pools.csv').open('w') as f:
    writer=csv.DictWriter(f, fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
print(json.dumps(dict(validation=report['validation'], summary=summary), indent=2, default=str))
