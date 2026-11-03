"""Repeat one sizing point in fresh scopes while the caller holds one batch lock."""
import argparse,pathlib,subprocess,json,time
p=argparse.ArgumentParser();p.add_argument('--binary',required=True);p.add_argument('--profile',required=True);p.add_argument('--records',required=True,type=pathlib.Path);p.add_argument('--ports-base',required=True);p.add_argument('--workload',required=True);p.add_argument('--cap',required=True);p.add_argument('--concurrency',required=True);p.add_argument('--repeats',type=int,default=3);p.add_argument('--sustained-seconds',default='0');p.add_argument('--scratch-prefix',default='tlsw-sizing-');p.add_argument('--upload-kib',default='16');p.add_argument('--rounds',default='3');a=p.parse_args()
a.records.mkdir(parents=True,exist_ok=False)
for repeat in range(1,a.repeats+1):
 subprocess.run(['python3','-B','tools/run_sizing.py','--batch','--binary',a.binary,'--profile',a.profile,'--ports-base',a.ports_base,'--records',str(a.records/f'r{repeat}'),'--workload',a.workload,'--cap',a.cap,'--concurrency',a.concurrency,'--scratch-prefix',a.scratch_prefix,'--upload-kib',a.upload_kib,'--rounds',a.rounds,'--sustained-seconds',a.sustained_seconds],check=True)
 if json.loads((a.records/f'r{repeat}'/'result.json').read_text())['verdict'] != 'PASS':
  break
