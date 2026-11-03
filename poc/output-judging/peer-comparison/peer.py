import numpy as np,itertools
EPS=1e-12
def peer(vectors,threshold):
 x=np.asarray(vectors,dtype=np.float64);assert x.ndim==2 and x.shape[0]==4 and np.isfinite(x).all();norm=np.linalg.norm(x,axis=1);assert (norm>0).all();x=x/norm[:,None]
 d=np.clip(1-x@x.T,0,2);np.fill_diagonal(d,0)
 s=[]
 for i in range(4):
  others=[j for j in range(4) if j!=i];den=np.median([d[j,k] for j,k in itertools.combinations(others,2)]);s.append(float(min(d[i,j] for j in others)/max(den,EPS)))
 winners=np.flatnonzero(np.array(s)==max(s));candidate=int(winners[0]) if len(winners)==1 else None
 return dict(distances=d.tolist(),scores=s,candidate=candidate,decision=candidate if candidate is not None and s[candidate]>threshold else 'no clear outlier')
def tests():
 equal=peer(np.ones((4,8)),0);assert equal['candidate'] is None and equal['decision']=='no clear outlier'
 x=np.array([[1,0,.01],[1,.01,0],[1,-.01,0],[0,0,1.]])
 r=peer(x,2);assert r['decision']==3
 for perm in itertools.permutations(range(4)):
  q=peer(x[list(perm)],2);assert q['decision']==perm.index(3);assert np.allclose(q['scores'],np.array(r['scores'])[list(perm)])
 return dict(equal_abstention=True,separated_outlier=True,permutations=24,feature_schema='peer receives only a finite 4xD numeric matrix and scalar threshold; no metadata')
if __name__=='__main__':print(tests())
