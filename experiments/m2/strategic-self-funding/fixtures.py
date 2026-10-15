"""Construct frozen inputs only. No reward, optimizer, payoff or loss calculation."""
from copy import deepcopy
from decimal import Decimal as D, InvalidOperation, localcontext, ROUND_HALF_EVEN
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRECISION = 60
SHARE_QUANTUM = D('1e-48')
AMOUNT_QUANTUM = D('1e-42')
TOLERANCE = D('1e-18')
ZERO, ONE = D(0), D(1)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def decimal(value, lower=ZERO, upper=None):
    try:
        result = D(str(value))
    except InvalidOperation as exc:
        raise ValueError('Invalid decimal') from exc
    require(result.is_finite(), 'Nonfinite decimal')
    require(result >= lower and (upper is None or result <= upper), 'Decimal outside bounds')
    return result


def encode_decimal(value):
    require(value.is_finite(), 'Cannot serialize nonfinite decimal')
    if value == 0:
        return '0'
    result = format(value, 'f')
    return result.rstrip('0').rstrip('.') if '.' in result else result


def serialize(value):
    """Hashable UTF-8, with Decimal strings; no newline, floats or exponent notation."""
    def convert(v):
        if isinstance(v, D):
            return encode_decimal(v)
        if isinstance(v, float):
            raise ValueError('Binary floating point forbidden')
        if isinstance(v, dict):
            return {k: convert(x) for k, x in v.items()}
        if isinstance(v, (tuple, list)):
            return [convert(x) for x in v]
        return v
    return json.dumps(convert(value), sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(serialize(value)).hexdigest()


def normalize(values, residual_index, quantum=SHARE_QUANTUM, total=ONE):
    require(len(values) == 100, 'Whole 100-pool vector required')
    require(0 <= residual_index < 100, 'Residual pool missing')
    require(all(v.is_finite() and v >= 0 for v in values), 'Invalid normalization input')
    denominator = sum(values, ZERO)
    require(denominator > 0, 'Undefined normalization at zero')
    out = [(v / denominator * total).quantize(quantum) for v in values]
    out[residual_index] += total - sum(out, ZERO)
    require(all(v >= 0 for v in out) and sum(out, ZERO) == total, 'Normalization conservation')
    return out


def amounts(shares, total, residual_index):
    out = [(v * total).quantize(AMOUNT_QUANTUM) for v in shares]
    out[residual_index] += total - sum(out, ZERO)
    require(all(v >= 0 for v in out) and sum(out, ZERO) == total, 'Amount conservation')
    return out


def retention(k, d, w):
    for v in (k, d, w):
        decimal(v, upper=ONE)
    return k + (ONE-k)*w, ONE-d+d*w


def inclusive(value, upper):
    """Accounting uses exact <=; verifier tolerance is for algebra agreement only."""
    return value <= upper


def cash_feasible(x, price, cost, z, budget, setup=ZERO):
    for v in (x, cost, setup):
        decimal(v)
    decimal(price, lower=D('1e-60'))
    decimal(z, upper=ONE)
    leakage = ONE-D('.5')*z+cost/price
    loss = leakage*x+(setup if x > 0 else ZERO)
    return budget is None or inclusive(loss, budget)


def capacity_feasible(x, price, additional_capacity):
    decimal(x); decimal(price, lower=D('1e-60')); decimal(additional_capacity)
    return inclusive(x/price, additional_capacity)


def load_contract():
    return tuple(json.loads((HERE / name).read_text()) for name in ('inputs.json', 'networks.json', 'scenarios.json'))


def source_inputs(manifest):
    for key in ('october_text', 'october_pdf'):
        item = manifest['sources'][key]
        require(hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest() == item['sha256'], 'Changed source: '+key)
    for path, sha in manifest['dependencies'].items():
        require(hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == sha, 'Changed dependency: '+path)
    path = ROOT/'experiments/m2/network-snapshot/read_snapshot.py'
    spec = importlib.util.spec_from_file_location('ex08_snapshot_reader', path)
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    src = manifest['sources']['snapshot']
    snap = reader.load_snapshot(expected_id=src['id'], expected_sha256=src['content_sha256'])
    observed = reader.round_inputs(snap, src['round'])
    require(observed['round_id'] == 4364 and len(observed['pools']) == 100, 'Matched-round population')
    require(src['window'] == {k: observed[k] for k in ('start_utc', 'end_utc_exclusive')}, 'Observation window')
    native = sorted(observed['pools'], key=lambda p: (-p['stake_lpt'], p['address']))
    operators = {p['address']: p for p in snap['orchestrators']}
    require(len(operators) == 100 and len({p['address'] for p in native}) == 100, 'Nonunique source identities')
    require(sum((p['stake_lpt'] for p in native), ZERO) == observed['active_stake_lpt'], 'Native stake conservation')
    require(sum((p['fees_eth'] for p in native), ZERO) == observed['fees_eth'], 'Native fee conservation')
    require(decimal(snap['prices']['lpt_usd_spot']) == decimal(manifest['parameters']['valuation']['value']), 'Valuation replay changed')
    return snap, observed, native, operators


def materialize(manifest=None, networks=None, scenarios=None):
    if manifest is None:
        manifest, networks, scenarios = load_contract()
    with localcontext() as ctx:
        ctx.prec = PRECISION
        ctx.rounding = ROUND_HALF_EVEN
        snap, observed, native, operators = source_inputs(manifest)
        F0 = observed['fees_usd_indexed']
        E0 = observed['scheduled_mint_ceiling_lpt']
        S0 = observed['active_stake_lpt']
        P0 = decimal(manifest['parameters']['valuation']['value'])
        V0 = D('.94')*E0*P0
        calibration = dict(F0_usdc=F0, E0_lpt=E0, S0_lpt=S0, P0_usdc_per_lpt=P0,
                           valued_scheduled_node_envelope_usdc=V0, measured_ratio=V0/F0,
                           round=4364, launch_relative_calibration_round=0,
                           snapshot_id=snap['snapshot_id'], snapshot_content_sha256=snap['integrity']['content_sha256'])
        totals = {'measured': F0, 'mid-path': V0/8, 'near-parity': V0, 'fee-leaning': V0/D('.5')}
        states = {}
        for profile in scenarios['profiles']:
            actor = profile['actor_rank']-1
            structure, start = profile['structure'], profile['start']
            if structure == 'R':
                raw_stakes = [p['stake_lpt'] for p in native]
                weights = [p['fees_eth'] for p in native]
            else:
                raw_stakes = [D(100-i)/5050 for i in range(100)] if structure == 'D' else [
                    D('.20') if i == 0 else D('.04') if i < 10 else D('.44')*D(100-i)/4095 for i in range(100)]
                weights = [D(i+1)/5050 for i in range(100)]
            # Stable lowest-ranked positive-weight nonactor absorbs rounding; it
            # cannot turn a retained zero-fee pool into negative fee business.
            fee_residual = max(i for i,v in enumerate(weights) if i != actor and v > 0)
            stake_residual = 99  # never one of the selected actors
            stake_shares = normalize(raw_stakes, stake_residual)
            stakes = raw_stakes if structure == 'R' else amounts(stake_shares, S0, stake_residual)
            parent_fee_shares = normalize(weights, fee_residual)
            fee_shares = list(parent_fee_shares)
            if start in ('low', 'high'):
                a = decimal(networks['headroom'][start])*stake_shares[actor]
                old = parent_fee_shares[actor]
                require(old < ONE, 'Headroom reallocation denominator')
                fee_shares = [(v*(ONE-a)/(ONE-old)).quantize(SHARE_QUANTUM) for v in parent_fee_shares]
                fee_shares[actor] = a  # preserve exact h*s; may have >48 fractional digits
                fee_shares[fee_residual] += ONE-sum(fee_shares, ZERO)
            elif start == 'aligned':
                fee_shares = list(stake_shares)
            else:
                require(start == 'native' and structure == 'R', 'Unsupported start')
            F = totals[profile['market']]
            fees = amounts(fee_shares, F, fee_residual)
            B, Q = D('.10')*F, D('.25')*F
            ov = profile['overrides']
            if 'budget_fraction' in ov:
                B = decimal(ov['budget_fraction'])*F
            if 'cash_bound' in ov:
                require(ov['cash_bound'] is None, 'Invalid cash-bound override')
                B = None
            response = ov.get('outside_response')
            competitor = next(i for i,v in enumerate(fees) if i != actor and v > 0)
            prices = [ONE]*100
            jobs = list(fees)  # outside generic price remains 1 except named competitor
            if response == 'proportional-double':
                fees = [v*2 for v in fees]; jobs = [v*2 for v in jobs]
            elif response == 'concentrated-add':
                fees[competitor] += F; jobs[competitor] += F
            elif response == 'price-routing':
                moved = jobs[actor]*decimal(ov['route_fraction'])
                jobs[actor] -= moved; jobs[competitor] += moved
                prices[competitor] = decimal(ov['competitor_price'])
                fees = [p*q for p,q in zip(prices,jobs)]
            else:
                require(response is None, 'Unknown response')
            total_fees = sum(fees, ZERO)
            vector = []
            for i,p in enumerate(native):
                o = operators[p['address']]
                k,d,w = p['operator_reward_cut_fraction'],p['delegator_fee_share_fraction'],decimal(o['operator_address_fraction_of_own_pool'])
                if i == actor and start != 'native':
                    k,d,w = ZERO,ONE,ONE
                if i == actor and 'w' in ov:
                    k,d,w = decimal(ov['k']),decimal(ov['d']),decimal(ov['w'])
                t,z = retention(k,d,w)
                caps = {'generic':dict(q_out=jobs[i],q_self=ZERO,p=prices[i],c=D('.30'),setup=ZERO,u=ZERO,
                                       capacity=jobs[i]+(Q if i==actor and ov.get('controlled_offer','generic')=='generic' else ZERO))}
                if i == actor and ov.get('controlled_offer') == 'niche':
                    caps['niche']=dict(q_out=ZERO,q_self=ZERO,p=decimal(ov.get('controlled_price','1')),
                                       c=decimal(ov.get('cost','.30')),setup=ZERO,u=ZERO,capacity=Q)
                if i == actor and 'cost' in ov and ov.get('controlled_offer','generic') == 'generic':
                    caps['generic']['c'] = decimal(ov['cost'])
                vector.append(dict(source_rank=i+1,source_key=p['address'],display_role=f'modeled-rank-{i+1}',
                    stake=stakes[i],declared_stake_share=stake_shares[i],parent_fee_share=parent_fee_shares[i],
                    assigned_fee_share=fee_shares[i],fee_reallocation_delta=fee_shares[i]-parent_fee_shares[i],
                    actual_outside_fee_share=fees[i]/total_fees if total_fees else ZERO,
                    outside_fee_usdc=fees[i],k=k,d=d,w=w,t=t,z=z,score=ONE,claim_at=profile['horizon'],caps=caps))
            earning_round = ov.get('earning_round',0)
            states[profile['id']]=dict(id=profile['id'],group=profile['group'],structure=structure,market=profile['market'],
                parent=profile['parent'],actor_rank=actor+1,actor_key=native[actor]['address'],start=start,
                fee_residual_rank=fee_residual+1,stake_residual_rank=stake_residual+1,
                original_F_usdc=F,outside_F_usdc=total_fees,total_stake_lpt=S0,
                cash_loss_allowance_usdc=B,additional_capacity_jobs=Q,budget_period=profile['budget_period'],
                controlled_offer=ov.get('controlled_offer','generic'),controlled_price=decimal(ov.get('controlled_price','1')),
                controlled_cost=decimal(ov.get('cost','.30')),setup_if_positive_usdc=decimal(ov.get('setup','0')),
                reading=ov.get('reading','mfs'),earning_round=earning_round,
                calibrated_base_ceiling_lpt=E0,scheduled_ceiling_lpt=E0/(2 if earning_round==840 else 1),
                valuation_usdc_per_lpt=P0*decimal(ov.get('valuation_multiplier','1')),burn_price_usdc_per_lpt=P0,
                competitor_rank=competitor+1 if response else None,response=response,
                source_snapshot_id=snap['snapshot_id'],source_content_sha256=snap['integrity']['content_sha256'],
                vector=vector)
        return states, calibration


def write_vectors(states):
    dest=HERE/'generated/vectors'
    dest.mkdir(parents=True,exist_ok=True)
    for name,state in states.items():
        (dest/(name+'.json')).write_bytes(serialize(state)+b'\n')
