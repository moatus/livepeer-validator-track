"""Build the M1.1 litepaper accounting workbook from docs/litepaper-2.0.md. Requires XlsxWriter."""

from __future__ import annotations

import hashlib
from pathlib import Path

import xlsxwriter


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "docs" / "litepaper-2.0.md"
OUTPUT = Path(__file__).resolve().parent / "litepaper-baseline-accounting.xlsx"
SOURCE_SHA256 = "5fc153408fb636d9750788ae987ada6daaa9fc3df3e44f70cadde51a6158fb71"
UNDEFINED = "undefined/needs rule"
CHECK = "check inputs"
VERSION = "v0.3 · 2026-09-26"


def account(fees, stakes, scores, budget=1000, node_share=0.94, node_cut=0.5,
            price=2, fee_retention=(0.8, 0.8), reward_retention=(0.3, 0.3),
            costs=(180, 130)):
    """Independent Python arithmetic for initial cached values, not an emissions rule."""
    total_fees, total_stake = sum(fees), sum(stakes)
    node_budget = budget * node_share
    rows = []
    for i in range(2):
        gross = fees[i]
        node_usdc = gross * node_cut
        fee_share = gross / total_fees if total_fees else None
        stake_share = stakes[i] / total_stake if total_stake else None
        mfs = min(fee_share, stake_share) if fee_share is not None and stake_share is not None else None
        eligible = node_budget * mfs if mfs is not None else None
        paid = eligible * scores[i] if eligible is not None else None
        rows.append(dict(gross=gross, node_usdc=node_usdc,
                         operator_fee=node_usdc * fee_retention[i],
                         delegator_fee=node_usdc * (1-fee_retention[i]),
                         bme=gross*(1-node_cut), cost=costs[i],
                         fee_net=node_usdc*fee_retention[i]-costs[i],
                         fee_share=fee_share, stake_share=stake_share, mfs=mfs,
                         score=scores[i], eligible=eligible, paid=paid,
                         operator_lpt=paid*reward_retention[i] if paid is not None else None,
                         delegator_lpt=paid*(1-reward_retention[i]) if paid is not None else None))
    if any(row["mfs"] is None for row in rows):
        unallocated = withheld = paid_total = None
    else:
        unallocated = node_budget * (1-sum(row["mfs"] for row in rows))
        withheld = sum(row["eligible"]-row["paid"] for row in rows)
        paid_total = sum(row["paid"] for row in rows)
    return dict(rows=rows, fees=total_fees, stake=total_stake, node_budget=node_budget,
                unallocated=unallocated, withheld=withheld, paid=paid_total,
                bme=total_fees*(1-node_cut), burned=total_fees*(1-node_cut)/price if price>0 else None)


def build():
    actual = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if actual != SOURCE_SHA256:
        raise SystemExit(f"Litepaper changed: expected {SOURCE_SHA256}, got {actual}. Review citations before rebuilding.")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb = xlsxwriter.Workbook(str(OUTPUT))
    wb.set_calc_mode("auto")
    navy, teal, blue, pale, gold, ink = "#16324F", "#087F8C", "#DDEBF7", "#EEF6F7", "#FFF1CC", "#233443"
    title = wb.add_format({"bold": True, "font_size": 18, "font_color": navy})
    subtitle = wb.add_format({"font_color": ink, "text_wrap": True, "valign": "top"})
    head = wb.add_format({"bold": True, "font_color": "#FFFFFF", "bg_color": navy, "text_wrap": True, "valign": "vcenter", "bottom": 1, "bottom_color": teal})
    label = wb.add_format({"font_color": ink, "valign": "vcenter"})
    note = wb.add_format({"font_color": "#526477", "text_wrap": True, "valign": "top"})
    note_yellow = wb.add_format({"font_color": ink, "bg_color": gold, "text_wrap": True})
    input_money = wb.add_format({"bg_color": blue, "num_format": '#,##0.00;[Red](#,##0.00);0.00', "font_color": navy})
    input_pct = wb.add_format({"bg_color": blue, "num_format": '0.0%', "font_color": navy})
    input_num = wb.add_format({"bg_color": blue, "num_format": '#,##0.00', "font_color": navy})
    usdc = wb.add_format({"num_format": '"USDC "#,##0.00;[Red]("USDC "#,##0.00);"USDC "0.00'})
    lpt = wb.add_format({"num_format": '"LPT "#,##0.00;[Red]("LPT "#,##0.00);"LPT "0.00'})
    pct = wb.add_format({"num_format": '0.0%'})
    plain = wb.add_format({"num_format": '#,##0.00;[Red](#,##0.00);0.00'})
    status = wb.add_format({"bold": True, "font_color": teal})

    def formula(ws, cell, expr, fmt=None, value=None):
        ws.write_formula(cell, expr, fmt, value if value is not None else UNDEFINED)

    def setup(ws, widths, freeze=(4, 0), print_area=None):
        ws.hide_gridlines(2)
        for col, width in widths.items():
            ws.set_column(col, col, width)
        ws.freeze_panes(*freeze)
        ws.set_landscape()
        ws.fit_to_pages(1, 1)
        if print_area:
            ws.print_area(print_area)

    # Inputs. All blue cells are editable; source status and units are adjacent.
    ins = wb.add_worksheet("Inputs")
    setup(ins, {0: 31, 1: 18, 2: 19, 3: 23, 4: 75, 7: 24, 8: 71}, (4, 1), "A1:I27")
    ins.write("A1", "M1.1 | Baseline inputs", title)
    ins.merge_range("A2:E3", f"{VERSION} · Draft, not reviewed. Automated QA passed; human milestone review pending. Blue cells are proposed starting values from the litepaper or illustrative modeling choices. One round; no fee-linked emissions rule.", subtitle)
    for c, h in enumerate(("Parameter", "Value", "Unit", "Status", "Basis / limit")):
        ins.write(3, c, h, head)
    input_rows = [
        (5, "Node fee cut", .5, "fraction of gross USDC", "Paper proposal", "Node/network split, lines 117–121; Appendix, lines 226–227"),
        (6, "BME network fee", .5, "fraction of gross USDC", "Paper proposal", "Node/network split, lines 117–121; Appendix, lines 226–227"),
        (8, "Node emission share", .94, "fraction of mint", "Paper proposal", "Appendix, lines 207–215 and 231"),
        (9, "Validator emission share", .01, "fraction of mint", "Paper proposal", "Appendix, lines 207–215 and 232; set allocation only"),
        (10, "Treasury emission share", .05, "fraction of mint", "Paper proposal", "Appendix, lines 207–215 and 233; set allocation only"),
        (12, "Buyback execution price", 2, "USDC / LPT", "Illustrative", "Price is not given; execution, slippage and timing remain open, lines 121–125, 189–200"),
        (14, "Entered emission envelope", 1000, "LPT / round", "Illustrative", "Authorized/entered budget, not established actual mint. Emissions choices open, lines 128–140; no 32× rule."),
    ]
    for row, name, value, unit, kind, basis in input_rows:
        ins.write(f"A{row}", name, label)
        ins.write_number(f"B{row}", value, input_pct if row in (5, 6, 8, 9, 10) else input_money)
        ins.write(f"C{row}", unit, note)
        ins.write(f"D{row}", kind, note)
        ins.write(f"E{row}", basis, note)
        if row in (5, 6, 8, 9, 10):
            ins.data_validation(f"B{row}", {"validate": "decimal", "criteria": "between", "minimum": 0, "maximum": 1})
        else:
            ins.data_validation(f"B{row}", {"validate": "decimal", "criteria": ">" if row == 12 else ">=", "value": 0})
        ins.set_row(row-1, 32)
    ins.write("A16", "Fee shares sum to 100%", label)
    formula(ins, "B16", '=IFERROR(IF(COUNT(B5:B6)=2,IF(AND(MIN(B5:B6)>=0,MAX(B5:B6)<=1,ABS(SUM(B5:B6)-1)<0.0000001),"OK","check inputs"),"check inputs"),"check inputs")', status, "OK")
    ins.write("A17", "Emission shares sum to 100%", label)
    formula(ins, "B17", '=IFERROR(IF(COUNT(B8:B10)=3,IF(AND(MIN(B8:B10)>=0,MAX(B8:B10)<=1,ABS(SUM(B8:B10)-1)<0.0000001),"OK","check inputs"),"check inputs"),"check inputs")', status, "OK")
    ins.write("A18", "All active inputs", label)
    formula(ins, "B18", '=IFERROR(IF(AND(B16="OK",B17="OK",COUNT(B12,B14)=2,COUNT(B23:C24)=4,COUNT(D23:F24)=6,COUNT(G23:G24)=2),IF(AND(B12>0,B14>=0,MIN(B23:C24)>=0,MIN(D23:F24)>=0,MAX(D23:F24)<=1,MIN(G23:G24)>=0),"OK","check inputs"),"check inputs"),"check inputs")', status, "OK")
    ins.merge_range("A20:E20", "TWO COOPERATIVE NODES | same period; customer fees and delegated stake are inputs, not evidence of independent demand", head)
    for c, h in enumerate(("Node", "Gross fees | USDC", "Stake | LPT", "Honesty multiplier | 0–1", "Operator fee cut | fraction", "Operator reward cut | fraction", "Operator cost | USDC", "Input status", "Source context")):
        ins.write(21, c, h, head)
    ins.set_column("F:F", 26)
    ins.set_column("G:G", 25)
    for row, name, vals in ((23, "A", (600, 600, 1, .8, .3, 180)), (24, "B", (400, 400, 1, .8, .3, 130))):
        ins.write(f"A{row}", name)
        for c, v in enumerate(vals, 1):
            ins.write_number(row-1, c, v, input_pct if c in (3, 4, 5) else input_num)
            ins.data_validation(row-1, c, row-1, c, {"validate": "decimal", "criteria": "between" if c in (3, 4, 5) else ">=", "minimum": 0, "maximum": 1} if c in (3, 4, 5) else {"validate": "decimal", "criteria": ">=", "value": 0})
        ins.write(f"H{row}", "Illustrative", note)
        ins.write(f"I{row}", "Fees/stake/score are illustrative; paper mechanics: MFS 51–63, delegation 65–77, multiplier 79–90, cuts Appendix 231–232. Costs: research assumption.", note)
        ins.set_row(row-1, 43)
    ins.merge_range("A26:I27", "Node fee cut is the portion of gross USDC routed to the node before its own fee cut for delegators. Operator reward cut divides only earned node LPT after the multiplier. Costs are illustrative operator cash costs; delegator costs, validator distribution, taxes and market liquidity are not modeled.", note_yellow)
    ins.set_row(20, 28)
    ins.set_row(21, 47)

    baseline = account((600, 400), (600, 400), (1, 1))
    co = wb.add_worksheet("Cooperative")
    setup(co, {0: 12, **{i: 18 for i in range(1, 16)}}, (5, 1), "A1:P30")
    co.write("A1", "Cooperative accounting | one round", title)
    co.merge_range("A2:P3", "USDC customer payments and LPT emissions are separate ledgers. MFS = min(fee share, stake share); node entitlement = entered LPT emission envelope × node share × MFS × honesty multiplier. This reconstructs main text lines 55–61, 84–86 with Appendix lines 207–215, 220, 231. No normalization or redistribution is assumed.", subtitle)
    headers = ["Node", "Gross fees\nUSDC", "Node receipt before cuts\nUSDC", "Operator fee retained\nUSDC", "Delegator fee share\nUSDC", "BME funding\nUSDC", "Operator cost\nUSDC", "Operator fee net\nUSDC", "Fee share", "Stake share", "MFS share", "Honesty score", "MFS-eligible\nLPT", "Node entitlement\nLPT", "Operator share\nLPT", "Delegator share\nLPT"]
    for c, h in enumerate(headers):
        co.write(4, c, h, head)
    co.set_row(4, 55)
    for idx, row in enumerate((6, 7)):
        ir = 23 + idx
        v = baseline["rows"][idx]
        co.write(f"A{row}", "A" if idx == 0 else "B", label)
        exprs = {
            "B": (f"=Inputs!B{ir}", v["gross"]),
            "C": (f'=IF(Inputs!$B$18="OK",B{row}*Inputs!$B$5,"{CHECK}")', v["node_usdc"]),
            "D": (f'=IF(Inputs!$B$18="OK",C{row}*Inputs!E{ir},"{CHECK}")', v["operator_fee"]),
            "E": (f'=IF(Inputs!$B$18="OK",C{row}-D{row},"{CHECK}")', v["delegator_fee"]),
            "F": (f'=IF(Inputs!$B$18="OK",B{row}*Inputs!$B$6,"{CHECK}")', v["bme"]),
            "G": (f"=Inputs!G{ir}", v["cost"]),
            "H": (f'=IF(Inputs!$B$18="OK",D{row}-G{row},"{CHECK}")', v["fee_net"]),
            "I": (f'=IF(Inputs!$B$18<>"OK","{CHECK}",IF(SUM($B$6:$B$7)=0,"{UNDEFINED}",B{row}/SUM($B$6:$B$7)))', v["fee_share"]),
            "J": (f'=IF(Inputs!$B$18<>"OK","{CHECK}",IF(SUM(Inputs!$C$23:$C$24)=0,"{UNDEFINED}",Inputs!C{ir}/SUM(Inputs!$C$23:$C$24)))', v["stake_share"]),
            "K": (f'=IF(OR(NOT(ISNUMBER(I{row})),NOT(ISNUMBER(J{row}))),"{UNDEFINED}",MIN(I{row},J{row}))', v["mfs"]),
            "L": (f"=Inputs!D{ir}", v["score"]),
            "M": (f'=IF(NOT(ISNUMBER(K{row})),"{UNDEFINED}",Inputs!$B$14*Inputs!$B$8*K{row})', v["eligible"]),
            "N": (f'=IF(NOT(ISNUMBER(M{row})),"{UNDEFINED}",M{row}*L{row})', v["paid"]),
            "O": (f'=IF(NOT(ISNUMBER(N{row})),"{UNDEFINED}",N{row}*Inputs!F{ir})', v["operator_lpt"]),
            "P": (f'=IF(NOT(ISNUMBER(N{row})),"{UNDEFINED}",N{row}-O{row})', v["delegator_lpt"]),
        }
        for col, (expr, val) in exprs.items():
            fmt = pct if col in "IJKL" else lpt if col in "MNOP" else usdc
            guarded = f'=IF(Inputs!$B$18<>"OK","{CHECK}",{expr[1:]})'
            formula(co, f"{col}{row}", guarded, fmt, val)
    co.write("A9", "TOTAL", head)
    for col in "BCDEFGHMNOP":
        val = sum(baseline["rows"][i][{"B":"gross","C":"node_usdc","D":"operator_fee","E":"delegator_fee","F":"bme","G":"cost","H":"fee_net","M":"eligible","N":"paid","O":"operator_lpt","P":"delegator_lpt"}[col]] for i in range(2))
        expr = (f'=IF(COUNT({col}6:{col}7)=2,SUM({col}6:{col}7),"{UNDEFINED}")'
                if col in "MNOP" else f"=SUM({col}6:{col}7)")
        guarded = f'=IF(Inputs!$B$18<>"OK","{CHECK}",{expr[1:]})'
        formula(co, f"{col}9", guarded, lpt if col in "MNOP" else usdc, val)
    co.merge_range("A12:P13", "The operator receives the node-side fee before any delegator fee cut. LPT reward cuts apply after MFS and the honesty multiplier. A fee-side operating loss can coexist with LPT rewards; the workbook does not convert those rewards into USDC or claim profitability. The score addresses dishonesty, not general uptime (litepaper lines 84–88).", note_yellow)
    co.merge_range("A16:P17", "A zero-stake node still receives its ordinary USDC fee portion. If either network fee total or network stake total is zero, MFS and LPT outcomes display 'undefined/needs rule'. The paper does not specify denominator behavior; zeros are never replaced by invented protocol outcomes.", note)

    ov = wb.add_worksheet("Ledger & limits")
    setup(ov, {0: 39, 1: 22, 2: 25, 3: 82}, (5, 1), "A1:D35")
    ov.write("A1", "Round ledger | separate units", title)
    ov.merge_range("A2:D3", f"{VERSION} · Draft, not reviewed. Automated QA is distinct from pending human milestone review. This reconstructs proposed starting values, not deployed behavior or an accepted protocol decision.", subtitle)
    for c, h in enumerate(("Line", "Value", "Unit", "Meaning / treatment")):
        ov.write(4, c, h, head)
    ledger = [
        (6, "Gross customer payments", "=Cooperative!B9", 1000, "USDC", "Customers pay nodes for real jobs; independent demand is not inferred."),
        (7, "Node-side receipt before cuts", "=Cooperative!C9", 500, "USDC", "Operator + delegator fee shares; before operator costs."),
        (8, "BME purchase funding", "=Cooperative!F9", 500, "USDC", "Separate fee-side route; no LPT minted here."),
        (9, "Operator retained fee", "=Cooperative!D9", 400, "USDC", "After illustrative operator fee cut; before operator costs."),
        (10, "Delegator fee share", "=Cooperative!E9", 100, "USDC", "Share of node-side receipt; not an extra network fee."),
        (11, "Operator fee net after costs", "=Cooperative!H9", 90, "USDC", "Excludes LPT rewards and delegator costs."),
        (13, "LPT purchased and burned", f'=IF(Inputs!$B$18<>"OK","{CHECK}",B8/Inputs!$B$12)', 250, "LPT", "Illustrative price; actual execution, slippage and timing unresolved."),
        (15, "Entered emission envelope", "=Inputs!B14", 1000, "LPT", "Authorized/entered budget, not established actual mint; no endogenous 32× fee rule."),
        (16, "Node emission envelope", "=B15*Inputs!B8", 940, "LPT", "94% starting value, editable."),
        (17, "Validator emission envelope", "=B15*Inputs!B9", 10, "LPT", "Allocation only; validator participation/distribution not modeled."),
        (18, "Treasury emission envelope", "=B15*Inputs!B10", 50, "LPT", "Allocation only; spending not modeled."),
        (20, "MFS-unallocated node amount", f'=IF(OR(NOT(ISNUMBER(Cooperative!K6)),NOT(ISNUMBER(Cooperative!K7))),"{UNDEFINED}",B16-Cooperative!M9)', 0, "LPT", "Gap before honesty scoring; no redistribution rule assumed."),
        (21, "Score-withheld node amount", f'=IF(NOT(ISNUMBER(Cooperative!N9)),"{UNDEFINED}",Cooperative!M9-Cooperative!N9)', 0, "LPT", "Separate gap caused by multiplier below 1; disposition unresolved."),
        (22, "Modeled node entitlement", '=IF(NOT(ISNUMBER(Cooperative!N9)),"undefined/needs rule",Cooperative!N9)', 940, "LPT", "After MFS and honesty multiplier; actual mint/settlement rule remains unresolved."),
        (23, "Operator share of entitlement", '=IF(NOT(ISNUMBER(Cooperative!O9)),"undefined/needs rule",Cooperative!O9)', 282, "LPT", "Illustrative operator reward cuts; not confirmed minted LPT."),
        (24, "Delegator share of entitlement", '=IF(NOT(ISNUMBER(Cooperative!P9)),"undefined/needs rule",Cooperative!P9)', 658, "LPT", "Illustrative delegator shares; not confirmed minted LPT."),
    ]
    for row, name, expr, val, unit, desc in ledger:
        ov.write(f"A{row}", name, label)
        guarded = f'=IF(Inputs!$B$18<>"OK","{CHECK}",{expr[1:]})'
        formula(ov, f"B{row}", guarded, lpt if unit == "LPT" else usdc, val)
        ov.write(f"C{row}", unit, note)
        ov.write(f"D{row}", desc, note)
    ov.write("A26", "Fee conservation", label)
    formula(ov, "B26", '=IF(Inputs!B18<>"OK","check inputs",IF(AND(COUNT(B6:B8)=3,ABS(B6-B7-B8)<0.0000001),"OK","check inputs"))', status, "OK")
    ov.write("A27", "Emission accounting", label)
    formula(ov, "B27", '=IF(Inputs!B18<>"OK","check inputs",IF(OR(NOT(ISNUMBER(B20)),NOT(ISNUMBER(B21))),"undefined/needs rule",IF(AND(COUNT(B15:B18)=4,COUNT(B20:B22)=3,ABS(B15-SUM(B17:B18)-SUM(B20:B22))<0.0000001),"OK","check inputs")))', status, "OK")
    ov.merge_range("A30:D32", "MFS remainder and score withholding are accounted for but their final mint/burn/rollover treatment is unspecified. The entered emission envelope is not a statement of actual LPT minted. The workbook does not infer supply change by subtracting purchased/burned LPT from that envelope.", note_yellow)

    sens = wb.add_worksheet("One-variable")
    setup(sens, {0: 20, **{i: 19 for i in range(1, 11)}, 11: 21}, (7, 2), "A1:L29")
    sens.write("A1", "One-variable sensitivity", title)
    sens.merge_range("A2:L3", "Hold the entered LPT envelope, B's fees and B's stake fixed. Change only A's fees or only A's stake. Both network denominators are recomputed from the displayed inputs. A/B honesty scores remain at their Inputs values. No adoption forecast.", subtitle)
    sens.merge_range("A5:L5", "A FEES CHANGE | B fees and both stakes fixed; entered LPT envelope held fixed", head)
    h1 = ["A fees\nUSDC", "Network fees\nUSDC", "A fee share", "A stake share", "A MFS", "B MFS", "MFS total", "A entitlement\nLPT", "B entitlement\nLPT", "MFS gap\nLPT", "Score gap\nLPT", "Row status"]
    for c, h in enumerate(h1): sens.write(5, c, h, head)
    sens.set_row(5, 38)
    fee_grid = (0, 250, 500, 600, 750, 1000, 1500)
    for row, a_fee in zip(range(7, 14), fee_grid):
        model = account((a_fee, 400), (600, 400), (1, 1))
        m = model["rows"]
        sens.write_number(f"A{row}", a_fee, input_num)
        sens.data_validation(f"A{row}", {"validate": "decimal", "criteria": ">=", "value": 0})
        formula(sens, f"L{row}", f'=IF(Inputs!$B$18<>"OK","{CHECK}",IFERROR(IF(ISNUMBER(A{row}),IF(A{row}>=0,"OK","{CHECK}"),"{CHECK}"),"{CHECK}"))', status, "OK")
        expressions = [
            ("B", f"=A{row}+Inputs!$B$24", model["fees"], usdc),
            ("C", f'=IF(B{row}=0,"{UNDEFINED}",A{row}/B{row})', m[0]["fee_share"], pct),
            ("D", '=IF(SUM(Inputs!$C$23:$C$24)=0,"undefined/needs rule",Inputs!$C$23/SUM(Inputs!$C$23:$C$24))', m[0]["stake_share"], pct),
            ("E", f'=IF(OR(NOT(ISNUMBER(C{row})),NOT(ISNUMBER(D{row}))),"{UNDEFINED}",MIN(C{row},D{row}))', m[0]["mfs"], pct),
            ("F", f'=IF(OR(NOT(ISNUMBER(C{row})),NOT(ISNUMBER(D{row}))),"{UNDEFINED}",MIN(Inputs!$B$24/B{row},Inputs!$C$24/SUM(Inputs!$C$23:$C$24)))', m[1]["mfs"], pct),
            ("G", f'=IF(OR(NOT(ISNUMBER(E{row})),NOT(ISNUMBER(F{row}))),"{UNDEFINED}",E{row}+F{row})', sum(x["mfs"] for x in m), pct),
            ("H", f'=IF(NOT(ISNUMBER(E{row})),"{UNDEFINED}",Inputs!$B$14*Inputs!$B$8*E{row}*Inputs!$D$23)', m[0]["paid"], lpt),
            ("I", f'=IF(NOT(ISNUMBER(F{row})),"{UNDEFINED}",Inputs!$B$14*Inputs!$B$8*F{row}*Inputs!$D$24)', m[1]["paid"], lpt),
            ("J", f'=IF(NOT(ISNUMBER(G{row})),"{UNDEFINED}",Inputs!$B$14*Inputs!$B$8*(1-G{row}))', model["unallocated"], lpt),
            ("K", f'=IF(NOT(ISNUMBER(G{row})),"{UNDEFINED}",Inputs!$B$14*Inputs!$B$8*G{row}-H{row}-I{row})', model["withheld"], lpt),
        ]
        for col, expr, val, fmt in expressions:
            formula(sens, f"{col}{row}", f'=IF($L{row}<>"OK","{CHECK}",{expr[1:]})', fmt, val)
    sens.merge_range("A16:L16", "A STAKE CHANGES | B stake and both fees fixed; entered LPT envelope held fixed", head)
    h2 = ["A stake\nLPT", "Network stake\nLPT", "A fee share", "A stake share", "A MFS", "B MFS", "MFS total", "A entitlement\nLPT", "B entitlement\nLPT", "MFS gap\nLPT", "Score gap\nLPT", "Row status"]
    for c, h in enumerate(h2): sens.write(16, c, h, head)
    sens.set_row(16, 38)
    stake_grid = (0, 100, 250, 400, 600, 1000, 1500)
    for row, a_stake in zip(range(18, 25), stake_grid):
        model = account((600, 400), (a_stake, 400), (1, 1))
        m = model["rows"]
        sens.write_number(f"A{row}", a_stake, input_num)
        sens.data_validation(f"A{row}", {"validate": "decimal", "criteria": ">=", "value": 0})
        formula(sens, f"L{row}", f'=IF(Inputs!$B$18<>"OK","{CHECK}",IFERROR(IF(ISNUMBER(A{row}),IF(A{row}>=0,"OK","{CHECK}"),"{CHECK}"),"{CHECK}"))', status, "OK")
        exprs = [
            ("B", f"=A{row}+Inputs!$C$24", model["stake"], plain),
            ("C", '=IF(SUM(Inputs!$B$23:$B$24)=0,"undefined/needs rule",Inputs!$B$23/SUM(Inputs!$B$23:$B$24))', m[0]["fee_share"], pct),
            ("D", f'=IF(B{row}=0,"{UNDEFINED}",A{row}/B{row})', m[0]["stake_share"], pct),
            ("E", f'=IF(OR(NOT(ISNUMBER(C{row})),NOT(ISNUMBER(D{row}))),"{UNDEFINED}",MIN(C{row},D{row}))', m[0]["mfs"], pct),
            ("F", f'=IF(OR(NOT(ISNUMBER(C{row})),NOT(ISNUMBER(D{row}))),"{UNDEFINED}",MIN(Inputs!$B$24/SUM(Inputs!$B$23:$B$24),Inputs!$C$24/B{row}))', m[1]["mfs"], pct),
            ("G", f'=IF(OR(NOT(ISNUMBER(E{row})),NOT(ISNUMBER(F{row}))),"{UNDEFINED}",E{row}+F{row})', sum(x["mfs"] for x in m), pct),
            ("H", f'=IF(NOT(ISNUMBER(E{row})),"{UNDEFINED}",Inputs!$B$14*Inputs!$B$8*E{row}*Inputs!$D$23)', m[0]["paid"], lpt),
            ("I", f'=IF(NOT(ISNUMBER(F{row})),"{UNDEFINED}",Inputs!$B$14*Inputs!$B$8*F{row}*Inputs!$D$24)', m[1]["paid"], lpt),
            ("J", f'=IF(NOT(ISNUMBER(G{row})),"{UNDEFINED}",Inputs!$B$14*Inputs!$B$8*(1-G{row}))', model["unallocated"], lpt),
            ("K", f'=IF(NOT(ISNUMBER(G{row})),"{UNDEFINED}",Inputs!$B$14*Inputs!$B$8*G{row}-H{row}-I{row})', model["withheld"], lpt),
        ]
        for col, expr, val, fmt in exprs:
            formula(sens, f"{col}{row}", f'=IF($L{row}<>"OK","{CHECK}",{expr[1:]})', fmt, val)
    sens.merge_range("A27:L28", "Edit blue values on Inputs or blue A values here. Each sensitivity row checks its blue input and shared settings before calculating. Formula caches describe the saved scenario; spreadsheet software recalculates on open. Rows are independent cases, not changes to Inputs node rows.", note_yellow)

    market = wb.add_worksheet("Pass-through margin")
    setup(market, {0: 39, 1: 22, 2: 24, 3: 82}, (5, 1), "A1:D21")
    market.write("A1", "Ordinary API pass-through | one job", title)
    market.merge_range("A2:D3", "Illustrative outsider case: a no-bond operator buys an upstream API call to fulfill a customer job. No quality, SLA, reward, or demand claim is inferred. The simple fee margin can be negative even when MFS rewards are zero.", subtitle)
    for c, h in enumerate(("Input / output", "Value", "Unit", "Basis / interpretation")): market.write(4, c, h, head)
    pass_rows = [
        (6, "Customer price", 1, "USDC / job", "Illustrative operator-set price; paper lines 51–63, 111–119"),
        (7, "Upstream API cost", .4, "USDC / job", "Illustrative third-party expense; research scenario"),
        (8, "Other variable cost", .02, "USDC / job", "Illustrative payment/compute overhead; research scenario"),
        (9, "Node fee cut", None, "fraction", "Linked to Inputs!B5; proposed initial split, paper lines 117–121"),
        (10, "Operator fee retention", None, "fraction", "Linked to Inputs!E23; illustrative 80% retention. A fee-only undelegated operator may use 100%; no sharing mandate inferred."),
    ]
    for row, name, val, unit, desc in pass_rows:
        market.write(f"A{row}", name, label)
        if val is not None:
            market.write_number(f"B{row}", val, input_money)
            market.data_validation(f"B{row}", {"validate": "decimal", "criteria": ">=", "value": 0})
        else:
            formula(market, f"B{row}", "=Inputs!B5" if row == 9 else "=Inputs!E23", pct, .5 if row == 9 else .8)
        market.write(f"C{row}", unit, note)
        market.write(f"D{row}", desc, note)
    market.write("A11", "Local input status", label)
    formula(market, "B11", '=IF(Inputs!B18<>"OK","check inputs",IFERROR(IF(COUNT(B6:B8)=3,IF(MIN(B6:B8)>=0,"OK","check inputs"),"check inputs"),"check inputs"))', status, "OK")
    market.write("C11", "validation", note)
    market.write("D11", "All three blue local inputs must be finite, numeric and nonnegative; linked fractions use Inputs validation.", note)
    for row, name, expr, val, desc in [
        (12, "Operator cash receipt", '=B6*B9*B10', .4, "After node-side and illustrative delegator fee sharing; before supplier costs."),
        (13, "Contribution margin", '=B12-B7-B8', -.02, "Cash per job; excludes fixed costs and LPT."),
        (14, "Break-even customer price", '=IF(B9*B10=0,IF(B7+B8>0,"no finite break-even","no unique break-even"),(B7+B8)/(B9*B10))', 1.05, "Zero retention/cut with positive costs has no finite break-even; zero costs make every price break even."),
    ]:
        market.write(f"A{row}", name, label)
        formula(market, f"B{row}", f'=IF($B$11<>"OK","{CHECK}",{expr[1:]})', usdc, val)
        market.write(f"C{row}", "USDC / job", note)
        market.write(f"D{row}", desc, note)
    market.merge_range("A17:D19", "Permissionless listing and ordinary fee receipts are explicit in the paper. The default assumes 80% operator retention after sharing with delegators; a fee-only undelegated operator may set 100%. An outsider still needs demand and viable margin; stake limits inflation rewards, not sales. No observed exclusion is claimed.", note_yellow)

    src = wb.add_worksheet("Source & decisions")
    setup(src, {0: 25, 1: 28, 2: 78, 3: 80}, (5, 1), "A1:D29")
    src.write("A1", "Source, interpretation, missing rules", title)
    src.merge_range("A2:D3", f"Primary source: Doug Petkanics, Livepeer 2.0 Litepaper (Sept 2026), snapshot docs/litepaper-2.0.md in the livepeer-validator-track repository; SHA-256 {actual}. Line references are to that snapshot.", subtitle)
    for c, h in enumerate(("Classification", "Paper heading / lines", "What the paper says", "Workbook treatment or decision needed")): src.write(4, c, h, head)
    source_rows = [
        ("Explicit paper", "Design Principles, 31–38", "Rewards should follow honest work; active roles; governance adjustability; explainable mechanisms.", "Objective only. Payment and execution are not themselves proof of independent demand or economic value."),
        ("Explicit paper", "Unified Node, 40–49", "AI work can be nondeterministic; validators judge honesty, including self-dealing and wrong results.", "No universal correctness oracle is assumed. Evidence and criteria remain to be specified."),
        ("Explicit paper", "Node operators / MFS, 51–63; Appendix 219–220", "Any address may register without fixed LPT bond. MFS = min(fee share, stake share). Fees are uncapped; stake caps inflation rewards.", "No-stake operator can earn ordinary USDC fee receipts, but receives zero MFS LPT when network stake is positive."),
        ("Explicit paper", "Delegation, 65–77", "Delegation and reward/fee-cut mechanics continue; stake backs nodes and influences top-N validator access.", "Illustrative cuts shown separately after gross node receipt and earned LPT."),
        ("Explicit paper", "Validators, 79–90; Appendix 221–224", "Top-staked opt-ins score 0–1; median multiplier governs reward eligibility; score targets dishonesty, not service quality.", "Input is an already-aggregated multiplier. Validator votes, timing, evidence and actual distribution are outside this workbook."),
        ("Explicit paper", "USDC / BME, 111–125; Appendix 225–233", "Starting 50/50 fee split; network share purchases LPT and initially burns 100%; 94/1/5 emission shares; separate mint.", "Track USDC fee flow, authorized emission envelope and purchased/burned LPT separately. Actual minted amount is not established."),
        ("Explicit paper", "Emissions, 128–140", "Section is an open idea draft with three emissions concepts.", "Hold one entered LPT round budget fixed to isolate allocation arithmetic, not to recommend an emissions policy. No fee-linked 32× rule is implemented."),
        ("Reconstruction", "MFS 55–61 + score 84–86 + Appendix 207–215, 231", "Paper gives components but no one-line complete node payout identity.", "Node payout = budget × node share × min(f_i/F, s_i/S) × multiplier, with no normalization. Not adopted protocol behavior."),
        ("Necessary missing detail", "MFS 55–63; Appendix 220, 231", "No rule states fate of unmatched MFS share or score-withheld node allocation.", "Show distinct gaps. Do not redistribute, burn or count either as certainly minted."),
        ("Necessary missing detail", "MFS 55–63; Emissions 128–140", "Zero network fees or zero network stake makes at least one share undefined.", "Display 'undefined/needs rule' for MFS and rewards."),
        ("Necessary missing detail", "BME 121–125; Appendix 228–230", "DEX execution and nondefault fee-side allocation remain open; Appendix wording has a denominator ambiguity for post-burn cuts.", "Model starting 100% burn only. Do not implement treasury/validator fee-side cuts."),
        ("Research hypothesis", "Node operators 51–63", "No-bond entry and ordinary fees are explicit; new suppliers may still face price/margin and customer-discovery pressure.", "Pass-through sheet tests a conditional business margin. No observed market exclusion claimed."),
        ("Research hypothesis", "Unified Node 40–49; Validators 79–90", "Judging nondeterministic work and distinguishing self-dealing from legitimate common ownership need criteria and contestable evidence.", "Not estimated by this accounting sheet. A real job can still lack independent demand."),
        ("Validator judgment", "Validators, 79–90; Rewards delay, 107–109", "Active validators assess node dishonesty and their median score affects reward eligibility at claim time.", "Evidence for nondeterministic jobs and legitimate common ownership needs criteria and review. A score does not set listing access or the emission budget."),
        ("Governance / protocol", "Design Principles 35–38; Validator 79–90; Emissions 128–140", "Adjustable and open policy choices require collective specification.", "Set emissions, denominator windows, MFS/score gap disposition, validator criteria/appeals and buyback execution; do not infer them from a validator score."),
    ]
    for row, values in enumerate(source_rows, 6):
        for col, value in enumerate(values): src.write(row-1, col, value, note)
        src.set_row(row-1, 61)
    src.merge_range("A22:D24", "This baseline distinguishes the litepaper's provisions from accounting interpretations and research hypotheses. It identifies missing rules without proposing successor mechanisms. Heading and line references to the docs/litepaper-2.0.md snapshot, with its SHA-256, are supplied for reproducibility.", note_yellow)
    wb.close()
    return OUTPUT


if __name__ == "__main__":
    print(build())
