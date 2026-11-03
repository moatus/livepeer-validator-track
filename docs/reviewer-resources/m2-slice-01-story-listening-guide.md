# Slice One: The Story, M2.1 to M2.3

> Historical September-source review guide. This preserves the original pilot narrative and then-current status commentary. For current October assumptions and the next work, use the [M2 specification](../m2/SPEC.md) and [Slice 2 preparation](../m2/SLICE-02.md). This guide is not an October review or acceptance.

About ten minutes. Built only from the validator-track workbench and repository, as at commit 31edc45. No identifiers are spoken. A short reference list sits at the end.

## The starting point

M1 left a worry. If fees drive the inflation reward, a participant might pay its own node for real jobs and collect more reward than the jobs cost. Proving the work happened doesn't settle it, because it did happen. M1 ranked this as the central untested risk, and also as one the paper itself half-answers: it points to the stake minimum, the mint cap, the seven-round delay and validator scoring.

So the first slice of M2 asked two questions, kept separate on purpose. Does one extra self-funded job pay? And could a validator tell it apart, in time, from an operator's own legitimate release testing?

## M2.1: what we learned from putting the pieces back together

The first lesson was that you can't test the worry until you decide how the paper's open rules read. So M2.1 built a register of twenty-two of them, each with a stated base reading and carried variants.

Three of those choices turned out to matter most.

The first is how the reward is computed. The main text says a node's share is the smaller of its fee share and its stake share, so stake sets a ceiling. The appendix describes it as proportional to work, with no stake term at all. The paper doesn't choose. Both were carried.

The second is how big the pool is. The paper's emissions section is an unfinished draft with three concepts: one ties the mint to fees up to a cap, one subtracts fee increases from a starting mint, and one follows participation. A fixed-pool control was added to isolate who takes a share, separate from how big the pool is.

The third is what counts as self-dealing, and when a lower score is warranted. Two standards, narrow and broad. Two readings of when to cut: only on evidence of a violation, or also when the operator doesn't explain.

M2.1 also learned something about the worry itself. The paper offers two different limits, one on a node's share and one on the size of the pool, and its answer to share-taking from a fixed pool is validator scoring and the delay. But the delay was argued for a one-round fee spike. Real jobs that are paid for and correctly run needn't look like a spike. So whether seven rounds produce evidence anyone can act on became the pivotal open question.

And it learned what the reward is supposed to buy is not defined. The paper says fees for honest work during bootstrapping. It doesn't say whether useful internal work counts, and it doesn't require independent customers. So three answers were kept apart from here on: is it profitable, is the intended contribution missing, and could a validator defensibly call it dishonest.

M2.1 closed by rating the paper's five expected relationships as conditional, not tested, and by noting that the nodes with the highest reward ceilings are also the ones eligible to validate. It narrowed the tests to stay small and handed them on.

## M2.2, first test: when does an extra job pay?

The first test was a small calculation. For each dollar of added fees, the organization loses the network's half, fifty cents, plus an illustrative thirty cents of execution. So eighty cents must be earned back in extra reward. Everything below is that arithmetic under stated controls. Costs, ownership and prices are illustrative.

Where a node's fee share already meets its stake share, in a fixed or shrinking pool, the stake minimum works. Extra fees add no share, and every added job loses.

Where a node has room under its ceiling, extra jobs first pay, then stop paying as it reaches the ceiling. The sign change comes at added fees of roughly a fifth, about equal to, and nearly four times existing outside fees, for illustrative stakes of one, five and twenty percent.

So the stake minimum is a real defense, but only where it binds.

Then the surprises.

First, pool growth. In the first concept below its cap, added fees make the pool bigger. A node already at its ceiling gains reward amount without gaining share. Above about two point seven percent stake share, that pays, until the cap binds. After that, the marginal job loses.

Second, the appendix reading. With no stake ceiling, extra jobs pay where the main text says they lose. The break-evens exist, but only at ten to fifty times existing outside fees, which is a boundary on paper, not a practical defense.

Third, a corner of the shrinking-pool concept where even honest outside work loses money. The defenses can cost honest participants too.

One more thing came out. A zero median removes the whole round's reward, including the reward from honest fees. So a cut can reverse a positive return, and a false cut costs useful testing the same. The step turns that into a threshold, not a prediction: in one example, the self-funded job flips to a loss if the chance of a zero median exceeds about half of one percent. That says nothing about how likely a cut actually is. For that you need the evidence.

## M2.2, second test: can evidence separate them?

Before any outcome was looked at, the work wrote down the allegation, the acceptable error, and the effort limit, and committed them. The tolerance is strict: a cut on legitimate testing is unacceptable. Missing proof is a limitation, not a success.

The test compared public records with public records plus one disclosed source: the operator's release plan and the change that followed, assumed to arrive five rounds after the job.

What it found. Payment, execution and correctness are all established. Independent demand is contradicted, given known common control. Economic value and dishonesty stay unknown. Every verdict, under both standards and both readings, is the same: does not separate.

Disclosure clears the testing case. It proves nothing against the self-funded case. The evidence is one-sided.

The two readings behave differently. If a cut needs evidence of a violation, nothing is cut, but the allegation stays unresolved. If a cut may follow silence, then with public records only it can hit legitimate testing, which fails the tolerance. With timely, authentic, safe disclosure, testing is spared and the unexplained job may be cut. But that cut answers silence, not evidence. So the readings differ in who is exposed, not in what is known.

This test is synthetic. It can't measure detection accuracy or reviewer effort, and one invented pair doesn't show it is impossible in general.

## M2.3: what it all adds up to

M2.3 held each of the paper's defenses up against what the tests showed. The network fee works where costs exceed reward. The stake ceiling works at fixed stake. The cap works on pool growth. The delay works if it brings actionable evidence, which wasn't shown. The lock works if its cost outweighs the gain, which was held at zero. Scoring works if a violation can be established, which wasn't. So each defense has real reach and a condition where it stops.

It then compared plausible completions of the paper. Main-text reward keeps a stake defense. The appendix removes it. Fixed pools remove pool growth but leave share-taking. None of these choices defines the missing contribution.

Then it sorted design questions by what would resolve them. Of thirty-two, twenty-six involve a specification, sixteen better evidence, fourteen incentive analysis, eleven a policy choice, with overlap. Only six need a specification alone. So most of this is not just build work.

## The conclusions

Four conclusions came out, each held at inference.

One, conditional returns are established. Some added jobs gain and some lose, under stated controls. The arithmetic is supported. The significance isn't, because the contribution isn't defined.

Two, assumed timely disclosure clears the lookalike without establishing the violation.

Three, defenses have distinct operating conditions and bounded reach.

Four, M3 receives the gaps alongside the retained strengths.

## What goes to M3

Three items, each with its counterevidence.

A contribution gap. The paper doesn't say what benefit the reward requires beyond real, honest paid work. If it accepts the tested jobs as honest work, the concern narrows, whatever the profit.

A conditional reward concern. If a defined contribution excludes these jobs, positive regions survive plausible completions even with working ceilings. Deferred variants can move that either way. It's not a verdict of abuse.

An evidence and response gap. Where different treatment is required, neither standard establishes the violation, and explanation-based cuts expose honest undisclosed testing.

The strengths go with them: outside service earns a separate cash cut, the stake minimum and cap work in named regions, costs defeat self-funding in others, and the honest-work objective doesn't require independent customers. Scoring targets dishonesty, and shared tooling and mutual accountability are the intended supports.

A bounded follow-up is recommended before M3 leans on these: outside ownership, higher cost, later ratios. It can move signs either way. At the paper's year-four ratio, for instance, the break-even stake share rises from about three percent to about eleven, so the tested five percent flips to a loss.

## What the slice does not say

It doesn't say self-payment is profitable, or that it isn't. It doesn't say anyone does it. It doesn't say validators can or can't tell cases apart in general. It doesn't say the paper is flawed. It chooses no rule. It's one slice, and all three steps are still marked in progress.

## The story in one paragraph

We started with a worry. We found we couldn't test it until the paper's open rules were read two ways. Then the arithmetic said: the defenses work where they bind, and not elsewhere, and which region you are in depends on rules the paper hasn't chosen. Then the evidence test said: for the pair tested, the records don't separate the cases, and the readings of when to cut only change who bears the risk. Underneath both, one question stayed open, what the reward is meant to buy, and that is a policy decision, not a test result. That's what goes to M3.

## Reference list. Not for listening.

M2.1: step page, rule register I-01 to I-22, conclusion CN-22, finding FR-42.

M2.2: experiments EX-03 and EX-04; findings FR-46 to FR-52.

M2.3: conclusions CN-23 to CN-26; design questions VD-06, VD-09, VD-12, VD-14, VD-19; critical questions GT-01, GT-03.
