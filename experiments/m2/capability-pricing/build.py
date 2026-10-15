#!/usr/bin/env python3
"""EX-06: finite connected October accounting; Python standard library only."""
from copy import deepcopy
import csv
from decimal import Decimal as D, getcontext
import hashlib
import importlib.util
import json
from pathlib import Path

getcontext().prec = 60
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ZERO, ONE = D(0), D(1)
EPS = D('1e-18')
PINNED = {
    'inputs.json': 'bf518c99987c042821438b4ceea3689aae2122dd7956032b7a1efe2b03b8524f',
    'scenarios.json': '7bf3f949d45570387674efe08f29f4ef47b8f7a7121f2ad9f606147d40a81aa5',
}
BRIDGE_SHA = '1b5f472cf255104bb4b1216cb48c947502f010023dc8bddc92752a9a3ac3c695'
READER_SHA = '56fbc40ddfd61a424c1cfe5e34e7a8418ff9146d3cc79f4b8ba8f00286373777'


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_inputs():
    for name, digest in PINNED.items():
        if hashlib.sha256((HERE/name).read_bytes()).hexdigest() != digest:
            raise ValueError('Frozen configuration changed: '+name)
    manifest = json.loads((HERE/'inputs.json').read_text())
    config = {k: v['value'] for k, v in manifest['inputs'].items()}
    grid = json.loads((HERE/'scenarios.json').read_text())
    for key, path in [('october_text_sha256', 'docs/litepaper-2.0.md'),
                      ('october_pdf_sha256', 'docs/sources/litepaper-2026-10.pdf')]:
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != config[key]:
            raise ValueError('October source changed: '+key)
    bridge_path = HERE.parent/'october-reconciliation/build.py'
    if hashlib.sha256(bridge_path.read_bytes()).hexdigest() != BRIDGE_SHA:
        raise ValueError('EX-05 source contract changed')
    bridge = load_module('ex05_bridge', bridge_path)
    reader_path = HERE.parent/'network-snapshot/read_snapshot.py'
    if hashlib.sha256(reader_path.read_bytes()).hexdigest() != READER_SHA:
        raise ValueError('Snapshot reader source contract changed')
    reader = load_module('ex06_reader', reader_path)
    snapshot = reader.load_snapshot(expected_id=config['snapshot_id'],
                                    expected_sha256=config['snapshot_content_sha256'])
    observed = reader.round_inputs(snapshot, config['matched_round'])
    window = config['observation_window']
    assert (observed['start_utc'], observed['end_utc_exclusive']) == (window['start_utc'], window['end_utc_exclusive'])
    # Explicit sibling interface check: no bridge-generated tables are loaded.
    _, bridge_round, bridge_pools = bridge.inputs()
    assert bridge_round['round_id'] == observed['round_id']
    base = []
    for i, p in enumerate(observed['pools']):
        link = config[f'pool_{i:02d}_proxy_link']
        assert link['pool_index'] == i
        operator = snapshot['orchestrators'][link['operator_index']]
        assert operator['address'] == p['address']
        fee = p['fees_eth']/observed['fees_eth']*observed['fees_usd_indexed']
        own = D(operator['operator_address_fraction_of_own_pool'])
        assert bridge.retention(p['operator_reward_cut_fraction'], p['delegator_fee_share_fraction'], own) == retention(p['operator_reward_cut_fraction'], p['delegator_fee_share_fraction'], own)
        base.append(dict(address=p['address'], stake=p['stake_lpt'], k=p['operator_reward_cut_fraction'],
                         d=p['delegator_fee_share_fraction'], w=own, score=D(config['baseline_score']),
                         claim_at=int(config['earliest_claim']),
                         caps={'generic': dict(q_out=fee/D(config['generic_price']), q_self=ZERO,
                              p=D(config['generic_price']), c=D(config['generic_unit_cost']),
                              setup=D(config['generic_setup_cost']), u=ZERO,
                              capacity=D(config['generic_capacity']))}))
    assert len(base) == len(bridge_pools) == 100
    assert abs(sum((p['stake'] for p in base), ZERO)-observed['active_stake_lpt']) <= D('1e-18')
    assert abs(sum((p['fees_eth'] for p in observed['pools']), ZERO)-observed['fees_eth']) <= D('1e-18')
    for p, bp in zip(base, bridge_pools):
        assert p['address'] == bp['address'] and p['caps']['generic']['q_out']*D(config['generic_price']) == bp['fee_usdc']
    return config, grid, observed, base, bridge


def retention(k, d, w):
    if any(not ZERO <= x <= ONE for x in (k, d, w)):
        raise ValueError('Invalid retention input')
    return k+(ONE-k)*w, ONE-d+d*w


def account(pools, ceiling, valuation, burn_price, horizon=7, reading='mfs',
            node=D('.94'), validator=D('.01'), treasury=D('.05'), node_fee=D('.5')):
    """Entitlement, timing and receipts; no output tables used as inputs."""
    if not pools or ceiling < 0 or valuation <= 0 or burn_price <= 0:
        raise ValueError('Invalid accounting input')
    fees = [sum((c['p']*(c['q_out']+c['q_self']) for c in p['caps'].values()), ZERO) for p in pools]
    total_fees, total_stake = sum(fees, ZERO), sum((p['stake'] for p in pools), ZERO)
    if total_stake <= 0 or any(f < 0 for f in fees):
        raise ValueError('Invalid denominator')
    if reading == 'appendix' and total_fees == 0:
        raise ValueError('Undefined appendix normalization at zero fees')
    if reading not in ('mfs', 'appendix') or (reading == 'appendix' and any(p['score'] != ONE for p in pools)):
        raise ValueError('Unsupported entitlement reading')
    rows = []
    for p, fee in zip(pools, fees):
        if not ZERO <= p['score'] <= ONE:
            raise ValueError('Score outside bounds')
        fs = fee/total_fees if total_fees else ZERO
        ss = p['stake']/total_stake
        weight = min(fs, ss) if reading == 'mfs' else fs
        before_score = ceiling*node*weight
        claimable = before_score*p['score']
        minted = claimable if p['claim_at'] is not None and p['claim_at'] <= horizon else ZERO
        r = dict(fees_usdc=fee, fee_share=fs, stake_share=ss,
                 pre_score_lpt=before_score, claimable_lpt=claimable, minted_lpt=minted,
                 score_withheld_lpt=before_score-claimable, pending_lpt=claimable-minted)
        for cap in ('generic', 'niche'):
            c = p['caps'].get(cap, dict(q_out=ZERO, q_self=ZERO, p=ZERO, c=ZERO, setup=ZERO, u=ZERO, capacity=ZERO))
            if any(c[key] < 0 for key in ('q_out', 'q_self', 'p', 'c', 'setup', 'u')) or c['q_out']+c['q_self'] > c['capacity']:
                raise ValueError('Invalid capacity/job input')
            for key in ('q_out', 'q_self', 'p', 'c', 'setup', 'capacity'):
                r[f'{cap}_{key}'] = c[key]
        r['outside_spending_usdc'] = sum((c['p']*c['q_out'] for c in p['caps'].values()), ZERO)
        r['controlled_spending_usdc'] = sum((c['p']*c['q_self'] for c in p['caps'].values()), ZERO)
        r['execution_cost_usdc'] = sum((c['c']*(c['q_out']+c['q_self']) for c in p['caps'].values()), ZERO)
        r['setup_cost_usdc'] = sum((c['setup'] for c in p['caps'].values()), ZERO)
        r['internal_use_value_usdc_equivalent'] = sum((c['u']*c['q_self'] for c in p['caps'].values()), ZERO)
        r['ownership_fraction'], r['reward_cut'], r['delegator_fee_share'] = p['w'], p['k'], p['d']
        nf = fee*node_fee
        r.update(operator_commission_fee_usdc=nf*(ONE-p['d']),
                 owned_delegator_fee_usdc=nf*p['d']*p['w'],
                 outside_delegator_fee_usdc=nf*p['d']*(ONE-p['w']),
                 operator_commission_lpt=minted*p['k'],
                 owned_delegator_lpt=minted*(ONE-p['k'])*p['w'],
                 outside_delegator_lpt=minted*(ONE-p['k'])*(ONE-p['w']))
        r['organization_retained_fee_usdc'] = r['operator_commission_fee_usdc']+r['owned_delegator_fee_usdc']
        r['organization_retained_lpt'] = r['operator_commission_lpt']+r['owned_delegator_lpt']
        rr, _ = retention(p['k'], p['d'], p['w'])
        r['organization_pending_lpt'] = r['pending_lpt']*rr
        r['organization_pending_value_usdc_equivalent'] = r['organization_pending_lpt']*valuation
        r['organization_net_cash_usdc_after_controlled_outflows_and_costs'] = r['organization_retained_fee_usdc']-r['controlled_spending_usdc']-r['execution_cost_usdc']-r['setup_cost_usdc']
        r['received_lpt_value_usdc_equivalent'] = r['organization_retained_lpt']*valuation
        r['organization_net_value_usdc_equivalent_at_declared_lpt_price'] = r['organization_net_cash_usdc_after_controlled_outflows_and_costs']+r['received_lpt_value_usdc_equivalent']+r['internal_use_value_usdc_equivalent']
        rows.append(r)
    summation = lambda key: sum((r[key] for r in rows), ZERO)
    summary = dict(network_fees_usdc=total_fees, network_stake_lpt=total_stake,
                   outside_spending_usdc=summation('outside_spending_usdc'),
                   controlled_spending_usdc=summation('controlled_spending_usdc'),
                   buyback_spending_usdc=total_fees*(ONE-node_fee), burn_execution_price_usdc_per_lpt=burn_price,
                   lpt_valuation_price_usdc_per_lpt=valuation, tokens_burned_lpt=total_fees*(ONE-node_fee)/burn_price,
                   scheduled_ceiling_lpt=ceiling, mfs_pre_score_node_entitlement_lpt=summation('pre_score_lpt'),
                   claimable_node_lpt_at_horizon=summation('claimable_lpt'), node_actually_minted_lpt_at_horizon=summation('minted_lpt'),
                   mfs_unallocated_never_minted_lpt=ceiling*node-summation('pre_score_lpt'),
                   score_withheld_unminted_lpt=summation('score_withheld_lpt'), pending_unclaimed_node_lpt=summation('pending_lpt'),
                   validator_full_mint_lpt=ceiling*validator, treasury_full_mint_lpt=ceiling*treasury)
    summary['total_actual_mint_lpt'] = summary['node_actually_minted_lpt_at_horizon']+ceiling*(validator+treasury)
    summary['net_supply_change_lpt_after_burn'] = summary['total_actual_mint_lpt']-summary['tokens_burned_lpt']
    for cap in ('generic', 'niche'):
        for kind in ('q_out', 'q_self'):
            summary[f'{cap}_{kind}'] = summation(f'{cap}_{kind}')
    return rows, summary


def main_states(config, grid, base):
    """Adapter for the hash-pinned natural-language configuration, not a history."""
    states = {}
    for case in grid['main']:
        sid = case['id']
        pools = deepcopy(states[case['parent']] if case['parent'] else base)
        selected = {alias: next(p for p in pools if p['address'] == address)
                    for alias, address in config['selected_operators'].items()}
        a, b = selected['A'], selected['B']
        ag, bg = a['caps']['generic'], b['caps']['generic']
        changes = {k: v['value'] for k, v in case['changes'].items()}
        if sid == 'S01':
            ag['p'] = D(changes['A.generic.price'])
        elif sid == 'S02':
            moved = D(config['rerouting_fraction'])*bg['q_out']
            ag['q_out'] += moved; bg['q_out'] -= moved
        elif sid == 'S03':
            for p in pools:
                p['caps']['generic']['p'] = D(config['discount_price'])
        elif sid in ('S04', 'S05'):
            a['caps']['niche'] = dict(q_out=D(config['niche_outside_demand']) if sid == 'S04' else ZERO,
                q_self=D(config['niche_jobs']) if sid == 'S05' else ZERO, p=D(config['niche_price']),
                c=D(config['niche_unit_cost']), setup=D(config['niche_setup_cost']),
                capacity=D(config['niche_capacity']), u=D(config['internal_use_value']) if sid == 'S05' else ZERO)
        elif sid == 'S06':
            a['caps']['niche']['u'] = D(config['no_use_value'])
        elif sid == 'S07':
            ag['q_self'] = D(changes['A.generic.controlled_jobs'])
            ag['u'] = D(config['internal_use_value'])
        elif sid == 'S08':
            ag['u'] = D(config['no_use_value'])
        elif sid == 'S09':
            bg['q_out'] += D(config['controlled_added_jobs'])
        elif sid == 'S10':
            bg['q_self'] = D(config['controlled_added_jobs'])
        elif sid == 'S11':
            bg['p'] = D(changes['B.generic.price'])
            for alias in ('A', 'B'):
                selected[alias]['caps']['generic']['q_out'] = next(p for p in base if p['address'] == config['selected_operators'][alias])['caps']['generic']['q_out']
        elif sid != 'S00':
            raise ValueError('Unknown main case')
        states[sid] = pools
    return states


def evaluate(config, observed, pools, valuation=None, horizon=7, reading='mfs'):
    rows, network = account(pools, observed['scheduled_mint_ceiling_lpt'],
        D(config['lpt_valuation_price']) if valuation is None else valuation, D(config['burn_execution_price']), horizon, reading,
        *[D(config[k]) for k in ('node_emission_share', 'validator_emission_share', 'treasury_emission_share', 'node_fee_share')])
    assert all(r['controlled_spending_usdc'] <= D(config['self_funding_budget']) for r in rows)
    summary = dict(network)
    chosen = set(config['selected_operators'].values())
    for alias, address in config['selected_operators'].items():
        row = rows[next(i for i, p in enumerate(pools) if p['address'] == address)]
        summary.update({alias+'_'+k: v for k, v in row.items()})
    rest = [r for p, r in zip(pools, rows) if p['address'] not in chosen]
    assert len(rest) == 98
    # Aggregate additive amounts only; prices, ownership and fractions do not add.
    for key in rows[0]:
        if key.endswith(('usdc', 'lpt', 'usdc_equivalent', 'lpt_price', 'costs', 'q_out', 'q_self')):
            summary['other_98_'+key] = sum((r[key] for r in rest), ZERO)
    return summary, rows


def comparison(summary, parent, decline, actor):
    result = dict(summary)
    for label, reference in [('parent', parent), ('decline', decline)]:
        for key, value in summary.items():
            result[label+'_delta_'+key] = value-reference[key]
    cash_key = actor+'_organization_net_cash_usdc_after_controlled_outflows_and_costs'
    token_key = actor+'_organization_retained_lpt'
    value_key = actor+'_organization_net_value_usdc_equivalent_at_declared_lpt_price'
    cash, tokens = summary[cash_key]-decline[cash_key], summary[token_key]-decline[token_key]
    utility = summary[actor+'_internal_use_value_usdc_equivalent']-decline[actor+'_internal_use_value_usdc_equivalent']
    result['actor_decline_net_cash_delta_usdc'] = cash
    result['actor_decline_received_lpt_delta_lpt'] = tokens
    result['actor_decline_net_value_delta_usdc_equivalent'] = summary[value_key]-decline[value_key]
    result['actor_decline_value_sign'] = sign(result['actor_decline_net_value_delta_usdc_equivalent'])
    tied = abs(cash+utility) <= EPS and abs(tokens) <= EPS
    result['break_even_lpt_valuation_usdc_per_lpt'] = ('undefined' if tied else
        'no finite threshold' if abs(tokens) <= EPS else reachable_root(-(cash+utility)/tokens))
    q_added = sum((summary[f'{actor}_{cap}_q_self']-decline[f'{actor}_{cap}_q_self'] for cap in ('generic', 'niche')), ZERO)
    result['break_even_added_execution_cost_usdc_per_job'] = reachable_root((summary[value_key]-decline[value_key]+summary[actor+'_execution_cost_usdc']-decline[actor+'_execution_cost_usdc'])/q_added) if q_added else 'undefined'
    retained_fraction, _ = retention(summary[actor+'_reward_cut'], summary[actor+'_delegator_fee_share'], summary[actor+'_ownership_fraction'])
    potential = summary[actor+'_pre_score_lpt']*retained_fraction*summary['lpt_valuation_price_usdc_per_lpt']
    result['whole_round_median_break_even_against_decline'] = ('undefined' if tied else
        ('no finite threshold' if abs(cash+utility) > EPS else 'undefined') if abs(potential) <= EPS else
        reachable_root((decline[token_key]*summary['lpt_valuation_price_usdc_per_lpt']-cash-utility)/potential, ONE))
    f = summary['network_fees_usdc']
    rest_fees = f-summary[actor+'_fees_usdc']
    stake_share = summary[actor+'_stake_share']
    result['additional_gross_fees_to_stake_cap_usdc'] = 'undefined' if not f else max(ZERO, stake_share*rest_fees/(ONE-stake_share)-summary[actor+'_fees_usdc']) if stake_share < ONE else 'no finite threshold'
    result['appendix_normalization'] = 'defined' if f else 'undefined'
    return result


def reachable_root(root, upper=None):
    if root <= ZERO:
        return 'none (root ≤ 0)'
    if upper is not None and root > upper:
        return 'none (root > 1)'
    return root


def sign(value):
    return 'positive' if value > D('1e-12') else 'negative' if value < -D('1e-12') else 'zero'


def run():
    config, grid, observed, base, bridge = load_inputs()
    states = main_states(config, grid, base)
    evaluated = {sid: evaluate(config, observed, pools) for sid, pools in states.items()}
    main, sensitivities, audits = [], [], []
    declines = {'S04': 'S00', 'S05': 'S00', 'S06': 'S00', 'S07': 'S02', 'S08': 'S02', 'S09': 'S00', 'S10': 'S00'}
    for case in grid['main']:
        sid = case['id']; parent_id = case['parent'] or sid
        decline_id = declines.get(sid, parent_id)
        actor = 'B' if sid in ('S09', 'S10') else 'A'
        result = comparison(evaluated[sid][0], evaluated[parent_id][0], evaluated[decline_id][0], actor)
        main.append(dict(id=sid, title=case['title'], status='illustrative', actor=actor, parent=parent_id,
                         decline=decline_id, horizon='n+7', reading='mfs', source=case['source'],
                         changes=json.dumps(case['changes'], sort_keys=True, separators=(',', ':')),
                         legitimate_reference=case['legitimate_reference'], **result))
        audits.append((sid, states[sid], *evaluated[sid]))
    for group in grid['sensitivities']:
        gid = group['id']
        for sid in group['parents']:
            for level in group['levels']:
                value = level['value']
                horizons = (7, 14) if gid == 'T-claim' else (7,)
                for horizon in horizons:
                    pools = deepcopy(states[sid]); ref_id = 'S00' if gid in ('T-appendix', 'T-zero') else 'S03' if gid == 'T-redistribution' else 'S02'
                    reference = deepcopy(states[ref_id]); valuation = None; reading = 'mfs'
                    def selected(ps, alias='A'):
                        return next(p for p in ps if p['address'] == config['selected_operators'][alias])
                    a = selected(pools)
                    if gid in ('T-price', 'T-cost', 'T-ownership'):
                        for ps in (pools, reference):
                            p = selected(ps)
                            if gid == 'T-price': p['caps']['generic']['p'] = D(value)
                            elif gid == 'T-cost': p['caps']['generic']['c'] = D(value)
                            elif value == '1': p['w'] = ONE
                    elif gid == 'T-score': a['score'] = D(value)
                    elif gid == 'T-valuation': valuation = D(value)
                    elif gid == 'T-claim': a['claim_at'] = 7 if value == 'n+7' else 14 if value == 'n+14' else None
                    elif gid == 'T-appendix': reading = 'appendix' if value == 'normalized fee-work appendix' else 'mfs'
                    elif gid == 'T-zero':
                        for p in pools: p['caps']['generic']['p'] = D(value)
                    elif gid == 'T-redistribution' and value != 'original q0':
                        b = selected(pools, 'B'); moved = D('.10')*b['caps']['generic']['q_out']
                        a['caps']['generic']['q_out'] += moved; b['caps']['generic']['q_out'] -= moved
                    after, rows = evaluate(config, observed, pools, valuation, horizon, reading)
                    before, ref_rows = evaluate(config, observed, reference, valuation, horizon, reading)
                    actor = 'B' if gid == 'T-appendix' else 'A'
                    result = comparison(after, before, before, actor)
                    if reading == 'appendix':
                        result['additional_gross_fees_to_stake_cap_usdc'] = 'not applicable to appendix'
                        result['whole_round_median_break_even_against_decline'] = 'not varied under appendix'
                    result.update({'reference_'+k: v for k, v in before.items()})
                    ident = f'{gid}:{sid}:{value}:n+{horizon}'
                    sensitivities.append(dict(id=ident, group=gid, scenario=sid, level=value, actor=actor,
                        reference=ref_id, horizon=f'n+{horizon}', reading=reading, status='illustrative',
                        source=group['source'], reference_rule=config['sensitivity_reference_rule'], **result))
                    audits += [(ident, pools, after, rows), (ident+':reference', reference, before, ref_rows)]
    return config, grid, observed, main, sensitivities, audits, bridge


def csv_write(path, rows):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def build():
    config, grid, observed, main, sensitivities, _, _ = run()
    out = HERE/'generated'; out.mkdir(exist_ok=True)
    provenance = dict(snapshot_id=config['snapshot_id'], snapshot_content_sha256=config['snapshot_content_sha256'],
        round=config['matched_round'], window_start_utc=observed['start_utc'], window_end_exclusive_utc=observed['end_utc_exclusive'],
        fee_series=config['fee_series'], usd_usdc_replay=config['usd_usdc_replay'],
        job_unit=config['synthetic_job_unit'],
        quantity_units='q_out/q_self/capacity: job-equivalents; p/c: USDC/job-equivalent; setup: USDC; shares/cuts/ownership: fractions; monetary and token fields: suffix units',
        schedule_r=config['schedule_r'],
        schedule_half_life=config['schedule_half_life'], source_text_sha256=config['october_text_sha256'],
        source_pdf_sha256=config['october_pdf_sha256'], inputs_sha256=PINNED['inputs.json'], scenarios_sha256=PINNED['scenarios.json'],
        unmodeled_cost_slippage_boundary=config['burn_market_boundary'])
    csv_write(out/'scenarios.csv', [dict(**provenance, **r) for r in main])
    csv_write(out/'sensitivities.csv', [dict(**provenance, **r) for r in sensitivities])
    lines = ['# Connected capability, pricing and self-funded traffic accounting', '',
        'Illustrative accounting on measured round-4364 fee/stake scale; synthetic divisible job-equivalents. All 100 pools remain in every denominator.', '',
        config['selected_operators_note'], '',
        f"Snapshot `{config['snapshot_id']}`, content SHA-256 `{config['snapshot_content_sha256']}`; raw redeemed ETH series, {observed['start_utc']} to {observed['end_utc_exclusive']} exclusive. Indexed USD is replayed 1:1 as hypothetical USDC.", '',
        'The one-round ceiling is calibrated from the measured mint ceiling at hypothetical r=0; the deployed round number is not rounds since launch. Scores, routing, price, demand, capacity, costs, ownership application and claim timing are declared controls.', '',
        'Net cash deducts controlled invoice outflows, all execution costs and setup once. Net value adds received unsold LPT at the stated valuation and declared internal use; pending LPT is reported separately and excluded. Outside delegator receipts remain outside the organization.', '',
        '| Case | Parent / decline | Actor | Cash delta USDC | Received LPT delta | Use value USDC-equivalent | Net value delta USDC-equivalent | Other 98 mint delta LPT |',
        '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for r in main:
        lines.append(f"| {r['id']} {r['title']} | {r['parent']} / {r['decline']} | {r['actor']} | {r['actor_decline_net_cash_delta_usdc']:.6f} | {r['actor_decline_received_lpt_delta_lpt']:.6f} | {r[r['actor']+'_internal_use_value_usdc_equivalent']:.6f} | {r['actor_decline_net_value_delta_usdc_equivalent']:.6f} | {r['decline_delta_other_98_minted_lpt']:.6f} |")
    lines += ['', '| Case | Fees USDC | Buyback USDC | Burn LPT | Ceiling LPT | Claimable LPT | Node mint LPT | MFS unused LPT | Withheld LPT | Pending LPT | Validator LPT | Treasury LPT | Net supply LPT |', '| --- |'+ ' ---: |'*12]
    for r in main:
        keys = ('network_fees_usdc','buyback_spending_usdc','tokens_burned_lpt','scheduled_ceiling_lpt','claimable_node_lpt_at_horizon','node_actually_minted_lpt_at_horizon','mfs_unallocated_never_minted_lpt','score_withheld_unminted_lpt','pending_unclaimed_node_lpt','validator_full_mint_lpt','treasury_full_mint_lpt','net_supply_change_lpt_after_burn')
        lines.append('| '+r['id']+' | '+' | '.join(f'{r[k]:.6f}' for k in keys)+' |')
    lines += ['', '| Sensitivity | Actor cash delta USDC | Received LPT delta | Net value delta USDC-equivalent | Sign | Pending network LPT |', '| --- | ---: | ---: | ---: | --- | ---: |']
    for r in sensitivities:
        lines.append(f"| {r['id']} | {r['actor_decline_net_cash_delta_usdc']:.6f} | {r['actor_decline_received_lpt_delta_lpt']:.6f} | {r['actor_decline_net_value_delta_usdc_equivalent']:.6f} | {r['actor_decline_value_sign']} | {r['pending_unclaimed_node_lpt']:.6f} |")
    lines += ['', 'The CSVs carry the complete ledger, parent and decline deltas, reference states for sensitivities, price/cost/capacity, ownership/cuts, all selected receipts and the other 98 aggregate. Thresholds are algebraic conditional bounds, not additional simulated cases. Zero-fee MFS shares are zero by convention; appendix normalization is undefined there. A median of zero removes the whole earning-round reward. Pending does not expire; score-withheld non-minting is a declared interpretation.', '',
        'Useful and no-credited-use pairs differ in declared use value only. Positive returns, common control, low prices and a unique capability establish no misconduct. Actual discovery, demand, productive use, beneficial ownership, authorized score evidence and validator distribution are outside the accounting. Full-claim amounts attribute issuance to one cohort, not a common mint timestamp. No endogenous token price, liquidity, financing or claim-expiry effect is modeled.']
    (out/'accounting.md').write_text('\n'.join(lines)+'\n')
    print(f'Built {len(main)} main cases and {len(sensitivities)} sensitivity rows in 9 groups; all 100 pools retained.')
    return main, sensitivities


if __name__ == '__main__':
    build()
