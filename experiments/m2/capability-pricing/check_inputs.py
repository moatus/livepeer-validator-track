#!/usr/bin/env python3
"""Validate frozen provenance/grid structure only; never evaluate scenario outcomes."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ALLOWED_STATUS = {'paper-stated', 'measured', 'illustrative', 'unresolved'}
ALLOWED_SCOPE = {'computed', 'stated', 'deferred'}
EXPECTED_NAMED_INPUTS = 89  # original 86 plus the three Gate A split/note entries
EXPECTED_POOL_LINKS = 100
EXPECTED_SNAPSHOT_BINDINGS = 918
MAX_SHARED_ILLUSTRATIVE_SOURCE = 2


def require(test, message):
    if not test:
        raise ValueError(message)


def labelled(record, where):
    require(record.get('status') in ALLOWED_STATUS, f'{where}: status')
    require(record.get('scope') in ALLOWED_SCOPE, f'{where}: scope')
    require(bool(record.get('source')), f'{where}: source')


def resolve(snapshot, pointer):
    require(pointer.startswith('/'), f'Invalid pointer {pointer}')
    result = snapshot
    for token in pointer[1:].split('/'):
        token = token.replace('~1', '/').replace('~0', '~')
        result = result[int(token)] if isinstance(result, list) else result[token]
    return result


def check():
    manifest = json.loads((HERE / 'inputs.json').read_text())
    grid = json.loads((HERE / 'scenarios.json').read_text())
    inputs = manifest['inputs']
    pool_links = {name for name in inputs if name.startswith('pool_') and name.endswith('_proxy_link')}
    require(pool_links == {f'pool_{i:02d}_proxy_link' for i in range(EXPECTED_POOL_LINKS)}, 'Pool-link inventory')
    require(len(inputs) - len(pool_links) == EXPECTED_NAMED_INPUTS, 'Named input count')
    require(len(manifest['snapshot_bindings']) == EXPECTED_SNAPSHOT_BINDINGS, 'Snapshot-binding count')
    source_counts = Counter(record['source'] for record in inputs.values() if record.get('status') == 'illustrative')
    require(all(count <= MAX_SHARED_ILLUSTRATIVE_SOURCE for count in source_counts.values()),
            'Illustrative source boilerplate: one source string may cover at most two named inputs')
    for name, record in inputs.items():
        labelled(record, name)
        require('value' in record and bool(record.get('unit')), f'{name}: value/unit')
    spec = importlib.util.spec_from_file_location('snapshot_reader', HERE.parent / 'network-snapshot/read_snapshot.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    snapshot = module.load_snapshot(expected_id=inputs['snapshot_id']['value'],
                                    expected_sha256=inputs['snapshot_content_sha256']['value'])
    for name, record in manifest['snapshot_bindings'].items():
        labelled(record, name)
        require(bool(record.get('unit')), f'{name}: unit')
        resolve(snapshot, record['json_pointer'])
    for key, relative in [('october_text_sha256', 'docs/litepaper-2.0.md'),
                          ('october_pdf_sha256', 'docs/sources/litepaper-2026-10.pdf')]:
        require(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == inputs[key]['value'], f'{key}: changed source')
    require(len(snapshot['rounds'][34]['pools']) == 100, 'Population changed')
    operators = inputs['selected_operators']['value']
    require(set(operators) == {'A', 'B'} and len(set(operators.values())) == 2, 'Operator limit')
    require(snapshot['rounds'][34]['round_id'] == inputs['matched_round']['value'] == 4364, 'Matched round')
    for name in ['pool_%02d_proxy_link' % i for i in range(100)]:
        link = inputs[name]['value']
        p = snapshot['rounds'][34]['pools'][link['pool_index']]
        o = snapshot['orchestrators'][link['operator_index']]
        require(p['address'] == o['address'], f'{name}: address mismatch')
    for alias, pool_index in [('A', 34), ('B', 20)]:
        require(snapshot['rounds'][34]['pools'][pool_index]['address'] == operators[alias], f'{alias}: pointer mismatch')
    require(not set(operators.values()) & {i['address'] for i in snapshot['identity_context']}, 'Documented role selected')
    for name in ['schema', 'execution_contract', 'report_contract']:
        labelled(grid[name], name)
    main = grid['main']
    require(1 <= len(main) <= 12, 'Main scenario bound')
    seen = set()
    require([row['order'] for row in main] == sorted(row['order'] for row in main), 'Cooperative order')
    require(main[0]['order'] == 0, 'Cooperative first')
    require(sum(row['order'] == 4 for row in main) == 1, 'Exactly one response')
    required_reports = grid['report_contract']['value']
    for row in main:
        labelled(row, row['id'])
        require(row['id'] not in seen, 'Duplicate scenario')
        require(row['parent'] is None or row['parent'] in seen, 'Parent must precede child')
        seen.add(row['id'])
        require(len(row['changed_operators']) <= 2 and set(row['changed_operators']) <= set(operators), 'Changed operator bound')
        require(bool(row['legitimate_reference']) and bool(row['changes']), 'Reference/changes required')
        require(row['reports'] == required_reports, 'Incomplete reports')
        for key, value in row['changes'].items():
            labelled(value, row['id'] + '.' + key)
            require('value' in value and value.get('unit'), 'Change value/unit')
        require('outcomes' not in row and 'results' not in row, 'No outcomes allowed')
    sensitivity_ids = set()
    for row in grid['sensitivities']:
        labelled(row, row['id'])
        require(row['id'] not in sensitivity_ids, 'Duplicate sensitivity')
        sensitivity_ids.add(row['id'])
        require(set(row['parents']) <= seen and bool(row['rule']), 'Sensitivity parent/rule')
        require(row['reports'] == required_reports, 'Sensitivity reports')
        for level in row['levels']:
            labelled(level, row['id'])
        if row['id'] in ['T-price', 'T-cost']:
            require(len(row['levels']) <= 3, 'Price/cost bound')
        require('outcomes' not in row and 'results' not in row, 'No sensitivity outcomes')
    require(sensitivity_ids == {'T-price', 'T-cost', 'T-score', 'T-ownership', 'T-valuation', 'T-claim', 'T-appendix', 'T-zero', 'T-redistribution'}, 'Required sensitivities')
    print(f'PASS: {len(inputs)} labelled inputs; {len(manifest["snapshot_bindings"])} resolved source fields; {len(main)} main scenarios; 2 selected operators; 9 independent sensitivity groups; no outcome evaluation.')


if __name__ == '__main__':
    check()
