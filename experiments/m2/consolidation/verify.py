#!/usr/bin/env python3
"""Independent arithmetic and real-ledger boundary checks EX-12.F1–F8."""
from collections import defaultdict
from copy import deepcopy
from decimal import Decimal as D
import json
import build as b
from check_inputs import check
Z=D(0);eps=D('1e-42')
def near(x,y):
    assert abs(x-y)<eps,(x,y,x-y)
def expect_error(call):
    try:call()
    except ValueError:return
    raise AssertionError('expected refusal')
def main():
    check();a,t,c,l,s=b.run();S=a['S'];F=a['F'];co={(v['case'],v['lane'],v['earning_round']):v for v in c}
    ro={(v['case'],v['lane'],v['round']):v for v in t}
    def row(lane,r):return co['SC-27',lane,r]
    def rnd(lane,r):return ro['SC-27',lane,r]
    # F1: solve (2+delta)/(100+delta)=.1 independently: delta=80/9.
    near(a['fresh'],S*D(4)/45);near(row('fresh',2)['network_stake_lpt'],S*49/45)
    near(row('fresh',2)['target_stake_lpt']/row('fresh',2)['network_stake_lpt'],D('.1'))
    assert a['fresh']>S*D('.08');near(rnd('fresh',1)['incoming_eligible_principal_lpt'],Z)
    print('EX-12.F1 PASS fresh 4S/45; Snew=49S/45; exact .10 target share')
    # F2: transfer conserves the complete denominator only after arrival.
    near(row('delayed-transfer',22)['network_stake_lpt'],S);near(row('delayed-transfer',23)['network_stake_lpt'],S)
    near(row('delayed-transfer',23)['target_stake_lpt'],S/10)
    ps,inc,src=b.state(a,'SC-27','delayed-transfer',23)
    near(a['base'][0]['stake']-ps[0]['stake'],S*D('.08'))
    for i in range(100):
        if i not in (0,49):near(ps[i]['stake'],a['base'][i]['stake'])
    print('EX-12.F2 PASS conserved transfer and unchanged other98 stake')
    # F3: unbond interim .92S, giving target share 1/46, not .02.
    for r in range(1,23):
        v=row('unbond-rebond',r);near(v['network_stake_lpt'],S*D('.92'));near(v['target_stake_lpt']/v['network_stake_lpt'],D(1)/46)
        near(v['source_moving_delegator_lpt'],Z);near(v['source_moving_delegator_fee_usdc'],Z)
        near(v['moving_forgone_lpt'],row('no-movement',r)['source_moving_delegator_lpt'])
    near(row('unbond-rebond',0)['source_moving_delegator_lpt'],row('no-movement',0)['source_moving_delegator_lpt'])
    near(row('unbond-rebond',23)['network_stake_lpt'],S)
    for lane in ['fresh','unbond-rebond','delayed-transfer']:
        for r in range(24):near(row(lane,r)['donor_pool_node_delta_lpt'],Z)
    assert row('unbond-rebond',1)['remaining_donor_lpt_delta']>0
    print('EX-12.F3 PASS interim denominator/source wait; donor pool unchanged while remaining receipts rise')
    # F4: earning entitlement and actual collection use different clocks.
    assert len(t)==368 and len(c)==192 and len(l)==19200
    near(rnd('fresh',6)['cumulative_node_mint_lpt'],Z)
    near(rnd('fresh',7)['node_mint_this_claim_lpt'],row('fresh',0)['node_actually_minted_lpt_at_horizon'])
    near(rnd('delayed-transfer',29)['incoming_receipt_this_claim_lpt'],Z)
    near(rnd('delayed-transfer',30)['incoming_receipt_this_claim_lpt'],row('delayed-transfer',23)['incoming_delegator_lpt'])
    assert rnd('delayed-transfer',30)['location']=='exit locked'
    ps,_,_=b.state(a,'SC-27','fresh',2)
    rows,net=b.evaluate(a,ps,2,horizon=8)
    near(net['node_actually_minted_lpt_at_horizon'],Z);assert net['pending_unclaimed_node_lpt']>0
    rows1,net1=b.evaluate(a,ps,2);near(net1['scheduled_ceiling_lpt'],net['scheduled_ceiling_lpt'])
    cut=deepcopy(ps);cut[49]['score']=Z
    zero,zn=b.E.account(cut,net['scheduled_ceiling_lpt'],D('1.71765'),D('1.71765'),9)
    for key in ['operator_commission_lpt','owned_delegator_lpt','outside_delegator_lpt']:near(zero[49][key],Z)
    near(zero[49]['organization_retained_fee_usdc'],rows1[49]['organization_retained_fee_usdc'])
    near(cut[49]['stake'],ps[49]['stake'])
    print('EX-12.F4 PASS n+7/earning ceiling; post-exit ownership; zero target median removes all node receipts only')
    # F5: independent cash identities: additional outside .5x-.3x=.2x;
    # controlled -x+.5x-.3x=-.8x; burn is already funded by the lost half.
    for lane in ['no-movement','fresh','unbond-rebond','delayed-transfer']:
        for r in range(24):
            v=co['SC-27',lane,r];w=co['SC-28',lane,r]
            near(v['target_incremental_work_cash_usdc'],D('.2')*a['x']);near(w['target_incremental_work_cash_usdc'],-D('.8')*a['x'])
            near(v['target_net_cash_usdc']-w['target_net_cash_usdc'],a['x'])
            near(v['target_operator_commission_lpt'],w['target_operator_commission_lpt'])
            near(w['tokens_burned_lpt'],(F+a['x'])/2/D('1.71765'))
    print('EX-12.F5 PASS matched work/rewards; .2x versus -.8x cash; charge once')
    # F6: real 100-pool ledgers, not aggregate-output self consistency alone.
    groups=defaultdict(list)
    for v in l:groups[v['case'],v['lane'],v['earning_round']].append(v)
    for key,rows in groups.items():
        v=co[key];assert len(rows)==100 and len({p['address'] for p in rows})==100
        sumv=lambda name:sum((p[name] for p in rows),Z)
        near(sumv('eligible_stake_lpt'),v['network_stake_lpt']);near(sumv('fees_usdc'),F+a['x'])
        near(sumv('minted_lpt'),v['node_actually_minted_lpt_at_horizon'])
        near(sumv('operator_commission_lpt')+sumv('owned_delegator_lpt')+sumv('outside_delegator_lpt'),sumv('minted_lpt'))
        near(sumv('operator_commission_fee_usdc')+sumv('owned_delegator_fee_usdc')+sumv('outside_delegator_fee_usdc'),(F+a['x'])/2)
        near(v['scheduled_ceiling_lpt'],sumv('minted_lpt')+v['mfs_unallocated_never_minted_lpt']+v['score_withheld_unminted_lpt']+v['validator_full_mint_lpt']+v['treasury_full_mint_lpt'])
        near(v['validator_full_mint_lpt'],v['scheduled_ceiling_lpt']/100);near(v['treasury_full_mint_lpt'],v['scheduled_ceiling_lpt']/20)
        near(v['net_supply_change_lpt_after_burn'],v['total_actual_mint_lpt']-v['tokens_burned_lpt'])
        near(v['node_mint_delta_lpt'],v['target_operator_lpt_delta']*10+v['donor_pool_node_delta_lpt']+v['other98_node_delta_lpt'])
    print('EX-12.F6 PASS 192 actual 100-pool ledgers; principal/fee/receipt/mint/unminted/burn conservation')
    # F7: hand fixture b20/B100, R40, k1/4, f200, d2/5 ->6LPT,8USDC.
    rr=b.receipt(D(20),dict(stake=D(100),k=D('.25'),d=D('.4')),dict(minted_lpt=D(40),fees_usdc=D(200)))
    near(rr[0],D(6));near(rr[1],D(8))
    for key,rows in groups.items():
        v=co[key];target=rows[49];donor=rows[0]
        near(v['donor_operator_owned_principal_lpt'],a['own'])
        near(v['target_operator_commission_lpt']+v['target_original_delegator_lpt']+v['incoming_delegator_lpt'],target['minted_lpt'])
        near(v['incoming_delegator_fee_usdc'],Z)
        # Independently apportion native donor reward/fees to actual eligible source candidate.
        b0=v['source_candidate_principal_lpt'];B=donor['eligible_stake_lpt'];k=donor['reward_cut'];d=donor['delegator_fee_share']
        near(v['source_moving_delegator_lpt'],b0*(1-k)*donor['minted_lpt']/B)
        near(v['source_moving_delegator_fee_usdc'],b0*d*donor['fees_usdc']/2/B)
        remaining=a['base'][0]['stake']-a['own']-a['move']
        near(v['remaining_donor_delegator_lpt'],remaining*(1-k)*donor['minted_lpt']/B)
        near(v['remaining_donor_delegator_fee_usdc'],remaining*d*donor['fees_usdc']/2/B)
        incoming=v['incoming_principal_lpt'];targetB=target['eligible_stake_lpt']
        near(v['incoming_delegator_lpt'],incoming*D('.9')*target['minted_lpt']/targetB)
        near(v['target_original_delegator_lpt'],S*D('.02')*D('.9')*target['minted_lpt']/targetB)
    assert a['base'][0]['d']==D('.51')
    contract=json.loads((b.HERE/'cases.json').read_text())
    assert contract['receipt_boundary']['target_validator_registration'] is False
    assert 'unknown' in contract['receipt_boundary']['donor_validator_registration']
    print('EX-12.F7 PASS 6LPT/8USDC hand fixture; post-cut ownership/source/destination attribution; validator participant exclusion')
    # F8: finite stop, exit principal and scalar/appendix edges.
    for lane in ['fresh','unbond-rebond','delayed-transfer']:
        near(rnd(lane,24)['incoming_eligible_principal_lpt'],Z);near(rnd(lane,30)['pending_node_lpt'],Z)
        near(rnd(lane,44)['withdrawn_principal_lpt'],Z)
        near(rnd(lane,45)['withdrawn_principal_lpt'],a['fresh'] if lane=='fresh' else a['move'])
    assert max(v['earning_round'] for v in c)==23 and max(v['claim_round'] for v in c)==30
    assert sum(row('fresh',r)['incoming_principal_lpt']>0 for r in range(24))==22
    assert sum(row('delayed-transfer',r)['incoming_principal_lpt']>0 for r in range(24))==1
    p0,_,_=b.state(a,'SC-27','no-movement',23);p1,_,_=b.state(a,'SC-27','delayed-transfer',23)
    ar,_=b.evaluate(a,p0,23,reading='appendix');br,_=b.evaluate(a,p1,23,reading='appendix')
    near(ar[49]['minted_lpt'],br[49]['minted_lpt'])
    assert b.receipt(Z,dict(stake=Z),{})==('undefined','undefined')
    for p in p0:
        for cap in p['caps'].values():cap['p']=Z
    zr,zn=b.evaluate(a,p0,0);near(zn['node_actually_minted_lpt_at_horizon'],Z)
    expect_error(lambda:b.evaluate(a,p0,0,reading='appendix'))
    for p in p0:p['stake']=Z
    expect_error(lambda:b.evaluate(a,p0,0))
    print('EX-12.F8 PASS exit/withdrawal/finite stop; appendix stake-independence; zero fees/stake and undefined receipt boundary')
    p=b.p1_context();rates=p['movement-rates.csv'];selected=[v for v in rates if v['measure']=='redelegation' and v['period']=='90-day window']
    assert len(selected)==2
    for v in selected:near(v['amount_lpt'],D('1061494.613512182428993605'));assert v['count_or_rate']==104
    print('P1 PASS actual pinned offline analyzer/raw event reconciliation; 104 movements/1061494.613512182428993605 LPT, separate start/end denominators')
if __name__=='__main__':main()
