#!/usr/bin/env python3
"""Independent constants, calculus and conservation checks; no table-derived fixtures."""
from collections import Counter, defaultdict
from copy import deepcopy
from decimal import Decimal as D, getcontext, ROUND_HALF_EVEN
import hashlib
import json

import fixtures as f
from adapter import Adapter, load_engine, replay_originals, ZERO, ONE, EPS, FROZEN

getcontext().prec=60
getcontext().rounding=ROUND_HALF_EVEN
CHECKS=Counter()


def check(ok,label):
    CHECKS[label]+=1
    if not ok:
        raise AssertionError(label)


def near(a,b,label):
    check(abs(D(a)-D(b))<=EPS,label)


def rows(path):
    with path.open() as stream:
        for line in stream:
            yield json.loads(line)


def fixture(N='128',B='20',fees=('10','30','60'),own='1',setup='0',offer='generic'):
    """Constants: F100; stakes .5/.3/.2, padded to 100 with zero-reward pools."""
    vector=[]
    for i in range(100):
        g=D(fees[i]) if i<3 else ZERO
        s=D(('.5','.3','.2')[i]) if i<3 else ZERO
        w=D(own) if i==0 else ONE
        caps={'generic':dict(q_out=g,q_self=ZERO,p=ONE,c=D('.3'),setup=ZERO,u=ZERO,capacity=g+(D(300) if i==0 and offer=='generic' else ZERO))}
        if i==0 and offer=='niche':
            caps['niche']=dict(q_out=ZERO,q_self=ZERO,p=ONE,c=D('.3'),setup=ZERO,u=ZERO,capacity=D(300))
        vector.append(dict(source_key=f'fixture-{i}',source_rank=i+1,stake=s,k=ZERO,d=ONE,w=w,
                           t=w,z=w,outside_fee_usdc=g,score=ONE,claim_at=7,caps=caps))
    return dict(id='hand-constant',actor_rank=1,vector=vector,outside_F_usdc=D(100),total_stake_lpt=ONE,
                cash_loss_allowance_usdc=D(B),additional_capacity_jobs=D(300),controlled_price=ONE,
                controlled_cost=D('.3'),setup_if_positive_usdc=D(setup),scheduled_ceiling_lpt=D(N)/D('.94'),
                valuation_usdc_per_lpt=ONE,burn_price_usdc_per_lpt=ONE,controlled_offer=offer,
                reading='mfs',start='low')


def independent_fixtures():
    # Expectations below are hand constants, never generated-table inputs.
    from build import Profile
    from build import stopping_label
    import strategy
    engine=load_engine()
    replay=replay_originals(engine)
    adapter=Adapter(engine,replay)
    state=fixture()
    p=Profile(state,adapter)
    optimum,candidates=p.optimize(D(25))
    near(optimum['x_usdc'],'20','hand interior optimum')
    near(p.increment(D(20)),'3.2','hand interior net value')
    r,n,m=p.evaluate(D(20))
    near(r[0]['claimable_lpt'],'32','hand actor claim')
    near(r[1]['claimable_lpt'],'32','hand diluted victim')
    near(r[2]['claimable_lpt'],'25.6','hand stake-limited protection')
    near(p.metrics(D(20))['honest_99_reward_loss_lpt'],'6.4','hand honest loss')
    near(p.metrics(D(20))['previously_unminted_allowance_change_lpt'],'12.8','hand released unminted allowance')
    near(strategy.derivative(state,D(20)),'0','hand stationary derivative')
    check(strategy.derivative(state,D(19))>0 and strategy.derivative(state,D(21))<0,'hand derivative sign bracket')
    near(strategy.collective_landmark(state,D('.2')),'50','hand collective landmark')
    near(strategy.individual_landmark(state,state['vector'][1],D('.2')),'25','hand individual landmark')
    check(strategy.break_even_roots(state)[0]==[D(44)],'hand nonzero break-even')
    near(p.increment(D(44)),0,'hand break-even evaluation')
    near(strategy.parameters(state)['head']/(1-D('.1')),D(4)/9,'hand cap headroom dilution')
    budget=fixture(N='1000',B='8')
    bp=Profile(budget,adapter)
    best,_=bp.optimize(D(10))
    near(best['x_usdc'],10,'hand budget constrained optimum')
    near(best['net_value_delta_usdc_equivalent'],D(812)/11,'hand budget constrained payoff')
    cap=fixture(N='1000',B='100')
    cp=Profile(cap,adapter)
    best,_=cp.optimize(D(125))
    near(best['x_usdc'],80,'hand cap kink optimum')
    near(best['net_value_delta_usdc_equivalent'],336,'hand cap kink payoff')
    check(strategy.derivative(cap,D(80),'left')>0 and strategy.derivative(cap,D(80),'right')==D('-.8'),'hand kink slopes')
    limited=fixture(N='1000');limited['cash_loss_allowance_usdc']=None
    limited['additional_capacity_jobs']=D(5);limited['vector'][0]['caps']['generic']['capacity']=D(15)
    lp=Profile(limited,adapter);best,_=lp.optimize(D(5))
    near(best['x_usdc'],5,'hand no-cash-bound capacity optimum')
    near(best['net_value_delta_usdc_equivalent'],D(272)/7,'hand capacity endpoint payoff')
    check(strategy.derivative(limited,D(5))>0 and stopping_label(limited,D(5),None,D(5),D(5))=='capacity endpoint','hand positive endpoint derivative and label')
    # Independent quadratic fixtures: two positive roots and a tangent root.
    from independent_math import roots,quantities
    two=fixture(N='160',setup='8')
    # .8x²-56x+800 roots are 20 and50, both below cap80.
    expected=[D(20),D(50)]
    check(roots(quantities(two))==expected,'independent two setup roots constants')
    actual=strategy.break_even_roots(two)[0]
    check(actual==expected,'builder two setup roots constants')
    tangent=fixture(N='128',setup='3.2')
    check(roots(quantities(tangent))==[D(20)] and strategy.break_even_roots(tangent)[0]==[D(20)],'independent tangent root constant')
    # Above-cap, zero reward retention and critical equality defend zero action.
    for edge in (fixture(fees=('60','20','20')),fixture(own='0'),fixture(N=str(D(800)/9))):
        ep=Profile(edge,adapter)
        best,_=ep.optimize(D(10))
        near(best['x_usdc'],0,'hand defended zero action')
    # Cash versus capacity are independent, inclusive and never EPS-expanded.
    bound=fixture(B='8')
    bound['additional_capacity_jobs']=D(10)
    bound['vector'][0]['caps']['generic']['capacity']=D(20)
    check(adapter.evaluate(bound,D(10))[2]['feasible'],'hand exact inclusive endpoint')
    try:
        adapter.evaluate(bound,D(10)+D('1e-30'))
    except ValueError:
        check(True,'hand beyond-capacity rejection')
    else:
        check(False,'hand beyond-capacity rejection')
    diagnostic=adapter.evaluate(bound,D(11),diagnostic=True)
    check(not diagnostic[2]['cash_feasible'] and not diagnostic[2]['capacity_feasible'],'hand D2 dual infeasibility')
    check(diagnostic[0][0]['generic_capacity']==D(20),'hand declared capacity preserved')
    cashonly=fixture(B='8')
    meta=adapter.evaluate(cashonly,D(11),diagnostic=True)[2]
    check(not meta['cash_feasible'] and meta['capacity_feasible'] and not meta['temporary_capacity_used'],'hand cash-only diagnostic uses declared capacity')
    # Setup is one absolute charge iff positive, and is part of B.
    setup=fixture(B='10',setup='2',offer='niche')
    a0=adapter.evaluate(setup,ZERO)[0][0]
    a10=adapter.evaluate(setup,D(10))[0][0]
    near(a0['setup_cost_usdc'],0,'hand zero setup reference')
    near(a10['setup_cost_usdc'],2,'hand setup charged once')
    check(adapter.evaluate(setup,D(10))[2]['cash_feasible'] and not adapter.evaluate(setup,D(11))[2]['cash_feasible'],'hand setup inside cash budget')
    useful=adapter.evaluate(state,D(20),useful=True)[0][0]
    near(useful['internal_use_value_usdc_equivalent'],20,'hand useful use value')
    near(useful['organization_net_value_usdc_equivalent_at_declared_lpt_price']-r[0]['organization_net_value_usdc_equivalent_at_declared_lpt_price'],20,'hand useful parity')
    niche=fixture(offer='niche')
    nr,nn,_=adapter.evaluate(niche,D(20))
    for key in ('claimable_lpt','organization_retained_lpt','organization_retained_fee_usdc','execution_cost_usdc',
                'organization_net_cash_usdc_after_controlled_outflows_and_costs','organization_net_value_usdc_equivalent_at_declared_lpt_price'):
        near(nr[0][key],r[0][key],'hand capability-label accounting parity')
    near(nn['total_actual_mint_lpt'],n['total_actual_mint_lpt'],'hand capability mint parity')
    # Claim age and scheduled allowance are separate. No cohort timeline outcome.
    pending=adapter.evaluate(state,D(20),horizon=6)
    near(pending[0][0]['minted_lpt'],0,'hand claim delay')
    near(pending[0][0]['pending_lpt'],32,'hand pending claim')
    scored=deepcopy(state);scored['vector'][0]['score']=ZERO
    sr,sn,_=adapter.evaluate(scored,D(20),useful=True)
    near(sr[0]['claimable_lpt'],0,'hand zero median whole round')
    near(sr[0]['score_withheld_lpt'],32,'hand zero median withholding')
    near(sr[0]['execution_cost_usdc'],9,'hand zero median preserves useful-work cost')
    near(sr[0]['internal_use_value_usdc_equivalent'],20,'hand zero median useful-work boundary')
    half=deepcopy(state);half['scheduled_ceiling_lpt']/=2
    near(adapter.evaluate(half,D(20))[0][0]['claimable_lpt'],16,'hand schedule half-life')
    appendix=deepcopy(state);appendix['reading']='appendix'
    ar,an,_=adapter.evaluate(appendix,D(20))
    near(ar[2]['claimable_lpt'],64,'hand appendix no stake cap')
    near(an['mfs_unallocated_never_minted_lpt'],0,'hand appendix full normalization')
    zero=deepcopy(state)
    for v in zero['vector']:
        v['caps']['generic']['q_out']=ZERO;v['outside_fee_usdc']=ZERO
    zero['outside_F_usdc']=ZERO
    zr,zn,_=adapter.evaluate(zero)
    near(zn['claimable_node_lpt_at_horizon'],0,'hand zero-fee MFS')
    check(strategy.individual_landmark(zero,zero['vector'][1],D('.2')) is None,'hand zero victim undefined')
    zero['reading']='appendix'
    try: adapter.evaluate(zero)
    except ValueError: check(True,'hand zero-fee appendix undefined')
    else: check(False,'hand zero-fee appendix undefined')
    # Source-independent external ownership fixture; gross transfers cancel once.
    partial=fixture(own='.25')
    pr,pn,_=adapter.evaluate(partial,D(20))
    near(pr[0]['organization_retained_fee_usdc'],'3.75','hand external fee exclusion')
    near(pr[0]['outside_delegator_fee_usdc'],'11.25','hand external fee recipient')
    near(pr[0]['organization_retained_lpt'],8,'hand external reward exclusion')
    near(pr[0]['outside_delegator_lpt'],24,'hand external reward recipient')
    return replay


def verify(core_only=True):
    CHECKS.clear()
    for name,sha in FROZEN.items():
        check(hashlib.sha256((f.HERE/name).read_bytes()).hexdigest()==sha,'frozen dispatch input hash')
    manifest,networks,grid=f.load_contract()
    states,cal=f.materialize(manifest,networks,grid)
    check(all(f.digest(s)==networks['vector_hashes'][sid] for sid,s in states.items()),'frozen vector hashes before accounting')
    original=independent_fixtures()
    out=f.HERE/('generated/core' if core_only else 'generated/full')
    generated=json.loads((out/'manifest.json').read_text())
    for name,sha in generated['file_sha256'].items():
        check(hashlib.sha256((out/name).read_bytes()).hexdigest()==sha,'output file digest')
    profiles=json.loads((out/'profiles.json').read_text())
    expected={sid for sid,s in states.items() if not core_only or s['group'] in ('core','fee-leaning','aligned','native')}
    check(len(profiles)==len(expected) and {r['profile'] for r in profiles}==expected,'exact frozen profile inventory')
    check(Counter(r['group'] for r in profiles)==Counter(states[sid]['group'] for sid in expected),'frozen group counts')
    lookup={r['profile']:r for r in profiles}
    from independent_math import verify_summary,expected_progression
    independent={}
    for r in profiles:
        state=states[r['profile']];v=state['vector'][state['actor_rank']-1]
        F,S=state['outside_F_usdc'],sum((p['stake'] for p in state['vector']),ZERO)
        independent[r['profile']]=verify_summary(state,r)
        a,s=v['outside_fee_usdc']/F,v['stake']/S
        near(r['actual_initial_actor_fee_share'],a,'actual monetary fee share')
        near(r['actual_actor_stake_share'],s,'actual monetary stake share')
        t=v['k']+(1-v['k'])*v['w'];z=1-v['d']+v['d']*v['w']
        L=1-D('.5')*z+state['controlled_cost']/state['controlled_price']
        N=D('.94')*state['scheduled_ceiling_lpt'];P=state['valuation_usdc_per_lpt']
        near(r['reward_retention'],t,'native/full reward retention')
        near(r['fee_retention'],z,'native/full fee retention')
        near(r['leakage_L'],L,'leakage identity')
        cap=max(ZERO,(s*F-v['outside_fee_usdc'])/(1-s))
        if r['start']=='aligned': cap=ZERO
        if state['reading']=='appendix': cap=None
        if cap is None:check(r['xcap_usdc'] is None,'appendix no cap')
        else:near(r['xcap_usdc'],cap,'cap algebra')
        near(r['dcap'],ONE if cap is None else max(ZERO,s-min(a,s))/(1-a),'headroom dcap identity')
        xe=None if r['cash_endpoint_usdc'] is None else D(r['cash_endpoint_usdc']);B=state['cash_loss_allowance_usdc'];K=state['setup_if_positive_usdc']
        if xe is not None:check(xe==0 or L*xe+K<=B,'cash endpoint exact feasibility')
        near(r['dB'],ONE if xe is None else xe/(F+xe),'budget dilution identity')
        near(r['single_fixed_stake_harm_limit'],min(D(r['dcap']),D(r['dB'])),'single fixed stake harm limit')
        if (cap is None or cap>0) and t>0:
            near(r['critical_ratio'],L/(t*(1-a)),'critical reward/fee ratio')
        else:
            check(isinstance(r['critical_ratio'],str) and r['critical_ratio'].startswith('no finite'),'critical ratio undefined/capped')
        if r['start']=='aligned':
            near(r['added_stake_identity_lpt'],0,'aligned stake identity equality')
        elif a>=s:
            near(r['added_stake_identity_lpt'],(a*S-v['stake'])/(1-a),'above-cap positive stake identity')
            check(D(r['added_stake_identity_lpt'])>=0,'no negative stake purchase')
        else:
            check(str(r['added_stake_identity_lpt']).startswith('not applicable'),'below-cap stake identity not applicable')
        x=D(r['feasible_optimum']['x_usdc']);end=independent[r['profile']][3]
        check(0<=x<=end and (B is None or L*x+(K if x>0 else ZERO)<=B) and x/state['controlled_price']<=state['additional_capacity_jobs'],'optimum inclusive bounds')
        # Independently derive the candidate set and objective from the rational
        # increment, rather than call strategy.py or sample a grid.
        choices={ZERO,end}
        if cap is not None and cap<=end: choices.add(cap)
        stationary=(P*N*t*(F-v['outside_fee_usdc'])/L).sqrt()-F if t>0 else -F
        if 0<stationary and (cap is None or stationary<=cap) and stationary<=end: choices.add(stationary)
        expected_payoff=lambda q:P*N*t*((v['outside_fee_usdc']+q)/(F+q)-a if cap is None else
            min((v['outside_fee_usdc']+q)/(F+q),s)-min(a,s))-L*q-(K if q>0 else ZERO)
        best=max(choices,key=lambda q:(expected_payoff(q),-q))
        near(x,best,'independent analytic candidate optimum')
        near(r['feasible_optimum']['net_value_delta_usdc_equivalent'],expected_payoff(x),'independent optimum payoff')
        if x==xe and x>0: check(r['stopping_reason']=='budget convention','budget-bound label')
        for candidate in r['candidate_evaluations']+r['unconstrained_candidate_evaluations']:
            q=D(candidate['x_usdc'])
            near(candidate['net_value_delta_usdc_equivalent'],expected_payoff(q),'independent candidate payoff')
            uncapped=P*N*t*(F-v['outside_fee_usdc'])/(F+q)**2-L
            left=uncapped if cap is None or q<=cap else -L
            right=uncapped if cap is None or q<cap else -L
            near(candidate['marginal_left'],left,'independent left derivative')
            near(candidate['marginal_right'],right,'independent right derivative')
        check(x<state['controlled_price']*state['additional_capacity_jobs'],'capacity not binding profitable optimum')
        if r['group'] in ('aligned','fee-leaning'):
            near(x,0,'aligned/fee-leaning zero optimum')
        if r['start']=='high': check(a<s,'high business remains below cap')
        for opt in ('feasible_optimum_accounting','unconstrained_optimum_accounting'):
            m=r[opt]
            gain=D(m['actor_gross_reward_gain_lpt']);loss=D(m['honest_99_reward_loss_lpt']);release=D(m['previously_unminted_allowance_change_lpt'])
            near(gain,loss+release,'gain unminted/peer-loss identity')
            if gain:
                near(D(m['previously_unminted_share_of_actor_gain'])+D(m['peer_loss_share_of_actor_gain']),1,'gain source shares')
            else: check(str(m['peer_loss_share_of_actor_gain']).startswith('undefined'),'zero gain undefined shares')
    point_lookup={}
    point_counts=Counter()
    point_sets=defaultdict(set)
    for point in rows(out/'progressions.jsonl'):
        sid=point['profile'];point_counts[sid]+=1;point_lookup[point['point']]=point
        point_sets[sid].add(D(point['x_usdc']))
        near(point['network']['network_fees_usdc'],D(point['baseline_network']['network_fees_usdc'])+D(point['x_usdc']),'progression denominator')
        check(point['network']==point['useful_reference_network'],'useful all-network parity')
        a,u=point['actor'],point['useful_reference_actor']
        for key in a:
            if key not in ('internal_use_value_usdc_equivalent','organization_net_value_usdc_equivalent_at_declared_lpt_price'):
                check(a[key]==u[key],'useful actor accounting parity')
        near(D(point['useful_reference_net_value_delta_usdc_equivalent'])-D(point['accounting']['net_value_delta_usdc_equivalent']),
             point['useful_reference_use_value_usdc_equivalent'],'useful incremental use only')
        if not point['capacity_feasible']:
            check(point['execution_label']=='hypothetical execution beyond declared capacity' and point['temporary_capacity_used'],'D2 label/temporary copy')
        else: check(not point['temporary_capacity_used'],'no D2 at capacity-feasible diagnostics')
        check(point['diagnostic']==(not point['feasible']),'actual diagnostic versus feasible point label')
    check(set(point_counts)==expected and all(1<=n<=8 for n in point_counts.values()),'finite deduplicated progression inventory')
    for sid,(p,x,u,e) in independent.items():
        check(point_sets[sid]==expected_progression(p,x,u,e),'complete independent progression selection set')
    aggregate=defaultdict(lambda:defaultdict(lambda:ZERO));seen=defaultdict(set)
    for effect in rows(out/'pool-effects.jsonl'):
        pid=effect['point'];rank=effect['source_rank'];sid=effect['profile'];point=point_lookup[pid]
        check(rank not in seen[pid],'unique pool in each point');seen[pid].add(rank)
        state=states[sid];v=state['vector'][rank-1];old,new=effect['baseline'],effect['changed']
        F=D(point['baseline_network']['network_fees_usdc']);T=D(point['network']['network_fees_usdc'])
        ss=v['stake']/state['total_stake_lpt'];N=D('.94')*state['scheduled_ceiling_lpt']
        near(new['stake_share'],ss,'all-pool fixed stake')
        near(new['claimable_lpt'],N*(D(new['fees_usdc'])/T if state['reading']=='appendix' else min(D(new['fees_usdc'])/T,ss)),'all-pool independent entitlement')
        near(old['claimable_lpt'],N*(D(old['fees_usdc'])/F if state['reading']=='appendix' else min(D(old['fees_usdc'])/F,ss)),'all-pool independent baseline')
        near(effect['absolute_reward_loss_lpt'],D(old['claimable_lpt'])-D(new['claimable_lpt']),'pool absolute loss')
        if D(old['claimable_lpt']):
            near(effect['relative_reward_loss'],D(effect['absolute_reward_loss_lpt'])/D(old['claimable_lpt']),'pool relative loss')
        else: check(str(effect['relative_reward_loss']).startswith('undefined'),'zero-victim relative loss undefined')
        near(D(new['organization_retained_fee_usdc'])+D(new['outside_delegator_fee_usdc']),D(new['fees_usdc'])/2,'all-pool fee receipt conservation')
        near(D(new['organization_retained_lpt'])+D(new['outside_delegator_lpt']),new['minted_lpt'],'all-pool reward conservation')
        near(new['ownership_fraction'],v['w'],'all-pool native/declared ownership')
        near(new['reward_cut'],v['k'],'all-pool native/declared reward cut')
        near(new['delegator_fee_share'],v['d'],'all-pool native/declared fee cut')
        near(new['outside_delegator_lpt'],D(new['minted_lpt'])*(1-v['k'])*(1-v['w']),'all-pool external reward exclusion')
        near(new['outside_delegator_fee_usdc'],D(new['fees_usdc'])/2*v['d']*(1-v['w']),'all-pool external fee exclusion')
        near(new['organization_net_cash_usdc_after_controlled_outflows_and_costs'],D(new['organization_retained_fee_usdc'])-D(new['controlled_spending_usdc'])-D(new['execution_cost_usdc'])-D(new['setup_cost_usdc']),'all-pool internal cancellation once')
        near(effect['external_delegator_reward_loss_lpt'],D(old['outside_delegator_lpt'])-D(new['outside_delegator_lpt']),'external delegator loss')
        near(effect['external_delegator_net_income_effect_usdc_equivalent'],
            D(new['outside_delegator_fee_usdc'])-D(old['outside_delegator_fee_usdc'])+
            (D(new['outside_delegator_lpt'])-D(old['outside_delegator_lpt']))*state['valuation_usdc_per_lpt'],'external delegator net income')
        if rank!=state['actor_rank']:
            check(effect['outside_fee_unchanged'] and old['outside_spending_usdc']==new['outside_spending_usdc'],'honest outside fees unchanged')
            near(effect['organization_net_income_effect_usdc_equivalent'],
                 (D(new['organization_retained_lpt'])-D(old['organization_retained_lpt']))*state['valuation_usdc_per_lpt'],'honest retained income effect')
            aggregate[pid]['honest_loss']+=D(effect['absolute_reward_loss_lpt'])
            aggregate[pid]['honest_organization_loss']+=D(old['organization_retained_lpt'])-D(new['organization_retained_lpt'])
            aggregate[pid]['honest_external_loss']+=D(old['outside_delegator_lpt'])-D(new['outside_delegator_lpt'])
        for key in ('fees_usdc','claimable_lpt','minted_lpt','pending_lpt','score_withheld_lpt','pre_score_lpt','outside_spending_usdc','controlled_spending_usdc'):
            aggregate[pid][key]+=D(new[key])
    for pid,point in point_lookup.items():
        check(seen[pid]==set(range(1,101)),'all 100 pools at each point')
        n=point['network'];a=aggregate[pid]
        for key,source in [('network_fees_usdc','fees_usdc'),('claimable_node_lpt_at_horizon','claimable_lpt'),
            ('node_actually_minted_lpt_at_horizon','minted_lpt'),('pending_unclaimed_node_lpt','pending_lpt'),
            ('score_withheld_unminted_lpt','score_withheld_lpt'),('mfs_pre_score_node_entitlement_lpt','pre_score_lpt')]:
            near(n[key],a[source],'all-pool aggregate '+key)
        near(point['accounting']['honest_99_reward_loss_lpt'],a['honest_loss'],'honest 99 aggregate loss')
        near(point['accounting']['honest_99_organization_retained_reward_loss_lpt'],a['honest_organization_loss'],'honest 99 retained aggregate')
        near(point['accounting']['honest_99_external_delegator_reward_loss_lpt'],a['honest_external_loss'],'honest 99 external aggregate')
        E=D(n['scheduled_ceiling_lpt'])
        near(E,D(n['node_actually_minted_lpt_at_horizon'])+D(n['pending_unclaimed_node_lpt'])+
             D(n['score_withheld_unminted_lpt'])+D(n['mfs_unallocated_never_minted_lpt'])+
             D(n['validator_full_mint_lpt'])+D(n['treasury_full_mint_lpt']),'schedule/mint/pending/unminted conservation')
        near(n['validator_full_mint_lpt'],E*D('.01'),'full validator envelope')
        near(n['treasury_full_mint_lpt'],E*D('.05'),'full treasury envelope')
        near(n['buyback_spending_usdc'],D(n['network_fees_usdc'])/2,'buyback half')
        near(n['tokens_burned_lpt'],D(n['buyback_spending_usdc'])/D(n['burn_execution_price_usdc_per_lpt']),'burn units')
        near(n['net_supply_change_lpt_after_burn'],D(n['total_actual_mint_lpt'])-D(n['tokens_burned_lpt']),'net supply identity')
    landmark_counts=Counter()
    for r in rows(out/'loss-landmarks.jsonl'):
        landmark_counts[r['profile']]+=1
        state=states[r['profile']];summary=lookup[r['profile']]
        if r['x_usdc'] is None:
            check(r['status'].startswith('undefined'),'undefined landmarks explicit');continue
        x=D(r['x_usdc']);target=D(r['target_fraction']);F=state['outside_F_usdc']
        near(r['engine_actual_loss_fraction'],target,'engine target-loss agreement')
        L=D(summary['leakage_L']);B=state['cash_loss_allowance_usdc'];Q=state['additional_capacity_jobs']
        K=state['setup_if_positive_usdc']
        check(r['cash_feasible']==(B is None or L*x+(K if x>0 else ZERO)<=B) and r['capacity_feasible']==(x/state['controlled_price']<=Q),'landmark exact independent feasibility')
        check(r['before_or_at_actor_feasible_optimum']==(x<=D(summary['feasible_optimum']['x_usdc'])),'landmark optimum ordering')
        if r['landmark_kind'].startswith('individual'):
            v=state['vector'][r['source_rank']-1];w=v['outside_fee_usdc']/F if state['reading']=='appendix' else min(v['outside_fee_usdc']/F,v['stake']/state['total_stake_lpt'])
            near(x,v['outside_fee_usdc']/(w*(1-target))-F,'independent individual loss root')
            if state['group'] in ('core','native','aligned','fee-leaning') and v['outside_fee_usdc']/F<=v['stake']/state['total_stake_lpt'] and target==D('.2'):
                check(x==state['controlled_price']*Q and r['capacity_feasible'] and r['capacity_position']=='at the capacity boundary','exact fee-limited 20 percent capacity endpoint')
        else:
            weight=lambda v,denom:v['outside_fee_usdc']/denom if state['reading']=='appendix' else min(v['outside_fee_usdc']/denom,v['stake']/state['total_stake_lpt'])
            old=sum((weight(v,F) for i,v in enumerate(state['vector']) if i!=state['actor_rank']-1),ZERO)
            new=sum((weight(v,F+x) for i,v in enumerate(state['vector']) if i!=state['actor_rank']-1),ZERO)
            near((old-new)/old,target,'independent collective piecewise root')
    check(set(landmark_counts)==expected and all(n==300 for n in landmark_counts.values()),'99 individual times 3 plus 3 collective landmarks')
    for r in rows(out/'break-even.jsonl'):
        near(r['net_value_delta_usdc_equivalent'],0,'engine nonzero break-even')
    if core_only:
        check(generated['counts']['supplementary_outcomes']==generated['counts']['timelines']==generated['counts']['evidence_outcomes']==0,'core-only outcome boundary')
    else:
        from verify_full import supplementary_checks,timeline_checks,evidence_checks
        supplementary_checks(states,profiles,out,check,near)
        timeline_checks(states,profiles,grid,out,check,near)
        evidence_checks(out,check)
    from adapter import write_json
    write_json(f.HERE/('generated/core-verification.json' if core_only else 'generated/full-verification.json'),dict(status='PASS',assertions=sum(CHECKS.values()),
        checks=dict(CHECKS),original_replay=original,
        limits='Arithmetic/provenance/finite accounting only; no empirical validity, hidden-purpose evidence, eligibility policy, detector performance or owner research acceptance.'))
    print(f'PASS independent {"core" if core_only else "full"} verifier: {sum(CHECKS.values())} assertions; {len(profiles)} profiles; independent endpoints/roots/progression and hand fixtures; all-pool conservation/landmarks and declared-stage checks.')


if __name__=='__main__':
    verify()
