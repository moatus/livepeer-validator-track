# Livepeer 2.0 Litepaper

By Doug Petkanics
September 2026

## Abstract

Livepeer was conceived a decade ago as the world's open video infrastructure. The world it operates in has changed significantly in that time, as media creation has moved from human-operated tools to AI agents that plan and execute entire creative workflows. The network's job has shifted from single-purpose transcoding to backing the full range of AI media compute capabilities that those agents need. This litepaper focuses on:

1. Clarifying why Livepeer's opportunity is to be the open infrastructure layer for agentic media creation, and why Livepeer is positioned to win in that category.
2. Laying out an opinionated, concrete protocol design for Livepeer 2.0. It focuses on the incentive mechanisms that determine how LPT captures value from network usage, and how rewards flow only to those doing real, honest work.

While a community driven process was used over the course of months to share numerous ideas and options to accomplish the above, this document aims to commit to one set of specific mechanisms and parameters that can work together to deliver on Livepeer's opportunity.

## The Agentic-First Opportunity

Media creation is being rebuilt around AI agents. Coding agents have already changed how software gets built, and the same shift is underway in video and media. AI models and increasingly capable workflows are unlocking impact across hundreds of use cases. While humans keep providing the taste, direction, and creative judgement, their agents execute on the underlying production work saving tremendous time and cost.

Producing a finished media asset today already means chaining together dozens of discrete AI-driven steps: scripting, scene generation, consistency across shots, voiceover, music, captioning, stitching, and more. There are often 40+ steps with human approval gates along the way to creating a production asset. 

Every major media company is racing to build its own proprietary version of this agentic pipeline. And while many startups offer closed products claiming to compete on the above, there is an opening for an open, community-powered alternative that wins on the same advantages that make open infrastructure win elsewhere: lower cost, wider capability coverage, digital payment rails, and no single point of control. 

**Livepeer's opportunity is to be the open video agent platform.** It combines a best-in-class open source media planning and execution agent, a community-contributed library of media skills and playbooks, and an open infrastructure network that competes to expose all of the world's known AI media compute capabilities at the lowest cost and highest availability. The three layers that enable this are:

- **The Livepeer Protocol** - a stake-based protocol aligning LPT's value with real network usage, responsible for incentives, coordination, payments, and security.
- **The Livepeer Network** — open infrastructure exposing every known media AI capability. In addition to GPU-hosted open models, this also means supporting API passthrough to third-party services and other media compute such as transcoding, muxing, captioning, and more.
- **The Livepeer Agent** — a video/media planning harness accessible via MCP through any popular agent (Claude, ChatGPT, Codex, and others), routing all of the resulting compute demand, and fees, through the Livepeer Network.

The Livepeer Agent is already working today, producing real output for media creators, and network usage can grow through the existing protocol while the tokeneconomics described below roll out. The rest of this document focuses on these economic and protocol incentive updates, and how they can work together to both enable and supercharge the network as the backing infrastructure needed to capture this opportunity.

## Design Principles

The below four principles were used to guide many of the decisions about which ideas and capabilities to include in this opinionated design. There are always tradeoffs and pros/cons in every approach, but these principles helped shape what was selected.

1. **Rewards should follow real work.** Fees generated for honest work, not just stake, should be the primary basis for earning inflationary LPT rewards during the network's bootstrapping phase.
2. **Every protocol role should do active work to add value to the network.** A role that exists purely for stake-based rent seeking should be modified into a role that actively adds value.
3. **Have a well intentioned incentive model, but leave room for governance to adjust.** No incentive model holds up perfectly over time as the network meets real world practicality. Include the parameters that let the community take control to maintain a fee/mint balance within the proper timeframes. 
4. **Simplicity is a feature.** Theoretically elegant mechanisms that node operators and delegators can't reason about are unhelpful in practice. Many of the choices below opt for a simpler path that the network can operate and explain, over complex mechanisms that can only be inferred through the code.

## The Unified Node Operator & Validator Model

Livepeer 2.0 needs two distinct work functions:

1. Node operators that actually do the work - run GPUs, call the APIs, execute the media compute agents request.
2. Validators that actually judge whether that work was done honestly, and determine whether a given node is eligible for its portion of inflationary LPT rewards.

This second function is new, as today's protocol has no honest-work judging mechanism at all. It pays rewards purely in proportion to stake, which worked reasonably well when transcoding was homogenous and quality-of-service verifiable. But it breaks down across hundreds of diverse, non-deterministic AI media job types where a node can self-deal work to itself and stake alone can't tell that apart from real usage. 

Livepeer 2.0 proposes addressing this via a new Validator set who's job is to score node honesty to determine rewards eligibility. However, while 2.0 introduces this new function, it is suggested that the top N nodes by stake who register for the validator role, inherit this role. **Node operators and validators are the same set of participants**, as they are uniquely suited to hold one another accountable to honest work, and already carry the weight of stake delegation to determine who has the most skin-in-the-game to ensure a continued, high performing network. (More on the scoring mechanisms and validator election mechanics below).

### Node operators: permissionless entry, rewards capped by stake. (MFS)

Any address can register as a node operator at any time, with **no fixed LPT bond required.** Nodes are listed in the onchain registry that the agent users use for discovery, and then advertise their capabilities, regions, and price for service selection. This eliminates the 100 node operator (Orchestrator) limit in the existing protocol, as there is no longer a cap.

Node operators continue to attract stake from delegators, and they earn LPT rewards under a **Min-Fee-Stake (MFS)** formula:

```
reward % = min(fee % of network total, stake % of network total)
```

A node that earns 10% of network fees in a round, but holds only 2% of total stake, earns rewards capped at 2%. A node earning 5% of fees with 5% of stake earns its full 5%. Fees themselves are never capped. A node can always earn more by doing more real work, but the *inflationary LPT reward* attached to that work is capped by how much stake (self-staked or delegated) is actually behind the node.

The MFS formula enables anyone to enter the network to compete for fees, but it mitigates the impacts of self-dealing fees to oneself for low stake nodes, as the rewards that they are entitled to are capped by their lack of stake. High stake nodes who are underperforming in terms of fee generation, would see their rewards capped, and stake would likely be better served moving towards nodes that are earning higher fees. The role of delegation becomes far more active, and far more rewarding for those who are providing security, through stake, to the network.

### Delegation secures nodes and elects who validates

Delegators stake directly toward node operators, using the same bonding, unbonding, and reward/fee-cut mechanics that delegation already uses today. However, active delegators have a far larger opportunity to route security and rewards towards the nodes that need to be have high economic bonds against the large amount of work they're performing. Therefore, active delegators can earn an outsized portion of rewards versus the passive delegators. 

The stake placed on a node determines its reward ceiling. Sticking with the example of a node that does 10% of the work on the network, but only has 2% of the stake: it's rewards remain capped at 2% of a round's rewards, unless it can attract more stake. There is a tremendous opportunity for delegators to move stake towards this node, to 5x its daily rewards. This should be reflected in the reward cut and fee share, leading to far greater return for the delegator than sitting on a node that is capped by its lack of fee earning potential (which is far harder to make up because it requires real hardware and operational investment and performance). 

This is a significant improvement over the passive yield aggregation of the staking role, which was not adding as much value relative to the amount of inflationary LPT issuance being paid out. Now active delegators who are placing stake at risk on the high performing nodes are rewarded far more than those sitting idle in a set-it-and-forget-it manner on non-contributing ghost nodes. 

Furthermore, the top N nodes by stake are eligible to act as the validators on the network. **Stake plays a critical role in securing the validator set against takeover or attack.** The more expensive it is to take over the majority of this set, the harder it is to attack the integrity of the work and rewards on the Livepeer network. 

Stake continues to carry weight in governance and treasury votes as well, securing the future evolution and public goods funding on the network.

Delegators are choosing, with real capital, both who does productive work on the network *and*, for the highest-stake nodes, who is trusted to judge that work honestly. That is a more active and more consequential role than delegation plays in the current protocol, where stake elects an orchestrator but has no bearing on judging honesty at all.

### The top nodes by stake can register as validators

Among node operators, the **top N by total stake** (self-staked plus delegated) are eligible to serve as validators, but they're not forced to do so. A node becomes an active validator by choosing to register for it. The proposed starting value for N is **33**. There are two reasons that a node might volunteer as a validator.

- **Mutual accountability.** Validators hold each other to honest account. If another validator, or a coordinated group, tries to unfairly zero out your node's rewards, being a validator yourself gives you standing to push back.  Participating is how a node protects its own interests in a network where reward eligibility is inherently subjective.
- **Direct compensation.** Active validators earn a `ValidatorRewardShare` of **1% of the post-BME LPT mint** for the period, split among all currently-active validators. This is intentionally small. The overwhelming majority of newly-minted LPT should still flow to node operators for real work, rather than to the validation function. But it's enough to make validating a genuinely incentivized job rather than an unpaid civic duty. Opting out has a real cost, even if small. 

Each active validator can assign every node a `RewardMultiplier` score from 0.0 to 1.0. The **median score** across active validators determines what fraction of a node's MFS-eligible reward it actually receives. 1.0 means full eligible rewards, 0.0 means none, and everything in between scales proportionally. Validators should not penalize nodes for legitimate performance limitations (regional coverage, model availability). Those already show up naturally as lower fees and lower rewards. The score exists to catch dishonest behavior such as self-dealing, fee fabrication, or serving incorrect results. It does not exist to grade quality of service.

The hard work behind that judgment such as building testing frameworks, network monitoring, dashboards, and anomaly detection, should be funded as a public good. Dedicating small groups of applied research engineers to this task will be far more efficient than duplicating the work across every active validator independently. Validators vote based on that published evidence or other surfaced criteria. 

Lastly, a heavily debated topic during the feedback period was whether this decentralized mechanism for validation was necessary, relative to just granting a centralized party the ability to set the `RewardMultiplier` for each node. I lean heavily towards the need for a decentralized, unstoppable, and trustless mechanism that doesn't rely on a single party - however I suggest that the smart contract address that governs the implementation for the `RewardMultiplier` scores be a governance swappable parameter, rather than a fixed hardcoded implementation. This would allow the community to take action and decide to grant this authority to an SPE or individual entity or alternate implementation in the future, should that be desired.

### 21 Round unbonding 

The unbonding period for all stake behind a node operator, whether it is self stake or delegated, is suggested to increase to 21 rounds. This is considered a compromise: 

* The current 7 round unbonding period is too short to meaningfully deter a node from misbehaving, as having capital locked with no rewards for 7 days is likely worth it to attempt rewards extraction.
* The 90 days suggested in the initial proposal still feels ok for node operators themselves. But since most of their stake will be delegated, and operational security considerations even suggest delegating stake to oneself from another wallet, the unbonding period also needs to apply to delegators. And the feedback was that a 90 day capital risk for delegators felt too long.

21 rounds provides a real capital lockup, such that malicious nodes can't just quickly unbond and register new malicious nodes under different identities, but it stops short of imposing multi-month illiquidity on all staked capital.

Delegators now have a real incentive to evaluate who they're backing, rather than treating delegation as risk-free yield. If their node misbehaves and has their rewards cut to zero, the delegators capital is also unable to be accessed or earn any rewards for the 21 day period.

One side effect of this is that `transferBond` needs to be eliminated, or subjected to a 21 day transfer period before being applied to the new node. Otherwise anyone could attack the network, and immediately `transferBond` to a new node address, knowing that the attacking node getting their rewards reduced would not affect their transferred stake.

Unfortunately, this is not a fully settled tradeoff. Part of the goal of this design is an active, liquid delegation market with delegators continuously moving their stake toward the highest performing understaked nodes. Subjecting `transferBond` to the 21-day wait period means delegation transfers will be slower and more deliberate. This will be revisited in the open questions to see if there are any solutions to this tension.

### Rewards delay of 7 rounds, retroactively scored

Rewards for a given round are not immediately claimable. They become claimable after a 7 round `RewardDelayPeriod`, and the score applied to determine the final payout is whatever the validator set's median `RewardMultiplier` score is for that node at the time of claiming. This directly addresses the most concrete attack scenario raised across the feedback: a node spikes its apparent fee earnings in a single round, hoping to claim a large reward before any validators notice and react. With a 7-round retroactive window, validators have real time to observe the anomaly, investigate, and drive the median score to zero before that reward ever becomes claimable. This prevents the "strike fast, cash out before anyone reacts" version of the attack without relying on validators to catch it instantly.

### Payments in USDC

Network payments and pricing move from ETH to **USDC**. Node operators price their services in USD and are paid in USDC, eliminating the confusion of the ETH-denominated fee flow, and removing price volatility from the calculation. It also sets up the fee side of the BME mechanism on a stable, predictable base.

## Burn Mint Equilibrium & Emissions

## The node/network split

Of the USDC fees a node earns, the starting value for the `BMENodeCut` is proposed as 50%, and the starting value for the `BMENetworkFee` is proposed as 50%. This means that half the fees go direct to the node to incentivize more work even when lacking stake, and 50% go into the BME to purchase LPT from the market and burn, in service of supply reduction.

It is suggested that the LPT purchased in this mechanism is **burned in full** with a `BMEBurnPercentage` of `100%`. Inflationary LPT rewards to node operators are funded by a separate, independently governed mint, and not by recycling bought-back LPT. The two supply levers - the burn driven by real usage, and the mint driven by the emissions schedule below - can be clean and separately reasoned about. The objective is that on a predictable schedule, the burn contribution reaches equilibrium with the supply inflation via emissions. While this can occur **faster** if fee growth accelerates rapidly, there is a long term timeline in which it is forced by the dynamics of the emissions schedule. This means that supply will be capped and predictable over time for the market's understanding of the token economics and value capture. 

![BME Value Flow](mechanism-flow-diagram.svg)

As for execution on the LPT buy backs, further research work is necessary to apply the best-in class DeFi designs for executing low-slippage and non-manipulatable onchain purchases from DEX liquidity pools that are controlled via governance. Example parameters for executing TWAP based purchases at specified intervals are provided below, but the design of this mechanism is left outside of this paper.


### Emissions schedule

**THIS SECTION REMAINS OPEN AND IS AN IDEA DRAFT. FINISH LATER POST SIMULATION WORK, AND RESEARCH AND DISCUSSION.**

The ideas for the emissions model, each spec'd out to varying degrees include:

1. The emissions as a % of fees start at 3200% per year, the current baseline, and half every two years, reaching an equilibrium with the BME around year 10/11. 
2. Same as above, but cap the total mint such that fees + mint don't extend beyond the current value of $35M. New mint = starting mint - any fee increase. This means net mint is never beyond that amount, and with 55% CAGR reaches equilibrium around year 7.
3. Leave current participation based inflation adjustment, except introduce the floor/ceiling caps at 2% annually and 10% annually. Continue declining to this level, and then BME leads to supply reduction (or equilibrium if adjustment knobs are tuned) when network fees == 4-20% of market cap (at 50% `BMENetworkFee`)

Below I include the AI-enabled draft of concept #1 above for reference and analysis.

#### AI Enabled Draft of Concept 1 -  declining share of fees, reaching equilibrium on its own — with a $50M/year cap as a guardrail

LPT emissions today run at roughly **30x annual network fee revenue** — a real, current ratio, not an illustrative one (Q1 2026 network fees were ~$257K for the quarter against ~$7.4M in quarterly staking rewards). That ratio needs to come down predictably as the network matures. The schedule: **emissions, as a percentage of network fees, halve every 2 years**, starting from today's ~3200% (32x) ratio.

Under the recommended growth assumption — a measured **~35% annual network-fee-growth rate** — the network never actually needs the hard cap to reach a healthy outcome. The declining ratio schedule gets there on its own:

| Year | Fees | Emissions target (% of fees) | LPT mint | LPT burned | Net mint (mint − burn) |
|---|---|---|---|---|---|
| 0 (today) | $1.1M | 3200% | $35M | $0.6M | $35M |
| 4 | $3.6M | 800% | $29M | $1.8M | $27M |
| 8 | $12.1M | 200% | $24M | $6.1M | $18M |
| 10 | $22.1M | 100% | $22M | $11.1M | $11M |
| 12 | $40.3M | 50% | $20M | $20M | **$0M (burn = mint, exactly)** |

Nominal emissions actually decline slightly over this period even as the network grows, because the ratio falls faster than fees rise under this more measured path. By year 12, burn and mint meet exactly — a structural property of the schedule itself (the ratio hits 50%, matching `BMENetworkFee`'s 50% burn rate), not a coincidence specific to this growth rate. This is the "equilibrium" the mechanism is named for, reached without the cap ever engaging.

**So what is the $50M cap actually for, if the recommended path never reaches it?** Two scenarios where it matters, and both are worth planning for even though neither is the base case:

- **Faster organic growth than expected.** If real network fee growth substantially outpaces the ~35% baseline — say, closer to **55% annually** — the ratio-times-fees target crosses $50M by around **year 4**, roughly eight years earlier than the recommended path's year-12 convergence:

  | Year | Fees | Emissions target (% of fees) | LPT mint, capped | LPT burned | Net mint (mint − burn) |
  |---|---|---|---|---|---|
  | 4 | $6.4M | 800% | **$50M (cap engages)** | $3.2M | $47M |
  | 8 | $36.7M | 200% | $50M | $18.3M | $32M |
  | 10 | $88.1M | 100% | $50M | $44.0M | $6M |
  | 12 | $211.5M | 50% | $50M | $105.8M | **-$56M (net deflationary)** |

  Mint holds flat at $50M from year 4 onward, and once fees pass $100M/year (twice the cap, since `BMENetworkFee` burns 50% of fees), burn overtakes the capped mint and the network turns net deflationary — around year 10 in this scenario. Full modeling of this stress-test path is in `emissions-schedule.md`.
- **A sudden spike in reported fees, from anywhere — including attempted self-dealing.** The cap doesn't distinguish between real accelerated growth and a burst of fabricated fee volume; it simply holds total mint at $50M/year regardless of how high the ratio-implied target goes in a given period. A node, or a coordinated set of nodes, attempting to inflate its apparent fee share doesn't unlock proportionally more network-wide minting once the cap is already binding — the same mechanism that guards against runaway organic growth also guards against this attack pattern, and would curb it starting as early as year 4 under the same math shown above.

This is a ceiling, not a promise: if fee growth tracks closer to the recommended 35% path, the declining ratio remains the binding constraint indefinitely and the cap may simply never engage — which is the intended, healthier outcome, not a failure of the design.

**Why a hard cap matters for self-dealing, specifically:** MFS already bounds how much of the reward pool any single node can claim, by capping it to that node's real stake share — faking fee volume beyond your true stake share earns nothing. The emissions cap adds a second, independent brake, but it's important to be precise about what it does and doesn't fix. It does *not* stop a node from trying to grab a larger *share* of an already-fixed reward pool by inflating its apparent fee percentage relative to other nodes in a given round — that's what validator scoring and the 7-round rewards delay are for. What the cap *does* remove is the incentive to inflate *network-wide* apparent fee volume in order to grow the total pool available in the first place, once that pool is already at its ceiling: past the cap, additional fee volume — real or fabricated — funds more BME burn without unlocking any additional LPT reward for anyone. It closes off one specific failure mode (grow the pie to grab a bigger absolute number) without claiming to solve the other (grab a bigger slice of a fixed pie), which real scoring and the delay mechanism remain responsible for.


## Not Included In This Design

There were a couple of concepts in the original design or that were debated heavily amongst the community that are not included in this version:

1. **No minimum self-stake requirement for node operators.** Having skin in the game for node operators may remain an important preference amongst gateway nodes that route work, however that can be left outside of the protocol. A stake requirement raises the barrier for new node operators joining the network, and requiring self stake on hot wallets running on nodes presents security risk. 
2. **No separate migration/election event.** With delegated staking towards nodes still on the table, and the top N nodes inheriting the validator slots, not separate migration period or election is necessary. This is good news as there's no need to disrupt network continuity to roll out these updates.
3. **No reward-eligibility ramp up period for node operators.** It was discussed as to whether new nodes would need to earn fees consistently over time to be rewards eligible, though this idea was discarded in favor of the 7 round reward delay to prevent bad actors from jumping in and stealing rewards through inflated fees without notice.

## In Summary

Livepeer 2.0 introduces some key improvements to the Livepeer protocol so that it can succeed at accruing value to LPT as network usage rises. Any address can register as a node to do work and earn, a combination of real fees plus stake determine what they earn, BME ties LPT's value directly to rising network usage through USDC-denominated fees, a predictable emissions schedule replaces an open-ended inflation curve, and attack vectors are closed via a 7-day reward delay and validation function determined by delegated stake. 

This document presents a cohesive recommendation, but none of this is final until some of the open questions below are worked through in simulation, testing, and continued feedback from our active community. In the meantime, this is a start that we can build and simulate against.

## Open Questions
The following questions remain unresolved and need proper engineering designs, simulation and modeling, or continued consensus building.

- **Securing PM payment mechanism with unlimited node count.**

- **Price oracle dependency for emissions function.** How can we secure an onchain LPT price oracle that isn't subject to manipulation?

- **Minimum validator participation.** Should validator compensation be dependent upon participation, or is stake movement alone enough to incentivize/punish non-performing validators?

- **transferBond vs the active delegation market.** If delegators are subject to 21-round unbonding to move stake, this inhibits the active delegation market.

- **The validator constitution.** The idea of a validator constitution is referenced repeatedly, but this needs to be written and reach consensus for ratification. It defines expected validator behavior. 


## Appendix

### Livepeer 2.0 Parameters

#### Accounting Identities

```
BMENodeCut + BMENetworkFee = 100% of gross fees
BMEBurnPercentage + BMETreasuryCut + BMEValidatorCut = 100% of purchased LPT
NodeEmissionShare + ValidatorEmissionShare + TreasuryEmissionShare = 100% of round emissions
```

All values below are considered as initial launch values.

| Parameter | Initial Value | Governance-adjustable? | Notes |
|---|---|---|---|
| Node operator cap (max # of nodes) | None | N/A | Any address may register as a node. No incentive to split stake across multiple identities since there's no per-node bond or cap. |
| Reward formula | `reward % = min(fee % of network, stake % of network)` | Formula itself: no. Underlying stake/fee measurement windows: yes | "MFS" — Min-Fee-Stake. |
| Validator set definition | Top N (starting 33) node operators by total stake (self + delegated) **who opt in to register as validators** | Yes — `ValidatorSetSize` | Eligibility is by stake rank. Participation is voluntary. A top-ranked node can decline. The next-highest-staked registered node fills the slot. |
| `ValidationScoreContract` | Decentralized median-of-scores (default) | Yes - swappable contract address | Governance can point this at an alternate mechanism (e.g., a centralized SPE/router) without a protocol migration. |
| `UnbondingPeriod` (self + delegated stake, incl. `transferBond`) | 21 rounds  | Yes | Applies uniformly to all stake behind a node operator, not just self-stake. And to bond transfers between nodes, to prevent a misbehaving node from relocating its stake ahead of a reward-ratio penalty. |
| `RewardsDelayPeriod` | 7 rounds | Yes | Rewards for round *n* become claimable at round *n+7*, using the median score current at time of claim. |
| Payment currency | USDC | N/A (could be revisited via governance/contract upgrade) | Replaces ETH-denominated fees. |
| `BMENodeCut` | 50% | Yes | Share of USDC fees paid directly to the node operator. |
| `BMENetworkFee` | 50% | Yes | Share of USDC fees diverted to BME (buys and burns LPT). |
| `BMEBurnPercentage` | 100% | Yes | Of the `BMENetworkFee` portion, share that is burned. Rewards are funded via a separate mint. |
| `BMETreasuryCut` | 0% | Yes | Percentage of the fee-side reward pool (post-burn) allocated to the DAO treasury. At BMEBurnPercentage = 100% this is always zero regardless of this parameter's value, since there is no post-burn pool. Becomes active if BMEBurnPercentage is reduced below 100% in future governance. |
| `BMEValidatorCut` | 0% | Yes | Percentage of the fee-side reward pool (post-burn) allocated to validators and their delegators. Same dependency on BMEBurnPercentage as BMETreasuryCut — inactive at 100% burn. Validators are compensated exclusively through emissions at starting values. |
| `NodeEmissionShare` | 94% | Yes | Percentage of round LPT emissions allocated to node operators. Distributed proportionally to each node's share of work completed in the round, weighted by that node's aggregate validator multiplier score. This is the primary incentive for node operators to perform quality work at starting values. |
| `ValidatorEmissionShare` | 1% | Yes | Percentage of round LPT emissions allocated to the validator set and their delegators. Distributed proportionally to each validator's delegated stake. Validators may set individual reward cuts that determine how much they retain vs. pass to delegators. This is the primary compensation for the validator scoring role. | 
| `TreasuryEmissionShare` | 5% | Yes | Percentage of round LPT emissions allocated to the DAO treasury. Accumulates for governance-approved expenditure on grants, development, and ecosystem growth. Governed by existing Livepeer treasury parameters. |
| Emissions-to-fees ratio schedule | 3200% (year 0), halving every 2 years | Yes | 1600% (yr 2), 800% (yr 4), 400% (yr 6), 200% (yr 8), 100% (yr 10), 50% (yr 12), continuing to halve. |
| Annual emissions hard cap | $50M/year (USD-equivalent) | Yes | Chosen relative to a ~$1M/week |

### DEX Execution Parameters

*More research to be done on the DEX execution for buybacks.**

| Parameter | Definition | Starting Value |
|---|---|---|
| `BMELiquidityPool` | On-chain address of the primary liquidity pool used to execute LPT purchases. Should be the deepest available LPT pool to minimize slippage and manipulation exposure. Governable to allow migration if a deeper pool emerges. | TBD |
| `BMETWAPInterval` | The look back window (in seconds) over which the time-weighted average price of LPT is calculated prior to executing a buy. Longer intervals are more resistant to price manipulation but introduce lag relative to spot price. Standard range across DeFi protocols is 30 minutes to 2 hours. | 3600s |
| `BMEBuyFrequency` | How often accumulated BMENetworkFee proceeds are deployed to purchase LPT. Batching purchases reduces gas overhead and makes buy timing less predictable to front-runners. Expressed in epochs. One purchase per epoch is the recommended starting cadence. | 1 round |
| `BMEMaxSlippage` | Maximum acceptable deviation between the TWAP reference price and the actual execution price, expressed as a percentage. If slippage would exceed this threshold the transaction reverts and accumulated fees roll over to the next buy interval. Prevents sandwich attacks from extracting value during large buys. | 1% |

