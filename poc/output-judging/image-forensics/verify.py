"""Offline independent numerical ridge fits; no torch, sklearn, weights or inference required.
Run python verify.py [--originals] in extracted review bundle with numpy installed.
"""
import pathlib,json,hashlib,sys
import numpy as np
P=pathlib.Path(__file__).resolve().parent
D=np.load(P/'features.npz');B=np.load(P/'baseline-inputs.npz');rows={r['key']:r for r in json.loads((P/'manifest.json').read_text())};fits=json.loads((P/'frozen-fits.json').read_text());out=json.loads((P/'results.json').read_text())['results'];preds=json.loads((P/'predictions.json').read_text());base=np.flatnonzero(D['variant']=='base');keys=D['key'][base];label=np.array([rows[k]['label'] for k in keys]);split=np.array([rows[k]['split'] for k in keys]);family=np.array([rows[k]['family'] for k in keys]);tr=(split=='train')&(label!='sdxl');cal=(split=='calibration')&(label!='sdxl');te=(split=='heldout')&(label!='sdxl');un=(split=='heldout')&(label=='sdxl');target=np.where(label=='sd15',1.,-1.);assert len(keys)==215 and te.sum()==36 and un.sum()==18
unique=np.unique(family[te]);draw=np.random.default_rng(904).integers(0,len(unique),(2000,len(unique)));assert np.array_equal(draw,np.load(P/'bootstrap-draws.npy'))
def close(a,b):assert np.allclose(a,b,rtol=2e-5,atol=2e-5),(np.max(np.abs(np.array(a)-np.array(b))))
def interval(v):
 s=np.array([v[family[te]==f].sum() for f in unique]);n=np.array([(family[te]==f).sum() for f in unique]);return np.quantile(s[draw].sum(1)/n[draw].sum(1),[.025,.975])
corrects={}
for name,fit in fits.items():
 X=D[name][base].astype(float) if name in ['learned','residual','visual'] else B['pickscore'][:,None] if name=='pickscore' else np.c_[D['visual'][base],B['pickscore']]
 mean=X[tr].mean(0);scale=X[tr].std(0);scale[scale==0]=1;close(mean,fit['mean']);close(scale,fit['scale']);z=(X-mean)/scale;zt=z[tr];zm=zt.mean(0);yc=target[tr]-target[tr].mean();zc=zt-zm
 best=None
 for alpha in [100,10,1,.1]:
  # Independent dual-form ridge solve, intercept from centered train data.
  coef=zc.T@np.linalg.solve(zc@zc.T+alpha*np.eye(tr.sum()),yc);intercept=float(target[tr].mean()-zm@coef);score=z[cal]@coef+intercept;acc=np.mean(np.where(score>0,'sd15','sd14')==label[cal])
  if best is None or acc>best[0]:best=(acc,alpha,coef,intercept)
 acc,alpha,coef,intercept=best;assert alpha==fit['alpha'];close(acc,fit['calibration_accuracy']);close(coef,fit['coef']);close(intercept,fit['intercept']);cent=np.stack([z[tr&(label==c)].mean(0) for c in ['sd14','sd15']]);close(cent,fit['centroids']);dist=lambda a:np.sqrt(((a[:,None,:]-cent)**2).mean(2)).min(1);threshold=np.quantile(dist(z[cal]),.95,method='higher');close(threshold,fit['rejection_threshold'])
 for variant,r in out[name].items():
  if not isinstance(r,dict):continue
  xx=X.copy()
  if variant!='base':
   for i,k in enumerate(keys):
    if split[i]=='heldout':xx[i]=D[name][np.flatnonzero((D['key']==k)&(D['variant']==variant))[0]]
  zz=(xx-mean)/scale;score=zz@coef+intercept;guess=np.where(score>0,'sd15','sd14');distance=dist(zz);accept=distance<=threshold;c=(guess[te]==label[te]).astype(int);corrects[name,variant]=c
  assert int(c.sum())==r['correct'] and r['n']==36;close(c.mean(),r['balanced_accuracy']);close(interval(c),r['cluster_ci95']);assert int((~accept[te]).sum())==r['known_false_rejections'];assert int(accept[te].sum())==r['known_accepted'];assert int(accept[un].sum())==r['unknown_accepted'];assert int((~accept[un]).sum())==r['unknown_rejected']
  confusion=[[int(((label[te]==a)&(guess[te]==b)).sum()) for b in ['sd14','sd15']] for a in ['sd14','sd15']];assert confusion==r['confusion']
  pp=[p for p in preds if p['feature']==name and p['variant']==variant];assert len(pp)==54
  for p,i in zip(pp,np.flatnonzero(te|un)):
   assert p['key']==keys[i] and p['prediction']==guess[i] and p['accepted']==bool(accept[i]);close(p['score'],score[i]);close(p['distance'],distance[i])
  assert r['primary_pass']==bool(c.mean()>=.75 and interval(c)[0]>.5 and (~accept[te]).mean()<=.1)
for name in fits:
 for v,r in out[name].items():
  if not isinstance(r,dict):continue
  delta=corrects[name,v]-corrects['pickscore','base'];pair=r['paired_vs_pickscore_base'];assert pair['improved']==int((delta>0).sum()) and pair['worsened']==int((delta<0).sum());close(pair['delta'],delta.mean());close(pair['cluster_ci95'],interval(delta))
for n,h in json.loads((P/'bundle-files.json').read_text()).items():assert hashlib.sha256((P/n).read_bytes()).hexdigest()==h,n
if '--originals' in sys.argv:
 src=P.parents[1]/'judge-score-fingerprinting-poc';hashes=json.loads((P/'original-hashes.json').read_text())
 for n,h in hashes.items():assert hashlib.sha256((src/n).read_bytes()).hexdigest()==h,n
print('PASS: independent fits, selected alphas, tolerant floats, exact predictions/counts, conditional paired bootstrap, artifact hashes'+('; original sources unchanged' if '--originals' in sys.argv else ''))
