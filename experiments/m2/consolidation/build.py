#!/usr/bin/env python3
"""EX-12: one frozen comparison; no output file is an input."""
from copy import deepcopy
from decimal import Decimal as D, getcontext, ROUND_HALF_EVEN
import csv, hashlib, importlib.util, json, sys
from pathlib import Path
from check_inputs import check
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
Z=D(0); O=D(1)
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
E=module('ex12_ex06',ROOT/'experiments/m2/capability-pricing/build.py')
def context():
    getcontext().prec=60;getcontext().rounding=ROUND_HALF_EVEN

def calibration():
    context();config,_,obs,raw,_=E.load_inputs();raw=sorted(raw,key=lambda p:(-p['stake'],p['address']))
    S=sum((p['stake'] for p in raw),Z);F=obs['fees_usd_indexed'];base=deepcopy(raw);t=base[49]
    oldS=t['stake'];oldF=t['caps']['generic']['q_out']*t['caps']['generic']['p']
    for p in base:
        if p is t:continue
        p['stake']=p['stake']*(D('.98')*S)/(S-oldS)
        c=p['caps']['generic'];fee=c['q_out']*c['p'];c['q_out']=fee*(D('.98')*F)/(F-oldF)/c['p']
    t['stake']=D('.02')*S;t.update(k=D('.10'),d=Z,w=Z)
    t['caps']['generic'].update(q_out=D('.02')*F,q_self=Z,p=O,c=D('.30'),setup=Z,u=Z,capacity=F)
    stake_res=S-sum((p['stake'] for p in base),Z);base[-1]['stake']+=stake_res
    last=next(p for p in reversed(base) if p is not t and p['caps']['generic']['q_out']>0)
    fee_res=F-sum((p['caps']['generic']['p']*p['caps']['generic']['q_out'] for p in base),Z)
    last['caps']['generic']['q_out']+=fee_res/last['caps']['generic']['p']
    assert abs(stake_res)<D('1e-45') and abs(fee_res)<D('1e-45')
    own=base[0]['stake']*base[0]['w'];move=D('.08')*S;fresh=D(4)*S/D(45);x=D(4)*F/D(45)
    assert base[0]['stake']-own>move
    return dict(config=config,obs=obs,base=base,S=S,F=F,own=own,move=move,fresh=fresh,x=x,stake_res=stake_res,fee_res=fee_res)

def state(a,case,lane,r,added=True):
    ps=deepcopy(a['base']);t=ps[49];d=ps[0]
    if added and r<=23:
        t['caps']['generic']['q_out' if case=='SC-27' else 'q_self']+=a['x']
    incoming=Z;source=a['move'] if lane in ('no-movement','delayed-transfer') or lane=='unbond-rebond' and r==0 else Z
    if lane=='fresh' and 2<=r<=23:incoming=a['fresh']
    elif lane=='unbond-rebond' and r>=1:
        d['stake']-=a['move']
        if 23<=r<=23:incoming=a['move']
    elif lane=='delayed-transfer' and r>=23:
        d['stake']-=a['move'];source=Z
        if r<=23:incoming=a['move']
    t['stake']+=incoming
    d['w']=a['own']/d['stake']
    for p in ps:p['claim_at']=r+7
    return ps,incoming,source

def receipt(principal,pool,row):
    if pool['stake']<=0:return 'undefined', 'undefined'
    return principal/pool['stake']*(O-pool['k'])*row['minted_lpt'],principal/pool['stake']*pool['d']*D('.5')*row['fees_usdc']

def evaluate(a,ps,r,score=O,reading='mfs',horizon=None):
    context();ps=deepcopy(ps)
    for p in ps:p['score']=score
    ceiling=a['obs']['scheduled_mint_ceiling_lpt']*(D(2)**(-D(r)/D(840)))
    rows,net=E.account(ps,ceiling,D('1.71765'),D('1.71765'),r+7 if horizon is None else horizon,reading)
    return rows,net

def run():
    a=calibration();c=json.loads((HERE/'cases.json').read_text());ledger=[];cohorts=[];timeline=[];summaries=[]
    for case in c['cases']:
        references=[]
        for r in c['earning_rounds']:
            ps,inc,src=state(a,case,'no-movement',r);rr,nn=evaluate(a,ps,r)
            references.append((ps,rr,nn))
        for lane in c['lanes']:
            group=[]
            for r in c['earning_rounds']:
                ps,inc,src=state(a,case,lane,r);rows,net=evaluate(a,ps,r);t,d=ps[49],ps[0];tr,dr=rows[49],rows[0]
                refps,refr,refnet=references[r]
                incoming_lpt,incoming_fee=receipt(inc,t,tr)
                source_lpt,source_fee=receipt(src,d,dr)
                refsource_lpt,refsource_fee=receipt(a['move'],refps[0],refr[0])
                remaining=a['base'][0]['stake']-a['own']-a['move']
                remain_lpt,remain_fee=receipt(remaining,d,dr)
                refremain_lpt,refremain_fee=receipt(remaining,refps[0],refr[0])
                original_lpt,original_fee=receipt(a['base'][49]['stake'],t,tr)
                row=dict(case=case,lane=lane,earning_round=r,claim_round=r+7,**net,
                    target_stake_lpt=t['stake'],incoming_principal_lpt=inc,source_candidate_principal_lpt=src,
                    target_operator_commission_lpt=tr['operator_commission_lpt'],target_original_delegator_lpt=original_lpt,
                    target_original_delegator_fee_usdc=original_fee,incoming_delegator_lpt=incoming_lpt,incoming_delegator_fee_usdc=incoming_fee,
                    source_moving_delegator_lpt=source_lpt,source_moving_delegator_fee_usdc=source_fee,
                    reference_source_moving_lpt=refsource_lpt,reference_source_moving_fee_usdc=refsource_fee,
                    remaining_donor_delegator_lpt=remain_lpt,remaining_donor_delegator_fee_usdc=remain_fee,
                    remaining_donor_lpt_delta=remain_lpt-refremain_lpt,remaining_donor_fee_delta_usdc=remain_fee-refremain_fee,
                    donor_pool_node_lpt=dr['minted_lpt'],donor_pool_node_delta_lpt=dr['minted_lpt']-refr[0]['minted_lpt'],
                    donor_operator_owned_principal_lpt=d['stake']*d['w'],donor_operator_lpt=dr['organization_retained_lpt'],
                    donor_operator_fee_usdc=dr['organization_retained_fee_usdc'],
                    target_jobs=tr['generic_q_out']+tr['generic_q_self'],target_outside_spending_usdc=tr['outside_spending_usdc'],
                    target_controlled_spending_usdc=tr['controlled_spending_usdc'],target_fee_recovery_usdc=tr['organization_retained_fee_usdc'],
                    target_execution_cost_usdc=tr['execution_cost_usdc'],target_net_cash_usdc=tr['organization_net_cash_usdc_after_controlled_outflows_and_costs'],
                    target_incremental_work_cash_usdc=tr['organization_net_cash_usdc_after_controlled_outflows_and_costs']-D('.2')*D('.02')*a['F'],
                    target_operator_lpt_delta=tr['operator_commission_lpt']-refr[49]['operator_commission_lpt'],
                    other98_node_lpt=sum((v['minted_lpt'] for i,v in enumerate(rows) if i not in (0,49)),Z),
                    other98_node_delta_lpt=sum((v['minted_lpt']-refr[i]['minted_lpt'] for i,v in enumerate(rows) if i not in (0,49)),Z),
                    node_mint_delta_lpt=net['node_actually_minted_lpt_at_horizon']-refnet['node_actually_minted_lpt_at_horizon'])
                if lane=='fresh':
                    row.update(moving_forgone_lpt='unknown outside return',moving_forgone_fee_usdc='unknown outside return',moving_net_receipt_delta_lpt='undefined',moving_net_receipt_delta_usdc='undefined')
                else:
                    row.update(moving_forgone_lpt=refsource_lpt-source_lpt,moving_forgone_fee_usdc=refsource_fee-source_fee,
                        moving_net_receipt_delta_lpt=incoming_lpt+source_lpt-refsource_lpt,
                        moving_net_receipt_delta_usdc=incoming_fee+source_fee-refsource_fee)
                cohorts.append(row);group.append(row)
                for i,(p,v) in enumerate(zip(ps,rows)):
                    ledger.append(dict(case=case,lane=lane,earning_round=r,claim_round=r+7,source_rank=i+1,address=p['address'],eligible_stake_lpt=p['stake'],**v))
            for r in c['observation_rounds']:
                ps,inc,src=state(a,case,lane,r);earned=[v for v in group if v['earning_round']<=r];claimed=[v for v in earned if v['claim_round']<=r];due=[v for v in group if v['claim_round']==r]
                principal=a['fresh'] if lane=='fresh' else a['move'] if lane!='no-movement' else Z
                location=('no movement' if lane=='no-movement' else ('outside' if lane=='fresh' else 'source eligible') if r==0 else
                    'withdrawn' if r>=45 else 'exit locked' if r>=24 else
                    'target eligible' if inc else 'source eligible' if lane=='delayed-transfer' or lane=='unbond-rebond' and r==0 else 'initial wait')
                timeline.append(dict(case=case,lane=lane,round=r,earning_cohort='yes' if r<=23 else 'no; exit/claim observation only',
                    information='before decision' if r==0 else 'historical shares/cuts; future purpose/persistence/scores unknown',
                    location=location,gross_new_principal_lpt=a['fresh'] if lane=='fresh' and r>=1 else Z,
                    moving_principal_lpt=principal,withdrawn_principal_lpt=principal if r>=45 else Z,
                    network_eligible_stake_lpt=sum((p['stake'] for p in ps),Z),target_eligible_stake_lpt=ps[49]['stake'],
                    incoming_eligible_principal_lpt=inc,source_candidate_eligible_principal_lpt=src,
                    ceiling_this_earning_lpt=sum((v['scheduled_ceiling_lpt'] for v in earned if v['earning_round']==r),Z),
                    node_mint_this_claim_lpt=sum((v['node_actually_minted_lpt_at_horizon'] for v in due),Z),
                    cumulative_node_mint_lpt=sum((v['node_actually_minted_lpt_at_horizon'] for v in claimed),Z),
                    pending_node_lpt=sum((v['claimable_node_lpt_at_horizon'] for v in earned if v['claim_round']>r),Z),
                    cumulative_unminted_allowance_lpt=sum((v['mfs_unallocated_never_minted_lpt'] for v in earned),Z),
                    cumulative_validator_mint_lpt=sum((v['validator_full_mint_lpt'] for v in earned),Z),
                    cumulative_treasury_mint_lpt=sum((v['treasury_full_mint_lpt'] for v in earned),Z),
                    incoming_receipt_this_claim_lpt=sum((v['incoming_delegator_lpt'] for v in due),Z),
                    source_receipt_this_claim_lpt=sum((v['source_moving_delegator_lpt'] for v in due),Z)))
            total={k:sum((v[k] for v in group),Z) for k in group[0] if isinstance(group[0][k],D) and k not in ['network_stake_lpt','target_stake_lpt','incoming_principal_lpt','source_candidate_principal_lpt','donor_operator_owned_principal_lpt','lpt_valuation_price_usdc_per_lpt','burn_execution_price_usdc_per_lpt']}
            if lane=='fresh':total.update(moving_forgone_lpt='unknown outside return',moving_forgone_fee_usdc='unknown outside return',moving_net_receipt_delta_lpt='undefined',moving_net_receipt_delta_usdc='undefined')
            summaries.append(dict(case=case,lane=lane,elevated_eligible_rounds=22 if lane=='fresh' else 1 if lane!='no-movement' else 0,
                gross_new_principal_lpt=a['fresh'] if lane=='fresh' else Z,moving_principal_lpt=a['move'] if lane in ('unbond-rebond','delayed-transfer') else Z,
                unknown_costs='acquisition/liquidity/gas/financing/opportunity; fresh outside return; validator participant receipts excluded',**total))
    return a,timeline,cohorts,ledger,summaries

def p1_context():
    # Invoke the actual pinned offline analyzer against the frozen extract, but redirect
    # table writes into this package. Generated P1 tables never supply any input.
    folder=ROOT/'experiments/m2/current-system-data-notes';sys.path.insert(0,str(folder))
    p=module('ex12_p1',folder/'analyze.py');captured={};p.write=lambda name,rows,columns=None:captured.update({name:list(rows)}) if name in ('movement-rates.csv','slow-path-summary.csv') else None
    doc,data=p.load();p.reconcile(data);p.movement(data)
    context()
    return captured

def serial(v):
    if isinstance(v,D):return str(v)
    raise TypeError(str(type(v)))
def write_csv(path,rows):
    with path.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def build():
    check();a,t,c,l,s=run();out=HERE/'generated';out.mkdir(exist_ok=True)
    for name,rows in [('rounds',t),('cohorts',c),('pool-ledger',l),('summary',s)]:write_csv(out/(name+'.csv'),rows)
    p=p1_context();(out/'p1-context.json').write_text(json.dumps(p,default=serial,indent=2)+'\n')
    (out/'calibration.json').write_text(json.dumps({k:v for k,v in a.items() if k not in ['config','obs','base']},default=serial,indent=2)+'\n')
    lines=['# EX-12 finite results','','Illustrative SC-27/SC-28 matched work; 100 pools, full scores, 24 earning rounds, claims n+7. Amounts below aggregate those cohorts, not forecasts. Node-envelope delegator receipts exclude validator participant income.','','| Case | Lane | New principal LPT | Incoming node LPT | Source candidate node LPT | Donor-pool change LPT | Remaining donor change LPT | Operator cash USDC | Operator commission LPT |','| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for v in s:lines.append('| '+v['case']+' | '+v['lane']+' | '+' | '.join(f'{v[k]:.6f}' for k in ['gross_new_principal_lpt','incoming_delegator_lpt','source_moving_delegator_lpt','donor_pool_node_delta_lpt','remaining_donor_lpt_delta','target_net_cash_usdc','target_operator_commission_lpt'])+' |')
    lines+=['','Fresh eligible overlap22, existing overlap1 follow the frozen window and clocks; they are not observed latency or opportunity duration. Exit24/withdraw45 are fixed choices. Acquisition, liquidity, gas, opportunity cost and fresh outside return remain unknown. Donor eligibility is not registration; target already top-N eligible and voluntarily unregistered.','','Full tables: rounds.csv (368), cohorts.csv (192), pool-ledger.csv (19,200), summary.csv (8). Ledger minted fields are each earning cohort at its claim; rounds.csv places mint at the actual claim round and retains pending. Validator/treasury envelope mint is attributed to earning rounds; no distribution is invented. No earnings after23 are included.','']
    (out/'results.md').write_text('\n'.join(lines))
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file() and p.name!='hashes.json'}
    (out/'hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
    print('Built 368 observation rows; 192 earning cohorts; 19200 pool ledger rows; 8 summaries; frozen P1 movement context.')
if __name__=='__main__':build()
