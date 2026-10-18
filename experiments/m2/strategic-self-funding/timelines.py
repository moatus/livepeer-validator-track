"""Ten frozen four-earning-round stock/cohort ledgers through EX-06 account()."""
from copy import deepcopy
from decimal import Decimal as D

import fixtures as f
from adapter import ZERO,ONE,EPS,write_json,write_jsonl
from build import CASH,VALUE,provenance
import strategy as st


def scheduled(base,n):
    return base*(D(2)**(-D(n)/D(840)))


def build(run):
    adapter=run['adapter'];states=run['states'];summaries=run['summaries']
    dest=f.HERE/'generated/full'
    timelines=[];earnings=[];horizons=[];poolrows=[];cohortrows=[]
    for definition in run['grid']['timelines']:
        parent=states[definition['parent']];summary=summaries[definition['parent']]
        actor=parent['actor_rank']-1;par=st.parameters(parent)
        initial=parent['cash_loss_allowance_usdc'];remaining=initial
        x0=summary['feasible_optimum']['x_usdc'];cohorts=[];spend=ZERO;cash_used=ZERO
        prov=provenance(parent,run['networks']['vector_hashes'][parent['id']],run['manifest'])
        prov.pop('earning_round')
        prov.update(timeline=definition['id'],timeline_parent=parent['id'],horizon='absolute hypothetical earning/collection rounds',
                    budget_period=definition['budget_period'])
        for n,factor in zip(definition['earning_rounds'],definition['desired_factors']):
            desired=D(factor)*x0
            state=deepcopy(parent);state.update(earning_round=n,scheduled_ceiling_lpt=scheduled(parent['calibrated_base_ceiling_lpt'],n),cash_loss_allowance_usdc=remaining)
            for v in state['vector']:v['claim_at']=definition['claim_delay']
            prior=remaining;cash_end=st.cash_endpoint(state,st.parameters(state))
            actual=max(ZERO,min(desired,cash_end,state['controlled_price']*state['additional_capacity_jobs']))
            rows,network,meta=adapter.evaluate(state,actual,horizon=0)
            useful,unet,_=adapter.evaluate(state,actual,useful=True,horizon=0)
            before,bnet,_=adapter.evaluate(state,ZERO,horizon=0)
            loss=before[actor][CASH]-rows[actor][CASH]
            # Use the exact source-defined leakage budget, not reward receipts.
            stock_loss=par['L']*actual
            f.require(abs(loss-stock_loss)<=EPS and stock_loss<=prior,'Timeline actual net loss and stock affordability')
            remaining=prior-stock_loss
            f.require(remaining>=0 and meta['feasible'] and not meta['temporary_capacity_used'],'Timeline declared stock/capacity only')
            spend+=actual;cash_used+=stock_loss
            item=dict(**prov,earning_round=n,cohort_claim_at=n+definition['claim_delay'],claim_delay=definition['claim_delay'],
                scheduled_ceiling_lpt=state['scheduled_ceiling_lpt'],original_base_ceiling_lpt=parent['calibrated_base_ceiling_lpt'],
                derived_cohort_state_sha256=f.digest(state),desired_factor=D(factor),frozen_r0_optimum_usdc=x0,
                desired_invoices_usdc=desired,actual_invoices_usdc=actual,gross_fee_recovery_usdc=rows[actor]['organization_retained_fee_usdc']-before[actor]['organization_retained_fee_usdc'],
                actual_net_cash_loss_usdc=stock_loss,desired_net_loss_usdc=par['L']*desired,cash_shortfall_usdc=par['L']*(desired-actual),
                initial_stock_usdc=initial,stock_before_usdc=prior,stock_after_usdc=remaining,
                actual_jobs=actual/state['controlled_price'],original_Qmax_jobs=parent['additional_capacity_jobs'],
                cash_truncated=actual<desired and cash_end<=state['controlled_price']*state['additional_capacity_jobs'],
                capacity_truncated=actual<desired and state['controlled_price']*state['additional_capacity_jobs']<cash_end,
                tokens_sold_usdc=ZERO,replenishment_usdc=ZERO,stock_uses_token_receipts=False,
                actor_at_earning=rows[actor],useful_actor_at_earning=useful[actor],baseline_actor_at_earning=before[actor],network_at_earning=network,baseline_network_at_earning=bnet,
                execution_label=meta['execution_label'],cash_feasible=meta['cash_feasible'],capacity_feasible=meta['capacity_feasible'])
            earnings.append(item);cohorts.append((state,actual,item))
        # Same-stock one-round comparator, followed by three no-purchase cohorts.
        one_x=x0;final_h=definition['final_horizon']
        for h in range(final_h+1):
            changed_sum={};baseline_sum={};one_sum={}
            cash_delta=ZERO;collected_org=ZERO;pending_org=ZERO;one_cash=ZERO;one_collected=ZERO;one_pending=ZERO
            gross_actor_gain=ZERO;honest_loss=ZERO;release=ZERO
            useful_value=ZERO
            for n,(state,x,item) in enumerate(cohorts):
                if h<n:continue
                age=h-n
                after,network,_=adapter.evaluate(state,x,horizon=age)
                useful,useful_network,_=adapter.evaluate(state,x,useful=True,horizon=age)
                before,bnet,_=adapter.evaluate(state,ZERO,horizon=age)
                one_state=deepcopy(state);one_state['cash_loss_allowance_usdc']=initial
                one,onet,_=adapter.evaluate(one_state,one_x if n==0 else ZERO,horizon=age)
                a,b,o=after[actor],before[actor],one[actor]
                useful_value+=useful[actor][VALUE]-b[VALUE]
                cash_delta+=a[CASH]-b[CASH];collected_org+=a['organization_retained_lpt']-b['organization_retained_lpt']
                pending_org+=a['organization_pending_lpt']-b['organization_pending_lpt']
                one_cash+=o[CASH]-b[CASH];one_collected+=o['organization_retained_lpt']-b['organization_retained_lpt']
                one_pending+=o['organization_pending_lpt']-b['organization_pending_lpt']
                gross_actor_gain+=a['claimable_lpt']-b['claimable_lpt']
                loss=sum((old['claimable_lpt']-new['claimable_lpt'] for i,(old,new) in enumerate(zip(before,after)) if i!=actor),ZERO)
                honest_loss+=loss;release+=bnet['mfs_unallocated_never_minted_lpt']-network['mfs_unallocated_never_minted_lpt']
                for sums,source in ((changed_sum,network),(baseline_sum,bnet),(one_sum,onet)):
                    for key,value in source.items():
                        if key not in ('network_stake_lpt','burn_execution_price_usdc_per_lpt','lpt_valuation_price_usdc_per_lpt'):
                            sums[key]=sums.get(key,ZERO)+value
                cohortrows.append(dict(**prov,collection_horizon=h,earning_round=n,cohort_age=age,claim_at=item['cohort_claim_at'],
                    actual_invoices_usdc=x,network=network,baseline_network=bnet,one_round_stock_network=onet,
                    actor=a,useful_actor=useful[actor],baseline_actor=b,one_round_stock_actor=o))
                for i,(old,new) in enumerate(zip(before,after)):
                    poolrows.append(dict(**prov,collection_horizon=h,earning_round=n,cohort_age=age,source_rank=i+1,
                        role='actor' if i==actor else 'honest outside-service role',actual_invoices_usdc=x,
                        baseline_claimable_lpt=old['claimable_lpt'],changed_claimable_lpt=new['claimable_lpt'],
                        baseline_minted_lpt=old['minted_lpt'],changed_minted_lpt=new['minted_lpt'],
                        baseline_pending_lpt=old['pending_lpt'],changed_pending_lpt=new['pending_lpt'],
                        baseline_retained_lpt=old['organization_retained_lpt'],changed_retained_lpt=new['organization_retained_lpt'],
                        absolute_claimable_reward_loss_lpt=old['claimable_lpt']-new['claimable_lpt'],
                        relative_claimable_reward_loss=(old['claimable_lpt']-new['claimable_lpt'])/old['claimable_lpt'] if old['claimable_lpt'] else 'undefined: zero baseline reward',
                        organization_cash_delta_usdc=new[CASH]-old[CASH],
                        organization_net_income_delta_usdc_equivalent=new[VALUE]-old[VALUE],
                        outside_fee_usdc=new['outside_spending_usdc'],outside_fee_unchanged=old['outside_spending_usdc']==new['outside_spending_usdc'],
                        baseline_limit='fee-limited' if old['fee_share']<old['stake_share'] else 'stake-limited',
                        changed_limit='fee-limited' if new['fee_share']<new['stake_share'] else 'stake-limited',
                        external_delegator_pending_loss_lpt=(old['pending_lpt']-new['pending_lpt'])*(ONE-old['reward_cut'])*(ONE-old['ownership_fraction']),
                        external_delegator_minted_loss_lpt=old['outside_delegator_lpt']-new['outside_delegator_lpt']))
            f.require(abs(gross_actor_gain-honest_loss-release)<=EPS,'Timeline gross actor gain/peer loss/unminted identity')
            horizons.append(dict(**prov,collection_horizon=h,claim_delay=definition['claim_delay'],initial_stock_usdc=initial,
                actual_spent_invoices_usdc=sum((item['actual_invoices_usdc'] for item in earnings[-4:] if item['earning_round']<=h),ZERO),
                cash_delta_usdc=cash_delta,remaining_stock_usdc=initial-
                    sum((item['actual_net_cash_loss_usdc'] for item in earnings[-4:] if item['earning_round']<=h),ZERO),
                collected_retained_lpt_delta=collected_org,pending_retained_lpt_delta=pending_org,
                collected_value_delta_usdc_equivalent=cash_delta+collected_org*parent['valuation_usdc_per_lpt'],
                pending_value_delta_usdc_equivalent=pending_org*parent['valuation_usdc_per_lpt'],
                useful_net_value_delta_usdc_equivalent=useful_value,
                one_round_stock_cash_delta_usdc=one_cash,one_round_stock_collected_lpt_delta=one_collected,
                one_round_stock_pending_lpt_delta=one_pending,
                one_round_stock_collected_value_delta_usdc_equivalent=one_cash+one_collected*parent['valuation_usdc_per_lpt'],
                gross_actor_claimability_gain_lpt=gross_actor_gain,honest_99_claimability_loss_lpt=honest_loss,
                previously_unminted_allowance_change_lpt=release,
                changed_network_cumulative=changed_sum,no_purchase_network_cumulative=baseline_sum,one_round_stock_network_cumulative=one_sum,
                tokens_sold_usdc=ZERO,replenishment_usdc=ZERO,unsold_receipts_do_not_fund_jobs=True))
        final=horizons[-1]
        timelines.append(dict(**prov,definition=definition,frozen_r0_optimum_usdc=x0,initial_stock_usdc=initial,
            actual_total_invoices_usdc=spend,actual_total_net_loss_usdc=cash_used,remaining_stock_usdc=remaining,
            desired_total_invoices_usdc=sum((D(x) for x in definition['desired_factors']),ZERO)*x0,
            cap_below_stock=par['cap'] is not None and par['cap']<initial/par['L'],
            pacing_interpretation='no pacing conclusion: cap below initial stock; repeated actions bounded by per-round cap' if par['cap'] is not None and par['cap']<initial/par['L'] else
                'spending escalation, not isolated pacing' if definition['schedule']=='escalating' else 'equal-total comparison only; fixed schedules, not multi-round optima',
            final_horizon=final_h,first_claim_at=definition['claim_delay'],last_claim_at=3+definition['claim_delay'],
            final=final,emissions_schedule_decline_fraction=ONE-scheduled(parent['calibrated_base_ceiling_lpt'],3)/parent['calibrated_base_ceiling_lpt'],
            schedule_scope='earningr0..3 decline<.3%; collection/funding experiment, not meaningful decay test',
            useful_reference_scope='add actual executed jobs as declared use1/job; fees/costs/rewards and stocks unchanged',
            useful_total_use_value_usdc_equivalent=spend/parent['controlled_price']))
    lookup={r['timeline']:r for r in timelines}
    for rank in (1,50,90):
        a=lookup[f'timeline-R-{rank}-constant'];b=lookup[f'timeline-R-{rank}-equal-total']
        f.require(abs(a['actual_total_invoices_usdc']-b['actual_total_invoices_usdc'])<=EPS and
                  abs(a['actual_total_net_loss_usdc']-b['actual_total_net_loss_usdc'])<=EPS,'Equal-total actual spending/cost parity')
        for row in (a,b):
            row['equal_total_spending_and_costs_match']=True
            row['equal_total_peer']=b['timeline'] if row is a else a['timeline']
            row['equal_total_peer_final_value_delta']=b['final']['collected_value_delta_usdc_equivalent'] if row is a else a['final']['collected_value_delta_usdc_equivalent']
    write_json(dest/'timelines.json',timelines);write_jsonl(dest/'timeline-earnings.jsonl',earnings)
    write_jsonl(dest/'timeline-horizons.jsonl',horizons);write_jsonl(dest/'timeline-cohorts.jsonl',cohortrows)
    write_jsonl(dest/'timeline-pool-effects.jsonl',poolrows)
    print(f'Built10 timelines;{len(earnings)} earning rows;{len(horizons)} horizon rows;{len(cohortrows)} cohort horizon ledgers;{len(poolrows)} pool rows.')
    return dict(timelines=len(timelines),timeline_earning_rows=len(earnings),timeline_horizon_rows=len(horizons),timeline_cohort_rows=len(cohortrows),timeline_pool_rows=len(poolrows))
