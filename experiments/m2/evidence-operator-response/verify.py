"""Compact EX-10 structural verifier; cannot certify access, judgment or error rates."""
import csv,hashlib,itertools,json,re,sys
from pathlib import Path
from check_k1 import inspect
from fee_summary import summary
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def require(ok,msg):
    if not ok:raise ValueError(msg)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name,cols):
    with (HERE/name).open(newline='') as f:
        r=csv.DictReader(f);require(r.fieldnames==cols,name+' columns');rows=list(r)
    require(rows and all(set(x)==set(cols) and all(v and v==v.strip() for v in x.values()) for x in rows),name+' empty/extra cells');return rows

def verify():
    require(sha(HERE/'tolerances.md')=='3a9a8d968b6ba77e4e8342ca4b9fb630086b323bd1e0f9432eaf6e90d9d77176','Changed prospective tolerance')
    m=json.loads((HERE/'source-manifest.json').read_text())
    for c in m['code']:
        require(re.fullmatch('[0-9a-f]{40}',c['commit']) is not None,'Code pin')
        for x in c['excerpts']:require(hashlib.sha256(x['text'].encode()).hexdigest()==x['sha256'],'Excerpt identity')
    for p in ['docs/litepaper-2.0.md','docs/sources/litepaper-2026-10.pdf','docs/sources/litepaper-2026-09.md']:
        entry=next(x for x in m['files'] if x['path']==p);require(sha(ROOT/p)==entry['sha256'],'Paper source '+p)
    om=json.loads((HERE/'outcome-source-manifest.json').read_text())
    for x in om['files']:require(sha(HERE/x['path'])==x['sha256'],'Outcome source '+x['path'])
    bundle=json.loads((HERE/'fixtures/bundle.json').read_text())
    for name,key in [('terms.json','terms_sha256'),('input.txt','input_sha256')]:require(sha(HERE/'fixtures'/name)==bundle[key],'Bundle term/input digest')
    obs=[]
    for c in bundle['cases']:
        o=inspect(HERE/c['output_path']);require(o['sha256']==c['output_sha256'],'Output identity');obs.append(o)
    require([(x['width'],x['height'],x['k1']) for x in obs]==[(512,512,True),(256,512,False)],'Fixed K1 fixtures')
    mc=['pair','case','standard','level','claim','value','evidence','source','arrival_round','note'];rows=read('matrix.csv',mc)
    standards=['term-breach','knowledge-required'];levels=['public','public+disclosed'];claims=[f'CL-{i:02}' for i in range(1,8)]
    keys=[tuple(r[k] for k in mc[:5]) for r in rows];expected=set(itertools.product(['sc10-sc11'],['SC-10','SC-11'],standards,levels,claims))
    require(len(keys)==len(set(keys)) and set(keys)==expected,'Matrix coverage')
    packet=(HERE/'packets/sc10-sc11.md').read_text()
    for r in rows:
        require(r['value'] in ['established','contradicted','unknown'],'Claim state')
        require(r['arrival_round'] in ['n+5','n+6','n+7'],'Arrival')
        for ev in r['evidence'].split('; '):require(ev in ['P0','Q','D1','C1','B0'] and ev in packet,'Evidence cross-link')
        for loc in r['source'].split('; '):require(loc=='not specified by the paper' or re.fullmatch(r'SRC-LP20-OCT L\d+-\d+',loc),'Source locator')
    vc=['pair','standard','level','verdict','who_discloses','burden','note'];vs=read('verdicts.csv',vc);keys=[]
    for r in vs:
        match=re.match(r'reading=([ab]); ',r['note']);require(match,'Reading label');keys.append((r['pair'],r['standard'],r['level'],match[1]))
        require(r['verdict'] in ['does not separate','separates only with disclosure','separates'],'Verdict value')
    require(len(keys)==len(set(keys)) and set(keys)==set(itertools.product(['sc10-sc11'],standards,levels,['a','b'])),'Verdict coverage')
    inv=read('record-inventory.csv',['category','pinned_paths','holder','public_private','retention_access','authentication_linkage','preclaim_availability','supported_claims','unsupported_claims','evidence_status'])
    require({x['category'] for x in inv}=={'probabilistic tickets','winning tickets','transcoding verification','capability adverts','orchestrator statistics','invoice price per job'} and len(inv)==6,'Inventory coverage')
    for row in inv:
        for ref in row['pinned_paths'].split('; '):
            repo,pin,path,ranges=re.fullmatch(r'([^@]+)@([0-9a-f]{40}):([^:]+):(.+)',ref).groups()
            source=next(c for c in m['code'] if c['repository']==repo and c['commit']==pin and c['path']==path)
            for rg in ranges.split(','):
                lo,hi=map(int,rg.split('-'));require(any(x['line_start']<=lo<=hi<=x['line_end'] for x in source['excerpts']),'Inventory excerpt range')
    tc=['comparison','standard','level','reading','tolerance','assessment','reason'];ts=read('tolerance-assessment.csv',tc)
    keys=[tuple(r[k] for k in tc[:5]) for r in ts];ids=['T-FC-a','T-MV-a','T-FC-b','T-MV-b','T-ER','T-EC','T-DP','T-T']
    require(len(keys)==len(set(keys)) and set(keys)==set(itertools.product(['sc10-sc11','sc25','sc26'],standards,levels,['a','b'],ids)),'Individual tolerance coverage')
    require(all(r['assessment'] in ['conditional','not-applicable','within-by-construction','not-met','limited','not-met-if-cut'] for r in ts),'Tolerance allowed values')
    for name in ['README.md','inheritance.md','fee-delay.md','operator-response.md','slice3-inputs.md','practitioner-dispositions.md']:require((HERE/name).is_file(),name)
    fees=summary();print(json.dumps({'k1_observations':obs,'selected_fee_summary':fees},indent=2))
    print('PASS: 56 claim rows; 8 verdict rows; 6 record categories; 192 separate tolerance cells; fixed sources/cross-links; bounded K1 and selected P1 arithmetic. Structure/bytes only, not substantive judgment, custody, practical access, human effort or empirical rates.')
if __name__=='__main__':
    try:verify()
    except (ValueError,AssertionError,KeyError,StopIteration,OSError) as e:print('FAIL:',e,file=sys.stderr);sys.exit(1)
