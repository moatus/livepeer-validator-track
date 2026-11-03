# Exploratory modeling for M3

[Profitability-window study](profitability-window/README.md) extends accepted M2 accounting to all pools and tests selected price/fee and parameter sensitivities. These calculations are exploratory inputs to M3, distinct from the accepted M2 artifacts.

Keep the accepted M2 inputs and rules unchanged. New models should answer a bounded question relevant to [M3’s workbench evaluation](../../validator-track-workbench.html#M3.2), preserve counterexamples, and separate assumptions from observations.

These models address **G01: reward objective and self-funded work**, carried from [M3.1 §1](../../validator-track-workbench.html#M3.1) into [M3.2 §6](../../validator-track-workbench.html#M3.2). They test economic conditions, not model identity or delivery. The complementary verification implementations live under [poc/](../../poc/README.md); the workbench brings their implications together.
