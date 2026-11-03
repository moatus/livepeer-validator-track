import pathlib,json,hashlib,time,tarfile,platform,subprocess
import numpy as np
P=pathlib.Path(__file__).resolve().parent;SRC=P.parents[1]/'judge-score-fingerprinting-poc'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,x):(P/n).write_text(json.dumps(x,indent=2)+'\n')
results=json.loads((P/'results.json').read_text());pred=json.loads((P/'predictions.json').read_text());draw=np.load(P/'bootstrap-draws.npy');families=results['heldout_families'];uncertainty={}
for name,rs in results['results'].items():
 uncertainty[name]={}
 for v,r in rs.items():
  if not isinstance(r,dict):continue
  pp=[p for p in pred if p['feature']==name and p['variant']==v];u={}
  for group in ['known','unknown']:
   qq=[p for p in pp if (p['truth']=='sdxl')==(group=='unknown')];n=np.array([sum(p['family']==f for p in qq) for f in families]);rej=np.array([sum(p['family']==f and not p['accepted'] for p in qq) for f in families]);rates=rej[draw].sum(1)/n[draw].sum(1);u[group]=dict(n=len(qq),rejected=int(rej.sum()),rejection_cluster_ci95=np.quantile(rates,[.025,.975]).tolist(),coverage_cluster_ci95=np.quantile(1-rates,[.025,.975]).tolist())
  uncertainty[name][v]=u
dump('uncertainty.json',dict(method='same 2000 whole-family draws seed904; conditional, not general confidence',results=uncertainty))
# Freeze a self-contained numerical artifact manifest; weights and environments never enter the bundle.
(P/'hardware.txt').write_text(subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,memory.used','--format=csv'],text=True)+subprocess.check_output(['df','-h',str(P)],text=True))
dump('actual-runtime.json',dict(wall_seconds_so_far=time.time()-float((P/'started.txt').read_text()),extraction=json.loads((P/'extraction-runtime.json').read_text()),analysis_seconds=results['analysis_seconds'],python=platform.python_version(),readiness_minutes_upper_bound=( (P/'PROTOCOL.json').stat().st_mtime-float((P/'started.txt').read_text()))/60,checkpoint_downloads=1,new_environments=0,packages_installed=0,judges=0,generators=0))
# Source integrity is independently rechecked by verify.py --originals; declaration only finalized after that succeeds.
files={str(f.relative_to(P)):sha(f) for f in P.rglob('*') if f.is_file() and f.name not in ['bundle-files.json','dragon_25class.pt','review-bundle.tar.gz','review-bundle.sha256','verification.log','integrity-final.json'] and '__pycache__' not in f.parts}
dump('bundle-files.json',files)
