"""Checked arbitrary-actor interface to the unchanged EX-06 account engine.

D2 is an accounting-only copy for explicitly requested infeasible diagnostics.
Declared physical capacity and independent cash feasibility always remain visible.
"""
from copy import deepcopy
from decimal import Decimal as D, getcontext, ROUND_HALF_EVEN
from fractions import Fraction
import hashlib
import importlib.util
import json
import subprocess
import sys

import fixtures as f

getcontext().prec = 60
getcontext().rounding = ROUND_HALF_EVEN
ZERO, ONE, EPS = D(0), D(1), D('1e-18')
FROZEN = {
    'inputs.json': '1e4ab4b3a1cbfbfd83d9cb377e762a66f273f154eefeb8e28b33fd799de234db',
    'networks.json': 'ae35c5fcd77b29ab70e40334c1eb0b555776bbd8a850d45ee624491783673d61',
    'scenarios.json': '9911ad19828bde1e0fd44ee119ce3566f5a37aee7db0fbad427a07b5fa43af8c',
    'fixtures.py': '1198d6b353a80800db5998f00cc474eb0f655b68d74e806efa96e25eec64148b',
}
ENGINE_PATH = f.ROOT/'experiments/m2/capability-pricing/build.py'
ENGINE_SHA = '77ca2f5a57425e8968ce0dda70a0bb3c2ca3071e7d5dd068bd5349a4c8d9243b'


def cash_feasible(state, x):
    """Exact affordability from original scalars, never rounded z or L."""
    actor = state['vector'][state['actor_rank']-1]
    z = 1-Fraction(actor['d'])+Fraction(actor['d'])*Fraction(actor['w'])
    leakage = 1-z/2+Fraction(state['controlled_cost'])/Fraction(state['controlled_price'])
    loss = leakage*Fraction(x)+(Fraction(state['setup_if_positive_usdc']) if x > 0 else 0)
    budget = state['cash_loss_allowance_usdc']
    return budget is None or loss <= Fraction(budget)


def capacity_feasible(state, x):
    """Exact physical jobs domain, independent of receipt division rounding."""
    return Fraction(x) <= Fraction(state['controlled_price'])*Fraction(state['additional_capacity_jobs'])


def load_engine():
    f.require(hashlib.sha256(ENGINE_PATH.read_bytes()).hexdigest() == ENGINE_SHA, 'Changed EX-06 engine')
    spec = importlib.util.spec_from_file_location('ex08_unchanged_ex06', ENGINE_PATH)
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    return engine


def checked_inputs():
    for name, sha in FROZEN.items():
        f.require(hashlib.sha256((f.HERE/name).read_bytes()).hexdigest() == sha, 'Changed dispatch input '+name)
    import check_inputs
    check_inputs.check()
    manifest, networks, grid = f.load_contract()
    states, calibration = f.materialize(manifest, networks, grid)
    # Check the exact entire serialized object again before any accounting call.
    f.require(all(f.digest(s) == networks['vector_hashes'][sid] for sid, s in states.items()), 'Accounting vector hash')
    return states, calibration, manifest, networks, grid


def replay_originals(engine):
    """The D2 precondition is live execution, never a saved-output input."""
    engine.build()
    result = engine.run()
    f.require(len(result[3]) == 12 and len({r['group'] for r in result[4]}) == 9, 'EX-06 replay population')
    for audit in result[5]:
        for pool in audit[1]:
            for cap in pool['caps'].values():
                f.require(cap['q_out']+cap['q_self'] <= cap['capacity'], 'Legacy declared capacity changed')
    process = subprocess.run([sys.executable, str(ENGINE_PATH.with_name('verify.py'))],
                             cwd=f.ROOT, capture_output=True, text=True, check=True)
    return dict(engine_sha256=ENGINE_SHA, main_cases=len(result[3]),
                sensitivity_rows=len(result[4]), sensitivity_groups=9,
                verifier_stdout=process.stdout, verifier_stderr=process.stderr,
                declared_capacities='unchanged original capacities; no diagnostic adapter',
                main_sha256=f.digest(result[3]), sensitivity_sha256=f.digest(result[4]))


class Adapter:
    def __init__(self, engine, original_replay):
        f.require(original_replay['engine_sha256'] == ENGINE_SHA and original_replay['main_cases'] == 12
                  and original_replay['sensitivity_groups'] == 9, 'D2 requires original replay')
        self.engine = engine

    def evaluate(self, state, x=ZERO, useful=False, diagnostic=False, horizon=7):
        f.decimal(x)
        actor = state['actor_rank']-1
        pools = [dict(address=p['source_key'], **{k: deepcopy(p[k]) for k in
                 ('stake', 'k', 'd', 'w', 'score', 'claim_at', 'caps')}) for p in state['vector']]
        offer = pools[actor]['caps'][state['controlled_offer']]
        offer['q_self'] = x/state['controlled_price']
        offer['setup'] = state['setup_if_positive_usdc'] if x > 0 else ZERO
        offer['u'] = ONE if useful else ZERO
        declared = deepcopy(pools)
        capacity_ok = capacity_feasible(state, x) and all(
            Fraction(c['q_out'])+(Fraction(x)/Fraction(state['controlled_price'])
                if i == actor and name == state['controlled_offer'] else Fraction(c['q_self'])) <= Fraction(c['capacity'])
            for i,p in enumerate(state['vector']) for name,c in p['caps'].items())
        cash_ok = cash_feasible(state, x)
        if not capacity_ok:
            f.require(diagnostic, 'Only labelled hypothetical diagnostics may exceed capacity')
            for p in pools:
                for c in p['caps'].values():
                    c['capacity'] = max(c['capacity'], c['q_out']+c['q_self'])
        rows, network = self.engine.account(pools, state['scheduled_ceiling_lpt'],
            state['valuation_usdc_per_lpt'], state['burn_price_usdc_per_lpt'], horizon, state['reading'])
        # Keep temporary engine capacity out of the reported service ledger.
        for i, row in enumerate(rows):
            for cap in ('generic', 'niche'):
                row[cap+'_capacity'] = declared[i]['caps'].get(cap, {}).get('capacity', ZERO)
        metadata = dict(cash_feasible=cash_ok, capacity_feasible=capacity_ok,
            feasible=cash_ok and capacity_ok, diagnostic=not (cash_ok and capacity_ok),
            execution_label='declared capacity' if capacity_ok else 'hypothetical execution beyond declared capacity',
            feasibility_inference='exact inclusive checks; hypothetical execution supplies no affordability or spare-capacity inference',
            declared_additional_capacity_jobs=state['additional_capacity_jobs'],
            declared_actor_offer_capacities_jobs={k: c['capacity'] for k, c in declared[actor]['caps'].items()},
            temporary_capacity_used=not capacity_ok, claim_age_horizon_rounds=horizon)
        return rows, network, metadata


def write_json(path, data):
    path.write_bytes(f.serialize(data)+b'\n')


def write_jsonl(path, rows):
    with path.open('wb') as stream:
        for row in rows:
            stream.write(f.serialize(row)+b'\n')


def load_json(path):
    """Outputs have explicit Decimal strings, retained as strings until needed."""
    return json.loads(path.read_text())
