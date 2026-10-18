#!/usr/bin/env python3
"""Independent constant fixtures plus connected-ledger invariants; no CSV inputs."""
from copy import deepcopy
from decimal import Decimal as D
from build import ZERO, ONE, account, retention, run, sign


def close(actual, expected, tolerance='1e-12'):
    assert abs(actual-D(expected)) <= D(tolerance), (actual, expected)


def fixture_pool(name, jobs, stake):
    return dict(address=name, stake=D(stake), k=D('.2'), d=D('.6'), w=D('.25'),
        score=ONE, claim_at=7, caps={'generic':dict(q_out=D(jobs), q_self=ZERO,
        p=ONE, c=D('.3'), setup=ZERO, u=ZERO, capacity=D(1000))})


def fixtures():
    # Hand constants: F=100, stake 50/50, E=1000, P=2. A reward=94,
    # B=470, retained fraction .4, fee retention .55. A costs 3.
    pools = [fixture_pool('A', 10, 50), fixture_pool('B', 90, 50)]
    rows, totals = account(pools, D(1000), D(2), D(2))
    for key, expected in {'node_actually_minted_lpt_at_horizon':'564',
        'mfs_unallocated_never_minted_lpt':'376', 'total_actual_mint_lpt':'624',
        'tokens_burned_lpt':'25', 'net_supply_change_lpt_after_burn':'599'}.items(): close(totals[key], expected)
    a = rows[0]
    for key, expected in {'operator_commission_fee_usdc':'2', 'owned_delegator_fee_usdc':'.75',
        'outside_delegator_fee_usdc':'2.25', 'operator_commission_lpt':'18.8',
        'owned_delegator_lpt':'18.8', 'outside_delegator_lpt':'56.4',
        'organization_retained_lpt':'37.6', 'organization_net_cash_usdc_after_controlled_outflows_and_costs':'-.25',
        'organization_net_value_usdc_equivalent_at_declared_lpt_price':'74.95'}.items(): close(a[key], expected)
    changed = deepcopy(pools); changed[0]['caps']['generic']['q_self'] = D(10)
    after, t = account(changed, D(1000), D(2), D(2))
    # A=940*20/110=170.90909; retained delta=.4*(170.90909-94).
    close(after[0]['pre_score_lpt'], '170.9090909090909090909090909090909')
    close(after[0]['organization_retained_lpt']-a['organization_retained_lpt'], '30.7636363636363636363636363636364')
    close(after[0]['organization_net_cash_usdc_after_controlled_outflows_and_costs']-a['organization_net_cash_usdc_after_controlled_outflows_and_costs'], '-10.25')
    close(after[0]['organization_net_value_usdc_equivalent_at_declared_lpt_price']-a['organization_net_value_usdc_equivalent_at_declared_lpt_price'], '51.2772727272727272727272727272727')
    close(t['total_actual_mint_lpt'], '700.9090909090909090909090909090909')
    close(t['tokens_burned_lpt'], '27.5')
    # Unrecovered invoice = network 5 + outside fee 2.25; execution 3.
    close(D(10)-(after[0]['organization_retained_fee_usdc']-a['organization_retained_fee_usdc']), '7.25')
    # Above-cap B: +10 controlled jobs, reward stays 470; cash/value=-10.25.
    above = deepcopy(pools); above[1]['caps']['generic']['q_self'] = D(10)
    br, _ = account(above, D(1000), D(2), D(2))
    close(br[1]['minted_lpt'], '470')
    close(br[1]['organization_net_value_usdc_equivalent_at_declared_lpt_price']-rows[1]['organization_net_value_usdc_equivalent_at_declared_lpt_price'], '-10.25')
    # Whole-round cut removes old and new reward, not just the increment.
    cut = deepcopy(changed); cut[0]['score'] = ZERO
    cr, ct = account(cut, D(1000), D(2), D(2))
    close(cr[0]['organization_retained_lpt'], '0'); close(ct['score_withheld_unminted_lpt'], '170.9090909090909090909090909090909')
    close(cr[0]['organization_net_value_usdc_equivalent_at_declared_lpt_price']-a['organization_net_value_usdc_equivalent_at_declared_lpt_price'], '-85.45')
    delayed = deepcopy(changed); delayed[0]['claim_at'] = 14
    dr, dt = account(delayed, D(1000), D(2), D(2), 7)
    close(dt['pending_unclaimed_node_lpt'], '170.9090909090909090909090909090909')
    close(dt['node_actually_minted_lpt_at_horizon'], '470')
    close(dr[0]['organization_pending_lpt'], '68.3636363636363636363636363636364')
    close(dr[0]['organization_retained_lpt'], '0')
    _, later = account(delayed, D(1000), D(2), D(2), 14)
    close(later['pending_unclaimed_node_lpt'], '0'); close(later['total_actual_mint_lpt'], '700.9090909090909090909090909090909')
    compressed = deepcopy(pools)
    for p in compressed: p['caps']['generic']['p'] = D('.5')
    rr, rt = account(compressed, D(1000), D(2), D(2))
    close(rt['node_actually_minted_lpt_at_horizon'], '564'); close(rt['tokens_burned_lpt'], '12.5')
    close(rr[0]['execution_cost_usdc'], '3')
    free = deepcopy(pools)
    for p in free: p['caps']['generic']['p'] = ZERO
    fr, ft = account(free, D(1000), D(2), D(2))
    close(ft['total_actual_mint_lpt'], '60'); close(ft['mfs_unallocated_never_minted_lpt'], '940')
    close(fr[0]['organization_net_cash_usdc_after_controlled_outflows_and_costs'], '-3')
    free_added = deepcopy(free); free_added[0]['caps']['generic']['q_self'] = D(10)
    far, _ = account(free_added, D(1000), D(2), D(2))
    close(far[0]['organization_net_value_usdc_equivalent_at_declared_lpt_price']-fr[0]['organization_net_value_usdc_equivalent_at_declared_lpt_price'], '-3')
    try: account(free, D(1000), D(2), D(2), reading='appendix')
    except ValueError as exc: assert 'Undefined' in str(exc)
    else: raise AssertionError('Zero appendix denominator accepted')
    _, at = account(pools, D(1000), D(2), D(2), reading='appendix')
    close(at['total_actual_mint_lpt'], '1000')
    ar, _ = account(above, D(1000), D(2), D(2), reading='appendix')
    # B normalized reward: 940*100/110 vs 940*.9; retained delta 3.41818.
    close(ar[1]['organization_retained_lpt']-D('338.4'), '3.4181818181818181818181818181818')
    close(ar[1]['organization_net_value_usdc_equivalent_at_declared_lpt_price']-(D('24.75')-D(27)+D('338.4')*2), '-3.4136363636363636363636363636364')
    assert retention(D('.2'), D('.6'), ONE) == (ONE, ONE)
    assert retention(ZERO, ONE, ZERO) == (ZERO, ZERO)


def invariants():
    config, grid, observed, main, sensitivities, audits, bridge = run()
    for ident, pools, s, rows in audits:
        assert len(pools) == len(rows) == 100, ident
        close(sum((p['stake'] for p in pools), ZERO), observed['active_stake_lpt'], '1e-18')
        close(sum((r['fees_usdc'] for r in rows), ZERO), s['network_fees_usdc'])
        close(sum((r['outside_spending_usdc']+r['controlled_spending_usdc'] for r in rows), ZERO), s['network_fees_usdc'])
        close(sum((r['fee_share'] for r in rows), ZERO), ONE if s['network_fees_usdc'] else ZERO)
        close(sum((r['stake_share'] for r in rows), ZERO), ONE)
        close(s['scheduled_ceiling_lpt'], s['node_actually_minted_lpt_at_horizon']+s['mfs_unallocated_never_minted_lpt']+s['score_withheld_unminted_lpt']+s['pending_unclaimed_node_lpt']+s['validator_full_mint_lpt']+s['treasury_full_mint_lpt'])
        close(s['claimable_node_lpt_at_horizon'], s['node_actually_minted_lpt_at_horizon']+s['pending_unclaimed_node_lpt'])
        close(s['buyback_spending_usdc'], s['tokens_burned_lpt']*s['burn_execution_price_usdc_per_lpt'])
        close(s['total_actual_mint_lpt']-s['tokens_burned_lpt'], s['net_supply_change_lpt_after_burn'])
        for p, r in zip(pools, rows):
            close(r['operator_commission_fee_usdc']+r['owned_delegator_fee_usdc']+r['outside_delegator_fee_usdc'], r['fees_usdc']/2)
            close(r['operator_commission_lpt']+r['owned_delegator_lpt']+r['outside_delegator_lpt'], r['minted_lpt'])
            close(r['organization_retained_fee_usdc']+r['outside_delegator_fee_usdc']+r['fees_usdc']/2, r['fees_usdc'])
            close(r['organization_retained_lpt']+r['outside_delegator_lpt'], r['minted_lpt'])
            close(r['organization_net_cash_usdc_after_controlled_outflows_and_costs'], r['organization_retained_fee_usdc']-r['controlled_spending_usdc']-r['execution_cost_usdc']-r['setup_cost_usdc'])
            close(r['organization_net_value_usdc_equivalent_at_declared_lpt_price'], r['organization_net_cash_usdc_after_controlled_outflows_and_costs']+r['organization_retained_lpt']*s['lpt_valuation_price_usdc_per_lpt']+r['internal_use_value_usdc_equivalent'])
            if p['score'] == ZERO: close(r['minted_lpt'], '0'); close(r['claimable_lpt'], '0')
        # Display aggregation conserves all recipients, including the other selected pool.
        for key in ('fees_usdc', 'minted_lpt', 'organization_retained_fee_usdc', 'outside_delegator_lpt'):
            close(s['A_'+key]+s['B_'+key]+s['other_98_'+key], sum((r[key] for r in rows), ZERO))
    m = {r['id']:r for r in main}
    assert len(main) == 12 and len(sensitivities) == 26
    assert {r['group'] for r in sensitivities} == {g['id'] for g in grid['sensitivities']}
    # Measured-scale sign lists and root constants below are regression pins,
    # not independent fixtures; fixtures() above retains the independent hand constants.
    main_signs = ['zero','negative','positive','negative','positive','positive','positive','positive','positive','positive','negative','negative']
    assert [r['actor_decline_value_sign'] for r in main] == main_signs
    close(m['S00']['generic_q_out'], m['S02']['generic_q_out'])
    close(m['S00']['generic_q_out'], m['S11']['generic_q_out'])
    for role in ('A', 'B'):
        close(m['S11'][role+'_generic_q_out'], m['S00'][role+'_generic_q_out'])
    close(m['S04']['network_fees_usdc']-m['S00']['network_fees_usdc'], '10')
    close(m['S08']['network_fees_usdc']-m['S02']['network_fees_usdc'], '5')
    for first, second in [('S05','S06'), ('S07','S08')]:
        for key in ('network_fees_usdc','node_actually_minted_lpt_at_horizon','A_organization_retained_fee_usdc','A_organization_retained_lpt','A_execution_cost_usdc','A_setup_cost_usdc'):
            close(m[first][key], m[second][key])
        close(m[first]['A_organization_net_value_usdc_equivalent_at_declared_lpt_price']-m[second]['A_organization_net_value_usdc_equivalent_at_declared_lpt_price'], '10')
    close(m['S10']['B_organization_retained_lpt'], m['S00']['B_organization_retained_lpt'])
    assert m['S10']['actor_decline_value_sign'] == 'negative'
    for key in ('node_actually_minted_lpt_at_horizon', 'mfs_unallocated_never_minted_lpt'):
        close(m['S03'][key], m['S00'][key])
    close(m['S03']['tokens_burned_lpt']*2, m['S00']['tokens_burned_lpt'])
    for r in sensitivities:
        assert r['actor_decline_value_sign'] == sign(r['actor_decline_net_value_delta_usdc_equivalent'])
        if r['group'] == 'T-price': close(r['A_generic_c'], '.30'); close(r['reference_A_generic_c'], '.30')
        if r['group'] == 'T-cost': close(r['A_generic_p'], '.5'); close(r['reference_A_generic_p'], '.5')
        if r['group'] == 'T-valuation': close(r['tokens_burned_lpt'], m['S08']['tokens_burned_lpt'])
        if r['group'] == 'T-claim' and r['pending_unclaimed_node_lpt']:
            close(r['A_organization_retained_lpt'], '0'); assert r['actor_decline_value_sign'] == 'negative'
        if r['group'] == 'T-ownership' and r['level'] == '1':
            close(r['A_outside_delegator_fee_usdc'], '0'); close(r['A_outside_delegator_lpt'], '0')
        if r['group'] == 'T-zero' and r['level'] == '0':
            assert r['appendix_normalization'] == 'undefined'
            close(r['node_actually_minted_lpt_at_horizon'], '0')
            close(r['tokens_burned_lpt'], '0')
            close(r['A_execution_cost_usdc'], m['S00']['A_execution_cost_usdc'])
        if r['group'] == 'T-redistribution':
            close(r['network_fees_usdc'], m['S03']['network_fees_usdc'])
            close(r['generic_q_out'], m['S03']['generic_q_out'])
            close(r['other_98_minted_lpt'], m['S03']['other_98_minted_lpt'])
    expected_signs = {
        'T-price':['positive']*3, 'T-cost':['positive']*3,
        'T-score':['positive','negative','positive','negative'],
        'T-ownership':['positive']*2, 'T-valuation':['negative','positive'],
        'T-claim':['positive','positive','negative','positive','negative','negative'],
        'T-appendix':['negative','positive'], 'T-zero':['zero','negative'],
        'T-redistribution':['zero','positive']}
    for gid, signs in expected_signs.items():
        assert [r['actor_decline_value_sign'] for r in sensitivities if r['group'] == gid] == signs, gid
    close(m['S08']['break_even_added_execution_cost_usdc_per_job'], '.77062080171851461555')
    close(m['S08']['break_even_lpt_valuation_usdc_per_lpt'], '1.01356518455794085922')
    close(m['S08']['whole_round_median_break_even_against_decline'], '.91721421507763101522')
    assert m['S10']['break_even_lpt_valuation_usdc_per_lpt'] == 'no finite threshold'
    assert m['S00']['break_even_lpt_valuation_usdc_per_lpt'] == 'undefined'
    assert m['S03']['break_even_lpt_valuation_usdc_per_lpt'] == 'no finite threshold'
    assert m['S00']['whole_round_median_break_even_against_decline'] == 'undefined'
    for r in main + sensitivities:
        for key in ('break_even_lpt_valuation_usdc_per_lpt', 'break_even_added_execution_cost_usdc_per_job'):
            if isinstance(r[key], D): assert r[key] > ZERO, (r.get('id'), key)
        median = r['whole_round_median_break_even_against_decline']
        if isinstance(median, D): assert ZERO < median <= ONE
    for r in sensitivities:
        if (r['group'], r['level']) in [('T-zero', '1'), ('T-redistribution', 'original q0')]:
            assert r['whole_round_median_break_even_against_decline'] == 'undefined'
        if (r['group'], r['level']) == ('T-zero', '0'):
            assert r['additional_gross_fees_to_stake_cap_usdc'] == 'undefined'
    # Explicit EX-05 cross-contract check on the full-score positive-fee reference.
    snap, obs, bp = bridge.inputs()
    _, bs = bridge.account(bp, obs['scheduled_mint_ceiling_lpt'], D(config['burn_execution_price']))
    close(bs['node_minted_lpt'], m['S00']['node_actually_minted_lpt_at_horizon'])
    close(bs['unused_node_unminted_lpt'], m['S00']['mfs_unallocated_never_minted_lpt'])
    close(bs['burned_lpt'], m['S00']['tokens_burned_lpt'])
    print('PASS: independent fixtures; all-100-pool conservation; costs, routing, entry, cap, score, claims, compression, redistribution, zero fees and appendix; 12 cases / 26 sensitivity rows / 9 groups; EX-05 interface.')


if __name__ == '__main__':
    fixtures()
    invariants()
