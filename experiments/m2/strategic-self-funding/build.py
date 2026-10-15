#!/usr/bin/env python3
"""Finite connected strategic ledger. No supplement outcomes in the core stage."""
from collections import Counter
from decimal import Decimal as D
import hashlib

import fixtures as f
from adapter import Adapter, ZERO, ONE, EPS, checked_inputs, load_engine, replay_originals, write_json, write_jsonl, cash_feasible, capacity_feasible
import strategy as st

CORE_GROUPS = {'core', 'fee-leaning', 'aligned', 'native'}
CASH = 'organization_net_cash_usdc_after_controlled_outflows_and_costs'
VALUE = 'organization_net_value_usdc_equivalent_at_declared_lpt_price'


def provenance(state, vector_hash, manifest):
    return dict(profile=state['id'], parent=state['parent'], group=state['group'],
        structure=state['structure'], market=state['market'], actor_rank=state['actor_rank'], start=state['start'],
        snapshot_id=state['source_snapshot_id'], snapshot_content_sha256=state['source_content_sha256'],
        input_vector_sha256=vector_hash, october_text_sha256=manifest['sources']['october_text']['sha256'],
        october_pdf_sha256=manifest['sources']['october_pdf']['sha256'],
        source_round=4364, earning_round=state['earning_round'], horizon='earning cohort n+7',
        units='amounts: USDC or USDC-equivalent as named; tokens: LPT; shares/loss: fractions; capacity/jobs: divisible jobs; prices/cost: USDC/job',
        status='illustrative October accounting with measured calibration and native proxies',
        actor_assumption='native measured cuts/address-ownership proxy' if state['start']=='native' else
                         'illustrative quarter-ownership retention override' if state['id'].startswith('retention-') else 'standardized full organizational retention upper bound',
        nonactor_assumption='native measured cuts/address-ownership proxies retained, including synthetic roles',
        purpose='modeler-known reward-seeking real executed work without credited use; no observed misconduct',
        budget_period=state['budget_period'], budget_label='budget convention',
        price_usdc_per_job=state['controlled_price'], cost_usdc_per_job=state['controlled_cost'],
        declared_B_usdc=state['cash_loss_allowance_usdc'], declared_Qmax_jobs=state['additional_capacity_jobs'],
        reading=state['reading'], own_stake_fixed=True)


class Profile:
    def __init__(self, state, adapter):
        self.state, self.adapter = state, adapter
        self.actor = state['actor_rank']-1
        self.par = st.parameters(state)
        self.cache = {}
        self.base = self.evaluate(ZERO)

    def evaluate(self, x, useful=False):
        key = (x,useful)
        if key not in self.cache:
            s=self.state
            cash_ok=cash_feasible(s,x)
            capacity_ok=capacity_feasible(s,x)
            self.cache[key] = self.adapter.evaluate(s,x,useful=useful,diagnostic=not (cash_ok and capacity_ok))
        return self.cache[key]

    def increment(self, x):
        row = self.evaluate(x)[0][self.actor]
        reference = self.base[0][self.actor]
        value = row[VALUE]-reference[VALUE]
        f.require(abs(value-st.algebra_increment(self.state,x)) <= EPS, self.state['id']+': independent payoff agreement')
        return value

    def optimize(self, endpoint=None):
        candidates = st.action_candidates(self.state,endpoint)
        evaluated = [dict(kind=k,x_usdc=x,net_value_delta_usdc_equivalent=self.increment(x),
                          marginal_left=st.derivative(self.state,x,'left'),marginal_right=st.derivative(self.state,x))
                     for k,x in candidates.items()]
        best = max(evaluated,key=lambda r:(r['net_value_delta_usdc_equivalent'],-r['x_usdc']))
        return best,evaluated

    def metrics(self,x):
        rows,network,meta = self.evaluate(x)
        before,bnet,_ = self.base
        a,b = rows[self.actor],before[self.actor]
        honest_loss = sum((old['claimable_lpt']-new['claimable_lpt'] for i,(old,new) in enumerate(zip(before,rows)) if i!=self.actor),ZERO)
        gain = a['claimable_lpt']-b['claimable_lpt']
        unminted_release = bnet['mfs_unallocated_never_minted_lpt']-network['mfs_unallocated_never_minted_lpt']
        f.require(abs(gain-honest_loss-unminted_release) <= EPS,'Actor gain/peer loss/unminted identity')
        honest_before = sum((r['claimable_lpt'] for i,r in enumerate(before) if i!=self.actor),ZERO)
        honest_retained_loss = sum((old['organization_retained_lpt']-new['organization_retained_lpt']
            for i,(old,new) in enumerate(zip(before,rows)) if i!=self.actor),ZERO)
        honest_external_loss = sum((old['outside_delegator_lpt']-new['outside_delegator_lpt']
            for i,(old,new) in enumerate(zip(before,rows)) if i!=self.actor),ZERO)
        return dict(**meta,gross_invoices_usdc=x,
            recovered_organization_fee_delta_usdc=a['organization_retained_fee_usdc']-b['organization_retained_fee_usdc'],
            cash_delta_usdc=a[CASH]-b[CASH],received_organization_lpt_delta=a['organization_retained_lpt']-b['organization_retained_lpt'],
            net_value_delta_usdc_equivalent=self.increment(x),
            realized_cash_profit_usdc=a[CASH]-b[CASH],unsold_tokens_are_not_realized_cash=True,
            actor_gross_reward_gain_lpt=gain,honest_99_reward_loss_lpt=honest_loss,
            honest_99_baseline_reward_lpt=honest_before,honest_99_changed_reward_lpt=honest_before-honest_loss,
            honest_99_collective_relative_reward_loss=honest_loss/honest_before if honest_before else 'undefined: zero initial honest reward',
            honest_99_organization_retained_reward_loss_lpt=honest_retained_loss,
            honest_99_external_delegator_reward_loss_lpt=honest_external_loss,
            honest_99_organization_net_income_effect_usdc_equivalent=-honest_retained_loss*self.par['P'],
            honest_99_external_delegator_net_income_effect_usdc_equivalent=-honest_external_loss*self.par['P'],
            previously_unminted_allowance_change_lpt=unminted_release,
            previously_unminted_share_of_actor_gain=unminted_release/gain if gain else 'undefined: zero actor reward gain',
            peer_loss_share_of_actor_gain=honest_loss/gain if gain else 'undefined: zero actor reward gain',
            gain_decomposition_basis='gross node claimability; organizational retention separately reported; negative allowance change restores unminted allowance',
            accumulated_value_per_invoice=self.increment(x)/x if x else 'undefined: zero invoice',
            marginal_left=st.derivative(self.state,x,'left'), marginal_right=st.derivative(self.state,x),
            fee_limited_victim_dilution=x/(self.par['F']+x) if self.par['F']+x else 'undefined')


def reach(profile,x,optimum):
    p,s = profile.par,profile.state
    _,_,meta = profile.evaluate(x)
    return dict(**meta,x_usdc=x,before_or_at_actor_feasible_optimum=x<=optimum,
        before_or_at_actor_cap=p['cap'] is None or x<=p['cap'],
        cap_position='no cap' if p['cap'] is None else 'before cap' if x<p['cap'] else 'at cap' if x==p['cap'] else 'after cap',
        capacity_position='at the capacity boundary' if x==s['controlled_price']*s['additional_capacity_jobs'] else
                          'within declared capacity' if meta['capacity_feasible'] else 'beyond declared capacity',
        conduct_label='zero action' if x==0 else 'within feasible optimum' if meta['feasible'] and x<=optimum else
                     'harm-only spending beyond actor optimum' if meta['feasible'] else 'diagnostic; harm-only or additional funding/capacity required')


def stopping_label(state,optimum,cash_end,capacity_end,endpoint):
    p=st.parameters(state)
    if optimum==0: return 'zero action'
    if optimum==cash_end: return 'budget convention'
    if optimum==p['cap']: return 'stake cap'
    if optimum==capacity_end: return 'capacity endpoint'
    f.require(0<optimum<endpoint and (p['cap'] is None or optimum<p['cap']) and
              abs(st.derivative(state,optimum))<=EPS,'Interior stop must be a strictly feasible stationary point below cap')
    return 'interior stationary point'


def build_profiles(core_only=True):
    states,cal,manifest,networks,grid = checked_inputs()
    engine = load_engine()
    replay = replay_originals(engine)
    adapter = Adapter(engine,replay)
    out = f.HERE/('generated/core' if core_only else 'generated/full')
    out.mkdir(parents=True,exist_ok=True)
    summaries,points,landmarks,break_evens,comparisons = [],[],[],[],[]
    comparison_effects=[]
    lookup={}
    definitions={r['id']:r for r in grid['profiles']}
    effects_path = out/'pool-effects.jsonl'
    effects_count = 0
    with effects_path.open('wb') as effects:
        for sid,state in states.items():
            if core_only and state['group'] not in CORE_GROUPS:
                continue
            profile = Profile(state,adapter)
            p = profile.par
            cash_end = st.cash_endpoint(state,p)
            capacity_end = state['controlled_price']*state['additional_capacity_jobs']
            endpoint = capacity_end if cash_end is None else min(cash_end,capacity_end)
            feasible,candidates = profile.optimize(endpoint)
            unlimited,unlimited_candidates = profile.optimize()
            optimum = feasible['x_usdc']
            # Feasible candidates must obey the declared capacities; D2 is never
            # used to make a constrained candidate eligible.
            for candidate in candidates:
                meta = profile.evaluate(candidate['x_usdc'])[2]
                f.require(meta['feasible'] and not meta['temporary_capacity_used'],'Optimizer feasibility')
            roots,root_status = st.break_even_roots(state)
            base,base_net,_ = profile.base
            # Check EX-06 comparison's unchanged cap-headroom expression.
            wrapped = dict(base_net,**{'A_'+k:v for k,v in base[profile.actor].items()})
            legacy_cap = engine.comparison(wrapped,wrapped,wrapped,'A')['additional_gross_fees_to_stake_cap_usdc']
            f.require(p['cap'] is None or abs(legacy_cap-p['cap'])<=EPS,'EX-06 cap algebra agreement')
            dcap = p['head']/(ONE-p['a']) if p['a']<1 else ZERO
            dB = cash_end/(p['F']+cash_end) if cash_end is not None else ONE
            dS = ((p['a']*p['S']-state['vector'][profile.actor]['stake'])/(ONE-p['a'])
                   if p['a']>=p['s'] and p['a']<1 else 'not applicable: actual fee share below stake cap')
            if p['aligned_equality']:
                dS = ZERO
            critical = p['L']/(p['t']*p['score']*(ONE-p['a'])) if p['t']*p['score']>0 and p['cap']!=0 and p['a']<1 else 'no finite profitable ratio at cap or zero retention/score'
            stopping = stopping_label(state,optimum,cash_end,capacity_end,endpoint)
            prov = provenance(state,networks['vector_hashes'][sid],manifest)
            summary = dict(**prov,actual_initial_actor_fee_share=p['a'],actual_actor_stake_share=p['s'],
                actual_initial_fee_minus_stake_share=p['a']-p['s'],aligned_declared_equality=p['aligned_equality'],
                initial_node_reward_lpt=base[profile.actor]['claimable_lpt'],
                reward_retention=p['t'],fee_retention=p['z'],leakage_L=p['L'],
                scheduled_node_valued_allowance_to_outside_fee_ratio=p['N']*p['P']/p['F'],critical_ratio=critical,
                gross_reward_headroom_lpt=p['N']*p['head'],organizational_reward_headroom_lpt=p['N']*p['head']*p['t'],
                xcap_usdc=p['cap'],cash_endpoint_usdc=cash_end,capacity_endpoint_usdc=capacity_end,
                feasible_endpoint_usdc=endpoint,feasible_optimum=feasible,unconstrained_optimum=unlimited,
                candidate_evaluations=candidates,unconstrained_candidate_evaluations=unlimited_candidates,
                stopping_reason=stopping,capacity_checked_but_not_binding_profitable_optimum=optimum<capacity_end,
                dcap=dcap,dB=dB,single_fixed_stake_harm_limit=min(dcap,dB),
                headroom_interpretation='upper bound on single fixed-stake profit-seeking dilution; landmarks beyond it require harm-only spending or additional funding',
                added_stake_identity_lpt=dS,added_stake_scope='actual a>=s only, equality zero; cost/availability/delay/response deferred; aligned declared equality suppresses monetary quantization residual',
                nonzero_break_even_spending_usdc=roots,nonzero_break_even_status=root_status,
                no_action_actor=base[profile.actor],no_action_network=base_net,
                feasible_optimum_accounting=profile.metrics(optimum),unconstrained_optimum_accounting=profile.metrics(unlimited['x_usdc']))
            summaries.append(summary)
            for root in roots:
                f.require(abs(profile.increment(root))<=EPS,'Break-even root agreement')
                break_evens.append(dict(**prov,**reach(profile,root,optimum),net_value_delta_usdc_equivalent=profile.increment(root),landmark_kind='nonzero break-even'))
            selections = [('zero',ZERO),('one percent F',D('.01')*p['F']),('ten percent F',D('.10')*p['F']),
                ('feasible optimum',optimum),('feasible endpoint',endpoint),('cap',p['cap']),
                ('unconstrained optimum',unlimited['x_usdc']),('F harm-only diagnostic',p['F'])]
            deduplicated = {}
            for label,x in selections:
                if x is not None:
                    deduplicated.setdefault(x,[]).append(label)
            f.require(len(deduplicated)<=8,'Progression limit')
            for n,(x,labels) in enumerate(sorted(deduplicated.items())):
                rows,network,meta = profile.evaluate(x)
                useful,use_net,_ = profile.evaluate(x,True)
                for i,(a,b) in enumerate(zip(rows,useful)):
                    f.require(all(a[k]==b[k] for k in a if k not in ('internal_use_value_usdc_equivalent',VALUE)),'Useful pair accounting parity')
                f.require(network==use_net,'Useful pair network parity')
                point_id = f'{sid}:point-{n}'
                points.append(dict(**prov,point=point_id,selected_as=labels,**reach(profile,x,optimum),
                    accounting=profile.metrics(x),network=network,baseline_network=base_net,
                    actor=rows[profile.actor],useful_reference_actor=useful[profile.actor],
                    useful_reference_net_value_delta_usdc_equivalent=useful[profile.actor][VALUE]-base[profile.actor][VALUE],
                    useful_reference_use_value_usdc_equivalent=x/state['controlled_price'],
                    useful_reference_network=use_net,useful_reference_parity='all 100 rows identical except actor declared use and net value'))
                for i,(before,after) in enumerate(zip(base,rows)):
                    loss = before['claimable_lpt']-after['claimable_lpt']
                    status = lambda r:('fee-work appendix; no stake cap' if state['reading']=='appendix' else
                        'fee-limited' if r['fee_share']<r['stake_share'] else 'stake-limited' if r['fee_share']>r['stake_share'] else 'at cap equality')
                    effect = dict(**prov,point=point_id,x_usdc=x,**meta,source_rank=i+1,role='actor' if i==profile.actor else 'honest outside-service role',
                        baseline=before,changed=after,absolute_reward_loss_lpt=loss,
                        relative_reward_loss=loss/before['claimable_lpt'] if before['claimable_lpt'] else 'undefined: zero baseline reward',
                        unchanged_outside_fee_usdc=before['outside_spending_usdc'],
                        outside_fee_unchanged=before['outside_spending_usdc']==after['outside_spending_usdc'],
                        organization_net_income_effect_usdc_equivalent=after[VALUE]-before[VALUE],
                        baseline_limit=status(before),changed_limit=status(after),crossed_limit=status(before)!=status(after),
                        external_delegator_baseline_fee_usdc=before['outside_delegator_fee_usdc'],
                        external_delegator_changed_fee_usdc=after['outside_delegator_fee_usdc'],
                        external_delegator_baseline_pending_lpt=before['pending_lpt']*(ONE-before['reward_cut'])*(ONE-before['ownership_fraction']),
                        external_delegator_changed_pending_lpt=after['pending_lpt']*(ONE-after['reward_cut'])*(ONE-after['ownership_fraction']),
                        external_delegator_reward_loss_lpt=before['outside_delegator_lpt']-after['outside_delegator_lpt'],
                        external_delegator_net_income_effect_usdc_equivalent=(after['outside_delegator_fee_usdc']-before['outside_delegator_fee_usdc'])+
                            (after['outside_delegator_lpt']-before['outside_delegator_lpt'])*p['P'])
                    effects.write(f.serialize(effect)+b'\n'); effects_count += 1
            for i,v in enumerate(state['vector']):
                if i==profile.actor:
                    continue
                for target in (D('.05'),D('.10'),D('.20')):
                    x = st.individual_landmark(state,v,target)
                    item = dict(**prov,landmark_kind='individual honest-pool loss',source_rank=i+1,target_fraction=target)
                    if x is None:
                        item.update(status='undefined: zero baseline victim reward',x_usdc=None,
                                    cash_feasible='undefined',capacity_feasible='undefined',feasible='undefined')
                    else:
                        r = profile.evaluate(x)[0][i]
                        actual_loss = (base[i]['claimable_lpt']-r['claimable_lpt'])/base[i]['claimable_lpt']
                        f.require(abs(actual_loss-target)<=EPS,'Individual target-loss root agreement')
                        item.update(**reach(profile,x,optimum),status='defined',engine_actual_loss_fraction=actual_loss,
                            actor_net_value_delta_usdc_equivalent=profile.increment(x))
                    landmarks.append(item)
            honest_initial = sum((r['claimable_lpt'] for i,r in enumerate(base) if i!=profile.actor),ZERO)
            for target in (D('.05'),D('.10'),D('.20')):
                x = st.collective_landmark(state,target)
                item = dict(**prov,landmark_kind='collective honest-99 reward loss',source_rank=None,target_fraction=target)
                if x is None:
                    item.update(status='undefined: zero baseline honest reward',x_usdc=None,cash_feasible='undefined',capacity_feasible='undefined',feasible='undefined')
                else:
                    metrics = profile.metrics(x)
                    actual_loss = metrics['honest_99_reward_loss_lpt']/honest_initial
                    f.require(abs(actual_loss-target)<=EPS,'Collective target-loss root agreement')
                    item.update(**reach(profile,x,optimum),status='defined',engine_actual_loss_fraction=actual_loss,
                                actor_net_value_delta_usdc_equivalent=metrics['net_value_delta_usdc_equivalent'])
                landmarks.append(item)
            lookup[sid]=summary
            if state['group'] not in CORE_GROUPS:
                from supplement import comparison
                item,extra=comparison(state,profile,summary,lookup[state['parent']],definitions[sid],prov)
                comparisons.append(item);comparison_effects.extend(extra)
    expected=69 if core_only else 135
    f.require(len(summaries)==expected,'Exact frozen profile inventory')
    if core_only:
        f.require(Counter(r['group'] for r in summaries)==Counter(core=54,**{'fee-leaning':3,'aligned':9,'native':3}),'Core group inventory')
    write_json(out/'profiles.json',summaries)
    write_jsonl(out/'progressions.jsonl',points)
    write_jsonl(out/'loss-landmarks.jsonl',landmarks)
    write_jsonl(out/'break-even.jsonl',break_evens)
    write_json(out/'legacy-replay.json',replay)
    if not core_only:
        write_json(out/'comparisons.json',comparisons)
        write_jsonl(out/'comparison-pool-effects.jsonl',comparison_effects)
    lines = ['# Strategic self-funding: finite core accounting','',
        'Illustrative one-round October accounting, with measured round-4364 calibration. Native references use actual cuts and address-ownership proxies; other actors use full-retention upper bounds. Unsold LPT value is separate from realized cash.', '',
        '| Profile | Actual fee/stake shares | Ratio | Feasible invoices USDC | Cash loss USDC | Retained net value USDC-equivalent | Stop | Honest reward loss LPT | Unminted share of actor gain |',
        '| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | --- |']
    for r in sorted(summaries,key=lambda r:(r['group']!='native',r['profile'])):
        m=r['feasible_optimum_accounting']
        share=m['previously_unminted_share_of_actor_gain']
        lines.append(f"| {r['profile']} | {r['actual_initial_actor_fee_share']:.8f}/{r['actual_actor_stake_share']:.8f} | {r['scheduled_node_valued_allowance_to_outside_fee_ratio']:.4f} | {r['feasible_optimum']['x_usdc']:.8f} | {-m['cash_delta_usdc']:.8f} | {m['net_value_delta_usdc_equivalent']:.8f} | {r['stopping_reason']} | {m['honest_99_reward_loss_lpt']:.8f} | {share if isinstance(share,str) else format(share,'.6f')} |")
    lines += ['', 'The JSON/JSONL files retain full precision, all 100 pools at every point, useful/no-action references, cash and service feasibility, individual and collective loss thresholds, pending versus actual claims, envelopes, buyback, burn and net supply. Beyond-capacity points are hypothetical accounting only. Common control, profitable real work and anonymous source-linked modeled roles establish no misconduct.', '',
        ('The 69 core/control/reference profiles are computed;66 supplements/timelines/evidence mapping are excluded by this stage boundary.' if core_only else
         'All135 frozen one-round profiles are computed. Supplementary comparisons retain fixed parent actions where specified and reoptimized actions. Timelines and evidence mapping are in separate files. E2/P1 and studies3–8 remain pending.')]
    (out/'accounting.md').write_text('\n'.join(lines)+'\n')
    counts=dict(profiles=len(summaries),groups=dict(Counter(r['group'] for r in summaries)),progression_points=len(points),
                pool_effects=effects_count,loss_landmarks=len(landmarks),break_even_landmarks=len(break_evens),
                supplementary_outcomes=len(comparisons),comparison_pool_effects=len(comparison_effects),timelines=0,evidence_outcomes=0)
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file() and p.name!='manifest.json'}
    write_json(out/'manifest.json',dict(stage='core-only' if core_only else 'full-profiles',counts=counts,calibration=cal,file_sha256=hashes,
        frozen_inputs={k:hashlib.sha256((f.HERE/k).read_bytes()).hexdigest() for k in ('inputs.json','networks.json','scenarios.json','fixtures.py')},
        numerical_contract='Decimal 60/ROUND_HALF_EVEN receipts; agreement 1e-18; cash/capacity feasibility by exact fractions from original scalars; affordable cash endpoint at most one representable step below exact maximum, except accepted native-measured-1 at most two; no tolerance-expanded bounds',
        outcome_boundary='69 core/control/reference rows only' if core_only else '135 frozen one-round profiles; timeline/evidence mapping separate'))
    print(f"Built {'core' if core_only else 'full'}: {counts}; outputs experiments/m2/strategic-self-funding/generated/{'core' if core_only else 'full'}/")
    return dict(counts=counts,states=states,calibration=cal,manifest=manifest,networks=networks,grid=grid,adapter=adapter,summaries=lookup)


def build_core():
    return build_profiles(True)['counts']


if __name__=='__main__':
    build_core()
