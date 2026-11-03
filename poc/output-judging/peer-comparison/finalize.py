import pathlib,json,time,hashlib,tarfile,datetime,html
P=pathlib.Path(__file__).resolve().parent
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8388608),b''):h.update(b)
 return h.hexdigest()
def dump(n,x):(P/n).write_text(json.dumps(x,indent=2)+'\n')
R=json.loads((P/'results.json').read_text());start=json.loads((P/'run-start.json').read_text());elapsed=time.time()-start['epoch'];extract=json.loads((P/'extraction.json').read_text());compute=dict(generation_and_analysis_enclosing_seconds=elapsed,gpu_hours_upper_bound=elapsed/3600,generation_call_seconds=R['accounting']['generation_seconds'],extraction_seconds=extract['seconds'],hosted_spend_usd=0,hardware_cost='not priced; zero hosted spend does not imply free hardware',end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),preflight_utc='2026-10-27T12:06:00Z',wall_since_first_gpu_preflight_seconds=time.time()-datetime.datetime(2026,10,27,12,6,tzinfo=datetime.timezone.utc).timestamp())
assert elapsed<3600 and compute['wall_since_first_gpu_preflight_seconds']<4500
dump('compute.json',compute)
notes=[]
for method,conds in R['heldout'].items():
 h=conds['honest'];j=conds['jpeg75'];c=conds['close'];b=conds['broad'];notes.append(f"{method}: honest false accusations {h['false_accusation']}/{h['valid']}; JPEG75 false accusations {j['false_accusation']}/{j['valid']}; correct substitute flags SD1.5 {c['correct']}/{c['valid']} and SDXL {b['correct']}/{b['valid']}; wrong honest accusations {c['wrong_honest_slot']} and {b['wrong_honest_slot']}, respectively.")
recommendation=' '.join(notes)+' Treat this as a bounded consistency screen only. The observed false accusations and missed substitutes, alongside the small sample and SDXL confound, do not support standalone model-identity enforcement or penalties. Independent scientific review remains pending; no expanded experiment is part of this delivery.'
dump('handoff.json',dict(status='complete execution; scientific review pending',recommendation=recommendation,freeze_sha256=sha(P/'freeze.json'),compute=compute,remote_full_images=str(P),local_expected='/home/mav/repos/livepeer/research/'+P.name,execution_audit=['No scientific method amendments.','verify_snapshot.py and finalize.py are supplemental verification/report-packaging scripts added after initial freeze (also verify_delivery.py); they do not generate images, extract features, calibrate or change decisions.','Host-only desktop processes observed before loading; no other compute task killed. Own SDXL process terminated after all records persisted when cleanup stalled; see execution-audit.json.','No repository, issue, board, journal, commit, push or publication changes.']))
page=(P/'report.html').read_text();lead='<p class="note"><strong>Result:</strong> Neither representation correctly flagged any SD1.5 substitute (0/19 each). RPA flagged14/19 SDXL substitutes but falsely accused18/19 honest JPEG75 groups. PickScore flagged4/19 SDXL substitutes and falsely accused2/19 ordinary honest groups. These results do not support using this peer rule alone to enforce model identity.</p>';page=page.replace('</h1>','</h1>'+lead,1);add='<h2>Result and bounded recommendation</h2><p>'+html.escape(recommendation)+'</p><h2>Compute and frozen identity</h2><pre>'+html.escape(json.dumps(compute,indent=2))+'</pre><p>Frozen protocol/code manifest SHA256: '+sha(P/'freeze.json')+'. Exact delivered file sizes and hashes: snapshot-files.json and snapshot.sha256; archive size/hash: review-bundle.json. These manifests exclude themselves to avoid circular hashes.</p>'
(P/'report.html').write_text(page.replace('</html>',add+'</html>'))
records=[json.loads(p.read_text()) for p in sorted((P/'records').glob('*.json'))]
dump('manifest.json',dict(generation=records,feature_file='features.npz',group_membership='groups.json',evaluation_labels='labels.json',distance_and_decision_file='decisions-blind.json',full_images_retained_remotely=True))
ranking=[]
for r in json.loads((P/'decisions.json').read_text()):
 if r['valid']:
  ranking.append(dict(method=r['method'],group=r['group'],scores=r['scores'],descending_slots=sorted(range(4),key=lambda k:-r['scores'][k]),unique_top=r['candidate'],truth=r['truth'],strictly_higher_than_truth=sum(v>r['scores'][r['truth']] for v in r['scores']) if r['truth'] is not None else None))
dump('rankings.json',ranking)
# Record every compact review file, no models/env/raw full images; original complete images stay remote.
exclude={'raw','normalized','nuisance','__pycache__'};files=[p for p in sorted(P.rglob('*')) if p.is_file() and not any(x in exclude for x in p.relative_to(P).parts) and p.name not in ['snapshot-files.json','snapshot.sha256','review-bundle.tar.gz','review-bundle.json']]
entries=[dict(path=str(p.relative_to(P)),bytes=p.stat().st_size,sha256=sha(p)) for p in files];dump('snapshot-files.json',dict(files=entries,total_files=len(entries),total_bytes=sum(e['bytes'] for e in entries)))
(P/'snapshot.sha256').write_text(''.join(e['sha256']+'  '+e['path']+'\n' for e in entries))
with tarfile.open(P/'review-bundle.tar.gz','w:gz') as t:
 for p in files+[P/'snapshot-files.json',P/'snapshot.sha256']:t.add(p,arcname=str(p.relative_to(P)))
dump('review-bundle.json',dict(file='review-bundle.tar.gz',bytes=(P/'review-bundle.tar.gz').stat().st_size,sha256=sha(P/'review-bundle.tar.gz'),snapshot_files=len(entries),snapshot_bytes=sum(e['bytes'] for e in entries),freeze_sha256=sha(P/'freeze.json')))
print(json.dumps(json.loads((P/'review-bundle.json').read_text()),indent=2));print(recommendation)
