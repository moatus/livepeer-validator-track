#!/usr/bin/env python3
"""Independent constants, edge fixtures and immutable full-population replay."""
from copy import deepcopy
from decimal import Decimal as D
import hashlib
import json
import subprocess
import sys
from build import (HERE, ROOT, Model, ZERO, ONE, aggregate, compensation, added_capital,
                   redistribute, run, digest, serialize, utility_delta, affordable_cost)


def close(a,b,tol=D('1e-18')):
    assert abs(a-D(str(b))) <= tol,(a,b)


def rejects(fn):
    try: fn()
    except (ValueError,ArithmeticError): return
    raise AssertionError('Expected rejection')


def fixtures():
    # F1: 16 low + 16 high; focal low/high/absent. Hand central positions 17/18.
    rest = [ZERO]*16+[ONE]*16
    assert [aggregate(rest+[x],'F') for x in (ZERO,ONE,None)] == [ZERO,ONE,ONE]
    assert [aggregate(rest+[x],'Q') for x in (ZERO,ONE,None)] == [ZERO,ONE,D('.5')]
    # F2: full absence, q-1/q, even tie, arbitrary valid fractional middle.
    assert aggregate([None]*33,'F') == aggregate([None]*33,'Q') == ONE
    assert aggregate([ZERO]*16+[None]*17,'Q') == ONE
    assert aggregate([ZERO]*17+[None]*16,'Q') == ZERO
    assert aggregate([ZERO]*11+[ONE]*11+[None]*11,'Q') == D('.5')
    assert aggregate([D('.2')]*8+[D('.8')]*10+[None]*15,'Q') == D('.8')
    for value in (D('-0.01'),D('1.01'),D('NaN'),D('Infinity'),'bad'):
        rejects(lambda:aggregate(rest+[value],'F'))
    rejects(lambda:aggregate([],'Q'));rejects(lambda:aggregate(rest+[ONE],'bad'))
    # F3: V=10 LPT, weights3:1, k=.25,w=.2 -> retained .4. Weighted gross7.5,
    # retained3, outside4.5. Equal gross5, retained2. At P=2 values6 and4 USDC.
    seats=[dict(address='A',stake=D(3),k=D('.25'),w=D('.2')),
           dict(address='B',stake=ONE,k=ZERO,w=ONE)]
    pay=compensation(seats,D(10));a=pay['recipients'][0]
    close(a['gross_lpt'],7.5);close(a['retained_lpt'],3);close(a['outside_delegator_lpt'],4.5)
    close(compensation(seats,D(10),'equal')['recipients'][0]['retained_lpt'],2)
    close(compensation(seats,D(10),eligible=[True,False])['recipients'][0]['gross_lpt'],10)
    close(compensation(seats,D(10),eligible=[False,True])['recipients'][0]['gross_lpt'],0)
    empty=compensation(seats,D(10),eligible=[False,False])
    close(empty['undistributed_minted_lpt'],10);assert empty['weight_denominator'] is None
    zero=deepcopy(seats)
    for p in zero:p['stake']=ZERO
    rejects(lambda:compensation(zero,D(10)))
    close(compensation(zero,D(10),'equal')['recipients'][0]['gross_lpt'],5)
    # F4: P=2 USDC/LPT, retained pay3 LPT, exposure loss .25*100 LPT,
    # review2, opportunity1, shared allocation .1*20=2, residual4 -> -45.
    close(utility_delta(D(2),D(3),D(-25),D(2),ONE,D(2),D(4)),-45)
    close(affordable_cost(D(2),D(3)),6)
    close(affordable_cost(D(2),D(3),D(-25),D(4)),-40)
    # Known E vs U at identical numeric scores: monetary delta0; extra review2
    # loses2 only conditional on equal o/tool/Z, not a fabricated observed sign.
    close(utility_delta(D(2),ZERO,ZERO,D(2),ZERO,ZERO,ZERO),-2)
    # F5: C1000; fee20/80, stake60/40 -> pre188/376, unused376.
    # A score .5 -> mint94, withheld94, B376. k.25,w.2 -> retain37.6,outside56.4.
    model=Model()
    def pool(address,jobs,stake):
        return dict(address=address,stake=D(stake),k=D('.25'),d=D('.6'),w=D('.2'),score=ONE,claim_at=7,
            caps={'generic':dict(q_out=D(jobs),q_self=ZERO,p=ONE,c=D('.3'),setup=ZERO,u=ZERO,capacity=D(1000))})
    pools=[pool('A',20,60),pool('B',80,40)];pools[0]['score']=D('.5')
    rows,n=model.engine.account(pools,D(1000),D(2),D(4))
    for key,value in {'node_actually_minted_lpt_at_horizon':470,'mfs_unallocated_never_minted_lpt':376,
        'score_withheld_unminted_lpt':94,'validator_full_mint_lpt':10,'treasury_full_mint_lpt':50,
        'tokens_burned_lpt':12.5,'total_actual_mint_lpt':530}.items():close(n[key],value)
    close(rows[0]['organization_retained_lpt'],37.6);close(rows[0]['outside_delegator_lpt'],56.4)
    close(rows[0]['organization_net_cash_usdc_after_controlled_outflows_and_costs'],-.8)
    pools[0]['claim_at']=8
    early,ne=model.engine.account(pools,D(1000),D(2),D(4),7)
    close(ne['pending_unclaimed_node_lpt'],94);close(early[0]['minted_lpt'],0)
    later,nl=model.engine.account(pools,D(1000),D(2),D(4),8)
    close(later[0]['minted_lpt'],94);close(nl['scheduled_ceiling_lpt'],1000)
    for p in pools:p['caps']['generic']['p']=ZERO
    zr,zn=model.engine.account(pools,D(1000),D(2),D(4))
    close(zn['mfs_unallocated_never_minted_lpt'],940);close(zn['total_actual_mint_lpt'],60)
    assert sum(r['execution_cost_usdc'] for r in zr)==30 # zero fees do not erase executed jobs
    rejects(lambda:model.engine.account(pools,D(1000),D(2),D(4),reading='appendix'))
    for p in pools:p['stake']=ZERO
    rejects(lambda:model.engine.account(pools,D(1000),D(2),D(4)))
    # F6: integer wei synthetic ranks 100..1: rank17=84 =>17*85=1445;
    # k3 uses14 entrants >rank20=81 =>1148; d5 rank22=79 =>1360.
    stakes=list(range(100,0,-1))
    assert added_capital(stakes)['new_capital_wei']==1445
    assert added_capital(stakes,3)['new_capital_wei']==1148
    assert added_capital(stakes,d=5)['new_capital_wei']==1360
    # Equal incumbent tie100: newcomers101; 17 donors fund1700 <1717,
    # 18 donors fund1800 >1717. Full-funding equality is rejected by strict >.
    red=redistribute([100]*100)
    assert red['donor_pool_count']==18 and red['redistributed_wei']==1717
    eq=[85]+[4]*16+[4]*83 # j1 available85 ==17*(rank18 4+1); must continue
    assert redistribute(eq)['donor_pool_count']>1
    print('PASS F1-F6: independent median, compensation, utility units, accounting/claims/zero and exact wei fixtures')


def check_ledger(ledger):
    n=ledger['network'];rows=ledger['participants'];v=ledger['validator_overlay']
    assert len(rows)==100 and len({r['address'] for r in rows})==100
    close(n['scheduled_ceiling_lpt'],sum((n[k] for k in ('node_actually_minted_lpt_at_horizon','mfs_unallocated_never_minted_lpt','score_withheld_unminted_lpt','pending_unclaimed_node_lpt','validator_full_mint_lpt','treasury_full_mint_lpt')),ZERO))
    close(sum((r['minted_lpt'] for r in rows),ZERO),n['node_actually_minted_lpt_at_horizon'])
    close(sum((r['fees_usdc'] for r in rows),ZERO),n['network_fees_usdc'])
    for r in rows:
        close(r['minted_lpt'],r['operator_commission_lpt']+r['owned_delegator_lpt']+r['outside_delegator_lpt'])
        close(r['fees_usdc']/2,r['operator_commission_fee_usdc']+r['owned_delegator_fee_usdc']+r['outside_delegator_fee_usdc'])
    close(sum((r['gross_lpt'] for r in v['recipients']),ZERO)+v['undistributed_minted_lpt'],n['validator_full_mint_lpt'])
    for r in v['recipients']:close(r['gross_lpt'],r['retained_lpt']+r['outside_delegator_lpt'])
    # Overlay distributes existing mint, never adds it to total_actual_mint.
    close(n['total_actual_mint_lpt'],n['node_actually_minted_lpt_at_horizon']+n['validator_full_mint_lpt']+n['treasury_full_mint_lpt'])


def invariants():
    model=Model();base_hash=model.base_hash;before=deepcopy(model.base)
    result=run()
    assert len(result['core'])==16 and len(result['controls'])==12 and len(result['seats'])==32
    baseline=result['baseline'];check_ledger(baseline)
    for cid,ledger in result['ledgers'].items():
        if cid=='C12':
            for sub in ledger.values():check_ledger(sub)
        else:check_ledger(ledger)
        if cid.startswith('V') or cid in [f'C{i:02}' for i in range(1,8)]:
            for a,b in zip(baseline['participants'],ledger['participants']):
                assert a['address']==b['address']
                if a['address']!=model.target:assert a==b,('rival reward transfer',cid)
                for key in ('fees_usdc','stake_share','fee_share','execution_cost_usdc','reward_cut','ownership_fraction','delegator_fee_share','organization_retained_fee_usdc'):
                    assert a[key]==b[key],(cid,key)
            assert ledger['validator_overlay']==baseline['validator_overlay']
    for row in result['core']:
        assert len(row['prefer_over'])==3
        assert all(p['known_retained_validator_delta_usdc']==ZERO for p in row['prefer_over'])
    for cid,factor in [('C10',D('.5')),('C11',D('.25'))]:
        ledger=result['ledgers'][cid]
        for key in ('scheduled_ceiling_lpt','validator_full_mint_lpt','node_actually_minted_lpt_at_horizon'):
            close(ledger['network'][key],baseline['network'][key]*factor)
        close(ledger['network']['network_fees_usdc'],baseline['network']['network_fees_usdc'])
    c12=result['ledgers']['C12']
    assert c12['at_n8_reference']['network']==baseline['network']
    target=next(p for p in baseline['participants'] if p['address']==model.target)
    close(c12['at_n7']['network']['pending_unclaimed_node_lpt'],target['minted_lpt'])
    assert model.base==before and digest(model.base)==base_hash
    assert model.ledger()==baseline # replay immutable input, not generated-file comparison
    # Hand source constants copied from frozen raw checkpoint pages, not generated tables:
    # 379659360603855438925991 +1, times17 =6454209130265542461741864 wei.
    end=[r for r in result['seats'] if r['block']==514893852]
    assert end[0]['new_capital_wei']==6454209130265542461741864
    assert end[0]['rank17_wei']==379659360603855438925991
    assert end[-1]['donor_pool_count']==2
    assert end[-1]['redistributed_wei']==6206912316848201439881046
    assert end[-1]['donor_controlled_wei']==8563354934939629961370029
    # Independently simulate final 33 ranks for each threshold (strict tie cannot fail).
    for s in result['seats']:
        ranked=[r for r in result['p1_rankings'] if r['block']==s['block']]
        assert len(ranked)==s['population'] and sum(r['stake_wei'] for r in ranked)==s['live_pool_stake_wei']
        assert ranked==sorted(ranked,key=lambda r:(-r['stake_wei'],r['address']))
        if s['premise']=='new capital':
            k,d=s['coordinated_count'],s['declined_count']
            incumbents=[(r['stake_wei'],r['rank']<=k,0) for r in ranked[d:]]
            newcomers=[(s['threshold_per_node_wei'],True,1)]*s['new_nodes']
            elected=sorted(incumbents+newcomers,reverse=True)[:33]
            assert sum(x[1] for x in elected)>=17
            assert s['new_capital_wei']==s['new_nodes']*s['threshold_per_node_wei']
        else:
            j=s['donor_pool_count'];available=sum(r['stake_wei'] for r in ranked[:j])
            assert available>s['redistributed_wei']
            assert available==s['redistributed_wei']+s['leftover_outside_eligible_wei']
            for prev in range(1,j):assert sum(r['stake_wei'] for r in ranked[:prev])<=17*(ranked[17+prev-1]['stake_wei']+1)
    # The unchanged EX-06 S00 shared summary reproduces exactly.
    old=model.engine.run()
    original=next(r for r in old[3] if r['id']=='S00')
    assert all(original[k]==v for k,v in baseline['network'].items())
    # Source identity + historical result hashes are explicit reproducible checks.
    assert base_hash=='670fcd44fc63cac1bcd7002a1f7ef4abc1a999b255f1062811f9a99aca24daf1'
    print('PASS F7-F12: 16/12/32 finite budget; all100 pools; ownership/mint; no rival transfer; earning/claim clocks; independent source wei; strict seat elections; immutable S00 replay')
    return result


if __name__=='__main__':
    fixtures();invariants()
    # Original verifier runs from source, with independent historical constants;
    # it never rebuilds/writes historical generated output files.
    subprocess.run([sys.executable,str(HERE.parent/'capability-pricing/verify.py')],cwd=ROOT,check=True)
    print('Limits: checks establish arithmetic/provenance and declared conditions, not private costs, practical evidence custody/access, beneficial ownership, actual participation or adopted policy.')
