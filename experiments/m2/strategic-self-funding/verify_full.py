"""Independent full-stage checks from frozen source states and arithmetic."""
from collections import defaultdict,Counter
from decimal import Decimal as D
import csv
import json
import hashlib

import fixtures as f
from independent_math import quantities,endpoints,optimum,payoff

Z,O,EPS=D(0),D(1),D('1e-18')
CASH='organization_net_cash_usdc_after_controlled_outflows_and_costs'
VALUE='organization_net_value_usdc_equivalent_at_declared_lpt_price'


def jsonl(path):
    with path.open() as stream:
        for line in stream:yield json.loads(line)


def supplementary_checks(states,profiles,out,check,near):
    lookup={r['profile']:r for r in profiles}
    comparisons=json.loads((out/'comparisons.json').read_text())
    check(len(comparisons)==66 and {r['profile'] for r in comparisons}=={sid for sid,s in states.items() if s['parent']},'exact 66 frozen supplementary comparisons')
    original=f.load_contract()[2];defs={r['id']:r for r in original['profiles']}
    points=list(jsonl(out/'progressions.jsonl'));pointlookup=defaultdict(list)
    for r in points:pointlookup[r['profile']].append(r)
    fixed_ids=set()
    for row in comparisons:
        sid=row['profile'];state=states[sid];parent=states[state['parent']];summary=lookup[sid];parent_row=lookup[state['parent']]
        p=quantities(state);pp=quantities(parent);parentx=optimum(pp,endpoints(pp)[1])[0]
        newx=optimum(p,endpoints(p)[1])[0];v=state['vector'][state['actor_rank']-1]
        near(row['parent_feasible_optimum_usdc'],parentx,'supplement parent optimum from source arithmetic')
        near(row['reoptimized_action_usdc'],newx,'supplement reoptimization from source arithmetic')
        near(row['reoptimized_accounting']['net_value_delta_usdc_equivalent'],payoff(p,newx),'supplement independent reoptimized payoff')
        check(row['overrides']==defs[sid]['overrides'],'exact named override only')
        group=state['group']
        if group=='one-factor':
            name=sid.split('-')[0]
            if name=='retention':check(v['k']==0 and v['d']==1 and v['w']==D('.25'),'quarter retention override')
            if name=='cost':
                check(v['caps']['generic']['c']==D('1.20') and v['caps']['generic']['q_out']==parent['vector'][state['actor_rank']-1]['caps']['generic']['q_out'],'cost override all actor outside jobs')
                near(row['no_purchase_actor']['execution_cost_usdc'],v['caps']['generic']['q_out']*D('1.20'),'matched same-cost no-purchase reference')
            if name=='valuation':check(state['valuation_usdc_per_lpt']==parent['valuation_usdc_per_lpt']*D('.1') and state['burn_price_usdc_per_lpt']==parent['burn_price_usdc_per_lpt'],'valuation not burn price')
            if name=='schedule':check(state['earning_round']==840 and state['scheduled_ceiling_lpt']==state['calibrated_base_ceiling_lpt']/2,'schedule base and earning half-life')
            basevalue=D('.94')*state['calibrated_base_ceiling_lpt']*state['burn_price_usdc_per_lpt']
            factor=D('.94')*state['scheduled_ceiling_lpt']*state['valuation_usdc_per_lpt']/basevalue
            measured=states[f'R-measured-{state["actor_rank"]}-low']
            base_ratios={'measured':D('.94')*measured['scheduled_ceiling_lpt']*measured['valuation_usdc_per_lpt']/measured['outside_F_usdc'],'near-parity':O}
            t=v['k']+(1-v['k'])*v['w']
            for market,R in base_ratios.items():
                expected=R*factor*t*(1-p['a'])-p['L'];r=row['other_scale_identity_signs'][market]
                near(r['marginal_value_at_zero'],expected,'other-scale derivative identity only')
                check(r['method']=='critical-ratio identity only; no extra profile or engine call','identity not added rows')
                check(r['positive_spending_sign'].startswith('positive')==(expected>0),'critical identity sign')
        if group=='appendix':
            check(state['reading']=='appendix' and summary['xcap_usdc'] is None,'three normalized full-score appendix rows')
            for point in pointlookup[sid]:near(point['network']['mfs_unallocated_never_minted_lpt'],0,'appendix allocation normalized')
        if group=='capability':
            check(v['caps']['generic']['capacity']==v['caps']['generic']['q_out'] and v['caps']['niche']['capacity']==state['additional_capacity_jobs'],'niche extra capacity allocated once')
            if sid=='niche-cost-setup-R-1':
                near(state['setup_if_positive_usdc'],2,'absolute niche setup2')
                for point in pointlookup[sid]:
                    x=D(point['x_usdc']);near(point['actor']['setup_cost_usdc'],D(2) if x>0 else Z,'setup once iff positive')
                    near(point['accounting']['cash_delta_usdc'],-D('.7')*x-(D(2) if x>0 else Z),'lower-cost setup within budget')
            else:
                near(row['reoptimized_action_usdc'],parentx,'matched capability optimum parity')
                near(row['reoptimized_accounting']['net_value_delta_usdc_equivalent'],parent_row['feasible_optimum_accounting']['net_value_delta_usdc_equivalent'],'matched capability payoff parity')
        if group in ('demand','price-routing','invoice-price'):
            fixed_ids.add(sid)
            check(state['cash_loss_allowance_usdc']==parent['cash_loss_allowance_usdc'] and state['additional_capacity_jobs']==parent['additional_capacity_jobs'],'response/invoice original bounds')
            near(row['fixed_parent_action_usdc'],parentx,'fixed parent action held')
            near(row['fixed_parent_action_accounting']['net_value_delta_usdc_equivalent'],payoff(p,parentx),'fixed parent action independent payoff')
            near(row['actual_outside_F_usdc'],sum((v['outside_fee_usdc'] for v in state['vector']),Z),'response denominator all100')
            near(row['outside_jobs_total'],sum((v['caps']['generic']['q_out'] for v in state['vector']),Z),'response outside jobs recomputed')
            near(row['outside_cost_total_usdc'],sum((v['caps']['generic']['q_out']*v['caps']['generic']['c'] for v in state['vector']),Z),'response cost recomputed')
        if group=='demand':check(state['outside_F_usdc']==2*parent['outside_F_usdc'],'doubling outside fees with fixed B/Q')
        if group=='price-routing':
            competitor=state['vector'][state['competitor_rank']-1]['caps']['generic']
            check(competitor['p']==D('.5') and competitor['c']==D('.30'),'competitor price covers all jobs; cost unchanged')
            near(row['outside_jobs_total'],sum((v['caps']['generic']['q_out'] for v in parent['vector']),Z),'routing preserves total outside jobs')
        if group=='budget':
            check(newx<p['capacity'] and row['capacity_does_not_bind_profitable_optimum'],'funding capacity only harm reach')
            check(row['capacity_binds_harm_only_reach']==(endpoints(p)[1]==p['capacity']),'funding physical endpoint reach')
            check(row['profitable_action_expands']==(newx>parentx),'added funding profit versus harm reach')
            near(row['harm_only_reach_fee_limited_dilution'],endpoints(p)[1]/(p['F']+endpoints(p)[1]),'funding harm dilution endpoint')
        if group=='invoice-price':
            check(state['controlled_price']==10 and state['controlled_cost']==D('.30') and v['caps']['generic']['p']==1,'invoice controlled price only, per-job cost unchanged')
            check(state['additional_capacity_jobs']==parent['additional_capacity_jobs'] and p['capacity']==D('2.5')*parent['original_F_usdc'],'price10 parent physical capacity and fee capacity')
            near(row['leakage_L'],D('.53'),'invoice leakage .53')
            near(row['leakage_floor'],D('.5'),'invoice leakage network floor .5')
            reported=parentx if defs[sid]['overrides']['action_policy']=='fixed-parent-optimum' else newx
            near(row['reported_action_usdc'],reported,'invoice fixed versus reoptimized policy')
            near(row['reported_accounting']['net_value_delta_usdc_equivalent'],payoff(p,reported),'invoice reported payoff through checked engine')
            point=next(r for r in pointlookup[sid] if D(r['x_usdc'])==state['outside_F_usdc'])
            check(point['capacity_feasible'] and not point['cash_feasible'] and not point['temporary_capacity_used'],'invoice xF capacity-feasible cash-infeasible no D2')
    by_fixed=defaultdict(set)
    for r in jsonl(out/'comparison-pool-effects.jsonl'):
        sid=r['profile'];by_fixed[sid].add(r['source_rank']);s=states[sid];p=quantities(s)
        old,new=r['baseline'],r['changed'];F=s['outside_F_usdc'];x=D(r['x_usdc'])
        near(new['fees_usdc'],D(old['fees_usdc'])+(x if r['source_rank']==s['actor_rank'] else Z),'fixed comparison fee change')
        near(new['claimable_lpt'],D('.94')*s['scheduled_ceiling_lpt']*min(D(new['fees_usdc'])/(F+x),s['vector'][r['source_rank']-1]['stake']/s['total_stake_lpt']),'fixed comparison all-pool entitlement')
        near(r['absolute_reward_loss_lpt'],D(old['claimable_lpt'])-D(new['claimable_lpt']),'fixed comparison all-pool loss')
    check(set(by_fixed)==fixed_ids and all(v==set(range(1,101)) for v in by_fixed.values()),'all100 pools for each eleven fixed-action comparison')


def timeline_checks(states,profiles,grid,out,check,near):
    definitions={r['id']:r for r in grid['timelines']};timelines=json.loads((out/'timelines.json').read_text())
    earnings=list(jsonl(out/'timeline-earnings.jsonl'));horizons=list(jsonl(out/'timeline-horizons.jsonl'))
    cohorts=list(jsonl(out/'timeline-cohorts.jsonl'));lookup={r['timeline']:r for r in timelines}
    check(len(timelines)==10 and set(lookup)==set(definitions),'exact ten fixed timeline selections')
    by_earn=defaultdict(list);by_h=defaultdict(dict);by_cohort=defaultdict(dict)
    for r in earnings:by_earn[r['timeline']].append(r)
    for r in horizons:by_h[r['timeline']][r['collection_horizon']]=r
    for r in cohorts:by_cohort[r['timeline']][(r['earning_round'],r['collection_horizon'])]=r
    pool_seen=defaultdict(set);pool_totals=defaultdict(lambda:defaultdict(lambda:Z))
    for r in jsonl(out/'timeline-pool-effects.jsonl'):
        key=(r['timeline'],r['earning_round'],r['collection_horizon']);rank=r['source_rank']
        check(rank not in pool_seen[key],'unique timeline pool');pool_seen[key].add(rank)
        definition=definitions[r['timeline']];s=states[definition['parent']];v=s['vector'][rank-1]
        n=r['earning_round'];h=r['collection_horizon'];F=s['outside_F_usdc'];x=D(r['actual_invoices_usdc'])
        # Independent schedule uses exp/log rather than the builder's power.
        E=s['calibrated_base_ceiling_lpt']*((-D(n)*D(2).ln()/D(840)).exp());N=D('.94')*E
        g=v['outside_fee_usdc'];ss=v['stake']/s['total_stake_lpt'];before=N*min(g/F,ss)
        after=N*min((g+(x if rank==s['actor_rank'] else Z))/(F+x),ss)
        eligible=h>=n+definition['claim_delay']
        near(r['baseline_claimable_lpt'],before,'independent timeline baseline allowance')
        near(r['changed_claimable_lpt'],after,'independent timeline all-pool allowance')
        near(r['changed_minted_lpt'],after if eligible else Z,'cohort actual mint once eligible')
        near(r['changed_pending_lpt'],Z if eligible else after,'cohort pending until delay')
        t=v['k']+(1-v['k'])*v['w'];near(r['changed_retained_lpt'],after*t if eligible else Z,'cohort external owner exclusion')
        check(r['outside_fee_unchanged'],'timeline outside service unchanged')
        for name in ('changed_claimable_lpt','changed_minted_lpt','changed_pending_lpt'):
            pool_totals[key][name]+=D(r[name])
    for tid,definition in definitions.items():
        s=states[definition['parent']];p=quantities(s);x0=optimum(p,endpoints(p)[1])[0];B=s['cash_loss_allowance_usdc'];remaining=B
        rows=by_earn[tid];check(len(rows)==4 and [r['earning_round'] for r in rows]==[0,1,2,3],'four earning rows per timeline')
        spend=Z;loss=Z
        for n,r in enumerate(rows):
            desired=D(definition['desired_factors'][n])*x0;cash=remaining/p['L']
            while p['L']*cash>remaining:cash=cash.next_minus()
            x=min(desired,cash,p['capacity']);old=remaining;remaining-=p['L']*x
            near(r['frozen_r0_optimum_usdc'],x0,'timeline r0 optimizer from frozen source')
            near(r['desired_invoices_usdc'],desired,'timeline exact desired schedule')
            near(r['actual_invoices_usdc'],x,'timeline stock/capacity truncation')
            near(r['stock_before_usdc'],old,'timeline initial shared stock progression')
            near(r['stock_after_usdc'],remaining,'timeline nonnegative stock no receipts funding')
            check(remaining>=0 and p['L']*x<=old and x/s['controlled_price']<=s['additional_capacity_jobs'],'timeline exact cash/capacity feasibility')
            near(r['cash_shortfall_usdc'],p['L']*(desired-x),'timeline desired cash shortfall')
            check(D(r['tokens_sold_usdc'])==D(r['replenishment_usdc'])==0 and not r['stock_uses_token_receipts'],'no sales/replenishment/reinvestment')
            near(r['useful_actor_at_earning'][VALUE],D(r['actor_at_earning'][VALUE])+x/s['controlled_price'],'timeline useful same-cost reference')
            spend+=x;loss+=p['L']*x
        final=lookup[tid];near(final['actual_total_invoices_usdc'],spend,'timeline total actual spend')
        near(final['actual_total_net_loss_usdc'],loss,'timeline total actual loss')
        near(final['remaining_stock_usdc'],remaining,'timeline final stock')
        check(final['cap_below_stock']==(p['cap']<B/p['L']),'cap-below-stock qualification')
        if final['cap_below_stock']:check(final['pacing_interpretation'].startswith('no pacing conclusion'),'no cap-below-stock pacing conclusion')
        check(set(by_h[tid])==set(range(definition['final_horizon']+1)),'every collection horizon through final')
        for h,row in by_h[tid].items():
            earned=[r for r in rows if r['earning_round']<=h]
            cash=-sum((D(r['actual_net_cash_loss_usdc']) for r in earned),Z)
            near(row['cash_delta_usdc'],cash,'collection horizon cash incurred once')
            near(row['remaining_stock_usdc'],B+cash,'collection cannot replenish stock')
            retained_gain=Z;pending_gain=Z;one_gain=Z
            aggregates=defaultdict(lambda:Z)
            for r in earned:
                n=r['earning_round'];cohort=by_cohort[tid][(n,h)];key=(tid,n,h)
                check(pool_seen[key]==set(range(1,101)),'all100 timeline pools at each cohort horizon')
                for name,poolname in [('claimable_node_lpt_at_horizon','changed_claimable_lpt'),('node_actually_minted_lpt_at_horizon','changed_minted_lpt'),('pending_unclaimed_node_lpt','changed_pending_lpt')]:
                    near(cohort['network'][name],pool_totals[key][poolname],'timeline all-pool aggregate '+name)
                a,b,o=cohort['actor'],cohort['baseline_actor'],cohort['one_round_stock_actor']
                retained_gain+=D(a['organization_retained_lpt'])-D(b['organization_retained_lpt'])
                pending_gain+=D(a['organization_pending_lpt'])-D(b['organization_pending_lpt'])
                one_gain+=D(o['organization_retained_lpt'])-D(b['organization_retained_lpt'])
                for k in ('scheduled_ceiling_lpt','node_actually_minted_lpt_at_horizon','pending_unclaimed_node_lpt','mfs_unallocated_never_minted_lpt','score_withheld_unminted_lpt','validator_full_mint_lpt','treasury_full_mint_lpt','tokens_burned_lpt','total_actual_mint_lpt'):
                    aggregates[k]+=D(cohort['network'][k])
                near(cohort['useful_actor'][VALUE],D(a[VALUE])+D(r['actual_invoices_usdc'])/s['controlled_price'],'timeline useful cohort horizon parity')
                check(D(o['controlled_spending_usdc'])==(x0 if n==0 else Z),'one-round same-stock comparator only r0 action')
            near(row['collected_retained_lpt_delta'],retained_gain,'collection retained tokens')
            near(row['pending_retained_lpt_delta'],pending_gain,'pending distinct from collected')
            near(row['collected_value_delta_usdc_equivalent'],cash+retained_gain*s['valuation_usdc_per_lpt'],'horizon realized cash versus valued unsold tokens')
            near(row['useful_net_value_delta_usdc_equivalent'],cash+retained_gain*s['valuation_usdc_per_lpt']+sum((D(r['actual_invoices_usdc'])/s['controlled_price'] for r in earned),Z),'useful horizon declared use only')
            near(row['one_round_stock_cash_delta_usdc'],-p['L']*x0,'one-round same-stock cash comparator')
            near(row['one_round_stock_collected_value_delta_usdc_equivalent'],-p['L']*x0+one_gain*s['valuation_usdc_per_lpt'],'one-round same-stock collected payoff')
            for k,value in aggregates.items():near(row['changed_network_cumulative'][k],value,'cumulative cohort accounting '+k)
            near(aggregates['scheduled_ceiling_lpt'],aggregates['node_actually_minted_lpt_at_horizon']+aggregates['pending_unclaimed_node_lpt']+aggregates['mfs_unallocated_never_minted_lpt']+aggregates['score_withheld_unminted_lpt']+aggregates['validator_full_mint_lpt']+aggregates['treasury_full_mint_lpt'],'timeline scheduled/mint/pending/permanent conservation')
        first=definition['claim_delay'];last=3+first
        near(by_h[tid][first-1]['collected_retained_lpt_delta'],0,'no collection before first cohort age')
        near(by_h[tid][last]['pending_retained_lpt_delta'],0,'no pending intervention at final claim')
        check(final['final_horizon']==last and D(final['emissions_schedule_decline_fraction'])<D('.003'),'final horizon and no short decay inference')
    for rank in (1,50,90):
        c=lookup[f'timeline-R-{rank}-constant'];e=lookup[f'timeline-R-{rank}-equal-total'];r=lookup[f'timeline-R-{rank}-escalating']
        near(c['actual_total_invoices_usdc'],e['actual_total_invoices_usdc'],'constant/equal-total actual spend parity')
        near(c['actual_total_net_loss_usdc'],e['actual_total_net_loss_usdc'],'constant/equal-total actual cost parity')
        near(r['desired_total_invoices_usdc'],D('2.5')*D(c['desired_total_invoices_usdc']),'escalating desired spending2.5x not pacing')
    seven=lookup['timeline-R-1-escalating'];fourteen=lookup['timeline-R-1-escalating-delay14']
    near(seven['actual_total_invoices_usdc'],fourteen['actual_total_invoices_usdc'],'delay does not finance more jobs')
    near(seven['final']['collected_value_delta_usdc_equivalent'],fourteen['final']['collected_value_delta_usdc_equivalent'],'delay changes collection horizon not full-score final value')


def evidence_checks(out,check):
    document=json.loads((out/'evidence-scope.json').read_text());rows=document['rows']
    config_path=f.ROOT/'experiments/m2/evidence-capability-pricing/config.json';config=json.loads(config_path.read_text())
    check(document['source_config_sha256']==hashlib.sha256(config_path.read_bytes()).hexdigest(),'evidence existing config source hash')
    check({r['id'] for r in rows}=={'existing-niche','existing-discount','new-strategic-volume','new-useful-pairs','undisclosed-control','invoice10','median0-algebra'},'exact compact evidence scope selection')
    with (config_path.parent/'verdicts.csv').open() as stream:verdicts=list(csv.DictReader(stream))
    check(len(verdicts)==64 and {r['verdict'] for r in verdicts}=={'does not separate'},'original64 keyed verdict scope only')
    for row in rows:
        check(set(row['inventory_records'])<=set(config['evidence_records']),'no new obtainable record/source kinds')
        check(all(row.get(k) for k in ('modeler_purpose','public_observations','disclosed_observations','rule_definition','procedural_response','disclosure_premise','verdict_scope')),'purpose/observations/rule/procedure/disclosure columns complete')
        if row['id'].startswith('existing-'):
            check('n+1' in row['disclosure_premise'] and 'n+5' in row['disclosure_premise'] and 'no extension' in row['verdict_scope'],'exact disclosure premise retained')
        else:check('not examined' in row['disclosure_premise'] and ('not examined' in row['verdict_scope'] or row['verdict_scope']=='algebra only; no verdict'),'unpacketed choices inherit no verdict')
    invoice=next(r for r in rows if r['id']=='invoice10')
    check('P-LIST' in invoice['public_observations'] and 'no price anomaly detector' in invoice['procedural_response'],'price observability without detector inference')
    check(document['limits'].endswith('E2/P1/studies3–8 remain pending.'),'pending practical evidence preserved')
