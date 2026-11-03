# Slice 2b: What the strategic test means

*Drafted research narrative. Owner research review remains pending. This guide is about meaning, not data points. For the role-by-role walk through, use the companion [three-story guide](m2-slice-02b-story-listening-guide.md). The spoken account ends before the reference list.*

About fifteen minutes. No identifiers are spoken. A few numbers appear where they carry the meaning.

## Where the story stood

Slice one started with a worry. If paid usage drives the inflation reward, an operator might pay itself for real jobs and collect more reward than the jobs cost. Proving the work happened does not settle it, because it did happen.

Slice one tested that worry in two parts. Does an extra self-funded job pay? And could a validator tell it apart from an operator's own legitimate testing? The answers were conditional. The paper's defenses worked where they bound, and stopped where they did not. Which region you were in depended on rules the paper had not chosen. The records did not separate the cases. And one question sat underneath everything: what is the reward actually meant to buy?

Slice two repeated this with the October paper. The October ceiling no longer grows with fees, which closed one door. But a fixed ceiling still leaves open who takes the share of it. The same two answers came back. Some real self-funded work paid and some lost. And the evidence still could not tell the cases apart.

Both slices shared a limit. Each used a small, illustrative setup, one operator in one network. A fair reader could say: you chose a convenient case. Slice 2b exists to answer that.

## Why 2b was asked

Slice 2b changes three things.

First, the actor stops probing and starts optimizing. Earlier, the question was whether one more job pays. Now the actor is motivated and chooses how much to spend, and the study finds where spending stops.

Second, the actor's position varies. There are three roles: the largest stake position, a middle one, and a lower one.

Third, the network varies. The conditions run from today's measured fees, where rewards dwarf fees, toward a network where fees are the dominant flow.

And a fourth question rides along. When the actor gains, who loses?

One premise needs saying plainly. The study declares that the actor's purpose is reward-seeking with no useful internal use. That is known to the modeler. Validators cannot see it. It is a premise for the scenario, not evidence anyone could obtain.

## How it was tested

The method is deliberately plain, and its plainness matters.

It builds a whole network of one hundred operators, using the measured snapshot, and keeps every operator in every denominator. Nobody is dropped to make a result tidy. It reuses the same accounting engine as slice two, so the results connect to what came before.

For each actor, it finds the best amount to spend by locating the exact turning points. It does not sample a grid and hope. Then at each spending level it recomputes every other operator's reward, so the losses are visible one by one.

The setups come in layers. A core set varies actor position, network shape, starting business and fee scale. Three further rows use the real measured network with its real cuts and no artificial help. Then come controls where the expected answer is zero. These matter most for trust. A test that can only find profit proves little. This one has setups built so that the right answer is that spending does not pay, and it must say so.

Finally, small one-at-a-time changes probe particular questions: cost, token value, ownership, capability labels, competition, funding, invoice price and timing. These are not multiplied together. Every selection was fixed before the results, and an independent verifier checks the arithmetic against hand-worked cases.

It is finite accounting, not a simulation of how people behave.

## What it found

The findings come as five ideas.

### One. The opportunity is a gap, and it belongs to position, not rank

The paper's main reward rule gives a node the smaller of its fee share and its stake share. So stake sets a ceiling. If your paid business is already at your stake share, more fees buy you nothing. If your business is below your stake share, there is a gap, and fees can fill it.

That gap is the whole opportunity. The three roles show it.

The largest role starts with a lot of unfilled room, so spending pays. The middle role already earns far more fees than its stake share. It has no room, and its best move is to spend nothing. The lower role has room, but a tiny amount, so it gains very little.

Same rule, three outcomes. The difference is where each sits relative to its own stake, not what rank it holds. The defense is real. It protects whoever already has business ahead of their stake.

There is an uncomfortable corollary. The gap is just stake share not yet matched by paid work. A legitimate newcomer has exactly that. The rule cannot tell a new honest operator from a self-funder. That echoes slice one: payment, execution and purpose are different claims.

### Two. The exposure is an exchange rate, and it is strongest now

The second idea explains why the gap pays at all. Every dollar an operator pays itself loses about eighty cents once the network's half and execution costs are counted. So the question is what a dollar of fees buys in reward.

Today the answer is a great deal. The scheduled reward allowance is worth around fifty-eight times the fees. When rewards dwarf fees, a small fee payment moves a large reward share.

As the network moves toward fees that are comparable to the allowance, that exchange rate worsens. At near parity, the best spending stops before the stake cap, because the next dollar no longer pays. In the fee-leaning checks, the best spending is zero.

So the exposure is not constant. It is largest while rewards dominate fees, and it fades as fees grow. That ties the worry to the paper's own bootstrapping story. But the scales are stress controls, not a forecast, and nothing here says when or whether the network gets there.

### Three. Most of the gain is new issuance, not taken from peers

When the actor gains, where does the reward come from?

Today about four fifths of the node allowance goes unminted, because fees and stake rarely line up. The actor's extra reward mostly unlocks some of that idle allowance. In every core setup where the actor gains, roughly three quarters to nine tenths of the actor's gross gain is newly released allowance. Only the remainder comes out of other operators.

That changes the shape of the harm. This is less a story of one operator robbing neighbors, and more a story of actual issuance rising while the ceiling stays fixed. A fixed ceiling is a limit, not a spend. Making fees independent of the ceiling stopped the ceiling growing. It did not stop real issuance from growing.

Peers still lose, and fee-limited pools lose noticeably, though modestly. Most of that falls on their external delegators, whose own customer payments are unchanged. Operators protected by their stake caps are untouched until the dilution reaches them.

And the actor does not keep most of what it gains. For the largest native role, only about four percent of the gross reward stays inside the organization, because cuts and delegation send the rest elsewhere. The full-retention setups that show large gains are upper bounds. They are not what the native participant would see.

So ownership becomes a hidden dial. How much of the stake behind an operator belongs to the operator's own organization largely decides whether this pays. The study can only proxy that from addresses. So can anyone else.

### Four. What stops the actor, and what does not

In the typical profile, the actor stops at its stake cap. Once its fee share reaches its stake share, extra spending adds cost and no reward. The cap is why one actor's harm is bounded by its own headroom.

Money is not the usual limit. In the one-round design, the limit on cash loss is a declared convention, not a measured resource. Giving the actor more funding mostly changes nothing for profit. It extends only how far the actor could go by spending purely to dilute others, which costs the actor money. The study separates greed from griefing. They are different threats with different limits.

Physical capacity never binds a profitable choice.

But one caution belongs here. For the largest native role, the stopping point is the budget convention, not the cap. A model choice is doing the defending there. The funding test shows that in some measured-scale cases more funding does enlarge the profitable move. So that part is soft.

A larger caveat sits underneath. Everything here holds the actor's stake fixed. If an actor could add stake to lift its own cap, the main limiter loosens. The study only computes how much stake that would take. It does not model the cost, availability or timing, and it hands that to a later study. The cap is only as strong as the cost of moving stake, and that cost is unknown.

The smaller tricks mostly fail to change the picture. Raising the invoice price cuts the part of the loss that goes to execution cost, but the network's charge remains. Labeling work as a unique capability changes no accounting. New outside demand shrinks the opportunity, because it changes the denominators. A competitor's price cut and rerouting can move it the other way. The direction depends on how the denominators shift. Those responses are imposed in the study, not observed.

And the rule text matters. Under the paper's appendix description, the stake ceiling disappears, and the middle and lower roles gain room. The paper has not chosen between the two readings. Whether the central defense exists at all depends on that choice.

### Five. Time buys a pause, and the evidence picture has not moved

Spending in steps instead of all at once helps a little, because added fee share has diminishing returns. That is a modest effect.

The claim delay matters more as an idea. Stretching the delay moves collection later. It does not fund a job, and it does not change the final value at full scores. A delay is a pause, not a price. It protects only if the pause produces evidence or scores that act on it. Elapsed time alone supplies neither.

This is the point where the evidence leg of the story stays where slice one left it. Slice 2b adds no new evidence. Its new spending volumes inherit no verdict. The earlier findings still stand within their narrow packet: disclosure can protect a legitimate, useful case, and the paired reward-only case stays unproved. Hidden purpose cannot be observed.

So the economics became sharper, and the evidence did not.

## How this fits the story from slice one

Slice one said the defenses work where they bind, and which region you are in depends on rules the paper has not chosen. Slice 2b draws the map of those regions. It shows how large the exposure is, who bears it, and what closes it.

Slice one's pivotal question was whether the seven-round delay produces evidence anyone can act on. Slice 2b adds that the delay has no economic force by itself. Everything rests on evidence, and evidence has not moved.

Slice one's deepest gap was that the paper does not say what the reward must buy beyond real, honest paid work. Slice 2b does not close that gap. It sharpens it. The activity is profitable in some regions, bounded in others, and not distinguishable from honest work by payment or execution. Under those conditions, the answer cannot come from more arithmetic. It is a policy definition.

Two things also got weaker, and they deserve to be said.

The worry is narrower than a simple reading suggests. The middle role is protected completely. The lower role gains almost nothing. The largest native role keeps a small share of its gross gain. Aligned networks, fee-leaning networks, and a much lower token value all close the opportunity. One fixed-stake actor's reach is bounded by its headroom. Most of the cost lands as extra issuance, not as theft from peers.

And nothing here shows that anyone does this.

So the honest summary is not that the system is broken. It is that the exposure is conditional, positional and bounded, and several of its dials are unobserved.

## Where the conclusions lead

The study names six dials that set the exposure: the ratio of reward to fees, the size of the gap between fee share and stake share, how much of the reward the organization actually retains, what the token is worth to whoever holds it, how easily stake can be moved, and which reading of the reward rule applies. Today, the first dial favors the opportunity. The other five are either unobserved or undecided.

Those unknowns sort into four kinds of work.

Specification. The reward formula and claim accounting need an authoritative reading, including the main-text versus appendix question, because that decides whether the stake defense exists.

Evidence. Whether anyone can obtain safe, timely, authentic material about purpose or control remains for the evidence studies. The unchanged finding is that today's records do not separate the cases.

Incentive analysis. Stake movement and acquisition, practical funding, competitor response, discovery, costs and token price all sit in preserved follow-up studies.

Policy. What the reward is meant to buy, beyond real honest work, remains a decision, not a result.

The next milestone receives these as open concerns, beside the strengths the evidence preserved: permissionless sales with separate fee receipts, a ceiling independent of fees, a stake cap that works within the main-text reading, a network charge and execution cost that make some self-payment lose money, delegation that leaks most gross reward away from the actor, and delayed claims that give investigation time to happen.

That list gives the next milestone a clear starting point. It does not choose a design.

## What this slice does not say

It does not say anyone does this. It does not say the paper is flawed, or that validators can or cannot tell cases apart in general. It does not predict when fees will approach the allowance. It does not say self-payment is profitable in practice, because ownership, token value and stake movement are unmeasured. It does not say the stated purpose could be observed. It adopts no parameter or rule. And the fixed schedules are not multi-round optima.

## The story in one paragraph

We began with a worry that paying yourself for real work could earn more reward than it costs. Slice one found the answer depended on conditions. Slice 2b mapped those conditions across positions and networks. The opportunity is a gap between fee share and stake share. It pays because today's rewards dwarf fees, it fades as fees grow, and it is bounded by the actor's own headroom and what it retains. Most of what it unlocks is new issuance, not stolen reward, and the defense it meets depends on how the paper reads its own rule and on whether stake can be moved. Meanwhile the evidence leg did not move, and a delay is only a pause. What remains is not more calculation. It is a rule to be specified and a question of what the reward is for, and that goes to the next milestone.

---

## Reference list. Not for listening.

- Governing study: [SLICE-02B v1.2](../m2/SLICE-02B.md) and [strategic self-funding implementation](../../experiments/m2/strategic-self-funding/README.md). Preceding slice: [SLICE-02](../m2/SLICE-02.md); historical slice one: [story guide](m2-slice-01-story-listening-guide.md).
- Results and reproduction: [EX-08 reader](../../experiments/m2/strategic-self-funding/README.md); run its unchanged reproduce command to regenerate `generated/full/`. Source figures for spoken claims:
  - Reward-to-fee ratio about 57.6 at the measured scale: `profiles.json`, `critical_ratio` and the README calibration.
  - About four fifths of node allowance unminted at baseline: `native-measured-1` `no_action_network` (never-minted 22,299.69 LPT of 27,531.2 LPT node allowance).
  - Released-allowance share of actor gain, about 0.74 to 0.90: `generated/full/accounting.md`, last column.
  - Retained about four percent of gross: CN-32 (92.73 of 2,310.48 LPT).
  - Native roles: `native-measured-1`, `-50`, `-90`.
  - Aligned, fee-leaning and low-valuation controls choose zero: README "Core results"; FR-62, FR-65.
- Workbench: M2.3 conclusions CN-31 to CN-34; findings FR-62 to FR-69; preceding conclusions CN-27 to CN-29, findings FR-54 to FR-61.
- Evidence scope: [EX-07](../../experiments/m2/evidence-capability-pricing/README.md) and `generated/full/evidence-scope.md`. No new packet or verdict.
- Paper: [October extraction](../litepaper-2.0.md), L81–84, L123–150, L198–213, L271–307, L388–416, L462–470, L646–670; [preserved PDF](../sources/litepaper-2026-10.pdf).
- Pending dependencies: E2, P1 and studies 3–8, including study 5/P1 HQ-01 for stake movement and acquisition and study 8 for price and liquidity. Technical checks do not confer owner research acceptance.
