"""The 66 frozen comparisons, using the shared Profile and EX-06 adapter."""
from decimal import Decimal as D

from adapter import ZERO,ONE,EPS
import fixtures as f


def comparison(state,profile,summary,parent,definition,prov):
    """No supplementary state or factor product is constructed here."""
    p=profile.par;group=state['group'];oldx=parent['feasible_optimum']['x_usdc']
    newx=summary['feasible_optimum']['x_usdc'];base,bnet,_=profile.base
    fixed=group in ('demand','price-routing','invoice-price')
    policy=definition['overrides'].get('action_policy','reoptimize')
    reported=oldx if policy=='fixed-parent-optimum' else newx
    result=dict(**prov,comparison_kind=group,overrides=definition['overrides'],
        action_policy=policy,parent_feasible_optimum_usdc=oldx,
        parent_net_value_delta_usdc_equivalent=parent['feasible_optimum_accounting']['net_value_delta_usdc_equivalent'],
        reoptimized_action_usdc=newx,reoptimized_accounting=profile.metrics(newx),
        reported_action_usdc=reported,reported_accounting=profile.metrics(reported),
        no_purchase_actor=base[profile.actor],no_purchase_network=bnet,
        outside_jobs_total=sum((v['caps']['generic']['q_out'] for v in state['vector']),ZERO),
        outside_cost_total_usdc=sum((v['caps']['generic']['q_out']*v['caps']['generic']['c'] for v in state['vector']),ZERO),
        original_budget_usdc=parent['declared_B_usdc'],current_budget_usdc=state['cash_loss_allowance_usdc'],
        original_additional_capacity_jobs=parent['declared_Qmax_jobs'],current_additional_capacity_jobs=state['additional_capacity_jobs'],
        actual_outside_F_usdc=state['outside_F_usdc'],original_parent_F_usdc=state['original_F_usdc'],
        critical_ratio=summary['critical_ratio'],leakage_L=p['L'],leakage_floor=ONE-D('.5')*p['z'],
        dcap=summary['dcap'],dB=summary['dB'],single_fixed_stake_harm_limit=summary['single_fixed_stake_harm_limit'],
        appendix_scope='normalized fee-work, no stake cap; dcap1 denotes limiting dilution at infinite invoices' if state['reading']=='appendix' else 'primary MFS fixed stake')
    if group=='one-factor':
        original_value=D('.94')*state['calibrated_base_ceiling_lpt']*state['burn_price_usdc_per_lpt']
        scale=p['N']*p['P']/original_value
        # Only the derivative/critical-ratio identity is used at other scales.
        _,networks,_=f.load_contract()
        measured=D(networks['calibration']['measured_ratio'])
        result['other_scale_identity_signs']={}
        for market,ratio in (('measured',measured),('near-parity',ONE)):
            margin=ratio*scale*p['t']*(ONE-p['a'])-p['L']
            result['other_scale_identity_signs'][market]=dict(
                method='critical-ratio identity only; no extra profile or engine call',
                effective_scheduled_reward_fee_ratio=ratio*scale,
                marginal_value_at_zero=margin,
                positive_spending_sign='positive infinitesimal value; below cap and zero setup' if margin>0 else
                    'zero action by concavity; nonpositive initial derivative')
    if group=='budget':
        parent_end=parent['feasible_endpoint_usdc'];endpoint=summary['feasible_endpoint_usdc']
        result.update(profitable_action_expands=newx>oldx,
            added_funding_effect='expands profitable optimum and harm-only reach' if newx>oldx else 'profitable optimum unchanged; only harm-only reach expands' if endpoint>parent_end else 'no change to profitable optimum or physical harm reach',
            harm_only_reach_endpoint_usdc=endpoint,
            harm_only_reach_fee_limited_dilution=endpoint/(p['F']+endpoint),
            capacity_binds_harm_only_reach=endpoint==summary['capacity_endpoint_usdc'],
            capacity_does_not_bind_profitable_optimum=newx<summary['capacity_endpoint_usdc'])
        f.require(result['capacity_does_not_bind_profitable_optimum'],'Defined funding study has no capacity-bound profitable optimum')
    if group=='invoice-price':
        result.update(parent_price_usdc_per_job=ONE,controlled_price_usdc_per_job=state['controlled_price'],
            same_fee_jobs_at_parent_price=reported,same_fee_jobs_at_controlled_price=reported/state['controlled_price'],
            parent_leakage_L=parent['leakage_L'],parent_critical_ratio=parent['critical_ratio'],
            physical_capacity_preserved=state['additional_capacity_jobs']==parent['declared_Qmax_jobs'],
            fee_capacity_usdc=state['controlled_price']*state['additional_capacity_jobs'],
            price_evidence_scope='maps only existing EX-07 payment/quote records; no verdict or detector')
    effects=[]
    if fixed:
        changed,network,meta=profile.evaluate(oldx)
        useful,use_net,_=profile.evaluate(oldx,True)
        result.update(fixed_parent_action_usdc=oldx,fixed_parent_action_accounting=profile.metrics(oldx),
            fixed_parent_action_network=network,fixed_parent_action_actor=changed[profile.actor],
            fixed_parent_useful_actor=useful[profile.actor],fixed_parent_useful_network=use_net,
            response_scope='fixed parent action versus matched changed-state no-purchase; reoptimization separately reported')
        for i,(before,after) in enumerate(zip(base,changed)):
            loss=before['claimable_lpt']-after['claimable_lpt']
            effects.append(dict(**prov,**meta,comparison_action='fixed parent action',x_usdc=oldx,
                source_rank=i+1,role='actor' if i==profile.actor else 'honest outside-service role',baseline=before,changed=after,
                absolute_reward_loss_lpt=loss,relative_reward_loss=loss/before['claimable_lpt'] if before['claimable_lpt'] else 'undefined: zero baseline reward',
                organization_net_income_effect_usdc_equivalent=after['organization_net_value_usdc_equivalent_at_declared_lpt_price']-before['organization_net_value_usdc_equivalent_at_declared_lpt_price'],
                external_delegator_reward_loss_lpt=before['outside_delegator_lpt']-after['outside_delegator_lpt']))
    if group=='capability':
        result['capability_scope']='identical matched price/cost/setup accounting; no separate reward pool' if state['setup_if_positive_usdc']==0 else 'rank1 lower cost .20/job, setup2 once iff positive, inside B; separate matched no-purchase reference'
    return result,effects
