import pathlib,json,time
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import RidgeClassifier
from sklearn.metrics import confusion_matrix
P=pathlib.Path(__file__).resolve().parent;SRC=P.parents[1]/'judge-score-fingerprinting-poc/2026-10-25'
def dump(n,x):(P/n).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def main():
 start=time.time();d=np.load(P/'features.npz');old=np.load(SRC/'local-scores.npz');rows=json.loads((P/'manifest.json').read_text());base=np.flatnonzero(d['variant']=='base');keys=d['key'][base];by={r['key']:r for r in rows};labels=np.array([by[k]['label'] for k in keys]);splits=np.array([by[k]['split'] for k in keys]);family=np.array([by[k]['family'] for k in keys]);known=labels!='sdxl';tr=known&(splits=='train');cal=known&(splits=='calibration');te=known&(splits=='heldout');unk=(~known)&(splits=='heldout');y=(labels=='sd15').astype(int)
 oi=np.array([np.flatnonzero((old['keys']==k)&(old['variants']=='base'))[0] for k in keys]);pick=old['pickscore'][oi,None]
 # Existing preference scores reused, heads and numerical comparisons recomputed on identical primary samples. No judge inference.
 features={'learned':d['learned'][base],'residual':d['residual'][base],'pickscore':pick,'visual':d['visual'][base],'visual+pickscore':np.c_[d['visual'][base],pick]};fits={}
 for name,X in features.items():
  sc=StandardScaler().fit(X[tr]);z=sc.transform(X);best=None
  for alpha in [100,10,1,.1]:
   clf=RidgeClassifier(alpha=alpha).fit(z[tr],labels[tr]);acc=float(np.mean(clf.predict(z[cal])==labels[cal]))
   if best is None or acc>best[0]:best=(acc,alpha,clf)
  acc,alpha,clf=best;cent=np.stack([z[tr&(labels==c)].mean(0) for c in ['sd14','sd15']]);dist=lambda a:np.sqrt(((a[:,None,:]-cent[None,:,:])**2).mean(2)).min(1)
  threshold=float(np.quantile(dist(z[cal]),.95,method='higher'))
  fits[name]=dict(alpha=alpha,calibration_accuracy=acc,mean=sc.mean_.tolist(),scale=sc.scale_.tolist(),coef=np.asarray(clf.coef_).reshape(-1).tolist(),intercept=float(np.asarray(clf.intercept_).reshape(-1)[0]),centroids=cent.tolist(),rejection_threshold=threshold,calibration_rejected=int((dist(z[cal])>threshold).sum()),calibration_n=int(cal.sum()))
 dump('frozen-fits.json',fits) # No heldout metrics have been computed above.
 families=np.unique(family[te]);draws=np.random.default_rng(904).integers(0,len(families),(2000,len(families)));np.save(P/'bootstrap-draws.npy',draws)
 def ci(values):
  sums=np.array([values[family[te]==f].sum() for f in families]);ns=np.array([(family[te]==f).sum() for f in families]);return np.quantile(sums[draws].sum(1)/ns[draws].sum(1),[.025,.975]).tolist()
 results={};predictions=[];corrects={}
 for name,fit in fits.items():
  results[name]={}
  for v in (['base','jpeg85','resize256'] if name in ['learned','residual','visual'] else ['base']):
   X=features[name].copy()
   if v!='base':
    for i,k in enumerate(keys):
     if splits[i]=='heldout':X[i]=d[name][np.flatnonzero((d['key']==k)&(d['variant']==v))[0]]
   z=(X-np.array(fit['mean']))/np.array(fit['scale']);score=z@fit['coef']+fit['intercept'];pred=np.where(score>0,'sd15','sd14');cent=np.array(fit['centroids']);distance=np.sqrt(((z[:,None,:]-cent[None,:,:])**2).mean(2)).min(1);accepted=distance<=fit['rejection_threshold'];correct=(pred[te]==labels[te]);corrects[name,v]=correct.astype(int)
   r=dict(n=int(te.sum()),correct=int(correct.sum()),balanced_accuracy=float(np.mean([np.mean(pred[te&(labels==c)]==c) for c in ['sd14','sd15']])),cluster_ci95=ci(correct),confusion=confusion_matrix(labels[te],pred[te],labels=['sd14','sd15']).tolist(),known_accepted=int(accepted[te].sum()),known_false_rejections=int((~accepted[te]).sum()),known_false_rejection_rate=float((~accepted[te]).mean()),known_coverage=float(accepted[te].mean()),unknown_n=int(unk.sum()),unknown_accepted=int(accepted[unk].sum()),unknown_rejected=int((~accepted[unk]).sum()),unknown_rejection_rate=float((~accepted[unk]).mean()))
   r['primary_pass']=r['balanced_accuracy']>=.75 and r['cluster_ci95'][0]>.5 and r['known_false_rejection_rate']<=.10
   results[name][v]=r
   for i in np.flatnonzero(te|unk):predictions.append(dict(feature=name,variant=v,key=str(keys[i]),family=str(family[i]),truth=str(labels[i]),prediction=str(pred[i]),score=float(score[i]),distance=float(distance[i]),accepted=bool(accepted[i])))
 for name in results:
  for v,r in results[name].items():
   c=corrects[name,v];b=corrects['pickscore','base'];delta=c-b;r['paired_vs_pickscore_base']=dict(improved=int((delta>0).sum()),worsened=int((delta<0).sum()),delta=float(delta.mean()),cluster_ci95=ci(delta),comparison='same 36 images; transformed representation vs original PickScore for robustness')
 for name in ['learned','residual']:
  for v in ['jpeg85','resize256']:results[name][v]['loss_pp']=100*(results[name]['base']['balanced_accuracy']-results[name][v]['balanced_accuracy'])
  results[name]['screen_verdict']='progress lead; fresh confirmation required' if all(results[name][v]['primary_pass'] for v in ['base','jpeg85','resize256']) and all(results[name][v]['loss_pp']<=15 for v in ['jpeg85','resize256']) else 'reject as inadequate on this exploratory screen'
 dump('predictions.json',predictions);dump('results.json',dict(results=results,n_usable=len(rows),primary_heldout=int(te.sum()),unknown_heldout=int(unk.sum()),heldout_families=families.tolist(),analysis_seconds=time.time()-start,exploratory=True,conditional_bootstrap=True))
 print(json.dumps({n:{v:r.get('balanced_accuracy') if isinstance(r,dict) else r for v,r in rs.items()} for n,rs in results.items()},indent=2))
if __name__=='__main__':main()
