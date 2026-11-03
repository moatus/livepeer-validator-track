"""Run both sample checkers in isolated directories; retain both exact outcomes.
Usage: python3 tools/check_evidence_samples.py runs/phase-28/validation-TIMESTAMP
"""
import pathlib,tempfile,shutil,json,subprocess,sys
R=pathlib.Path(sys.argv[1]);R.mkdir(parents=True,exist_ok=False)
B=str(pathlib.Path('target/release/witness').resolve());C=str(pathlib.Path('tools/cleanroom_check.py').resolve());rows=[]
for source in sorted(pathlib.Path('samples/evidence').iterdir()):
 if not source.is_dir():continue
 clean=pathlib.Path(tempfile.mkdtemp(prefix='sample-',dir=R))
 for n in ('package.json','request.http','response.http','trust.json','expected.json'):shutil.copy2(source/n,clean/n)
 args=['--evidence','package.json','--client-request','request.http','--client-response','response.http','--trust-list','trust.json']
 p=subprocess.run([B,'check',*args],capture_output=True,text=True,cwd=clean);got=json.loads(p.stdout);expected=json.loads((clean/'expected.json').read_text());assert 'profile' in expected,(source,'missing expected profile')
 match=all(got.get(n)==expected.get(n) for n in ('result','link','profile')) and ((p.returncode==0)==(expected['result']=='PASS'))
 other=subprocess.run(['python3',C,'check',*args],capture_output=True,text=True,cwd=clean)
 try:independent=json.loads(other.stdout)
 except ValueError:independent=dict(stdout=other.stdout,stderr=other.stderr)
 rows.append(dict(case=source.name,clean_directory=str(clean),expected=expected,rust=dict(result=got,exit=p.returncode,match=match),cleanroom=dict(result=independent,exit=other.returncode,match=all(independent.get(n)==expected.get(n) for n in ('result','link','profile')) and ((other.returncode==0)==(expected['result']=='PASS')))))
(R/'sample-checks.json').write_text(json.dumps(rows,indent=2)+'\n')
assert all(r['rust']['match'] and r['cleanroom']['match'] for r in rows),[r for r in rows if not (r['rust']['match'] and r['cleanroom']['match'])]
print(json.dumps(dict(rust_matched=sum(r['rust']['match'] for r in rows),cleanroom_matched=sum(r['cleanroom']['match'] for r in rows),total=len(rows),new_chain_samples=sum(r['case'].startswith('job-') for r in rows))))
