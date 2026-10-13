#!/usr/bin/env python3
"""Validate Phase 1's finite input contract, never calculate economic outcomes."""
from collections import Counter
from copy import deepcopy
from decimal import Decimal as D, localcontext, ROUND_HALF_EVEN
import hashlib
import json
from pathlib import Path
import fixtures as f

HERE = Path(__file__).resolve().parent


def expected_profiles():
    """Independent enumeration of the authorized selection and override keys."""
    expected = {}
    def put(name,group,s,m,k,start,parent=None,overrides=None):
        expected[name]=(group,s,m,k,start,parent,overrides or {})
    def core(s,m,k,start='low'): return f'{s}-{m}-{k}-{start}'
    for s in ('R','D','C'):
        for m in ('measured','mid-path','near-parity'):
            for k in (1,50,90):
                for start in ('low','high'):
                    put(core(s,m,k,start),'core',s,m,k,start)
    for k in (1,50,90):
        put(f'R-fee-leaning-{k}-low','fee-leaning','R','fee-leaning',k,'low')
        put(f'native-measured-{k}','native','R','measured',k,'native')
        for m in ('measured','mid-path','near-parity'):
            put(f'aligned-{m}-{k}','aligned','R',m,k,'aligned')
    factors={'retention':{'w':'.25','k':'0','d':'1'},'cost':{'cost':'1.20'},
             'valuation':{'valuation_multiplier':'.10'},'schedule':{'earning_round':840}}
    for s in ('R','D','C'):
        for k in (1,50,90):
            for factor,ov in factors.items():
                put(f'{factor}-{s}-{k}','one-factor',s,'mid-path',k,'low',core(s,'mid-path',k),ov)
    for k in (1,50,90):
        parent=core('R','mid-path',k)
        put(f'appendix-R-{k}','appendix','R','mid-path',k,'low',parent,{'reading':'appendix'})
        put(f'niche-R-{k}','capability','R','mid-path',k,'low',parent,{'controlled_offer':'niche'})
        for response in ('proportional-double','concentrated-add'):
            put(f'{response}-R-{k}','demand','R','mid-path',k,'low',parent,
                {'outside_response':response,'preserve_parent_budget_capacity':True,'action_policy':['parent-feasible-optimum','reoptimize']})
    put('niche-cost-setup-R-1','capability','R','mid-path',1,'low',core('R','mid-path',1),
        {'controlled_offer':'niche','cost':'.20','setup':'2','setup_when':'x>0; charged once and included in B'})
    put('price-routing-R-1','price-routing','R','mid-path',1,'low',core('R','mid-path',1),
        {'outside_response':'price-routing','preserve_parent_budget_capacity':True,'competitor_price':'.5','route_fraction':'.25','action_policy':['parent-feasible-optimum','reoptimize']})
    for s in ('R','D','C'):
        for m in ('measured','near-parity'):
            for name,ov in [('B-F',{'budget_fraction':'1'}),('capacity-only',{'cash_bound':None})]:
                put(f'{name}-{s}-{m}','budget',s,m,1,'low',core(s,m,1),ov)
    for m in ('measured','near-parity'):
        for action in ('fixed-parent-optimum','reoptimize'):
            put(f'invoice10-{m}-{action}','invoice-price','R',m,1,'low',core('R',m,1),
                {'controlled_offer':'niche','controlled_price':'10','action_policy':action,'preserve_parent_budget_capacity':True})
    return expected


def check_schema(manifest, networks, grid):
    required_counts={'core':54,'fee-leaning':3,'aligned':9,'native':3,'one-factor':36,'appendix':3,
                     'capability':4,'demand':6,'price-routing':1,'budget':12,'invoice-price':4,'timelines':10}
    f.require(grid['coverage_counts']==required_counts,'Coverage count contract')
    expected=expected_profiles()
    f.require(len(grid['profiles'])==135,'Finite profile count')
    seen=set()
    for row in grid['profiles']:
        sid=row['id']
        f.require(sid in expected and sid not in seen,'Unpermitted/duplicate profile')
        seen.add(sid)
        actual=tuple(row[k] for k in ('group','structure','market','actor_rank','start','parent','overrides'))
        f.require(actual==expected[sid],sid+': selection/override differs')
        f.require(row['parent'] is None or row['parent'] in seen,sid+': missing/forward parent')
        f.require(row['references']=={'decline':sid+':outside-no-purchase','useful':sid+':useful-internal','use_value_per_job':'1'},sid+': paired references')
        f.require(row['horizon']==7 and row['budget_period']=='one earning round',sid+': horizon/budget period')
        f.require(row['status']=='illustrative' and row['scope']=='computed' and row['source'],sid+': provenance')
        f.require(row['outcome_status']=='pending' and not {'results','outcomes','payoff'} & row.keys(),sid+': no outcomes')
    f.require(seen==set(expected),'Missing named selection')
    f.require(dict(Counter(r['group'] for r in grid['profiles']))=={k:v for k,v in required_counts.items() if k!='timelines'},'Group counts')
    f.require(grid['order'][0]=='cooperative outside-no-purchase' and grid['no_extra_cross_products'] is True,'Ordering/finite scope')
    expected_timelines={f'timeline-R-{k}-{s}' for k in (1,50,90) for s in ('constant','escalating','equal-total')} | {'timeline-R-1-escalating-delay14'}
    f.require(len(grid['timelines'])==10 and {t['id'] for t in grid['timelines']}==expected_timelines,'Timeline coverage')
    factors={'constant':['.25']*4,'escalating':['.25','.50','.75','1'],'equal-total':['.10','.20','.30','.40']}
    for t in grid['timelines']:
        late=t['id'].endswith('delay14')
        f.require(t['parent']==f'R-mid-path-{t["actor_rank"]}-low','Timeline parent')
        f.require(t['desired_factors']==factors[t['schedule']] and t['earning_rounds']==[0,1,2,3],'Timeline schedule')
        f.require(t['claim_delay']==(14 if late else 7) and t['final_horizon']==(17 if late else 10),'Collection horizon')
        f.require(t['budget_period']=='one initial stock across all four rounds' and t['outcome_status']=='pending','Stock/no outcomes')
        f.require(t['comparators']==['matched four-round no-purchase baseline','one-round deployment of same initial B','constant versus equal-total for pacing only'],'Timeline comparators')
    f.require(sum(map(D,factors['constant']))==sum(map(D,factors['equal-total']))==1,'Equal desired total')
    f.require(sum(map(D,factors['escalating']))==D('2.5'),'Escalation desired total')
    boundaries={r['id']:r for r in grid['independent_boundaries']}
    f.require(set(boundaries)=={'above-cap','zero-fees','zero-victim','zero-retention','capacity-inclusive','invalid-negative','invalid-nonfinite'},'Boundary fixture coverage')
    f.require(D(boundaries['above-cap']['fee_share'])>D(boundaries['above-cap']['stake_share']),'Above-cap fixture')
    f.require(boundaries['zero-fees']['total_fees']=='0' and boundaries['zero-victim']['victim_fee_share']=='0','Zero fixture inputs')
    f.require(grid['legacy_replay']['cases']==[f'S{i:02d}' for i in range(12)],'Original case dependency')
    f.require(len(set(grid['legacy_replay']['sensitivity_groups']))==9,'Original sensitivity dependency')
    ser=networks['serialization']
    f.require(ser['precision']==60 and ser['rounding']=='ROUND_HALF_EVEN' and ser['share_quantum']=='1e-48' and ser['amount_quantum']=='1e-42','Precision contract')
    f.require(ser['tolerance']=='1e-18' and ser['stake_residual_rank']==100,'Residual/tolerance contract')
    for record in manifest['parameters'].values():
        f.require(record['status'] in ('paper-stated','measured','illustrative','unresolved') and record['unit'] and record['source'] and record['scope']=='stated premise','Input provenance')
    p={k:v['value'] for k,v in manifest['parameters'].items()}
    for key,value in {'node_share':'.94','validator_share':'.01','treasury_share':'.05','node_fee_share':'.5',
                      'price':'1','cost':'.30','setup':'0','budget_fraction':'.10','capacity_fraction':'.25',
                      'score':'1','use_value':'1','valuation':'1.71765','burn_price':'1.71765','half_life':'840',
                      'claim_delay':7,'actor_ranks':[1,50,90],'business_starts':{'low':'.25','high':'.90'}}.items():
        f.require(p[key]==value,'Changed frozen parameter '+key)


def check_states(states,cal,networks,manifest):
    f.require(json.loads(f.serialize(cal))==networks['calibration'],'Calibration changed')
    f.require(set(states)==set(networks['vector_hashes']),'Vector hash inventory')
    identity=None
    with localcontext() as ctx:
        ctx.prec=60;ctx.rounding=ROUND_HALF_EVEN
        _, observed, source, operators = f.source_inputs(manifest)
        native_keys = [p['address'] for p in source]
        for sid,state in states.items():
            f.require(f.digest(state)==networks['vector_hashes'][sid],sid+': vector hash')
            vec=state['vector']; actor=state['actor_rank']-1
            f.require(len(vec)==100 and [p['source_rank'] for p in vec]==list(range(1,101)),sid+': source ranks')
            keys=[p['source_key'] for p in vec]
            if identity is None: identity=keys
            f.require(keys==identity==native_keys and len(set(keys))==100 and keys[actor]==state['actor_key'],sid+': stable identities')
            if state['structure']=='R':
                f.require(all(p['stake']==source[i]['stake_lpt'] for i,p in enumerate(vec)),sid+': measured stakes')
                for i,p in enumerate(vec):
                    f.require(abs(p['parent_fee_share']-source[i]['fees_eth']/observed['fees_eth'])<f.TOLERANCE,sid+': measured fee proportions')
                    if source[i]['fees_eth']==0 and state['start']!='aligned' and not state['response']:
                        f.require(p['assigned_fee_share']==0 or i==actor,sid+': retained zero-fee pool')
            f.require(state['actor_rank'] in (1,50,90) and state['fee_residual_rank']!=state['actor_rank'],sid+': actor/residual')
            for key in ('declared_stake_share','parent_fee_share','assigned_fee_share'):
                f.require(sum((p[key] for p in vec),D(0))==1,sid+': share sum '+key)
            f.require(sum((p['stake'] for p in vec),D(0))==cal['S0_lpt'],sid+': stake conservation')
            f.require(sum((p['outside_fee_usdc'] for p in vec),D(0))==state['outside_F_usdc'],sid+': fee conservation')
            f.require(all(vec[i]['stake']>=vec[i+1]['stake']-f.TOLERANCE for i in range(99)),sid+': synthetic ranks')
            if state['structure'] in ('D','C'):
                for i,p in enumerate(vec):
                    s=D(100-i)/5050 if state['structure']=='D' else (D('.2') if i==0 else D('.04') if i<10 else D('.44')*D(100-i)/4095)
                    f.require(abs(s-p['declared_stake_share'])<f.TOLERANCE,sid+': stake formula')
                    f.require(abs(p['parent_fee_share']-D(i+1)/5050)<f.TOLERANCE,sid+': fee weight formula')
                    f.require(p['stake']>0 and p['assigned_fee_share']>0,sid+': positive synthetic vector')
            if state['start'] in ('low','high'):
                h=D('.25') if state['start']=='low' else D('.90')
                a=h*vec[actor]['declared_stake_share']
                f.require(vec[actor]['assigned_fee_share']==a,sid+': actor override')
                for i,p in enumerate(vec):
                    if i!=actor:
                        expected=p['parent_fee_share']*(1-a)/(1-vec[actor]['parent_fee_share'])
                        f.require(abs(expected-p['assigned_fee_share'])<f.TOLERANCE,sid+': nonactor relative weights')
                f.require(any(p['fee_reallocation_delta']!=0 for i,p in enumerate(vec) if i!=actor),sid+': visible reallocation')
            if state['start']=='aligned':
                f.require(all(p['assigned_fee_share']==p['declared_stake_share'] for p in vec),sid+': no headroom override')
            if state['start']=='native':
                f.require(all(p['assigned_fee_share']==p['parent_fee_share'] for p in vec),sid+': no native override')
            for i,p in enumerate(vec):
                if i!=actor or state['start']=='native':
                    native_cut=source[i]
                    native_ownership=D(operators[p['source_key']]['operator_address_fraction_of_own_pool'])
                    f.require((p['k'],p['d'],p['w'])==(native_cut['operator_reward_cut_fraction'],native_cut['delegator_fee_share_fraction'],native_ownership),sid+': source-native proxies')
                t,z=f.retention(p['k'],p['d'],p['w'])
                f.require((t,z)==(p['t'],p['z']) and p['score']==1 and p['claim_at']==7,sid+': retention/claim/score')
                caps=p['caps'];g=caps['generic']
                f.require(g['p']*g['q_out']==p['outside_fee_usdc'] and g['q_self']==0,sid+': outside fee/jobs')
                additional=g['capacity']-g['q_out']+caps.get('niche',{}).get('capacity',D(0))
                f.require(additional==(state['additional_capacity_jobs'] if i==actor else 0),sid+': capacity allocated once')
                f.require(all(c['setup']==0 and c['u']==0 for c in caps.values()),sid+': zero-action setup/use')
            if state['parent']:
                parent=states[state['parent']]
                f.require([p['source_key'] for p in parent['vector']]==keys,sid+': parent identity')
                for i,p in enumerate(vec):
                    f.require(p['stake']==parent['vector'][i]['stake'],sid+': fixed stake')
                    if i!=actor:
                        f.require((p['k'],p['d'],p['w'])==tuple(parent['vector'][i][k] for k in ('k','d','w')),sid+': native victim proxies')
                if state['response'] or state['group']=='invoice-price':
                    f.require(state['additional_capacity_jobs']==parent['additional_capacity_jobs'] and state['cash_loss_allowance_usdc']==parent['cash_loss_allowance_usdc'],sid+': preserved original bounds')
                if state['response'] in ('proportional-double','concentrated-add'):
                    f.require(state['outside_F_usdc']==2*parent['outside_F_usdc'],sid+': doubled spending')
                if state['response']=='price-routing':
                    old=parent['vector'];j=state['competitor_rank']-1
                    f.require(sum((p['caps']['generic']['q_out'] for p in vec),D(0))==sum((p['caps']['generic']['q_out'] for p in old),D(0)),sid+': jobs preserved')
                    f.require(vec[j]['caps']['generic']['p']==D('.5') and vec[j]['caps']['generic']['c']==D('.30'),sid+': price independent of cost')
                if state['group']=='invoice-price':
                    f.require(vec[actor]['caps']['generic']==parent['vector'][actor]['caps']['generic'] | {'capacity':parent['vector'][actor]['caps']['generic']['q_out']},sid+': generic offer unchanged')
                    f.require(vec[actor]['caps']['niche']['p']==10 and state['controlled_cost']==D('.30'),sid+': niche price10/cost unchanged')
            if state['group'] in ('core','aligned','fee-leaning'):
                f.require(vec[actor]['t']==vec[actor]['z']==1,sid+': full-retention upper bound')
                f.require(state['cash_loss_allowance_usdc']==D('.10')*state['original_F_usdc'] and state['additional_capacity_jobs']==D('.25')*state['original_F_usdc'],sid+': diagnostic bounds')
            f.require(state['scheduled_ceiling_lpt']==cal['E0_lpt']/(2 if state['earning_round']==840 else 1),sid+': schedule calibration')


def expect_rejection(operation,label):
    try: operation()
    except (ValueError,KeyError): return
    raise AssertionError('Negative boundary accepted: '+label)


def boundary_checks(manifest,networks,grid):
    for value in ('-.1','NaN','Infinity','-Infinity'):
        expect_rejection(lambda: f.decimal(value),value)
    expect_rejection(lambda:f.normalize([D(0)]*100,99),'zero normalization')
    expect_rejection(lambda:f.normalize([D(1)]*99,98),'dropped pool')
    expect_rejection(lambda:f.retention(D('1.01'),D(0),D(1)),'invalid cut')
    expect_rejection(lambda:f.serialize({'float':.1}),'binary float')
    for what in ('missing','duplicate','aligned-override','budget-period','timeline','unpermitted-override'):
        bad=deepcopy(grid)
        if what=='missing':bad['profiles'].pop()
        elif what=='duplicate':bad['profiles'][-1]=deepcopy(bad['profiles'][0])
        elif what=='aligned-override':next(r for r in bad['profiles'] if r['group']=='aligned')['start']='low'
        elif what=='budget-period':bad['profiles'][0]['budget_period']='initial stock'
        elif what=='timeline':bad['timelines'][0]['final_horizon']=9
        else:bad['profiles'][0]['overrides']={'reward_bonus':'1'}
        expect_rejection(lambda:check_schema(manifest,networks,bad),what)
    with localcontext() as ctx:
        ctx.prec=60
        F=D(100); Q=F/D(4);price=D(1);L=D('.8');B=D(10)
        f.require(f.capacity_feasible(Q,price,Q) and not f.capacity_feasible(Q+D('1e-40'),price,Q),'Inclusive capacity endpoint')
        f.require(f.cash_feasible(B/L,price,D('.3'),D(1),B) and not f.cash_feasible(B/L+D('1e-40'),price,D('.3'),D(1),B),'Inclusive cash endpoint')
        f.require(F*D('.20')/(1-D('.20'))==Q,'20% core capacity identity (no loss outcomes)')
        f.require(f.cash_feasible(D(0),price,D('.2'),D(1),D(0),D(2)),'No setup at zero action')
        f.require(not f.cash_feasible(D(1),price,D('.2'),D(1),D(2),D(2)),'Setup within cash allowance')
        f.require(f.retention(D(0),D(1),D('.25'))==(D('.25'),D('.25')),'Retention fixture')
        f.require(f.encode_decimal(D('1.2300'))=='1.23' and f.encode_decimal(D('0E-50'))=='0','Decimal serialization')
    f.require(manifest['undefined_contracts']['zero_initial_victim_reward'].startswith('relative loss undefined'),'Zero-victim display')
    f.require(manifest['undefined_contracts']['zero_fees'].endswith('appendix normalization undefined'),'Zero-fee display')


def check():
    manifest,networks,grid=f.load_contract()
    for name,sha in networks['contract_hashes'].items():
        f.require(hashlib.sha256((HERE/name).read_bytes()).hexdigest()==sha,'Changed frozen contract '+name)
    check_schema(manifest,networks,grid)
    states,cal=f.materialize(manifest,networks,grid)
    check_states(states,cal,networks,manifest)
    boundary_checks(manifest,networks,grid)
    # Freeze the interface shape without importing/calling the reward engine.
    import ast
    module=ast.parse((f.ROOT/'experiments/m2/capability-pricing/build.py').read_text())
    account=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='account')
    f.require([a.arg for a in account.args.args]==['pools','ceiling','valuation','burn_price','horizon','reading','node','validator','treasury','node_fee'],'EX-06 accounting interface')
    f.write_vectors(states)
    print('PASS: 135 frozen 100-pool input vectors (54 core, 3 fee-leaning, 9 aligned, 3 native, 66 supplements); 10 timeline selections; source/dependency/vector hashes; conservation, selections, bounds and negative/undefined contracts; no reward/payoff outcomes.')


if __name__=='__main__':
    check()
