# Validator scoring

Task: [M2.9, issue 31](https://github.com/moatus/livepeer-validator-track/issues/31), GT-02 and GT-09. Status: drafted prospective rules; no payoff or seat-control results yet.

Question: under which rule, participation, cost and overlapping-interest conditions can scoring from evidence be preferable to leniency, abstention or an unsupported low score, and what conditional stake places majority seats?

[Assumptions and reconstruction](assumptions.md) declare evidence boundaries, roles, score/compensation rules, utility units, ledger interfaces, conditional seat assumptions and the stop rule. [Source manifest](input-manifest.json) pins October text/PDF, EX-06/08 ledger code, frozen P1 and both E2 inputs. [Finite comparison contract](cases.json) fixes 16 core choices, 12 named controls and 32 conditional seat rows before calculations. Counts are illustrative research budgets, not observed behavior.

Inputs distinguish paper proposals, measured current-system calibration and illustrative completions. E2's inconclusive purpose input stays inconclusive; its K1 term-breach input is sufficient only with stipulated authentication/custody and safe timely access. Knowledge-required stays unknown. The VD-19 premise is research, not adopted policy. P1 stake thresholds are not acquisition costs. Both P1 and E2 remain drafted, unpublished and pending owner review. September sources stay historical.

Method: reuse the unchanged full-population shared ledger's score/claim inputs, with a separate distribution/cost overlay on its existing validator envelope. Compare symbolic action and participation utilities; unsupported signs remain unknown. Reproduce conditional seat premises from frozen P1 raw pages without extraction. No simulation, new evidence investigation or token purchase model.

Results: none at this prospective boundary. Limits: numeric low scores, missing-score/quorum completions, pay eligibility, cuts applied to validator rewards and synthetic overlapping interests are assumptions. Source hash checks establish byte identity, not usable evidence, ownership, observed effort or behavior. The main-text MFS and appendix work-weighted node wording remain distinct; adverse appendix scores exceed the inherited ledger interface.

Reproduce prospective input checks from repository root, Python 3.10+ standard library only, offline, without Git metadata:

```bash
python3 experiments/m2/validator-scoring/check_inputs.py
```
