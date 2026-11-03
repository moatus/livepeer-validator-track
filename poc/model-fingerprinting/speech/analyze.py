import pathlib,json,csv,re,collections,itertools,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=pathlib.Path(__file__).resolve().parent
rows=[json.load(open(f)) for f in sorted((P/'runs').glob('*.json'))]
manifest={r['id']:r for r in json.load(open(P/'dataset.json'))['clips']}
models=['parakeet','whisper']
inst=[r for r in rows if r['instrumented']]
first={}
for r in sorted(inst,key=lambda r:(r['round'],r['clip'])):first.setdefault((r['model'],r['clip']),r)
def baseline(r):
 w=r['words'];d=np.array([x['end']-x['start'] for x in w]);gap=np.array([max(0,b['start']-a['end']) for a,b in zip(w,w[1:])])
 return [len(w)/manifest[r['clip']]['duration'],d.mean(),d.std(),gap.mean() if len(gap) else 0]
def classify(feature):
 cal={m:np.array([feature(r) for (mm,c),r in first.items() if mm==m and r['split']=='calibration']) for m in models}
 means={m:v.mean(0) for m,v in cal.items()};scale=np.maximum(np.sqrt(np.mean([v.var(0,ddof=1) for v in cal.values()],axis=0)),1e-6)
 def dist(x,m):return float(np.mean(((x-means[m])/scale)**2))
 predictions=[];conf=np.zeros((2,2),int)
 for (m,c),r in first.items():
  if r['split']!='evaluation':continue
  x=np.array(feature(r));scores={mm:dist(x,mm) for mm in models};pred=min(scores,key=scores.get);conf[models.index(m),models.index(pred)]+=1
  predictions.append(dict(model=m,clip=c,predicted=pred,scores=scores))
 return dict(means={k:v.tolist() for k,v in means.items()},scale=scale.tolist(),confusion=conf.tolist(),predictions=predictions,accuracy=float(np.trace(conf)/conf.sum())),scale
internal,scale=classify(lambda r:r['fingerprint']);base,_=classify(baseline)
frozen=json.load(open(P/'frozen-before-evaluation.json'))
assert np.allclose(scale,frozen['scale'],rtol=1e-12,atol=1e-12)
assert all(np.allclose(internal['means'][m],frozen['means'][m],rtol=1e-12,atol=1e-12) for m in models)
repeat=[];cross=[]
for m in models:
 for c in manifest:
  rr=[r for r in inst if r['model']==m and r['clip']==c]
  for a,b in itertools.combinations(rr,2):
   repeat.append(dict(model=m,clip=c,split=manifest[c]['split'],reload=a['round']!=b['round'],distance=float(np.sqrt(np.mean(((np.array(a['fingerprint'])-b['fingerprint'])/scale)**2)))))
for c in manifest:
 a=first[('parakeet',c)];b=first[('whisper',c)]
 cross.append(dict(clip=c,split=manifest[c]['split'],distance=float(np.sqrt(np.mean(((np.array(a['fingerprint'])-b['fingerprint'])/scale)**2)))))
def describe(x):
 x=np.array(x);return dict(n=len(x),min=float(x.min()),median=float(np.median(x)),mean=float(x.mean()),max=float(x.max()),p95=float(np.quantile(x,.95)))
timing={}
rng=np.random.default_rng(42)
for m in models:
 rr=[r for r in rows if r['model']==m and r['round']==0]
 pairs=[]
 for c in manifest:
  a=next(r for r in rr if r['clip']==c and not r['instrumented']);b=next(r for r in rr if r['clip']==c and r['instrumented'])
  pairs.append(dict(clip=c,baseline=a['seconds'],instrumented=b['seconds'],delta=b['seconds']-a['seconds'],percent=100*(b['seconds']/a['seconds']-1)))
 delta=np.array([r['delta'] for r in pairs]);boots=np.mean(rng.choice(delta,size=(5000,len(delta))),axis=1)
 timing[m]=dict(baseline_seconds=describe([r['baseline'] for r in pairs]),instrumented_seconds=describe([r['instrumented'] for r in pairs]),paired_delta_seconds=describe(delta),mean_delta_bootstrap95=np.quantile(boots,[.025,.975]).tolist(),percent=describe([r['percent'] for r in pairs]),peak_allocated_GiB=max(r['peak_allocated'] for r in rows if r['model']==m)/2**30,peak_reserved_GiB=max(r['peak_reserved'] for r in rows if r['model']==m)/2**30,pairs=pairs)
def norm(s):return re.findall(r"[a-z0-9]+",s.lower())
def edits(a,b):
 d=list(range(len(b)+1))
 for i,x in enumerate(a):
  nd=[i+1]
  for j,y in enumerate(b):nd.append(min(nd[-1]+1,d[j+1]+1,d[j]+(x!=y)))
  d=nd
 return d[-1]
quality={}
for m in models:
 refs=[norm(manifest[c]['text']) for mm,c in first if mm==m]
 hyps=[norm(r['text']) for (mm,c),r in first.items() if mm==m]
 quality[m]=dict(normalized_word_error_rate=sum(edits(a,b) for a,b in zip(refs,hyps))/sum(map(len,refs)),reference_words=sum(map(len,refs)))
agreement=[]
for c in manifest:
 a=norm(first[('parakeet',c)]['text']);b=norm(first[('whisper',c)]['text'])
 agreement.append(dict(clip=c,split=manifest[c]['split'],edit_fraction=edits(a,b)/max(1,len(a)),identical=a==b))
extra={}
for m in models:
 ev=[r for (mm,c),r in first.items() if mm==m and r['split']=='evaluation']
 extra[m]=dict(repeat=describe([r['distance'] for r in repeat if r['model']==m]),reload_repeat=describe([r['distance'] for r in repeat if r['model']==m and r['reload']]),different_audio=describe([float(np.sqrt(np.mean(((np.array(a['fingerprint'])-b['fingerprint'])/scale)**2))) for a,b in itertools.combinations(ev,2)]))
contributions=((np.array(internal['means']['parakeet'])-internal['means']['whisper'])/scale)**2
json.dump(dict(squared_centroid_gap_per_feature=contributions.tolist(),description='Calibration-only contributions; descriptive inspection, no feature selection'),open(P/'calibration-contributions.json','w'),indent=2)
all_eval_inst=[r for r in inst if r['split']=='evaluation']
all_repeat_errors=sum(min(models,key=lambda m:float(np.mean(((np.array(r['fingerprint'])-internal['means'][m])/scale)**2)))!=r['model'] for r in all_eval_inst)
recording=[json.loads(line) for line in open(P/'recording-times.jsonl')]
summary=dict(per_model_distances=extra,all_heldout_instrumented_errors=all_repeat_errors,all_heldout_instrumented_n=len(all_eval_inst),recording_seconds=describe([r['seconds'] for r in recording]),json_job_bytes=describe([r['bytes'] for r in recording]),run_count=len(rows),instrumented_count=len(inst),internal=internal,output_baseline=base,repeat_all=describe([r['distance'] for r in repeat]),repeat_reload=describe([r['distance'] for r in repeat if r['reload']]),cross_heldout=describe([r['distance'] for r in cross if r['split']=='evaluation']),timing=timing,quality=quality,identical_transcript_clips=sum(r['identical'] for r in agreement),identical_transcript_heldout=sum(r['identical'] and r['split']=='evaluation' for r in agreement),fingerprint_float32_bytes=96)
json.dump(summary,open(P/'results.json','w'),indent=2)
json.dump(dict(repeat=repeat,cross=cross,agreement=agreement),open(P/'distances.json','w'),indent=2)
# Frozen classifier is derived solely from calibration rows; persist its fit separately.
json.dump(dict(config_sha256=hashlib.sha256((P/'config.json').read_bytes()).hexdigest(),means=internal['means'],scale=internal['scale']),open(P/'frozen-classifier.json','w'),indent=2)
with open(P/'runs.csv','w') as f:
 w=csv.DictWriter(f,fieldnames=['model','clip','split','round','instrumented','seconds','peak_allocated','peak_reserved']);w.writeheader();w.writerows({k:r[k] for k in w.fieldnames} for r in rows)
fig,ax=plt.subplots(1,2,figsize=(10,4))
a=[r['distance'] for r in repeat if r['split']=='evaluation'];b=[r['distance'] for r in cross if r['split']=='evaluation']
ax[0].boxplot([a,b],tick_labels=['Same model repeats','Different models']);ax[0].set_yscale('symlog',linthresh=1e-5);ax[0].set_ylabel('RMS standardized activation-statistic difference');ax[0].set_title('Held-out matched audio')
cm=np.array(internal['confusion']);ax[1].imshow(cm,cmap='Blues');ax[1].set_xticks([0,1],models);ax[1].set_yticks([0,1],models);ax[1].set_xlabel('Predicted');ax[1].set_ylabel('Actual');ax[1].set_title('Held-out first runs (36 model/clip pairs)')
for i in range(2):
 for j in range(2):ax[1].text(j,i,str(cm[i,j]),ha='center',va='center',color='white' if i==j else 'black')
fig.tight_layout();fig.savefig(P/'separation.png',dpi=180)
print(json.dumps({k:v for k,v in summary.items() if k not in ['internal','output_baseline','timing']},indent=2));print('accuracy',internal['accuracy'],'baseline',base['accuracy'])
