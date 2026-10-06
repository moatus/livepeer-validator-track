"""Independent hand constants and meaningful branch checks; never read generated outputs."""

from dataclasses import replace
import math

from build import Inputs, UNDEFINED, account, break_evens, marginal, pool, reward


def close(actual, expected):
    assert math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-8), (actual, expected)


def fixtures():
    p = Inputs(F=3000, f=300, s=.05)
    # EX-03.F1: 100 paid, 50 recovered, 30 cost; binding share earns no extra LPT.
    r = account(p, "C0", "MFS", 100)
    close(r["delta_reward_lpt"], 0)
    close(r["delta_cash_usdc"], -80)
    close(r["delta_usdc"], -80)
    # EX-03.F2: .94*32*(130-30) = 3008 USDC, minus 80; equal prices cancel.
    for price in (1, 7):
        low = replace(p, f=30, p_mint=price, p_claim=price)
        r = account(low, "C1", "MFS", 100)
        close(r["delta_reward_lpt"]*price, 3008)
        close(r["delta_usdc"], 2928)
    # EX-03.F3: .94*32*.05*100=150.4 USDC, minus 80.
    r = account(p, "C1", "MFS", 100)
    close(r["delta_reward_lpt"], 150.4)
    close(r["delta_usdc"], 70.4)
    # EX-03.F4: positive C2 target drops by 100 for an added 100; derivative -1.
    close(pool(p, "C2", 100)[0]-pool(p, "C2", 0)[0], -100)
    close(pool(p, "C2", 100)[1], -1)
    # EX-03.F5: N=90240; 400/3100-300/3000=9/310; no stake dependence.
    for stake in (.01, .05, .20):
        r = account(replace(p, s=stake), "C0", "appendix", 100)
        close(r["delta_reward_lpt"], 2619.8709677419356)
        close(r["delta_usdc"], 2539.8709677419356)
    # EX-03.F6: C1, f=30: lose prior .94*32*30=902.4 plus cash cost 80.
    r = account(replace(p, f=30), "C1", "MFS", 100, q=1)
    close(r["expected_usdc"], -982.4)
    # EX-03.F7: F1 plus 100 of internal use value.
    close(account(p, "C0", "MFS", 100, "SC-23", u=1)["delta_usdc"], 20)
    # EX-03.F8: no network fee denominator; not an invented zero share.
    assert account(Inputs(F=0, f=0), "C0", "MFS", 0) == {"status": UNDEFINED}
    # EX-03.F9: above both ceilings, C1 fixed pool and MFS share; slope -0.8.
    scale = Inputs(f=Inputs().F*.1)
    cap_x = 50_000_000/365/32-scale.F
    close(marginal(scale, "C1", "MFS", cap_x, side="left"), .704)
    close(marginal(scale, "C1", "MFS", cap_x, side="right"), -.8)
    close(account(scale, "C1", "MFS", scale.F)["delta_usdc"], -505.2054794520548)
    # EX-03.F10: C2 floor is zero at x=35000000/365; right slope zero.
    floor_x = 35_000_000/365
    close(pool(p, "C2", floor_x)[0], 0)
    close(pool(p, "C2", floor_x, "left")[1], -1)
    close(pool(p, "C2", floor_x, "right")[1], 0)
    close(reward(p, "C2", "MFS", floor_x), 0)
    floor_job = account(p, "C2", "MFS", floor_x, "SC-23", u=1, q=1)
    close(floor_job["expected_usdc"], 14671.232876712327)
    assert floor_job["q_star"] == "no finite q* (zero reward at risk)"
    # EX-03.F11: fractional appendix score normalized once: a=.1,m=.5 => 1/19.
    close(reward(p, "C0", "appendix", 0, .5), 4749.473684210526)
    # EX-03.F12: exclude outsider fee/reward shares without changing pilot sweeps.
    split = replace(p, omega=.5, rho=.8, phi=.3)
    r = account(split, "C1", "MFS", 100)
    close(r["delta_cash_usdc"], -85)
    close(r["delta_reward_lpt"], 97.76)
    close(r["delta_usdc"], 12.76)
    print("EX-03.F1–F12 independent hand fixtures: PASS")


def boundaries_and_sensitivity():
    # Analytic roots use no values read from the generated tables.
    p = Inputs(s=.05, f=Inputs().F*.025)
    for concept in ("C0", "C3"):
        roots, _ = break_evens(p, concept, "MFS")
        close(roots[0], .94)
    roots, _ = break_evens(p, "C0", "appendix")
    close(roots[0], 35.66)
    low = replace(p, s=.01, f=p.F*.005)
    roots, _ = break_evens(low, "C1", "MFS")
    close(roots[0], .30128205128205127)
    assert break_evens(replace(low, f=p.F*.02), "C1", "MFS")[0] == []
    count = 0
    for concept in ("C0", "C1", "C2", "C3"):
        for reading in ("MFS", "appendix"):
            for s in (.01, .05, .20):
                for b in (s/2, 2*s):
                    inp = replace(p, s=s, f=p.F*b)
                    roots, _ = break_evens(inp, concept, reading)
                    for z in roots:
                        close(account(inp, concept, reading, z*inp.F)["delta_usdc"], 0)
                        assert account(inp, concept, reading, z*(1-1e-5)*inp.F)["delta_usdc"] > 0
                        assert account(inp, concept, reading, z*(1+1e-5)*inp.F)["delta_usdc"] < 0
                    for x in (p.F*.001, p.F*.5, p.F*16, p.F*64):
                        base = account(inp, concept, reading, x)
                        one = account(inp, concept, reading, x, q=1)
                        close(one["expected_usdc"], -inp.p_claim*base["R_before_org_lpt"]+base["delta_cash_usdc"])
                        close(reward(inp, concept, reading, x, 0), 0)
                        test = account(inp, concept, reading, x, "SC-23", u=1, q=.05)
                        close(test["expected_usdc"], base["delta_usdc"]+x-.05*base["R_after_org_lpt"])
                        if isinstance(base["q_star"], float):
                            close(account(inp, concept, reading, x, q=base["q_star"])["expected_usdc"], 0)
                        # Finite difference validates the analytic marginal away from kinks.
                        h = x*1e-5
                        left = account(inp, concept, reading, x-h)["delta_usdc"]
                        right = account(inp, concept, reading, x+h)["delta_usdc"]
                        assert math.isclose((right-left)/(2*h), base["marginal_right"],
                                            rel_tol=1e-7, abs_tol=1e-6)
                        count += 1
                    assert account(inp, concept, reading, 0, q=1)["delta_usdc"] == 0
                    assert account(inp, concept, reading, 0, q=1)["expected_usdc"] == 0
                    assert account(inp, concept, reading, 0)["average"] == UNDEFINED
    print(f"48 concept/reading/start combinations: roots and {count} derivative/whole-round sensitivity checks PASS")


def cooperative_sign_regions():
    """Assert the qualified prose claim, including its two-root C2 exception."""
    checked = 0
    for concept in ("C0", "C1", "C2", "C3"):
        for reading in ("MFS", "appendix"):
            for s in (.01, .05, .20):
                for b in (s/2, 2*s):
                    p = Inputs(s=s, f=Inputs().F*b)
                    for case, u in (("SC-01", 0), ("SC-23", 1)):
                        roots, _ = break_evens(p, concept, reading, case, u)
                        exceptional = (concept, reading, s, b) == ("C2", "appendix", .20, .40)
                        if exceptional:
                            # Rounded hand constants from the piecewise identities, not output files.
                            assert len(roots) == 2, (concept, reading, s, b, case, roots)
                            for actual, expected in zip(roots, (24.0128, 59.8182)):
                                assert math.isclose(actual, expected, rel_tol=0, abs_tol=5e-5)
                            # These negatives directly refute the former positive-throughout claim.
                            for z in (24.1, 31.8, 59):
                                assert account(p, concept, reading, z*p.F, case, u)["delta_usdc"] < 0
                            for z in (24, 59.9, 64):
                                assert account(p, concept, reading, z*p.F, case, u)["delta_usdc"] > 0
                        else:
                            assert roots == [], (concept, reading, s, b, case, roots)
                            assert account(p, concept, reading, .01*p.F, case, u)["delta_usdc"] > 0
                            assert account(p, concept, reading, 64*p.F, case, u)["delta_usdc"] > 0
                        checked += 1
    print(f"{checked} outside/testing sign regions: PASS; exactly two C2/appendix exceptions at the same start")


if __name__ == "__main__":
    fixtures()
    boundaries_and_sensitivity()
    cooperative_sign_regions()
