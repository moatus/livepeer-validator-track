#!/usr/bin/env python3
"""Offline prospective contract checks; no payoff, seat result or Git dependency."""
from pathlib import Path
import hashlib
import itertools
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def require(ok, message):
    if not ok:
        raise ValueError(message)

def check():
    manifest = json.loads((HERE/'input-manifest.json').read_text())
    cases = json.loads((HERE/'cases.json').read_text())
    paths = [p['path'] for p in manifest['files']]
    require(len(paths) == len(set(paths)), 'duplicate pin')
    for item in manifest['files']:
        path = ROOT/item['path']
        require(path.resolve().is_relative_to(ROOT), 'source escapes repository')
        require(hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], 'changed source: '+item['path'])
    require(cases['no_outcomes'] is True, 'not prospective')
    core = cases['core']
    require(len(core) == cases['core_count'] == 16, 'core budget')
    require({(r['evidence'],r['aggregation'],r['action']) for r in core} == set(itertools.product(['P','K'],['F','Q'],['E','L','A','U'])), 'missing/duplicate comparison')
    require(len({r['id'] for r in core}) == 16, 'duplicate core id')
    require(all((r['others_zero'],r['others_one'],r['others_missing']) == (16,16,0) for r in core), 'pivotal baseline drift')
    require(len(cases['controls']) == cases['control_count'] == 12, 'control budget')
    require([r['id'] for r in cases['controls']] == [f'C{i:02}' for i in range(1,13)], 'control ids')
    require(cases['actions'] == {
        'E': {'P':1,'K':0,'basis':'case review from E2 evidence'},
        'L': {'P':1,'K':1,'basis':'lenient without case review'},
        'A': {'P':None,'K':None,'basis':'no submission'},
        'U': {'P':0,'K':0,'basis':'unsupported coordination without independent review'}}, 'action contract drift')
    seats = cases['seats']
    require(seats['N'] == 33 and seats['majority'] == 17 and seats['cross_product'] is False, 'seat premises')
    require(seats['k'] == [0,1,3,5] and seats['d'] == [0,5,10,16], 'seat control drift')
    require(len(seats['checkpoints'])*(len(seats['k'])+len(seats['d'])-1+1) == cases['seat_row_count'] == 32, 'seat row budget')
    prose = (HERE/'assumptions.md').read_text()
    for phrase in ['knowledge-required','stipulated, not demonstrated','not protocol policy','not principal slashing','not redistributed','not token purchase costs','score-withheld','opportunity','ΔU','S00']:
        require(phrase.lower() in prose.lower(), 'missing declared boundary: '+phrase)
    for file in HERE.glob('*.md'):
        text = file.read_text()
        for target in re.findall(r'\]\(([^)]+)\)', text):
            if '://' in target or target.startswith('#'): continue
            require((file.parent/target.split('#')[0]).exists(), 'broken document link '+target)
    print(f'PASS: {len(paths)} pinned sources; 16 prospective core comparisons; 12 named controls; 32 seat rows; boundary and document-link checks; no outcomes computed')

if __name__ == '__main__':
    check()
