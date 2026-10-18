#!/usr/bin/env python3
"""EX-11: finite offline scoring/pay overlay and exact P1 seat arithmetic."""
from copy import deepcopy
from decimal import Decimal as D, getcontext
from pathlib import Path
import base64
import csv
import hashlib
import importlib.util
import json
import zlib

getcontext().prec = 100
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ZERO, ONE = D(0), D(1)
WEI = 10**18


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def serialize(obj):
    return (json.dumps(obj, default=str, sort_keys=True, indent=2, ensure_ascii=False)+'\n').encode()


def digest(obj):
    return hashlib.sha256(serialize(obj)).hexdigest()


def aggregate(scores, rule, n=33, quorum=17):
    """Fixed active set; None is absence, never an adverse finding."""
    if len(scores) != n or rule not in ('F', 'Q') or not 1 <= quorum <= n:
        raise ValueError('Invalid aggregation contract')
    if any(s is not None and (not D(str(s)).is_finite() or not ZERO <= D(str(s)) <= ONE) for s in scores):
        raise ValueError('Invalid score')
    submitted = [D(str(s)) for s in scores if s is not None]
    if rule == 'Q' and len(submitted) < quorum:
        return ONE
    values = sorted([ONE if s is None else D(str(s)) for s in scores] if rule == 'F' else submitted)
    mid = len(values)//2
    return values[mid] if len(values)%2 else (values[mid-1]+values[mid])/2


def compensation(seats, envelope, weights='stake', eligible=None):
    """Distribute existing full mint; no mint operation occurs here."""
    if envelope < ZERO or weights not in ('stake', 'equal'):
        raise ValueError('Invalid compensation contract')
    eligible = [True]*len(seats) if eligible is None else eligible
    if len(eligible) != len(seats):
        raise ValueError('Eligibility length')
    a = [p['stake'] if weights == 'stake' else ONE for p in seats]
    if any(x < ZERO for x in a):
        raise ValueError('Negative weight')
    denom = sum((x for x,e in zip(a,eligible) if e), ZERO)
    if any(eligible) and denom == ZERO:
        raise ValueError('Undefined zero eligible weight denominator')
    receipts = []
    for p,x,e in zip(seats,a,eligible):
        gross = envelope*x/denom if e else ZERO
        operator = gross*p['k']
        owned = gross*(ONE-p['k'])*p['w']
        outside = gross*(ONE-p['k'])*(ONE-p['w'])
        receipts.append(dict(address=p['address'], eligible=e, weight=x,
            gross_lpt=gross, operator_commission_lpt=operator, owned_delegator_lpt=owned,
            retained_lpt=operator+owned, outside_delegator_lpt=outside))
    return dict(split=weights, eligible_count=sum(eligible), weight_denominator=denom if any(eligible) else None,
                gross_envelope_lpt=envelope, undistributed_minted_lpt=envelope if not any(eligible) else ZERO,
                recipients=receipts)


def utility_delta(price, validator_delta_lpt, node_exposure_delta_lpt, effort_delta,
                  opportunity_delta, allocated_tool_delta, residual_delta):
    """USDC-equivalent per cohort; explicit residual, never an assumed benefit."""
    return price*(validator_delta_lpt+node_exposure_delta_lpt)-effort_delta-opportunity_delta-allocated_tool_delta+residual_delta


def affordable_cost(price, retained_validator_lpt, exposure_delta_lpt=ZERO, residual_delta=ZERO):
    """Join iff incremental effort+opportunity+allocated tooling <= this RHS."""
    return price*(retained_validator_lpt+exposure_delta_lpt)+residual_delta


def added_capital(stakes, k=0, d=0):
    """Integer wei; k,d are separate controls in the frozen experiment."""
    count, rank = 17-k, 17+k+d
    return dict(new_nodes=count, cutoff_original_rank=rank,
        threshold_per_node_wei=stakes[rank-1]+1,
        new_capital_wei=count*(stakes[rank-1]+1),
        existing_coordinated_wei=sum(stakes[:k]), declined_count=d, coordinated_count=k)


def redistribute(stakes):
    available = 0
    for j in range(1,len(stakes)-17+1):
        available += stakes[j-1]
        required = 17*(stakes[17+j-1]+1)
        if available > required:
            return dict(donor_pool_count=j, donor_controlled_wei=available,
                cutoff_original_rank=17+j, threshold_per_node_wei=stakes[17+j-1]+1,
                redistributed_wei=required, leftover_outside_eligible_wei=available-required,
                new_capital_wei=0, new_nodes=17, existing_coordinated_wei=available,
                coordinated_count=0, declined_count=0)
    raise ValueError('No sufficient donor set')


def seat_tables():
    """Decode only frozen P1 checkpoint raw pages; no analyzer/generated input."""
    doc = json.loads((HERE.parent/'current-system-data-notes/livepeer-arbitrum-p1-20260717-20261015-v1.json').read_text())
    canonical = json.dumps({k:v for k,v in doc.items() if k!='integrity'}, sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
    if hashlib.sha256(canonical).hexdigest() != doc['integrity']['content_sha256']:
        raise ValueError('P1 content integrity')
    sources = doc['provenance']['sources']
    ranks, summaries, table = [], [], []
    for block,refs in sorted(doc['data']['transcoders'].items(),key=lambda x:int(x[0])):
        pools = []
        for ref in refs:
            response = json.loads(zlib.decompress(base64.b64decode(sources[ref]['raw_response_zlib_base64'])))
            pools.extend(response['data']['transcoders'])
        def wei(p):
            v = D(p['totalStake'])*WEI
            if v != int(v) or v < 0: raise ValueError('Non-exact P1 wei')
            return int(v)
        pools.sort(key=lambda p:(-wei(p),p['id']))
        if len({p['id'] for p in pools}) != len(pools): raise ValueError('Duplicate P1 pool')
        stakes = [wei(p) for p in pools]
        total = sum(stakes)
        # Active-round stake is a different RPC denominator, retained separately.
        state = next(x for x in doc['data']['state'] if str(x['block'])==block and x['signature']=='getTotalBonded()')
        raw = json.loads(zlib.decompress(base64.b64decode(sources[state['source']]['raw_response_zlib_base64'])))['result']
        summary = dict(block=int(block), population=len(pools), positive_stake_count=sum(x>0 for x in stakes),
            active_flag_count=sum(p['active'] for p in pools), live_pool_stake_wei=total,
            active_round_bonded_wei=int(raw,16), rank17_wei=stakes[16], rank33_wei=stakes[32],
            top33_registered_count=sum(p['status']=='Registered' for p in pools[:33]))
        summaries.append(summary)
        for rank,p in enumerate(pools,1):
            ranks.append(dict(block=int(block), rank=rank,address=p['id'],stake_wei=wei(p),
                active=p['active'],status=p['status'],activation_round=p['activationRound'],
                deactivation_round=p['deactivationRound'],live_pool_denominator_wei=total))
        for k,d in [(0,0),(1,0),(3,0),(5,0),(0,5),(0,10),(0,16)]:
            table.append(dict(id=f'S{len(table)+1:02}', premise='new capital', **summary, **added_capital(stakes,k,d),
                acquisition_control_cost_usdc='unknown', liquidity='unknown',
                premise_note='All opt in except largest d declines; fixed incumbents; existing largest k coordinated; strict +1 wei entrants'))
        table.append(dict(id=f'S{len(table)+1:02}',premise='redistribution',**summary,**redistribute(stakes),
            acquisition_control_cost_usdc='unknown',liquidity='unknown',
            premise_note='Smallest number j of highest-stake donor pools; control of all delegated stake stipulated; strict available > required'))
    return table,ranks,summaries


class Model:
    def __init__(self):
        self.engine = module('ex11_ex06',HERE.parent/'capability-pricing/build.py')
        self.config,self.grid,self.observed,base,_ = self.engine.load_inputs()
        self.base = self.engine.main_states(self.config,self.grid,base)['S00']
        self.base_hash = digest(self.base)
        ranked = sorted(self.base,key=lambda p:(-p['stake'],p['address']))
        self.seats = ranked[:33]
        self.focal = ranked[1]['address']
        self.target = self.config['selected_operators']['A']
        self.ceiling = self.observed['scheduled_mint_ceiling_lpt']
        self.price = D(self.config['lpt_valuation_price'])
        self.burn_price = D(self.config['burn_execution_price'])

    def ledger(self, score=ONE, age=0, claim=7, horizon=7):
        pools = deepcopy(self.base)
        for p in pools:
            if p['address']==self.target:
                p['score'],p['claim_at'] = score,claim
        # Only the three declared schedule ages are numerical comparisons.
        if age not in (0,840,1680): raise ValueError('Undeclared schedule age')
        ceiling = self.ceiling/(2**(age//840))
        rows,network = self.engine.account(pools,ceiling,self.price,self.burn_price,horizon)
        pay = compensation(self.seats,network['validator_full_mint_lpt'])
        participants = [dict(address=p['address'],input_stake_lpt=p['stake'],applied_score=p['score'],claim_at=p['claim_at'],**r) for p,r in zip(pools,rows)]
        return dict(score=score,earning_schedule_age=age,claim_at=claim,horizon=horizon,
            participants=participants,network=network,validator_overlay=pay,
            costs=dict(network_shared_tool_usdc='K_tool (unknown; charged once)',
                private_effort_usdc='c_i(a), unknown',opportunity_usdc='o_i(a), unknown',
                participant_tool_allocation_usdc='alpha_i(a)*K_tool, unknown',
                execution_costs='unchanged original participant execution_cost_usdc'),
            source_identity=dict(snapshot_id=self.config['snapshot_id'],round=self.observed['round_id'],
                original_s00_sha256=self.base_hash, target=self.target,focal_validator=self.focal))

    def action(self,case,contract):
        score = contract['actions'][case['action']][case['evidence']]
        scores = [ZERO]*case['others_zero']+[ONE]*case['others_one']+[None]*case['others_missing']+[score]
        median = aggregate(scores,case['aggregation'])
        ledger = self.ledger(median)
        target = next(p for p in ledger['participants'] if p['address']==self.target)
        focal = next(p for p in ledger['participants'] if p['address']==self.focal)
        pay = next(p for p in ledger['validator_overlay']['recipients'] if p['address']==self.focal)
        row = dict(**case,submission=score,aggregate_multiplier=median,
            basis=contract['actions'][case['action']]['basis'],
            retained_validator_lpt=pay['retained_lpt'], outside_validator_delegator_lpt=pay['outside_delegator_lpt'],
            retained_validator_value_usdc_equivalent=pay['retained_lpt']*self.price,
            target_minted_lpt=target['minted_lpt'], target_retained_lpt=target['organization_retained_lpt'],
            target_outside_delegator_lpt=target['outside_delegator_lpt'],
            focal_own_node_retained_lpt=focal['organization_retained_lpt'],
            cross_target_value_coefficient_usdc=self.price*target['minted_lpt'],
            conditional_utility='P_claim*(retained_G_i + native_own_node_R_i + sum_cross x_ij*R_j) - c_i(a) - o_i(a) - alpha_i(a)*K_tool + Z_i(a); add invariant ledger cash',
            participation_validator_only_rhs_usdc_equivalent=affordable_cost(self.price,pay['retained_lpt']),
            action_invariant_cash_usdc=focal['organization_net_cash_usdc_after_controlled_outflows_and_costs'],
            native_baseline_value_before_unknown_validator_costs_usdc_equivalent=focal['organization_net_value_usdc_equivalent_at_declared_lpt_price']+pay['retained_lpt']*self.price,
            participation_condition='incremental c+o+alpha*K_tool <= P_claim*retained_G_i + P_claim*sum_j x_ij*(R_j(a)-R_j(replacement)) + DeltaZ; replacement scores unknown outside C01-C03',
            valuation_threshold='P_claim >= (incremental c+o+alpha*K_tool-DeltaZ)/(retained_G_i + sum_j x_ij*DeltaR_j) only if denominator > 0; reverse if < 0; if zero require costs <= DeltaZ')
        return row,ledger


def run():
    module('ex11_pins',HERE/'check_inputs.py').check()
    contract = json.loads((HERE/'cases.json').read_text())
    model = Model()
    core,controls,ledgers = [],[],{}
    # Cooperative controls are evaluated before ordinary/pivotal choices.
    definitions = {'C01':('F',[ONE]*33), 'C02':('F',[ZERO]*33),'C03':('Q',[ZERO]*33),
        'C04':('Q',[ZERO]*16+[None]*17),'C05':('Q',[ZERO]*17+[None]*16),
        'C06':('Q',[ZERO]*11+[ONE]*11+[None]*11),'C07':('F',[ZERO]*16+[None]*17)}
    for c in contract['controls']:
        row = dict(c)
        cid = c['id']
        if cid in definitions:
            rule,scores = definitions[cid]
            m = aggregate(scores,rule)
            row.update(aggregation=rule,submitted_count=sum(s is not None for s in scores),aggregate_multiplier=m)
            ledgers[cid] = model.ledger(m)
            row['participation'] = ('With evidence-following replacement, node/delegator delta=0; affordable incremental c+o+alpha*K_tool <= retained_G_i*P_claim+DeltaZ' if cid in ('C01','C02','C03') else 'Replacement score unknown; general participation inequality applies')
        elif cid=='C08':
            row['comparison'] = 'G_equal=V/33; G_stake=V*b_i/sum_A b_j; equal exceeds stake iff b_i < sum_A b_j/33. Multiply difference by t_i^v*P_claim; no score-weight change.'
        elif cid=='C09':
            row['comparison'] = 'For timely set T: G_i=V*1(i in T)*b_i/sum_T b_j versus V*b_i/sum_A b_j. Abstainer gets 0 in T rule; timely valid E,L,U all eligible regardless accuracy. T empty: V remains minted undistributed. Nonempty T with sum_T b_j=0: undefined. No recipient identities stipulated.'
        elif cid in ('C10','C11'):
            age = 840 if cid=='C10' else 1680
            ledgers[cid] = model.ledger(ONE,age=age)
            row.update(earning_schedule_age=age,claim_age=7,compensation_ratio_to_r0=D(1)/(2**(age//840)),
                comparison='Same fees/jobs/costs/valuation; node and validator LPT envelopes shrink; affordable incremental role cost shrinks if all other utility terms fixed, no participation forecast')
        elif cid=='C12':
            ledgers[cid] = dict(at_n7=model.ledger(ONE,claim=8,horizon=7),at_n8_reference=model.ledger(ONE,claim=8,horizon=8))
            row['comparison'] = 'Original r=0 B_target unchanged; at n+7 with claim n+8 B_target pending. At actual claim n+8 payout=B_target*m8, m8 symbolic in [0,1]. Full-score n+8 reference shown only; Delta versus n+7 claim=B_target*(m8-m7). No second ceiling decay; later score is not invented.'
        controls.append(row)
    for case in sorted(contract['core'],key=lambda c:({'E':0,'L':1,'A':2,'U':3}[c['action']],c['id'])):
        row,ledger = model.action(case,contract)
        core.append(row);ledgers[case['id']]=ledger
    # All alternatives, not only medians: private/opportunity/tool/residual terms are independent symbols.
    for row in core:
        row['prefer_over'] = []
        for other in core:
            if (other['evidence'],other['aggregation']) != (row['evidence'],row['aggregation']) or other['action']==row['action']: continue
            row['prefer_over'].append(dict(other_action=other['action'],
                known_retained_validator_delta_usdc=(row['retained_validator_lpt']-other['retained_validator_lpt'])*model.price,
                cross_target_x_coefficient_usdc=row['cross_target_value_coefficient_usdc']-other['cross_target_value_coefficient_usdc'],
                condition='Delta(c+o+alpha*K_tool) <= known_validator_delta + x_i,target*cross_target_coefficient + DeltaZ; must hold for every alternative; equality permits a tie; other node rewards unchanged'))
    seats,ranks,populations = seat_tables()
    return dict(core=core,controls=controls,seats=seats,p1_rankings=ranks,p1_populations=populations,
        ledgers=ledgers,baseline=model.ledger(),
        status='conditional illustrative research; P1/E2 pending owner review',
        unknowns=['private/contested effort','opportunity/liquidity costs','shared tool engineering cost and incidence','coordination/standing/business residuals','cross-node ownership','replacement scores','acquisition/control costs and available liquidity'],
        evidence_boundary='P inconclusive. K sufficient only term breach with stipulated authentication/custody/safe timely same-byte access; knowledge-required unknown; VD-19 research premise only',
        interpretation_limit='Main-text MFS; score-withheld non-minting inherited completion. Appendix adverse-score calculation unsupported; results depend on reading.')


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',newline='') as f:
        writer = csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for row in rows:
            writer.writerow({k:json.dumps(v,default=str,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in row.items()})


def build():
    result = run()
    out = HERE/'generated';out.mkdir(exist_ok=True)
    (out/'results.json').write_bytes(serialize(result))
    for key in ('core','controls','seats','p1_rankings','p1_populations'):
        write_csv(out/(key+'.csv'),result[key])
    lines = ['# EX-11 conditional action table','',result['evidence_boundary'],'',result['interpretation_limit'],'',
        'Cooperative controls first: C01 P/F=1; C02 K/F=0; C03 K/Q=0. K has the stipulated conditions above. These are assumptions, not measured agreement.','',
        '|Input|Rule|Choice|Submission|Median|Retained validator LPT|Target node LPT|Outside target delegator LPT|',
        '|---|---|---|---|---|---|---|---|']
    for row in sorted(result['core'],key=lambda r:r['id']):
        lines.append('|'+ '|'.join(str(row[k]) for k in ('evidence','aggregation','action','submission','aggregate_multiplier','retained_validator_lpt','target_minted_lpt','target_outside_delegator_lpt'))+'|')
    lines += ['', 'Every row carries all three pairwise utility inequalities and a separate participation inequality in core.csv/results.json. The fixed 16-zero/16-one background is a pivotal control. Unknown cost, x and residual terms prevent an unconditional preference. E and U retain different evidentiary bases even when both submit 0. No direct transfer of withheld node allowance. No principal slashing.', '', '## Conditional seat table', '', 'All amounts below are exact integer LPT wei. Acquisition/control cost, liquidity and ability to command delegated stake are unknown. Addresses are not organizations or evidence of misconduct.', '', '|Block|Premise|k|d|New nodes|Original cutoff rank|New capital wei|Controlled existing wei|Donors|', '|---|---|---|---|---|---|---|---|---|']
    for r in result['seats']:
        lines.append('|'+ '|'.join(str(r.get(k,'')) for k in ('block','premise','coordinated_count','declined_count','new_nodes','cutoff_original_rank','new_capital_wei','existing_coordinated_wei','donor_pool_count'))+'|')
    (out/'tables.md').write_text('\n'.join(lines)+'\n')
    print('Built 16 core + 12 controls + 32 seat rows; all-pool ledgers and symbolic inequalities: '+str(out.relative_to(ROOT)))


if __name__ == '__main__':
    build()
