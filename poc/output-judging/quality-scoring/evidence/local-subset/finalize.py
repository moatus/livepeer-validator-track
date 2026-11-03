import pathlib,json,hashlib,datetime,subprocess,tarfile
P=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,x):(P/n).write_text(json.dumps(x,indent=2)+'\n')
for n,args in [('host-after.txt',['nvidia-smi']),('memory-after.txt',['free','-h']),('disk-after.txt',['df','-h',str(P)])]:
 (P/n).write_text(subprocess.check_output(args,text=True))
records=[json.loads(f.read_text()) for f in (P/'records').glob('*.json')]
assert len(records)==216
cleanup=dict(closed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),generated_attempts=216,paid_calls=0,uploads=0,rerolls=0,model_processes='All experiment generation and scoring subprocesses exited; inspect host-after.txt',other_jobs='No other process stopped, restarted or reconfigured',old_artifacts='Read only; exact SD1.x files rehashed against prior identities',product_changes=False,git_commits=False,publication=False,driver_system_changes=False,containers=False,new_models_env='Retained in this experiment for reproduction; excluded from review bundle',temporary_files='No experiment service, model container or background job remains; temporary downloads managed inside local models/.cache',containment_deviation='Initial uv dependency install used shared default cache; new entries may have been added there. Old venvs and model caches not mutated. Shared cache entries not deleted to preserve concurrent jobs.',cleanup_policy='Retain all experiment artifacts; no destructive cleanup')
dump('cleanup.json',cleanup)
dump('code-hashes-final.json',{p.name:sha(p) for p in sorted(P.glob('*.py'))})
ledger=(P/'spend.jsonl').read_text()
if 'terminal_accounting' not in ledger:
 with (P/'spend.jsonl').open('a') as f:f.write(json.dumps(dict(event='terminal_accounting',timestamp=cleanup['closed_at'],hosted_calls=0,estimated_usd=0,actual_usd=0,actual_usage_receipts=[],unobservable_paid_settlement=False,note='No inference submissions or uploads; billing account statement not queried'))+'\n')
skipdirs={'.venv','models','hf-cache','uv-cache','__pycache__'}
skipfiles={'artifact-checksums.sha256','review-bundle.tar.gz','review-bundle.sha256','verification.json','verification.log'}
files=[p for p in sorted(P.rglob('*')) if p.is_file() and not (set(p.relative_to(P).parts)&skipdirs) and p.name not in skipfiles]
(P/'artifact-checksums.sha256').write_text(''.join(f'{sha(p)}  {p.relative_to(P)}\n' for p in files))
# Recompute and verify the final terminal manifest before bundling its proof.
r=subprocess.run([str(P/'.venv/bin/python'),str(P/'verify.py')],capture_output=True,text=True);(P/'verification.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stdout+r.stderr
representatives={r['normalized'] for r in records if r['split']=='heldout' and r['draw']==0 and r['status']=='ok'}
selected=[]
for p in P.iterdir():
 if p.is_file() and p.name not in {'review-bundle.tar.gz','review-bundle.sha256'}:selected.append(p)
selected+=list((P/'stability-inputs').glob('*.png'))+[P/n for n in sorted(representatives)]
with tarfile.open(P/'review-bundle.tar.gz','w:gz') as tar:
 for p in sorted(selected):tar.add(p,arcname=str(p.relative_to(P)),recursive=False)
(P/'review-bundle.sha256').write_text(sha(P/'review-bundle.tar.gz')+'  review-bundle.tar.gz\n')
print(json.dumps(dict(artifact_files_hashed=len(files),bundle_bytes=(P/'review-bundle.tar.gz').stat().st_size,bundle_sha256=sha(P/'review-bundle.tar.gz'),verification='passed'),indent=2))
