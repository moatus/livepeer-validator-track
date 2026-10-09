#!/usr/bin/env python3
"""Independent numeric fixtures and full-population accounting identities."""
from decimal import Decimal as D
from build import account, inputs, job_delta, retention


def close(actual, expected):
    assert abs(actual-D(expected)) < D('1e-12'), (actual, expected)


pools = [dict(address='A',fee_usdc=D(10),stake_lpt=D(50),reward_cut=D('.2'),delegator_fee_share=D('.6'),own_fraction=D('.25')),
         dict(address='B',fee_usdc=D(90),stake_lpt=D(50),reward_cut=D('.2'),delegator_fee_share=D('.6'),own_fraction=D('.25'))]
a, s = account(pools, D(1000), D(2))
# Hand calculation: A MFS=.1, B=.5; 940*.6=564; other roles=60; burn=50/2.
for key, expected in {'mfs_sum':'.6','node_minted_lpt':'564','total_minted_lpt':'624',
                      'unused_node_unminted_lpt':'376','burned_lpt':'25'}.items():
    close(s[key],expected)
close(a[0]['operator_reward_lpt'],'37.6')  # (20% + 80%*25%)*94
close(a[0]['operator_fee_usdc'],'2.75')  # 5*(40%+60%*25%)
b, t = account(pools,D(1000),D(2),additions={'A':D(10)})
# A receives 940*(20/110)=170.909... LPT; B remains at 470.
close(b[0]['node_reward_lpt'],'170.90909090909090909')
close(t['total_minted_lpt'],'700.90909090909090909')
# Retained incremental reward 30.763636... LPT * $2 + $2.75 fee - $10 payment - $3 cost.
close(job_delta(a[0],b[0],D(10),D(1),D(3),D(2)),'51.27727272727272727')
close(job_delta(a[0],b[0],D(10),D(1),D(3),D(2),False),'61.27727272727272727')
# Full control cancels only own fee-side receipt; network half remains lost once.
assert retention(D('.2'),D('.6'),D(1)) == (D(1),D(1))
assert retention(D(0),D(1),D(0)) == (D(0),D(0))
# Invoice change never changes execution cost automatically.
close(job_delta(a[0],b[0],D(10),D(1),D(4),D(2)),'50.27727272727272727')
_, compressed=account(pools,D(1000),D(2),D('.5'))
close(compressed['total_minted_lpt'],'624')
close(compressed['burned_lpt'],'12.5')

snapshot, observed, pools=inputs()
assert len(pools)==100
rows, s=account(pools,observed['scheduled_mint_ceiling_lpt'],D(snapshot['prices']['lpt_usd_spot']))
crows,c=account(pools,observed['scheduled_mint_ceiling_lpt'],D(snapshot['prices']['lpt_usd_spot']),D('.5'))
for key in ('node_minted_lpt','total_minted_lpt','unused_node_unminted_lpt'):
    close(s[key],c[key])
close(c['burn_funding_usdc'],s['burn_funding_usdc']/2)
close(s['total_minted_lpt']+s['unused_node_unminted_lpt'],s['scheduled_ceiling_lpt'])
for r in rows:
    close(r['operator_reward_lpt']+r['other_addresses_reward_lpt'],r['node_reward_lpt'])
    close(r['operator_fee_usdc']+r['other_addresses_fee_usdc'],r['fee_usdc']/2)
assert sum(r['fee_usdc']>0 for r in rows)==27
print('PASS: two hand-computed states, operator/delegator transfers, independent costs, compression, and all-100-pool accounting.')
