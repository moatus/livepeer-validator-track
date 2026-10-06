#!/usr/bin/env python3
"""Check an evidence tabletop's structure; never infer pair-specific judgments."""

import argparse
import csv
from itertools import product
from pathlib import Path
import re
import sys


MATRIX_COLUMNS = (
    'pair', 'case', 'standard', 'level', 'claim', 'value',
    'evidence', 'source', 'arrival_round', 'note',
)
VERDICT_COLUMNS = (
    'pair', 'standard', 'level', 'verdict', 'who_discloses', 'burden', 'note',
)
STANDARDS = ('narrow', 'broad')
LEVELS = ('public', 'public+disclosed')
CLAIMS = ('CL-01', 'CL-02', 'CL-03', 'CL-05', 'CL-06', 'CL-07')
VALUES = {'established', 'contradicted', 'unknown'}
VERDICTS = {'separates', 'does not separate', 'separates only with disclosure'}
ARRIVALS = {'n', 'after n+7'} | {f'n+{i}' for i in range(1, 8)}
SOURCE_PATTERNS = (
    re.compile(r'SRC-LP20 L[1-9]\d*(?:-[1-9]\d*)?(?:, L[1-9]\d*(?:-[1-9]\d*)?)*'),
    re.compile(r'SRC-(?:GOLP|PROTOCOL) [\w.-]+(?:/[\w.-]+)+(?:\:\d+(?:-\d+)?)?'),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_csv(path, columns):
    with path.open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames == list(columns), f'{path.name}: columns must be {columns}')
        rows = list(reader)
    require(rows, f'{path.name}: no rows')
    for number, row in enumerate(rows, 2):
        require(None not in row, f'{path.name}:{number}: extra cells')
        for column in columns:
            require(isinstance(row[column], str) and row[column].strip(),
                    f'{path.name}:{number}: empty {column}')
            require(row[column] == row[column].strip(),
                    f'{path.name}:{number}: surrounding whitespace in {column}')
    return rows


def verify(folder, readings):
    require(readings and len(set(readings)) == len(readings), 'readings must be distinct and nonempty')
    require(all(re.fullmatch(r'[a-z][a-z0-9_-]*', r) for r in readings), 'invalid reading label')
    for name in ('README.md', 'tolerances.md'):
        path = folder / name
        require(path.is_file() and path.read_text(encoding='utf-8').strip(), f'missing or empty {name}')
    matrix = read_csv(folder / 'matrix.csv', MATRIX_COLUMNS)
    verdicts = read_csv(folder / 'verdicts.csv', VERDICT_COLUMNS)
    cases_by_pair = {}
    keys = set()
    for row in matrix:
        require(re.fullmatch(r'[a-zA-Z0-9_-]+', row['pair']), 'invalid pair identifier')
        require(re.fullmatch(r'SC-\d{2}', row['case']), 'invalid case identifier')
        require(row['standard'] in STANDARDS, 'invalid standard')
        require(row['level'] in LEVELS, 'invalid level')
        require(row['claim'] in CLAIMS, 'invalid claim')
        require(row['value'] in VALUES, 'invalid claim value')
        require(row['arrival_round'] in ARRIVALS, 'invalid arrival round')
        for source in row['source'].split('; '):
            require(source == 'not specified by the paper'
                    or any(pattern.fullmatch(source) for pattern in SOURCE_PATTERNS),
                    f'invalid source locator: {source}')
        key = tuple(row[column] for column in MATRIX_COLUMNS[:5])
        require(key not in keys, f'duplicate matrix key: {key}')
        keys.add(key)
        cases_by_pair.setdefault(row['pair'], set()).add(row['case'])
    expected = set()
    for pair, cases in cases_by_pair.items():
        require(len(cases) == 2, f'{pair}: a pair must have exactly two cases')
        packet = folder / 'packets' / f'{pair}.md'
        require(packet.is_file() and packet.read_text(encoding='utf-8').strip(), f'missing packet for {pair}')
        expected.update((pair, *combination) for combination in product(cases, STANDARDS, LEVELS, CLAIMS))
    require(keys == expected, f'incomplete matrix: missing {sorted(expected - keys)}')
    verdict_keys = set()
    for row in verdicts:
        require(row['pair'] in cases_by_pair, 'verdict pair absent from matrix')
        require(row['standard'] in STANDARDS, 'invalid verdict standard')
        require(row['level'] in LEVELS, 'invalid verdict level')
        require(row['verdict'] in VERDICTS, 'invalid separation verdict')
        match = re.match(r'^reading=([a-z][a-z0-9_-]*); ', row['note'])
        require(match is not None, 'verdict note must begin reading=<label>; ')
        reading = match.group(1)
        require(reading in readings, f'unrequested reading: {reading}')
        key = (row['pair'], row['standard'], row['level'], reading)
        require(key not in verdict_keys, f'duplicate verdict key: {key}')
        verdict_keys.add(key)
    expected_verdicts = set(product(cases_by_pair, STANDARDS, LEVELS, readings))
    require(verdict_keys == expected_verdicts,
            f'incomplete verdicts: missing {sorted(expected_verdicts - verdict_keys)}')
    return len(matrix), len(verdicts), len(cases_by_pair)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', nargs='?', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--readings', default='a,b', help='comma-separated verdict reading labels')
    args = parser.parse_args()
    try:
        matrix, verdicts, pairs = verify(args.folder, tuple(args.readings.split(',')))
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1
    print(f'PASS: {matrix} claim rows; {verdicts} verdict rows; {pairs} pair(s). Structure only; judgments checked by hand.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
