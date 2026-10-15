"""Closed forms locate finite candidates; EX-06 evaluates every payoff."""
from decimal import Decimal as D
from adapter import ZERO, ONE, EPS, cash_feasible
import fixtures


def parameters(state):
    p = state['vector'][state['actor_rank']-1]
    F, f = state['outside_F_usdc'], p['outside_fee_usdc']
    S = sum((v['stake'] for v in state['vector']), ZERO)
    s, a = p['stake']/S, f/F if F else ZERO
    t, z = p['k']+(ONE-p['k'])*p['w'], ONE-p['d']+p['d']*p['w']
    L = ONE-D('.5')*z+state['controlled_cost']/state['controlled_price']
    N, P = D('.94')*state['scheduled_ceiling_lpt'], state['valuation_usdc_per_lpt']
    cap = max(ZERO, (s*F-f)/(ONE-s)) if s < 1 else None
    # The frozen aligned control declares exact equality. Its monetary
    # quantization residual is shown in actual shares, never stake acquisition.
    aligned = state['start'] == 'aligned'
    if aligned:
        fixtures.require(abs(a-s) <= EPS, 'aligned declared equality within agreement tolerance')
        cap = ZERO
    head = max(ZERO, s-min(a,s)) if not aligned else ZERO
    if state['reading'] == 'appendix':
        cap, head = None, ONE-a
    return dict(F=F, f=f, S=S, s=s, a=a, t=t, z=z, L=L, N=N, P=P,
                cap=cap, head=head, K=state['setup_if_positive_usdc'],
                score=p['score'], aligned_equality=aligned)


def cash_endpoint(state, par):
    B, L, K = state['cash_loss_allowance_usdc'], par['L'], par['K']
    if B is None:
        return None
    if B <= K:
        return ZERO
    x = (B-K)/L
    # Original scalars determine exact affordability; rounded L only seeds x.
    while not cash_feasible(state,x):
        x = x.next_minus()
    # Preserve an affordable seed within the conservative precision contract.
    # The accepted native reference is two steps below the exact maximum;
    # every other endpoint allows at most one. No tolerance permits overspend.
    conservative_steps = 2 if state['id']=='native-measured-1' else 1
    def beyond_precision(value):
        for _ in range(conservative_steps+1):
            value=value.next_plus()
        return value
    while cash_feasible(state,beyond_precision(x)):
        x = x.next_plus()
    return x


def action_candidates(state, endpoint=None):
    p = parameters(state)
    out = {'zero': ZERO}
    if endpoint is not None:
        out['endpoint'] = endpoint
    if p['cap'] is not None and (endpoint is None or p['cap'] <= endpoint):
        out['cap kink'] = p['cap']
    if p['F'] > 0 and p['t'] > 0 and not (p['cap'] == 0):
        stationary = (p['P']*p['N']*p['t']*p['score']*(p['F']-p['f'])/p['L']).sqrt()-p['F']
        if stationary > 0 and (p['cap'] is None or stationary <= p['cap']) and (endpoint is None or stationary <= endpoint):
            out['stationary'] = stationary
    return out


def algebra_increment(state, x, useful=False):
    """Independent agreement expression, not a ledger or reward engine."""
    p = parameters(state)
    new_share = (p['f']+x)/(p['F']+x) if p['F']+x else ZERO
    if state['reading'] == 'mfs':
        weight_delta = min(new_share,p['s'])-min(p['a'],p['s'])
    else:
        weight_delta = new_share-p['a']
    return (p['P']*p['N']*p['t']*p['score']*weight_delta-p['L']*x
            -(p['K'] if x > 0 else ZERO)+(x/state['controlled_price'] if useful else ZERO))


def derivative(state, x, side='right'):
    p = parameters(state)
    if p['F'] == 0:
        return 'undefined at zero outside-fee denominator'
    if p['cap'] is not None and (x > p['cap'] or (x == p['cap'] and side == 'right')):
        return -p['L']
    return p['P']*p['N']*p['t']*p['score']*(p['F']-p['f'])/(p['F']+x)**2-p['L']


def break_even_roots(state):
    p = parameters(state)
    if p['F'] == 0:
        return [], 'undefined at zero outside-fee denominator'
    W = p['P']*p['N']*p['t']*p['score']*(ONE-p['a'])
    roots = []
    if p['cap'] != 0:
        if p['K'] == 0:
            root = W/p['L']-p['F']
            if root > 0 and (p['cap'] is None or root <= p['cap']):
                roots.append(root)
        else:
            b = p['L']*p['F']+p['K']-W
            disc = b*b-4*p['L']*p['K']*p['F']
            if disc >= 0:
                for root in ((-b-disc.sqrt())/(2*p['L']),(-b+disc.sqrt())/(2*p['L'])):
                    if root > 0 and (p['cap'] is None or root <= p['cap']):
                        roots.append(root)
    if p['cap'] is not None:
        root = (p['P']*p['N']*p['t']*p['score']*p['head']-p['K'])/p['L']
        if root > 0 and root >= p['cap']:
            roots.append(root)
    return sorted(set(roots)), 'defined' if roots else 'none: no positive spending breaks even'


def collective_landmark(state, target):
    """Solve the monotone piecewise victim-weight sum, without sampled search."""
    p = parameters(state)
    victims = [v for i,v in enumerate(state['vector']) if i != state['actor_rank']-1]
    if p['F'] == 0:
        return None
    if state['reading']=='appendix':
        return p['F']*target/(ONE-target) if any(v['outside_fee_usdc']>0 for v in victims) else None
    baseline = sum((min(v['outside_fee_usdc']/p['F'],v['stake']/p['S'])*v['score'] for v in victims), ZERO)
    if baseline == 0:
        return None
    goal = (ONE-target)*baseline
    kinks = sorted({ZERO} | {max(ZERO,v['outside_fee_usdc']/(v['stake']/p['S'])-p['F'])
                             for v in victims if v['stake'] > 0})
    for index, left in enumerate(kinks):
        right = kinks[index+1] if index+1 < len(kinks) else None
        capped, numerator = ZERO, ZERO
        for v in victims:
            s, g, m = v['stake']/p['S'], v['outside_fee_usdc'], v['score']
            crossing = g/s-p['F'] if s > 0 else None
            if crossing is not None and crossing > left:
                capped += s*m
            else:
                numerator += g*m
        if goal > capped and numerator > 0:
            root = numerator/(goal-capped)-p['F']
            if root >= left and (right is None or root <= right):
                return root
    raise AssertionError('Missing collective piecewise root')


def individual_landmark(state, victim, target):
    p = parameters(state)
    g, s = victim['outside_fee_usdc'], victim['stake']/p['S']
    if state['reading']=='appendix':
        return p['F']*target/(ONE-target) if p['F'] and g*victim['score']>0 else None
    w = min(g/p['F'],s) if p['F'] else ZERO
    if w*victim['score'] == 0:
        return None
    if g/p['F'] <= s:
        # Preserve the exact .25F endpoint instead of dividing g by g/F.
        return p['F']*target/(ONE-target)
    return g/(w*(ONE-target))-p['F']
