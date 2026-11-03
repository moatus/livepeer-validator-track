import pathlib,json,hashlib,datetime,collections
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageDraw
P=pathlib.Path(__file__).resolve().parent
R=[json.loads(f.read_text()) for f in sorted((P/'runs').glob('*.json'))]
F=json.loads((P/'frozen-classifier.json').read_text());labels=F['labels'];centers=np.array([F['centers'][l] for l in labels]);scale=np.array(F['scale'])
def v(r):return np.fromfile(r['fingerprint'],dtype='<f4').astype(float)
def d(x):return np.mean(((x-centers)/scale)**2,axis=1)
def pred(r):return labels[int(np.argmin(d(v(r))))]
def dump(n,x):(P/n).write_text(json.dumps(x,indent=2)+'\n')
rng=np.random.default_rng(20261025)
eval=[r for r in R if r['tag']=='first' and r['split']=='evaluation']
cal=[r for r in R if r['tag']=='first' and r['split']=='calibration']
assert len(eval)==80 and len(cal)==40
correct=[pred(r)==r['label'] for r in eval]
conf={l:{k:sum(r['label']==l and pred(r)==k for r in eval) for k in labels} for l in labels}
bygroup={g:dict(correct=sum(pred(r)==r['label'] for r in eval if r['group']==g),n=sum(r['group']==g for r in eval)) for g in sorted(set(r['group'] for r in eval))}
byseed={str(s):dict(correct=sum(pred(r)==r['label'] for r in eval if r['seed']==s),n=sum(r['seed']==s for r in eval)) for s in sorted(set(r['seed'] for r in eval))}
promptids=sorted(set(r['prompt_id'] for r in eval));prompt_acc=np.array([np.mean([pred(r)==r['label'] for r in eval if r['prompt_id']==p]) for p in promptids]);boot=rng.choice(prompt_acc,(10000,len(prompt_acc))).mean(1)
# Wilson interval, useful when bootstrap degenerates at perfect accuracy; independence limited by prompts/groups.
def wilson(k,n):
 z=1.95996398454;p=k/n;den=1+z*z/n;c=(p+z*z/(2*n))/den;h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den;return [c-h,c+h]
first={(r['label'],r['prompt_id'],r['seed']):r for r in cal+eval}
repeat={};repeat_deltas=[]
for tag in ['repeat-inprocess','repeat-reload']:
 rs=[r for r in R if r['tag']==tag];assert len(rs)==20
 rows=[]
 for r in rs:
  b=first[(r['label'],r['prompt_id'],r['seed'])];delta=v(r)-v(b)
  rows.append(dict(key=r['key'],max_abs=float(abs(delta).max()),standardized_rms=float(np.sqrt(np.mean((delta/scale)**2))),bitwise=bool(np.array_equal(v(r),v(b))),same_image=r['image_sha256']==b['image_sha256'],same_prediction=pred(r)==pred(b)))
  repeat_deltas.append((tag,r['label'],rows[-1]['standardized_rms']))
 repeat[tag]=dict(n=len(rs),bitwise=sum(x['bitwise'] for x in rows),same_images=sum(x['same_image'] for x in rows),same_predictions=sum(x['same_prediction'] for x in rows),max_abs=max(x['max_abs'] for x in rows),max_standardized_rms=max(x['standardized_rms'] for x in rows),rows=rows)
timing={}
for label in labels:
 base={ (r['prompt_id'],r['seed']):r for r in R if r['label']==label and r['tag']=='timing-baseline'}
 inst={ (r['prompt_id'],r['seed']):r for r in R if r['label']==label and r['tag']=='timing-instrumented'}
 assert len(base)==len(inst)==10
 b=np.array([base[k]['seconds'] for k in base]);i=np.array([inst[k]['seconds'] for k in base]);delta=i-b;percent=100*(i/b-1)
 idx=rng.integers(0,10,(10000,10))
 timing[label]=dict(n_pairs=10,baseline_median_seconds=float(np.median(b)),instrumented_median_seconds=float(np.median(i)),median_paired_delta_seconds=float(np.median(delta)),median_paired_overhead_percent=float(np.median(percent)),paired_bootstrap_95_delta_seconds=np.quantile(np.median(delta[idx],axis=1),[.025,.975]).tolist(),paired_bootstrap_95_overhead_percent=np.quantile(np.median(percent[idx],axis=1),[.025,.975]).tolist(),same_images=sum(base[k]['image_sha256']==inst[k]['image_sha256'] for k in base),samples=[dict(prompt_id=k[0],seed=k[1],baseline_seconds=base[k]['seconds'],instrumented_seconds=inst[k]['seconds'],order='baseline-first' if j%2==0 else 'instrumented-first') for j,k in enumerate(base)],peak_allocated_bytes={tag:max(r['memory']['allocated'] for r in R if r['label']==label and r['tag']==tag) for tag in ['timing-baseline','timing-instrumented']},peak_reserved_bytes={tag:max(r['memory']['reserved'] for r in R if r['label']==label and r['tag']==tag) for tag in ['timing-baseline','timing-instrumented']})
gap=((centers[0]-centers[1])/scale)**2;contribution=gap/gap.sum();order=np.argsort(contribution)[::-1]
C=json.loads((P/'config.json').read_text());names=[f'{s}/{l}/{f}' for s in C['observed_steps'] for l in C['layers'] for f in C['features']]
contributions=[dict(feature=names[j],fraction=float(contribution[j])) for j in order]
# Diagnostic partition specified in analysis script before held-out collection; no model selection.
parts={}
for name,cols in [('magnitude',np.array([j for j in range(54) if j%6<4])),('shape_moments',np.array([j for j in range(54) if j%6>=4]))]:
 def pp(r):return labels[int(np.argmin(np.mean(((v(r)[cols]-centers[:,cols])/scale[cols])**2,axis=1)))]
 parts[name]=dict(correct=sum(pp(r)==r['label'] for r in eval),n=len(eval),fraction_of_standardized_centroid_gap=float(contribution[cols].sum()),diagnostic_only=True)
identities={l:json.loads((P/f'identity-{l}.json').read_text()) for l in labels}
component_comparison={f:identities[labels[0]]['files'][f]==identities[labels[1]]['files'].get(f) for f in identities[labels[0]]['files'] if f.endswith(('.safetensors','.json','.txt'))}
seedstable=[]
for l in labels:
 for p in promptids:
  rs=[r for r in eval if r['label']==l and r['prompt_id']==p];seedstable.append(len(set(pred(r) for r in rs))==1)
results=dict(experiment='IMG-002',status='complete',models={l:{k:identities[l][k] for k in ['repo','revision']} for l in labels},heldout=dict(correct=sum(correct),n=len(eval),accuracy=float(np.mean(correct)),independent_prompts=20,semantic_groups=10,model_prompt_cases=40,seeds_per_prompt=2,confusion=conf,by_group=bygroup,by_seed=byseed,prompt_cluster_bootstrap_95_accuracy=np.quantile(boot,[.025,.975]).tolist(),all_correct_prompt_count=int(np.sum(prompt_acc==1)),wilson_95_all_correct_prompt_rate=wilson(int(np.sum(prompt_acc==1)),20),seed_prediction_agreement=dict(agree=sum(seedstable),n=len(seedstable))),calibration=dict(prompts=10,semantic_groups=5,n=40,per_model=20),fingerprint=dict(floats=54,bytes=216,dtype='float32'),repeatability=repeat,timing=timing,contributions=contributions,diagnostic_partitions=parts,component_file_hash_matches=component_comparison,nsfw_flags=sum(bool(r['nsfw'] and any(r['nsfw'])) for r in R),total_saved_generations=len(R),analysis_timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat())
dump('results.json',results)
dump('distances.json',[dict(key=r['key'],truth=r['label'],prediction=pred(r),squared_distances=d(v(r)).tolist()) for r in cal+eval])
fig,axs=plt.subplots(1,2,figsize=(12,4))
for j,label in enumerate(labels):
 rs=[r for r in eval if r['label']==label];scores=[d(v(r))[1]-d(v(r))[0] for r in rs]
 axs[0].scatter(np.arange(len(rs))+j*.15,scores,s=20,label=label,alpha=.7)
axs[0].axhline(0,color='black',lw=1);axs[0].set(xlabel='Held-out prompt/seed index within model',ylabel='Squared distance(sd15) − distance(sd14)',title='Frozen classifier on 20 held-out prompts');axs[0].legend()
axs[1].barh(range(10),[contribution[j] for j in order[:10]]);axs[1].set_yticks(range(10),[names[j].replace('_blocks','') for j in order[:10]],fontsize=6);axs[1].invert_yaxis();axs[1].set(xlabel='Fraction of standardized centroid gap',title='Top calibration feature contributions');fig.tight_layout();fig.savefig(P/'separation.png',dpi=180);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(10,4))
for j,l in enumerate(labels):
 for t,offset in [('repeat-inprocess',-.1),('repeat-reload',.1)]:
  y=[x[2] for x in repeat_deltas if x[0]==t and x[1]==l];axs[0].scatter(np.full(len(y),j+offset),y,label=f'{l} {t}')
 for s in timing[l]['samples']:axs[1].plot([j-.15,j+.15],[s['baseline_seconds'],s['instrumented_seconds']],alpha=.5,marker='.')
axs[0].set_xticks([0,1],labels);axs[0].set(ylabel='RMS standardized fingerprint difference',title='Fixed prompt/seed repeats');axs[0].legend(fontsize=6)
axs[1].set_xticks([-.15,.15,.85,1.15],['1.4 base','1.4 hook','1.5 base','1.5 hook']);axs[1].set(ylabel='Synchronized full generation seconds',title='10 paired warm generations per model');fig.tight_layout();fig.savefig(P/'repeatability-overhead.png',dpi=180);plt.close(fig)
# Representative saved images; never read by classification.
canvas=Image.new('RGB',(4*256,3*280),'white');draw=ImageDraw.Draw(canvas)
for row,pid in enumerate(['p10','p18','p28']):
 for col,(label,seed) in enumerate([(l,s) for l in labels for s in [3303,4404]]):
  r=first[(label,pid,seed)];im=Image.open(r['image']).resize((256,256));canvas.paste(im,(col*256,row*280));draw.text((col*256+4,row*280+258),f'{label} {pid} seed {seed}',fill='black')
canvas.save(P/'contact-sheet.png')
print(json.dumps({k:results[k] for k in ['heldout','timing','diagnostic_partitions']},indent=2))
