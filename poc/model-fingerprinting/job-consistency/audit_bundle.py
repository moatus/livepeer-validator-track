"""Run the exported verifier with a read-access audit hook.
Logical separation only: this is not a security sandbox or OS isolation.
"""
import sys,pathlib,runpy,json,time
P=pathlib.Path(__file__).resolve().parent;B=P/'bundle';sys.dont_write_bytecode=True
reads=[]
def audit(event,args):
 if event!='open' or not isinstance(args[0],(str,bytes)):return
 try:p=pathlib.Path(args[0]).resolve()
 except (ValueError,TypeError):return
 mode=args[1]
 if isinstance(mode,str) and any(x in mode for x in ['w','a','x','+']):return
 if p.is_relative_to(P) and not p.is_relative_to(B):raise RuntimeError('Verifier attempted read outside exported bundle')
 reads.append(str(p))
sys.path.insert(0,str(B));sys.argv=[str(B/'verifier.py'),str(B),'--output',str(P/'audit-decisions.json')]
sys.addaudithook(audit)
t=time.perf_counter();runpy.run_path(str(B/'verifier.py'),run_name='__main__');elapsed=time.perf_counter()-t
# Read after execution only, for audit report. The verifier has finished.
(P/'access-audit.json').write_text(json.dumps(dict(seconds_including_imports=elapsed,bundle_data_reads=sorted({x for x in reads if pathlib.Path(x).is_relative_to(B)}),private_reads=[],external_reads=sorted({x for x in reads if not pathlib.Path(x).is_relative_to(B)}),logical_separation_only=True),indent=2)+'\n')
print('Artifact-only execution completed with private experiment reads forbidden')
