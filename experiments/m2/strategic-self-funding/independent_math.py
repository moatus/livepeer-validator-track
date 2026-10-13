"""Verifier-only source-state arithmetic; no builder, strategy or output imports.

These expressions independently test the optimizer's proof obligations. They do
not generate accounting ledgers; all reported receipts use EX-06 account().
"""
from decimal import Decimal as D
from fractions import Fraction as Q

Z,O,EPS=D(0),D(1),D('1e-18')


def exact_cash_feasible(state,x):
    """Independent rational inequality from original d/w/c/p/setup/B."""
    actor=state['vector'][state['actor_rank']-1]
    leakage=1-(1-Q(actor['d'])*(1-Q(actor['w'])))/2+Q(state['controlled_cost'])/Q(state['controlled_price'])
    B=state['cash_loss_allowance_usdc']
    return B is None or Q(x)*leakage+(Q(state['setup_if_positive_usdc']) if x>0 else 0)<=Q(B)


def exact_capacity_feasible(state,x):
    return Q(x)/Q(state['controlled_price'])<=Q(state['additional_capacity_jobs'])


def quantities(state):
    actor=state['vector'][state['actor_rank']-1]
    F=state['outside_F_usdc'];S=sum((v['stake'] for v in state['vector']),Z)
    a=actor['outside_fee_usdc']/F if F else Z;s=actor['stake']/S
    t=actor['k']+(1-actor['k'])*actor['w'];z=1-actor['d']+actor['d']*actor['w']
    L=1-D('.5')*z+state['controlled_cost']/state['controlled_price']
    C=D('.94')*state['scheduled_ceiling_lpt']*state['valuation_usdc_per_lpt']*t*actor['score']
    cap=max(Z,(s*F-actor['outside_fee_usdc'])/(1-s)) if s<1 else None
    if state['start']=='aligned': cap=Z
    if state['reading']=='appendix': cap=None
    head=Z if state['start']=='aligned' else max(Z,s-min(a,s))
    return dict(F=F,f=actor['outside_fee_usdc'],a=a,s=s,L=L,C=C,cap=cap,head=head,K=state['setup_if_positive_usdc'],
                capacity=state['controlled_price']*state['additional_capacity_jobs'],B=state['cash_loss_allowance_usdc'],
                exact_L=1-(1-Q(actor['d'])*(1-Q(actor['w'])))/2+Q(state['controlled_cost'])/Q(state['controlled_price']),
                conservative_steps=2 if state['id']=='native-measured-1' else 1)


def payoff(p,x):
    after=(p['a']*p['F']+x)/(p['F']+x)
    reward=after-p['a'] if p['cap'] is None else min(after,p['s'])-min(p['a'],p['s'])
    return p['C']*reward-p['L']*x-(p['K'] if x>0 else Z)


def endpoints(p):
    if p['B'] is None: cash=None
    elif p['B']<=p['K']: cash=Z
    else:
        cash=(p['B']-p['K'])/p['L']
        # Compare to the exact source-defined quotient, independently of the
        # implementation's cash predicate and its rounded retention scalars.
        limit=(Q(p['B'])-Q(p['K']))/p['exact_L']
        while Q(cash)>limit: cash=cash.next_minus()
        while Q(precision_successor(cash,p['conservative_steps']))<=limit: cash=cash.next_plus()
    return cash,p['capacity'] if cash is None else min(cash,p['capacity'])


def precision_successor(value,conservative_steps):
    for _ in range(conservative_steps+1):value=value.next_plus()
    return value


def optimum(p,endpoint=None):
    choices={Z}
    if endpoint is not None: choices.add(endpoint)
    if p['cap'] is not None and (endpoint is None or p['cap']<=endpoint): choices.add(p['cap'])
    stationary=(p['C']*(p['F']-p['f'])/p['L']).sqrt()-p['F']
    if stationary>0 and (endpoint is None or stationary<=endpoint) and (p['cap'] is None or stationary<=p['cap']):
        choices.add(stationary)
    return max(choices,key=lambda x:(payoff(p,x),-x)),choices


def roots(p):
    """Complete positive roots of each quadratic/rational and linear piece."""
    roots=[];F,L,K,C=p['F'],p['L'],p['K'],p['C'];cap=p['cap']
    if F==0: return []
    # Multiplying x(C(1-a)/(F+x)-L)-K by F+x gives a quadratic.
    b=L*F+K-C*(1-p['a']);disc=b*b-4*L*K*F
    if K==0 and cap!=0:
        r=C*(1-p['a'])/L-F
        if r>0 and (cap is None or r<=cap): roots.append(r)
    elif disc>=0 and cap!=0:
        for r in ((-b-disc.sqrt())/(2*L),(-b+disc.sqrt())/(2*L)):
            if r>0 and (cap is None or r<=cap): roots.append(r)
    if cap is not None:
        r=(C*p['head']-K)/L
        if r>0 and r>=cap: roots.append(r)
    return sorted(set(roots))


def expected_progression(p,feasible,unconstrained,endpoint):
    return {x for x in (Z,D('.01')*p['F'],D('.10')*p['F'],feasible,endpoint,p['cap'],unconstrained,p['F']) if x is not None}


def verify_summary(state,row):
    """Raise even under -O; expected values never come from the output."""
    def require(ok,msg):
        if not ok: raise AssertionError(msg+': '+state['id'])
    def same(a,b,msg): require(abs(D(a)-D(b))<=EPS,msg)
    p=quantities(state);cash,end=endpoints(p)
    require(row['cash_endpoint_usdc'] is None if cash is None else D(row['cash_endpoint_usdc'])==cash,'Cash endpoint from frozen state')
    require(D(row['feasible_endpoint_usdc'])==end,'Conservative feasible endpoint from frozen state')
    if cash is not None and cash>0:
        limit=(Q(p['B'])-Q(p['K']))/p['exact_L']
        require(Q(cash)<=limit and Q(precision_successor(cash,p['conservative_steps']))>limit,
                'Exact cash feasibility and conservative representable-step precision')
    if end==p['capacity']: require(end/state['controlled_price']==state['additional_capacity_jobs'],'Exact physical endpoint')
    elif end==0: require(p['B']<=p['K'],'Zero endpoint setup discontinuity')
    else:
        require(exact_cash_feasible(state,end),'Exact rational endpoint feasibility')
    require(exact_cash_feasible(state,D(row['feasible_optimum']['x_usdc'])) and
            exact_capacity_feasible(state,D(row['feasible_optimum']['x_usdc'])),'Exact constrained optimum feasibility')
    for candidate in row['candidate_evaluations']:
        require(exact_cash_feasible(state,D(candidate['x_usdc'])) and exact_capacity_feasible(state,D(candidate['x_usdc'])),
                'Exact constrained candidate feasibility')
    x,choices=optimum(p,end);unconstrained,_=optimum(p)
    same(row['feasible_optimum']['x_usdc'],x,'Complete constrained candidate optimum')
    same(row['unconstrained_optimum']['x_usdc'],unconstrained,'Complete unconstrained candidate optimum')
    expected=roots(p);reported=list(map(D,row['nonzero_break_even_spending_usdc']))
    require(len(reported)==len(expected),'Complete piecewise positive-root count')
    for r,e in zip(reported,expected): same(r,e,'Complete piecewise positive-root set')
    if row['stopping_reason']=='interior stationary point':
        q=D(row['feasible_optimum']['x_usdc'])
        require(0<q<end and (p['cap'] is None or q<p['cap']),'Strict interior/cap condition')
        same(p['C']*p['F']*(1-p['a'])/(p['F']+q)**2-p['L'],0,'Interior zero derivative')
    return p,x,unconstrained,end
