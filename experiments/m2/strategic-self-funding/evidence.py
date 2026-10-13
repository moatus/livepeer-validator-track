"""Map economic purposes to the existing EX-07 inventory; no new verdicts."""
import json
import hashlib

import fixtures as f
from adapter import write_json

BASE='experiments/m2/evidence-capability-pricing/'
ROWS=[
    dict(id='existing-niche',scope='existing packeted S04/S05/S06/S06-N only',
         modeler_purpose='outside service/useful internal work/reward-only work; knowing representation only explicit -N overlay',
         public_observations='P-LIST quote/job linkage; P-PAY accurate settlement; P-CTRL accurate control/funding disclosure; P-OBS competent service checks; P-REP representation only',
         disclosed_observations='D-N authentic linked production/test plan and output use for S05 only',
         rule_definition='VD-19/I-20–21; knowing falsity/purpose or circular reward-only purpose is a separate claim',
         procedural_response='existing reading a needs evidence; reading b non-explanation consequences are not proof or a median response',
         disclosure_premise='accurate control/funding at n+1; authenticated competent checks at n+2; authentic adequate safe linked S05 bundle at n+5; close n+7',
         verdict_scope='existing EX-07 does not separate, both standards/levels/readings; no extension',
         source_paths=[BASE+'packets/niche.md',BASE+'verdicts.csv',BASE+'config.json'],inventory_records=['P-LIST','P-PAY','P-CTRL','P-OBS','P-REP','D-N']),
    dict(id='existing-discount',scope='existing packeted S02/S07/S08/S08-N only',
         modeler_purpose='ordinary routing/useful internal tests/reward-only work; knowing representation only explicit -N overlay',
         public_observations='P-LIST quotes; P-PAY accurate payments; P-CTRL accurately disclosed control/funding; P-OBS service observations; P-REP representation',
         disclosed_observations='D-D authentic selection/routing log linked to S07 internal test plan only',
         rule_definition='VD-19/I-20–21; price/control/profit alone does not establish selected violation',
         procedural_response='existing keyed a/b consequences distinct from evidence separation; no automatic cut or warranted median',
         disclosure_premise='accurate control/funding at n+1; authenticated competent checks at n+2; authentic adequate safe linked S07 bundle at n+5; close n+7',
         verdict_scope='existing EX-07 does not separate, both standards/levels/readings; no extension',
         source_paths=[BASE+'packets/discount.md',BASE+'verdicts.csv',BASE+'config.json'],inventory_records=['P-LIST','P-PAY','P-CTRL','P-OBS','P-REP','D-D']),
    dict(id='new-strategic-volume',scope='new core/one-factor/funding/response/timeline generic full-price volumes and niche relabelled volumes',
         modeler_purpose='reward-only real work with no credited use, stipulated dishonest for this model; known only to modeler',
         public_observations='existing payment/quote/execution record kinds could describe jobs if available; no new observed packet or purpose evidence',
         disclosed_observations='none supplied or guaranteed',rule_definition='VD-19 remains unresolved eligibility policy; owner/modeler ground truth is not evidence',
         procedural_response='not examined; new volumes inherit no keyed consequence or median behavior',
         disclosure_premise='not examined: no new accurate-control or useful-bundle packet at these volumes',
         verdict_scope='not examined',source_paths=[BASE+'README.md',BASE+'config.json'],inventory_records=['P-LIST','P-PAY','P-OBS']),
    dict(id='new-useful-pairs',scope='new matched useful internal accounting references',
         modeler_purpose='declared productive/internal use1 USDC-equivalent/job; identical fees/costs/rewards to strategic pair',
         public_observations='payments/execution alone do not establish internal use or subsidy value',
         disclosed_observations='a linked authentic safe adequate useful bundle is a dependency, not supplied for these new references',
         rule_definition='VD-19 contribution remains distinct from execution and declared model utility',
         procedural_response='not examined; existing useful clearance does not establish a new paired violation',
         disclosure_premise='not examined: original D-N/D-D premise is limited to original S05/S07',
         verdict_scope='not examined',source_paths=[BASE+'packets/niche.md',BASE+'packets/discount.md'],inventory_records=['P-PAY','P-OBS','D-N','D-D']),
    dict(id='undisclosed-control',scope='undisclosed common control/beneficial ownership for any new choice',
         modeler_purpose='control assumed inside accounting boundary only',public_observations='no ownership-discovery source or guaranteed disclosure supplied',
         disclosed_observations='none supplied',rule_definition='control alone establishes neither reward-only purpose nor a violation',
         procedural_response='not examined; E2/control-evidence dependency',
         disclosure_premise='not examined: cannot inherit original truthful P-CTRL n+1 premise',
         verdict_scope='not examined',source_paths=[BASE+'config.json',BASE+'README.md'],inventory_records=['P-CTRL']),
    dict(id='invoice10',scope='four controlled invoice-price rows at stipulated price10 versus base1',
         modeler_purpose='reward-only model purpose, with fewer executed jobs for the same gross fee',
         public_observations='price10 is visible if the linked quote is in existing P-LIST; P-PAY shows paid amounts and P-OBS execution under their premises; base1 is illustrative, not an empirical market benchmark',
         disclosed_observations='no new control/use/market-price source supplied',
         rule_definition='price/payment facts do not define dishonesty, an above-market policy or economic value',
         procedural_response='not examined; no price anomaly detector, new verdict or warranted score',
         disclosure_premise='not examined: map original public P-LIST/P-PAY/P-OBS inventory only, no new packet',
         verdict_scope='not examined',source_paths=[BASE+'packets/niche.md',BASE+'config.json'],inventory_records=['P-LIST','P-PAY','P-OBS']),
    dict(id='median0-algebra',scope='independent useful-work arithmetic fixture only',modeler_purpose='legitimate useful-work boundary with all executed-job costs retained',
         public_observations='none; no adverse score observed or warranted',disclosed_observations='none; no new evidence outcome',
         rule_definition='October median affects entire earning-round entitlement at claim, not an uptime/quality grade',
         procedural_response='algebra only; no individual-score-to-median response or defense conclusion',
         disclosure_premise='not examined',verdict_scope='algebra only; no verdict',
         source_paths=['docs/litepaper-2.0.md','experiments/m2/strategic-self-funding/verify.py'],inventory_records=[]),
]


def build():
    config=json.loads((f.ROOT/(BASE+'config.json')).read_text())
    records=set(config['evidence_records'])
    for row in ROWS:
        f.require(set(row['inventory_records'])<=records,'No new evidence record kind')
        f.require(all((f.ROOT/path).is_file() for path in row['source_paths']),'Evidence map source exists')
    dest=f.HERE/'generated/full'
    write_json(dest/'evidence-scope.json',dict(rows=ROWS,source_config_sha256=hashlib.sha256((f.ROOT/(BASE+'config.json')).read_bytes()).hexdigest(),
        limits='Scope mapping only; original synthetic verdicts restricted to original packets/disclosure premises. No new evidence outcome, source, arrival, packet, detector or warranted median. E2/P1/studies3–8 remain pending.'))
    lines=['# Existing evidence scope beside strategic accounting','',
        'Modeler purpose is distinct from obtainable observations, a selected rule and permitted procedural response. The new ledger supplies no new purpose evidence.','',
        '| Scope | Purpose | Public/disclosed observations | Rule dependency | Procedural response | Exact disclosure premise | Verdict scope |',
        '| --- | --- | --- | --- | --- | --- | --- |']
    for r in ROWS:
        lines.append('| '+' | '.join(str(r[k])+(' Disclosed: '+r['disclosed_observations'] if k=='public_observations' else '') for k in ('scope','modeler_purpose','public_observations','rule_definition','procedural_response','disclosure_premise','verdict_scope'))+' |')
    (dest/'evidence-scope.md').write_text('\n'.join(lines)+'\n')
    print('Built7 compact evidence-scope mappings;0 new verdicts/packets/observations.')
    return dict(evidence_scope_rows=len(ROWS),new_evidence_outcomes=0)
