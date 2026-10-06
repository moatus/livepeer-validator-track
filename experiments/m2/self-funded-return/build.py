"""EX-03: bounded, illustrative one-job arithmetic; Python standard library only."""

from __future__ import annotations

import csv
import hashlib
import math
from dataclasses import dataclass, replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[2] / "docs" / "litepaper-2.0.md"
SOURCE_SHA256 = "5fc153408fb636d9750788ae987ada6daaa9fc3df3e44f70cadde51a6158fb71"
UNDEFINED = "undefined/needs rule"
CONCEPTS = ("C0", "C1", "C2", "C3")
READINGS = ("MFS", "appendix")
CASES = (("SC-01", 0.0), ("SC-23", 1.0), ("SC-07", 0.0))
MAX_Z = 64.0


@dataclass(frozen=True)
class Inputs:
    F: float = 1_100_000 / 365
    f: float = (1_100_000 / 365) * .025
    s: float = .05
    rounds: float = 365
    node_cut: float = .5
    node_share: float = .94
    kappa: float = .3
    omega: float = 1
    rho: float = 1
    phi: float = 1
    p_mint: float = 1
    p_claim: float = 1
    ratio: float = 32

    def validate(self):
        for name, value in vars(self).items():
            if not math.isfinite(value):
                raise ValueError(f"Nonfinite {name}")
        if self.F < 0 or not 0 <= self.f <= self.F or self.kappa < 0:
            raise ValueError("Require F >= f >= 0 and nonnegative cost")
        for name in ("s", "node_cut", "node_share", "omega", "rho", "phi"):
            if not 0 <= getattr(self, name) <= 1:
                raise ValueError(f"Invalid fraction {name}")
        if min(self.rounds, self.p_mint, self.p_claim, self.ratio) <= 0:
            raise ValueError("Positive clocks, prices and ratio required")


def pool(p, concept, x, side="right"):
    """Return USD-equivalent mint and one-sided USD slope, before conversion to LPT."""
    if concept not in CONCEPTS:
        raise ValueError(concept)
    cap = 50_000_000 / p.rounds
    fixed = min(p.ratio * p.F, cap)
    if concept in ("C0", "C3"):
        return fixed, 0.0
    if concept == "C1":
        raw = p.ratio * (p.F + x)
        equal = math.isclose(raw, cap, rel_tol=1e-12, abs_tol=1e-9)
        slope = p.ratio if (equal and side == "left") or (raw < cap and not equal) else 0
        return min(raw, cap), slope
    # I-09: starting mint minus increase from F0=F; literal ceiling not computed.
    target = 35_000_000 / p.rounds - x
    equal = math.isclose(target, 0, abs_tol=1e-9)
    slope = -1 if (equal and side == "left") or (target > 0 and not equal) else 0
    return max(0, target), slope


def reward(p, concept, reading, x, median=1):
    if reading not in READINGS:
        raise ValueError(reading)
    if p.F == 0:
        return None  # before-job comparison has no fee denominator
    a = (p.f + x) / (p.F + x)
    N = p.node_share * pool(p, concept, x)[0] / p.p_mint
    if reading == "MFS":
        return N * min(a, p.s) * median
    denom = a * median + 1 - a  # every other median is 1
    return N * a * median / denom if denom > 0 else None


def cash_rate(p, case, u):
    recovered = p.node_cut * (p.rho + (1 - p.rho) * p.omega)
    return recovered - p.kappa + (u - 1 if case != "SC-01" else 0)


def marginal(p, concept, reading, x, case="SC-07", u=0, side="right"):
    """Derivative at median 1. Left/right values preserve threshold kinks."""
    a = (p.f + x) / (p.F + x)
    da = (p.F - p.f) / (p.F + x) ** 2
    if reading == "MFS":
        equal = math.isclose(a, p.s, rel_tol=1e-12, abs_tol=1e-14)
        below = (equal and side == "left") or (a < p.s and not equal)
        weight, dw = min(a, p.s), da if below else 0
    else:
        weight, dw = a, da
    e, de = pool(p, concept, x, side)
    ownership = p.phi + (1 - p.phi) * p.omega
    return (p.p_claim / p.p_mint * ownership * p.node_share * (de * weight + e * dw)
            + cash_rate(p, case, u))


def account(p, concept, reading, x, case="SC-07", u=0, q=0, median=1):
    p.validate()
    if (case not in {c for c, _ in CASES} or not math.isfinite(x) or x < 0
            or not math.isfinite(u) or u < 0 or not 0 <= q <= 1 or not 0 <= median <= 1):
        raise ValueError("Invalid job, case, use value, probability or median")
    if p.F == 0:
        return {"status": UNDEFINED}
    rb = reward(p, concept, reading, 0)
    ra = reward(p, concept, reading, x, median)
    full = reward(p, concept, reading, x, 1)
    if ra is None or full is None:
        return {"status": UNDEFINED}
    own = p.phi + (1 - p.phi) * p.omega
    before, after, after_full = rb * own, ra * own, full * own
    cash = cash_rate(p, case, u) * x
    delta = p.p_claim * (after - before) + cash
    base_delta = p.p_claim * (after_full - before) + cash
    # Declining the job makes no score event; q sensitivities apply only to x>0.
    effective_q = q if x > 0 else 0
    expected = (1 - effective_q) * p.p_claim * after_full - p.p_claim * before + cash
    a = (p.f + x) / (p.F + x)
    return dict(status="illustrative", a=a, region="a<s" if a < p.s - 1e-14 else "a>=s",
                E_before_lpt=pool(p, concept, 0)[0] / p.p_mint,
                E_after_lpt=pool(p, concept, x)[0] / p.p_mint,
                R_before_org_lpt=before, R_after_org_lpt=after,
                delta_reward_lpt=after-before, delta_cash_usdc=cash,
                delta_usdc=delta, average=delta/x if x else UNDEFINED,
                marginal_left=marginal(p, concept, reading, x, case, u, "left") if x else UNDEFINED,
                marginal_right=marginal(p, concept, reading, x, case, u),
                expected_usdc=expected,
                q_star=("none" if base_delta <= 1e-9 else base_delta/(p.p_claim*after_full)
                        if after_full > 0 else "no finite q* (zero reward at risk)"),
                false_cut_cost_usdc=effective_q*p.p_claim*after_full,
                use_break_even=-(p.p_claim*(full*own-before)/x + cash_rate(p, "SC-07", 0)) if x else UNDEFINED,
                other_appendix_before_lpt=p.node_share*pool(p, concept, 0)[0]/p.p_mint-rb if reading == "appendix" else "not aggregated",
                other_appendix_after_lpt=p.node_share*pool(p, concept, x)[0]/p.p_mint-ra if reading == "appendix" else "not aggregated")


def boundaries(p, concept, reading):
    points = [0.0, MAX_Z]
    if reading == "MFS" and p.s < 1:
        points.append((p.s - p.f/p.F)/(1-p.s))
    if concept == "C1":
        points.append(50_000_000/p.rounds/(p.ratio*p.F)-1)
    if concept == "C2":
        points.append(35_000_000/p.rounds/p.F)
    return sorted(set(z for z in points if 0 <= z <= MAX_Z))


def polynomial_roots(a, b, c):
    """Real roots of a degree <=2 polynomial, using a stable quadratic evaluation."""
    if abs(a) < 1e-14:
        return [-c/b] if abs(b) > 1e-14 else []
    d = b*b-4*a*c
    if d < 0:
        return []
    t = -.5*(b+math.copysign(math.sqrt(d), b))
    return [t/a, c/t] if t else [-b/(2*a)]


def sign(v):
    return "zero" if abs(v) < 1e-7 else "positive" if v > 0 else "negative"


def break_evens(p, concept, reading, case="SC-07", u=0):
    """All nonzero q=0 roots on [0,64], from exact piecewise degree <=2 identities.

    In each region e/F=A+Bz and reward weight is either s or (b+z)/(1+z).
    Multiplication by positive (1+z) gives a quadratic, so no grid can miss a root.
    """
    b = p.f/p.F
    h = p.node_share*p.p_claim/p.p_mint*(p.phi+(1-p.phi)*p.omega)
    r0 = p.p_claim*reward(p, concept, reading, 0)*(p.phi+(1-p.phi)*p.omega)/p.F
    cash = cash_rate(p, case, u)
    points = boundaries(p, concept, reading)
    roots = []
    for lo, hi in zip(points, points[1:]):
        mid = (lo+hi)/2
        e, slope = pool(p, concept, mid*p.F)
        A, B = e/p.F-slope*mid, slope
        if reading == "MFS" and (b+mid)/(1+mid) >= p.s:
            piece_roots = polynomial_roots(0, h*B*p.s+cash, h*A*p.s-r0)
        else:
            piece_roots = polynomial_roots(h*B+cash, h*(A+B*b)-r0+cash, h*A*b-r0)
        for z in piece_roots:
            if z > 1e-10 and lo-1e-9 <= z <= hi+1e-9:
                if not any(math.isclose(z, r, abs_tol=1e-8) for r in roots):
                    roots.append(z)
    roots.sort()
    cuts = [0]+roots+[MAX_Z]
    regions = []
    for lo, hi in zip(cuts, cuts[1:]):
        v = account(p, concept, reading, (lo+hi)/2*p.F, case, u)["delta_usdc"]
        regions.append(f"{sign(v)} on {lo:.6g}<x/F<{hi:.6g}")
    return roots, "; ".join(regions)


def csv_write(name, rows):
    with (HERE/name).open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def fmt(value):
    return f"{value:.6g}" if isinstance(value, (int, float)) else str(value)


def build():
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise SystemExit("Litepaper snapshot changed; review the citations before rebuilding")
    sweeps, breaks, sensitivity = [], [], []
    md = ["# EX-03 illustrative tables", "", "All results are illustrative, conditional one-round arithmetic (not measurements).",
          "F=1,100,000/365 USDC; 94% nodes; 50% node cut; cost κ=0.3; full ownership; equal unit mint/claim prices; claim n+7; median 1.",
          "C0 and C3 calibrated to C1 at x=0. C2 uses starting mint minus fee increase. x/F spans 0–64; zero is declining the job.",
          "Appendix work is read as fee share. SC-23 uses illustrative u=1; for other positive use values, Δ23=Δ07+ux.",
          "SC-06 has the same arithmetic apart from u. All ordinary fee receipts are separate from LPT rewards.",
          "Slopes are left/right at kinks; at x=0 only the right derivative is defined. Δ/x is undefined at zero.",
          "Tables put SC-01 outside work first, useful release testing next, then SC-07 reward-seeking real work. Their difference is payer/use accounting, not evidence of purpose.", ""]
    for concept in CONCEPTS:
        for reading in READINGS:
            md += [f"## {concept}, {reading}: illustrative average / marginal returns", ""]
            for s in (.01, .05, .20):
                for start, b in (("below", s/2), ("above", 2*s)):
                    p = Inputs(s=s, f=Inputs().F*b)
                    for case, u in CASES:
                        roots, signs = break_evens(p, concept, reading, case, u)
                        breaks.append(dict(status="illustrative", concept=concept, reading=reading, s=s,
                                           start=start, f_over_F=b, case=case, u=u, q=0,
                                           roots_x_over_F=";".join(fmt(r) for r in roots) or "no sign change in the swept range",
                                           roots_x_usdc=";".join(fmt(r*p.F) for r in roots) or "none", signs=signs))
                    grid = sorted(set([0, .001, .01, .1, .5, 1, 16, 32, MAX_Z]+boundaries(p, concept, reading)))
                    md += [f"### s={s:g}, f/F={b:g} ({start} MFS ceiling at start)", "",
                           "| x/F | MFS position | SC-01 average; slope L/R | SC-23 (u=1) average; slope L/R | SC-07 average; slope L/R |", "| ---: | --- | --- | --- | --- |"]
                    for z in grid:
                        values = []
                        for case, u in CASES:
                            result = account(p, concept, reading, z*p.F, case, u)
                            sweeps.append(dict(status="illustrative", concept=concept, reading=reading, s=s,
                                               start=start, f_over_F=b, x_over_F=z, x_usdc=z*p.F,
                                               case=case, u=u, q=0, **{k:v for k,v in result.items() if k != "status"}))
                            values.append(f"{fmt(result['average'])}; {fmt(result['marginal_left'])}/{fmt(result['marginal_right'])}")
                        md.append(f"| {fmt(z)} | {result['region']} | "+" | ".join(values)+" |")
                    md += ["", "Illustrative q=0 sign regions and nonzero break-evens:", ""]
                    for row in breaks[-3:]:
                        md.append(f"- {row['case']}: {row['signs']}; x/F={row['roots_x_over_F']}.")
                    md.append("")
                    for z in (.01, .5, 1):
                        for case, u in CASES:
                            for q in (0, .05, .5, 1):
                                r = account(p, concept, reading, z*p.F, case, u, q=q)
                                sensitivity.append(dict(status="illustrative", concept=concept, reading=reading, s=s,
                                                        start=start, f_over_F=b, x_over_F=z, case=case, u=u, q=q,
                                                        delta_usdc=r["delta_usdc"], expected_usdc=r["expected_usdc"],
                                                        expected_over_x=r["expected_usdc"]/(z*p.F), q_star=r["q_star"],
                                                        reward_at_risk_usdc=r["R_after_org_lpt"]*p.p_claim,
                                                        false_cut_cost_usdc=r["false_cut_cost_usdc"] if case == "SC-23" else "not labelled false cut"))
    md += ["## Illustrative q* and false-cut sensitivity", "",
           "q is the probability of a whole-round zero median after a job, not a measured detection or error rate.",
           "E[Δ]=Δ(q=0)−q P_claim R_after_org. For positive base Δ, q*=Δ/(P_claim R_after_org); otherwise none.",
           "q* greater than 1 means no feasible q makes the return nonpositive. Positive return with zero reward at risk has no finite q*. For SC-23 the same lost reward is a false-cut cost.",
           "sensitivity.csv reports x/F=0.01,0.5,1 for all concepts, readings, starts and cases, at q=0,0.05,0.5,1.", "",
           "| Concept | Reading | s | Start | x/F | SC-07 q* | SC-23 q* (u=1) | SC-23 E[Δ]/x at q=.05 | SC-23 false-cut cost at q=.05 (USDC) |",
           "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |"]
    index = {(r['concept'],r['reading'],r['s'],r['start'],r['x_over_F'],r['case'],r['q']):r for r in sensitivity}
    for row in sensitivity:
        if row['case'] == 'SC-07' and row['q'] == 0:
            key = (row['concept'],row['reading'],row['s'],row['start'],row['x_over_F'])
            release = index[key+('SC-23', .05)]
            md.append("| "+" | ".join(fmt(v) for v in (*key, row['q_star'], release['q_star'], release['expected_over_x'],release['false_cut_cost_usdc']))+" |")
    csv_write("sweep.csv", sweeps)
    csv_write("break-even.csv", breaks)
    csv_write("sensitivity.csv", sensitivity)
    (HERE/"tables.md").write_text("\n".join(md)+"\n")
    print(f"Illustrative: {len(sweeps)} sweep rows, {len(breaks)} sign/break-even rows, {len(sensitivity)} sensitivity rows; tables.md")


if __name__ == "__main__":
    build()
