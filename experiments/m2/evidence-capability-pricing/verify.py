#!/usr/bin/env python3
"""Verify evidence coverage, source coordinates and the frozen tolerance content.

Checks structure and provenance, never the substantive hand judgments.
Optional --source-root SRC-GOLP=PATH or SRC-PROTOCOL=PATH checks full originals.
"""
import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path
import re
import subprocess
import sys

MATRIX_COLUMNS = ('pair','case','standard','level','claim','value','evidence','source','arrival_round','note')
VERDICT_COLUMNS = ('pair','case','standard','level','reading','verdict','who_discloses','burden','procedural_note','note')
SOURCE_COLUMNS = ('id','kind','source','path','line_start','line_end','pdf_page','quote','sha256','arrival_round','reach','upstream_path','upstream_revision','upstream_line_start','upstream_line_end','upstream_file_sha256')
VALUES = {'established','contradicted','unknown'}
VERDICTS = {'separates','does not separate','separates only with disclosure'}
TOLERANCE_SHA256 = 'df904d04e7bc2c94f789510d9922ca3c633f1ddb6a90f92eff17f1d2a99162ac'
TOLERANCE_COMMIT = 'fc5d202501a413cb7b4009a12c49919f58c22500'

def require(condition, message):
    if not condition: raise ValueError(message)

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def words(text): return ' '.join(text.split())

def bounded_path(base, relative):
    p=(base/relative).resolve()
    require(not Path(relative).is_absolute() and p.is_relative_to(base.resolve()), f'path outside source root: {relative}')
    require(p.is_file(), f'missing source path: {relative}')
    return p

def read_csv(path, columns, optional=()):
    with path.open(newline='',encoding='utf-8') as f:
        r=csv.DictReader(f)
        require(r.fieldnames==list(columns), f'{path.name}: wrong columns')
        rows=list(r)
    require(rows, f'{path.name}: empty')
    for n,row in enumerate(rows,2):
        require(None not in row, f'{path.name}:{n}: extra column')
        for col in columns:
            v=row[col]
            require(isinstance(v,str) and (col in optional or v.strip()), f'{path.name}:{n}: empty {col}')
            require(v==v.strip(),f'{path.name}:{n}: surrounding whitespace in {col}')
    return rows

def round_number(value, horizon):
    m=re.fullmatch(r'n\+(\d+)',value)
    require(m and 0<int(m[1])<=horizon, f'invalid arrival: {value}')
    return int(m[1])

def check_source(row, folder, repo, roots, config):
    locator=row['source']
    if locator=='not specified by the paper':
        require(not any(row[k] for k in SOURCE_COLUMNS[3:9]),f"{row['id']}: unspecified source has a file/quote")
        require(not any(row[k] for k in SOURCE_COLUMNS[11:]),f"{row['id']}: unspecified source has upstream coordinates")
        return
    p=bounded_path(folder if row['path'].startswith('sources/') else repo,row['path'])
    require(sha(p)==row['sha256'],f"{row['id']}: source hash mismatch")
    lines=p.read_text(encoding='utf-8').splitlines()
    a,b=int(row['line_start']),int(row['line_end'])
    require(1<=a<=b<=len(lines),f"{row['id']}: source lines do not exist")
    selected='\n'.join(lines[a-1:b])
    require(row['quote'] and words(row['quote']) in words(selected),f"{row['id']}: quoted text does not match source lines")
    paper=re.fullmatch(r'SRC-LP20-OCT L(\d+)-(\d+)',locator)
    if paper:
        require((a,b)==(int(paper[1]),int(paper[2])),f"{row['id']}: paper locator differs from file coordinates")
        require(row['path']==config['paper_path'] and row['sha256']==config['paper_sha256'],f"{row['id']}: wrong paper snapshot")
        headings=[(i+1,int(m[1])) for i,line in enumerate(lines) if (m:=re.fullmatch(r'## PDF page (\d+)',line))]
        active=[page for start,page in headings if start<=a][-1]
        require(active==int(row['pdf_page']),f"{row['id']}: wrong PDF page")
        next_start=min((start for start,page in headings if start>a),default=len(lines)+1)
        require(b<next_start,f"{row['id']}: crosses PDF page")
        require(not row['upstream_path'],f"{row['id']}: paper has unexpected upstream path")
        return
    code=re.fullmatch(r'(SRC-GOLP|SRC-PROTOCOL) ([\w./-]+):(\d+)-(\d+)',locator)
    require(code is not None,f"{row['id']}: invalid source locator")
    sid,upstream,ua,ub=code.groups(); ua,ub=int(ua),int(ub)
    require(row['path'].startswith('sources/') and upstream==row['upstream_path'],f"{row['id']}: code path mismatch")
    require((ua,ub)==(int(row['upstream_line_start']),int(row['upstream_line_end'])) and b-a==ub-ua,f"{row['id']}: excerpt coordinate mismatch")
    require(a==1 and b==len(lines) and ua>0,f"{row['id']}: truncated/misaligned excerpt")
    require(re.fullmatch('[0-9a-f]{40}',row['upstream_revision']) and re.fullmatch('[0-9a-f]{64}',row['upstream_file_sha256']),f"{row['id']}: missing pinned original identity")
    if sid in roots:
        original=bounded_path(roots[sid],upstream)
        require(sha(original)==row['upstream_file_sha256'],f"{row['id']}: original file hash mismatch")
        original_lines=original.read_text().splitlines()
        require(ub<=len(original_lines) and original_lines[ua-1:ub]==lines,f"{row['id']}: excerpt differs from original")

def verify(folder, roots=None):
    roots=roots or {}
    folder=folder.resolve(); repo=folder.parents[2]
    config=json.loads((folder/'config.json').read_text())
    require(config['schema_version']==1,'unsupported config schema')
    require(config['tolerance_sha256']==TOLERANCE_SHA256 and config['tolerance_commit']==TOLERANCE_COMMIT,'changed tolerance identity')
    require(sha(folder/'tolerances.md')==TOLERANCE_SHA256,'tolerances differ from the preceding committed content')
    if (repo/'.git').exists():
        raw=subprocess.check_output(['git','-C',str(repo),'show',TOLERANCE_COMMIT+':experiments/m2/evidence-capability-pricing/tolerances.md'])
        require(raw==(folder/'tolerances.md').read_bytes(),'tolerances differ from their Git commit')
    for k in ('paper','pdf'):
        require(sha(bounded_path(repo,config[k+'_path']))==config[k+'_sha256'],f'{k} snapshot hash mismatch')
    for path,digest in config.get('shared_sources',{}).items():
        require(sha(bounded_path(repo,path))==digest,'shared frozen source hash mismatch')
    require((folder/'README.md').read_text().strip(),'empty README')
    for name in config['packet_files'].values(): require(bounded_path(folder,name).read_text().strip(),'empty packet')
    sources=read_csv(folder/'source-index.csv',SOURCE_COLUMNS,optional=SOURCE_COLUMNS[3:9]+SOURCE_COLUMNS[11:])
    require(len({r['id'] for r in sources})==len(sources),'duplicate source ID')
    source_map={r['id']:r for r in sources}
    for row in sources:
        require(row['arrival_round']=='context' or round_number(row['arrival_round'],config['horizon']),'bad source arrival')
        check_source(row,folder,repo,roots,config)
    records=config['evidence_records']
    for eid,r in records.items():
        round_number(r['arrival_round'],config['horizon'])
        require(r['access'] in {'public','disclosed'},f'{eid}: invalid access')
        require(r['source_ids'] and set(r['source_ids'])<=source_map.keys(),f'{eid}: missing evidence source')
        for sid in r['source_ids']:
            v=source_map[sid]['arrival_round']
            require(v=='context' or round_number(v,config['horizon'])<=round_number(r['arrival_round'],config['horizon']),f'{eid}: source arrives after record')
    matrix=read_csv(folder/'matrix.csv',MATRIX_COLUMNS)
    mkeys=set()
    for row in matrix:
        family=row['pair']; case=row['case']
        require(family in config['families'] and case in config['families'][family]['cases'],'unconfigured family/case')
        require(row['standard'] in config['standards'] and row['level'] in config['levels'] and row['claim'] in config['claims'],'invalid matrix key')
        require(row['value'] in VALUES,'invalid claim value')
        key=tuple(row[k] for k in MATRIX_COLUMNS[:5]); require(key not in mkeys,'duplicate matrix key'); mkeys.add(key)
        for rule in config.get('matrix_note_requirements', []):
            if all(row.get(k)==v for k,v in rule['selector'].items()):
                require(all(phrase in row['note'] for phrase in rule['required']), 'missing configured element assessment in matrix note')
        evidence=row['evidence'].split('; ')
        require(len(set(evidence))==len(evidence) and set(evidence)<=records.keys(),'unknown/duplicate evidence record')
        source_ids=[]
        for eid in evidence:
            rec=records[eid]
            if rec['access']=='disclosed':
                require(row['level']=='public+disclosed','disclosed evidence leaked into public level')
                require(eid==config['disclosed_records'][family] and case==config['families'][family]['useful'],'disclosed source assigned outside its configured case/family')
            source_ids.extend(rec['source_ids'])
        expected_sources=list(dict.fromkeys(source_map[s]['source'] for s in dict.fromkeys(source_ids)))
        require(row['source'].split('; ')==expected_sources,'evidence source citations missing or mismatched')
        latest=max(round_number(records[e]['arrival_round'],config['horizon']) for e in evidence)
        require(round_number(row['arrival_round'],config['horizon'])==latest,'matrix arrival not latest relied-on record/cutoff')
    expected={(family,*ks) for family,f in config['families'].items() for ks in itertools.product(f['cases'],config['standards'],config['levels'],config['claims'])}
    require(mkeys==expected,'incomplete matrix coverage')
    verdicts=read_csv(folder/'verdicts.csv',VERDICT_COLUMNS); vkeys=set()
    for row in verdicts:
        key=tuple(row[k] for k in VERDICT_COLUMNS[:5])
        require(key not in vkeys,'duplicate verdict key'); vkeys.add(key)
        require(row['verdict'] in VERDICTS,'invalid separation verdict')
    expected_verdicts={(family,*ks) for family,f in config['families'].items() for ks in itertools.product(f['cases'],config['standards'],config['levels'],config['readings'])}
    require(vkeys==expected_verdicts,'incomplete keyed verdict coverage')
    # Packet IDs are auditable references rather than unchecked prose-only names.
    for family,name in config['packet_files'].items():
        packet=(folder/name).read_text()
        for case in config['families'][family]['cases']: require(case in packet,'packet omits configured case')
        ids=set(re.findall(r'\b(?:O|U|G|P)-(?:[A-Z]+(?:-[A-Z]+)?)\b',packet))
        require(ids<=source_map.keys()|records.keys(),'packet has unresolved source/record ID')
    return len(matrix),len(verdicts),len(sources)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder',nargs='?',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--source-root',action='append',default=[],metavar='SOURCE=PATH')
    args=p.parse_args()
    try:
        roots={}
        for item in args.source_root:
            sid,path=item.split('=',1); require(sid in {'SRC-GOLP','SRC-PROTOCOL'},'invalid source root ID'); roots[sid]=Path(path)
        m,v,s=verify(args.folder,roots)
    except (OSError,ValueError,KeyError,IndexError,csv.Error,subprocess.CalledProcessError) as e:
        print(f'FAIL: {e}',file=sys.stderr); return 1
    print(f'PASS: {m} claim rows; {v} keyed case/consequence rows; {s} source records; source coordinates/quotes/hashes and committed tolerance content. Structure/provenance only; judgments checked by hand.')
    return 0

if __name__=='__main__': sys.exit(main())
