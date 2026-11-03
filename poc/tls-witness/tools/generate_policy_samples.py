"""Regenerate offline policy controls from committed genuine fixture captures.

Usage: python3 -B tools/generate_policy_samples.py
Only a fresh in-memory test key signs these controls; no private key file is
read or written. These signatures are NOT new TLS observations.
"""
import copy
import hashlib
import json
import pathlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

ROOT = pathlib.Path(__file__).resolve().parents[1] / 'samples/evidence'
LABEL = 'TEST ONLY: local fixture test key'
key = Ed25519PrivateKey.generate()
pub = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()

def load(name):
    source = ROOT / name
    return {name: (json.loads(path.read_text()) if path.suffix == '.json' else path.read_bytes())
            for path in source.iterdir() if path.name in ('package.json', 'trust.json', 'request.http', 'response.http')
            for name in [path.name]}

def save(name, files, link, profile):
    target = ROOT / name
    target.mkdir(exist_ok=True)
    files['expected.json'] = dict(result='FAIL', link=link, profile=profile)
    for filename, value in files.items():
        path = target / filename
        path.write_bytes(value) if isinstance(value, bytes) else path.write_text(json.dumps(value, indent=2) + '\n')

base = load('credential-hidden-receipt')
for name in ('withheld-empty-range', 'withheld-under-full-disclosure', 'withheld-unknown-header',
             'withheld-missing-header', 'withheld-titlecase-header', 'withheld-wrong-circuit'):
    files = copy.deepcopy(base)
    package = files['package.json']
    package['test_only'] = LABEL + '; re-signed metadata policy control, not a TLS observation'
    receipt = package['receipt']
    withheld = receipt['record']['request']['withheld']
    if name == 'withheld-empty-range':
        withheld['end'] = withheld['start']
    elif name == 'withheld-under-full-disclosure':
        receipt['verdict']['profile'] = 'full-disclosure-fixture'
    elif name == 'withheld-unknown-header':
        withheld['header'] = 'cookie'
    elif name == 'withheld-missing-header':
        del withheld['header']
    elif name == 'withheld-titlecase-header':
        withheld['header'] = 'Authorization'
    else:
        withheld['no_cr_lf'] = '00' * 32
    verdict = receipt['verdict']
    profile = verdict['profile']
    verdict['root'] = hashlib.sha256(canonical(receipt['record'])).hexdigest()
    verdict['verifier_pub'] = pub
    package['witness_key_id'] = pub
    verdict.pop('sig', None)
    verdict['sig'] = key.sign(canonical(verdict)).hex()
    package['credential_cleanup']['profile'] = profile
    files['trust.json']['witnesses'] = [dict(label=LABEL, public_key=pub, profiles=[profile])]
    save(name, files, 'inclusion' if name == 'withheld-missing-header' else 'session',
         None if name == 'withheld-missing-header' else profile)

for name in ('job-later-entry-inclusion', 'job-later-entry-hex', 'job-later-entry-nonobject'):
    files = load('job-complete')
    chain = files['package.json']['chain']
    if name == 'job-later-entry-inclusion':
        chain[1]['receipt']['record']['response']['body_bytes'] += 1
        profile, link = None, 'inclusion'
    else:
        profile, link = chain[0]['receipt']['verdict']['profile'], 'evidence'
        if name == 'job-later-entry-hex':
            chain[1]['request_hex'] = 'not-hex'
        else:
            chain[1] = None
    files['package.json']['test_only'] = 'Unsigned later-entry failure control around committed genuine fixture captures'
    save(name, files, link, profile)
print('Generated six labelled policy controls and three chain controls; no key files used.')
