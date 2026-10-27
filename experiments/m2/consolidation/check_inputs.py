#!/usr/bin/env python3
"""Validate frozen prospective sources/finite boundaries before any calculation."""
import hashlib,json,re,importlib.util
from decimal import Decimal as D, getcontext
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def require(ok,message):
    if not ok: raise ValueError(message)
def check():
    m=json.loads((HERE/'input-manifest.json').read_text()); c=json.loads((HERE/'cases.json').read_text())
    paths=[x['path'] for x in m['files']]
    require(len(paths)==len(set(paths)), 'duplicate source')
    for item in m['files']:
        p=(ROOT/item['path']).resolve()
        require(p.is_relative_to(ROOT),'source escapes repository')
        require(p.stat().st_size==item['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],'changed source '+item['path'])
    require(c['no_outcomes'] is True,'prospective boundary')
    require(c['cases']==['SC-27','SC-28'] and c['lanes']==['no-movement','fresh','unbond-rebond','delayed-transfer'],'finite lanes')
    require(c['observation_rounds']==list(range(46)) and c['earning_rounds']==list(range(24)), 'finite timeline')
    require(len(c['cases'])*len(c['lanes'])*len(c['observation_rounds'])==c['row_count']==368,'observation count')
    require(len(c['cases'])*len(c['lanes'])*len(c['earning_rounds'])==c['earning_cohort_count']==192,'earning count')
    require(c['withdrawal_round']-c['exit_request_round']==21,'exit wait')
    require(c['existing_eligible_round']==23 and c['fresh_eligible_round']==2 and c['claim_delay_rounds']==7,'frozen clocks')
    require(c['target_source_rank']==50 and c['donor_source_rank']==1,'source selection')
    require(c['study7_cases']==['SC-32','SC-33','SC-34'] and c['studies']==[5,6,7,8],'study scope')
    require(c['source_readings']['transfer_requirement_locators']=='SRC-LP20-OCT L246-258, L592-597; unsettled tradeoff L525','transfer requirement locators')
    require(c['receipt_boundary']['target_validator_registration'] is False,'voluntary target registration boundary')
    require(c['receipt_boundary']['donor_validator_registration']=='unknown; eligibility is not opt-in','unknown donor registration')
    require(c['persistence_boundary']['exit_basis']=='modeler-fixed at 24, not observed decline or delegator foresight','exit information boundary')
    require('m=0 gives zero cohort LPT' in c['score_boundary']['identity'],'zero-median boundary')
    text=(HERE/'assumptions.md').read_text()
    for phrase in ['not protocol policy','source-pool','not latency','not confiscated','elimination-or-delay requirement','opportunity','denominator','appendix','M4.1','M4.3','not observed access']:
        require(phrase.lower() in text.lower(),'missing boundary '+phrase)
    for f in HERE.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',f.read_text()):
            if '://' not in target and not target.startswith('#'):
                require((f.parent/target.split('#')[0]).exists(),'missing document '+target)
    # Validate actual frozen calibration and donor capacity, without any reward call.
    getcontext().prec=60
    engine_path=ROOT/'experiments/m2/capability-pricing/build.py'
    spec=importlib.util.spec_from_file_location('close_ex06_inputs',engine_path)
    engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
    config,grid,observed,pools,bridge=engine.load_inputs()
    ranked=sorted(pools,key=lambda p:(-p['stake'],p['address']))
    S=sum((p['stake'] for p in pools),D(0)); target=ranked[49]
    donor_after=ranked[0]['stake']*(D('.98')*S)/(S-target['stake'])
    require(len(pools)==100 and S>0 and observed['fees_usd_indexed']>0,'calibration population/denominators')
    require(donor_after*(1-ranked[0]['w'])>D('.08')*S,'frozen donor lacks outside-delegated transferable principal')
    print('CALIBRATION INPUTS:',json.dumps({'round':observed['round_id'],'stake_lpt':str(S),'fees_usdc_replay':str(observed['fees_usd_indexed']),'donor_source_rank':1,'target_source_rank':50,'donor_sufficiency':'strictly exceeds .08 S; no rewards calculated'}))
    print(f'PASS: {len(paths)} source/contract pins; 368 frozen observation rows, 192 earning cohorts; four study boundaries; input check computes no outcomes')
if __name__=='__main__': check()
