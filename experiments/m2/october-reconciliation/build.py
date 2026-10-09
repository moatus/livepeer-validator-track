#!/usr/bin/env python3
"""EX-05: bounded October reconciliation, Decimal accounting, no network calls."""
from decimal import Decimal as D, getcontext
import csv
import hashlib
import importlib.util
from pathlib import Path

getcontext().prec = 60
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE_SHA = '3e4a385ec19837f4b506b01989fac62cc33f99f28411bc1258f10c065e29240e'
spec = importlib.util.spec_from_file_location('snapshot', HERE.parent / 'network-snapshot/read_snapshot.py')
snapshot_reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot_reader)
ZERO, ONE = D(0), D(1)
NODE, VALIDATOR, TREASURY = D('.94'), D('.01'), D('.05')
NODE_FEE_CUT = D('.5')


def retention(reward_cut, delegator_fee_share, own_fraction):
    """Operator commission plus its own address's pro-rata delegator receipts."""
    for value in (reward_cut, delegator_fee_share, own_fraction):
        if not ZERO <= value <= ONE:
            raise ValueError('Invalid cut/ownership fraction')
    return (reward_cut + (ONE-reward_cut)*own_fraction,
            ONE-delegator_fee_share + delegator_fee_share*own_fraction)


def account(pools, ceiling, lpt_price, fee_scale=ONE, additions=None):
    """Recompute every pool against network denominators; full scores only."""
    if ceiling < 0 or lpt_price <= 0 or fee_scale <= 0 or not pools:
        raise ValueError('Positive price, fee scale and population required')
    additions = additions or {}
    if set(additions) - {p['address'] for p in pools} or any(x < 0 for x in additions.values()):
        raise ValueError('Invalid added payment')
    fees = {p['address']: p['fee_usdc']*fee_scale+additions.get(p['address'], ZERO) for p in pools}
    total_fees = sum(fees.values(), ZERO)
    total_stake = sum((p['stake_lpt'] for p in pools), ZERO)
    if total_fees <= 0 or total_stake <= 0:
        raise ValueError('Zero denominator requires a rule')
    rows = []
    for p in pools:
        f, s = fees[p['address']]/total_fees, p['stake_lpt']/total_stake
        mfs = min(f, s)
        reward = ceiling*NODE*mfs
        reward_retention, fee_retention = retention(p['reward_cut'], p['delegator_fee_share'], p['own_fraction'])
        node_fee = fees[p['address']]*NODE_FEE_CUT
        rows.append(dict(address=p['address'], fee_usdc=fees[p['address']], fee_share=f,
                         stake_share=s, mfs=mfs, node_reward_lpt=reward,
                         operator_reward_lpt=reward*reward_retention,
                         other_addresses_reward_lpt=reward*(ONE-reward_retention),
                         operator_fee_usdc=node_fee*fee_retention,
                         other_addresses_fee_usdc=node_fee*(ONE-fee_retention)))
    node_minted = sum((r['node_reward_lpt'] for r in rows), ZERO)
    summary = dict(fees_usdc=total_fees, scheduled_ceiling_lpt=ceiling,
                   mfs_sum=sum((r['mfs'] for r in rows), ZERO), node_minted_lpt=node_minted,
                   validator_minted_lpt=ceiling*VALIDATOR, treasury_minted_lpt=ceiling*TREASURY,
                   total_minted_lpt=node_minted+ceiling*(VALIDATOR+TREASURY),
                   unused_node_unminted_lpt=ceiling*NODE-node_minted,
                   burn_funding_usdc=total_fees*(ONE-NODE_FEE_CUT),
                   burned_lpt=total_fees*(ONE-NODE_FEE_CUT)/lpt_price)
    return rows, summary


def job_delta(before, after, invoice, jobs, cost_per_job, lpt_price, self_funded=True):
    """USD≈USDC assumption; LPT is valued only at this explicit price."""
    if jobs < 0 or invoice < 0 or cost_per_job < 0 or lpt_price <= 0:
        raise ValueError('Invalid job input')
    return (after['operator_fee_usdc']-before['operator_fee_usdc']
            +(after['operator_reward_lpt']-before['operator_reward_lpt'])*lpt_price
            -(invoice*jobs if self_funded else ZERO)-cost_per_job*jobs)


def inputs():
    if hashlib.sha256((ROOT/'docs/litepaper-2.0.md').read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError('October source changed; review citations')
    snapshot = snapshot_reader.load_snapshot()
    observed = snapshot_reader.round_inputs(snapshot, 4364)
    operators = {o['address']: o for o in snapshot['orchestrators']}
    pools = []
    for p in observed['pools']:
        o = operators[p['address']]
        pools.append(dict(address=p['address'], fee_usdc=p['fees_eth']/observed['fees_eth']*observed['fees_usd_indexed'],
                          stake_lpt=p['stake_lpt'], reward_cut=p['operator_reward_cut_fraction'],
                          delegator_fee_share=p['delegator_fee_share_fraction'],
                          own_fraction=D(o['operator_address_fraction_of_own_pool'])))
    # Do not silently renormalize an incomplete subset.
    if abs(sum((p['stake_lpt'] for p in pools), ZERO)-observed['active_stake_lpt']) > D('1e-18'):
        raise ValueError('Pool stake does not exhaust network denominator')
    if abs(sum((p['fees_eth'] for p in observed['pools']), ZERO)-observed['fees_eth']) > D('1e-18'):
        raise ValueError('Pool fees do not exhaust network denominator')
    return snapshot, observed, pools


def csv_write(path, rows):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build():
    snapshot, observed, pools = inputs()
    ceiling, price = observed['scheduled_mint_ceiling_lpt'], D(snapshot['prices']['lpt_usd_spot'])
    baseline, summary = account(pools, ceiling, price)
    _, compressed = account(pools, ceiling, price, D('.5'))
    top = sorted(pools, key=lambda p: (-p['stake_lpt'], p['address']))[:10]
    base_lookup = {r['address']: r for r in baseline}
    scenarios = []
    for rank, p in enumerate(top, 1):
        invoice, jobs, cost = D('1'), ONE, D('.30')
        changed, totals = account(pools, ceiling, price, additions={p['address']:invoice*jobs})
        after = next(r for r in changed if r['address']==p['address'])
        before = base_lookup[p['address']]
        net = job_delta(before, after, invoice, jobs, cost, price)
        scenarios.append(dict(round_stake_rank=rank, address=p['address'], invoice_usdc_per_job=invoice,
                              job_count=jobs, execution_cost_usdc_per_job=cost,
                              operator_address_own_fraction=p['own_fraction'],
                              reward_cut=p['reward_cut'], delegator_fee_share=p['delegator_fee_share'],
                              added_operator_fee_usdc=after['operator_fee_usdc']-before['operator_fee_usdc'],
                              self_funded_outlay_usdc=invoice*jobs, execution_cost_usdc=cost*jobs,
                              added_operator_reward_lpt=after['operator_reward_lpt']-before['operator_reward_lpt'],
                              added_operator_reward_value_usdc=(after['operator_reward_lpt']-before['operator_reward_lpt'])*price,
                              self_funded_cash_only_delta_usdc=after['operator_fee_usdc']-before['operator_fee_usdc']-invoice*jobs-cost*jobs,
                              self_funded_delta_usdc=net,
                              external_customer_delta_usdc=job_delta(before, after, invoice, jobs, cost, price, False),
                              max_cost_usdc_for_self_funded_break_even=net+cost,
                              preferred_of_one_job_or_none='one job' if net>0 else 'none',
                              network_mint_delta_lpt=totals['total_minted_lpt']-summary['total_minted_lpt'],
                              other_pools_reward_delta_lpt=sum((r['node_reward_lpt'] for r in changed if r['address']!=p['address']),ZERO)-sum((r['node_reward_lpt'] for r in baseline if r['address']!=p['address']),ZERO)))
    out=HERE/'generated'; out.mkdir(exist_ok=True)
    csv_write(out/'baseline-pools.csv', baseline)
    csv_write(out/'network-cases.csv', [dict(case='baseline',**summary),dict(case='half-price-constant-shares',**compressed)])
    csv_write(out/'top-ten-standalone.csv', scenarios)
    lines=['# October Slice 1 reconciliation — generated results','',
           '**Illustrative October accounting using observed round 4364 inputs; not observed October behavior.**','',
           'Mint totals attribute eventual issuance to this round: all eligible nodes are assumed to claim at n+7 with score 1 unchanged. They are not immediate round-n mint observations; the separate 6% validator/treasury allocation is included on the same cohort basis.','',
           f"Snapshot `{snapshot['snapshot_id']}`, content SHA-256 `{snapshot['integrity']['content_sha256']}`.",'',
           '| Network quantity | Baseline | 50% uniform fee compression |','| --- | ---: | ---: |']
    for key in summary:
        lines.append(f'| {key} | {summary[key]:.6f} | {compressed[key]:.6f} |')
    lines += ['', 'The compression case fixes stake, scores, jobs, execution costs and LPT price. It changes gross prices only; no routing or demand response is inferred.', '',
              '| Stake rank | Operator address | $1 outside-customer job: valued return USDC | $1 self-funded job: valued return USDC | Break-even execution cost USDC/job |','| --- | --- | ---: | ---: | ---: |']
    for r in scenarios:
        lines.append(f"| {r['round_stake_rank']} | `{r['address']}` | {r['external_customer_delta_usdc']:.6f} | {r['self_funded_delta_usdc']:.6f} | {r['max_cost_usdc_for_self_funded_break_even']:.6f} |")
    positives=sum(r['self_funded_delta_usdc']>0 for r in scenarios)
    lines += ['',f'{positives}/10 independent one-job comparisons have positive modeled incremental operator-address return valued in USDC at $0.30/job execution cost. These alternatives cannot be added together: each holds every other pool fixed. Negative break-even costs mean no nonnegative execution cost makes that self-payment profitable.', '',
              'Outside-customer case is a cooperative comparison, not evidence that recorded demand is independent. A legitimate internal job has the same accounting as a self-funded reward-motivated job; its internal utility is unmeasured and excluded. Neither a positive valued-return result nor common ownership proves misconduct.', '',
              'See the README for assumptions, source conflicts, ownership limitations and the Slice 2 boundary.']
    (out/'results.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))
    return baseline, summary, compressed, scenarios


if __name__=='__main__':
    build()
