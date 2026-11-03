"""Exercise the real local job router. Fresh output directory on each invocation."""
import os,json,pathlib,subprocess,socket,time,ssl,urllib.request,threading,tempfile,shutil,resource,hashlib
from datetime import datetime
R=pathlib.Path('runs/phase-28')/('fixture-'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime()));R.mkdir(parents=True,exist_ok=False)
B=str(pathlib.Path('target/release/witness').resolve());BASE=pathlib.Path('runs/phase-22').resolve();CA=pathlib.Path('target/tlsn-src/crates/server-fixture/certs/src/tls/root_ca.crt').resolve()
ENV={k:v for k,v in os.environ.items() if k not in ('OPENROUTER_API_KEY','OPENROUTER_MANAGEMENT_KEY')};ENV.update(RUST_LOG='warn',MALLOC_ARENA_MAX='2',RAYON_NUM_THREADS='2',HARDWARE_CONCURRENCY='2')
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:16]);children=[]
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def bound():resource.setrlimit(resource.RLIMIT_AS,(10_000_000_000,10_000_000_000))
def launch(name,cmd):
 p=subprocess.Popen(cmd,env=ENV,stdout=(R/(name+'.log')).open('w'),stderr=subprocess.STDOUT,preexec_fn=bound);children.append(p);save(R/(name+'.command.json'),dict(command=cmd,pid=p.pid,affinity=sorted(os.sched_getaffinity(0)),address_space_cap=10_000_000_000));return p
def port(n):
 try:s=socket.create_connection(('127.0.0.1',n),.1);s.close();return True
 except OSError:return False
def wait(n):
 for _ in range(100):
  if port(n):return
  time.sleep(.1)
 raise RuntimeError('port timeout '+str(n))
def stop(p):
 if p.poll() is None:p.terminate();p.wait(15)
context=ssl.create_default_context(cafile=str(CA));context.check_hostname=False
trust={'v':1,'witnesses':[{'label':'local witness shares operator host; not independent','public_key':(BASE/'witness-b.pub').read_text().strip()}],'operators':[(BASE/'operator.pub').read_text().strip()],'server_name':'test-server.io','path':'/jobs'}
def events():return [json.loads(l) for l in (R/'events.jsonl').read_text().splitlines()]
def client(label):
 d=R/label/'client';d.mkdir(parents=True)
 body=json.dumps({'model':'fixture','input':label,'fixture_mode':label},separators=(',',':')).encode()
 raw=(f'POST /jobs HTTP/1.1\r\nHost: router\r\nContent-Type: application/json\r\nX-Client-Nonce: {label}\r\nX-Client-Require-Witness: true\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n').encode()+body
 (d/'request.http').write_bytes(raw);start=time.time_ns();parts=[]
 with socket.create_connection(('127.0.0.1',8087)) as s:
  s.settimeout(90);s.sendall(raw)
  while True:
   part=s.recv(65536)
   if not part:break
   parts.append(part)
 response_end=time.time_ns();res=b''.join(parts);(d/'response.http').write_bytes(res)
 rid=next(l.split(b':',1)[1].strip().decode() for l in res.split(b'\r\n\r\n')[0].split(b'\r\n') if l.lower().startswith(b'x-witness-receipt:'))
 for _ in range(1400):
  with urllib.request.urlopen('http://127.0.0.1:8087/evidence/'+rid,timeout=5) as f:e=json.load(f)
  if e['state']!='pending':break
  time.sleep(.05)
 else:raise RuntimeError('pending timeout')
 save(d/'package.json',e);save(d/'trust.json',trust);save(d/'timestamps.json',dict(start_unix_ns=start,response_end_unix_ns=response_end,end_unix_ns=time.time_ns()))
 clean=pathlib.Path(tempfile.mkdtemp(prefix='tlsw-job-',dir='/tmp'))
 for n in ('package.json','request.http','response.http','trust.json'):shutil.copy2(d/n,clean/n)
 p=subprocess.run([B,'check','--evidence','package.json','--client-request','request.http','--client-response','response.http','--trust-list','trust.json'],cwd=clean,capture_output=True,text=True)
 checked=json.loads(p.stdout);save(d/'check.json',dict(checked,clean_directory=str(clean)))
 return dict(case=label,receipt_id=rid,check=checked,state=e['state'])
rows=[]
source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
save(R/'build-identity.json',dict(source_commit=source_commit,binary_sha256=hashlib.sha256(pathlib.Path(B).read_bytes()).hexdigest(),cargo_lock_sha256=hashlib.sha256(pathlib.Path('Cargo.lock').read_bytes()).hexdigest(),tlsn_tag='v0.1.0-alpha.15',allowed_diffs=['patch/tlsn-mux-stream-cap.diff','patch/tlsn-session-frame-limit.diff'],new_crates=0))
try:
 assert not any(port(p) for p in (4017,7049,8087))
 common={'host':'test-server.io','address':'127.0.0.1:4017'}
 save(R/'obtain.json',common|{'method':'POST','path':'/keys','credential_field':'/key','body':{'include_byok_in_limit':True,'limit':.05}})
 save(R/'revoke.json',common|{'method':'PATCH','path':'/keys/{obtain:/data/hash}','body':{'disabled':True}})
 save(R/'probe.json',common|{'method':'POST','path':'/probe','fixture_model':'fixture'})
 fixture=launch('fixture',['python3','-u','tools/job_fixture.py',str(R)])
 for _ in range(100):
  if (R/'fixture.log').read_text().strip():break
  time.sleep(.1)
 witness=launch('witness',[B,'verifier','--credential-handling','revealed','--listen','127.0.0.1:7049','--key',str(BASE/'witness-b.key'),'--roots',str(CA),'--operator-pub',str(BASE/'operator.pub'),'--resolve','test-server.io=127.0.0.1:4017','--max-sent','65536','--max-recv','262144','--threads','1','--allow-server','test-server.io','--record-dir',str(R/'witness')]);wait(7049)
 router=launch('router',[B,'router','--job','--path','/jobs','--listen','127.0.0.1:8087','--operator-key',str(BASE/'operator.key'),'--host','test-server.io','--witness','127.0.0.1:7049','--ca-cert',str(CA),'--obtain-request',str(R/'obtain.json'),'--revoke-request',str(R/'revoke.json'),'--dead-check-request',str(R/'probe.json'),'--max-sent','65536','--max-recv','262144','--session-timeout','45','--evidence-deadline','90','--admission-log',str(R/'admissions.jsonl'),'--record-dir',str(R/'receipts')]);wait(8087)
 for label in ('normal-a','normal-b','pending','bad-digest','cut'):
  if label=='cut':
   result=[];error=[]
   def work():
    try:result.append(client(label))
    except Exception as e:error.append(e)
   previous={e.get('receipt_id') for e in events() if e['event']=='submit'}
   t=threading.Thread(target=work);t.start()
   until=time.monotonic()+30
   while not [e for e in events() if e['event']=='submit' and e.get('receipt_id') not in previous]:
    assert time.monotonic()<until;time.sleep(.005)
   submit=next(e for e in events() if e['event']=='submit' and e.get('receipt_id') not in previous)
   directory=R/'receipts'/submit['receipt_id']/'step-1'
   while not list(directory.glob('*.receipt.json')) or not list(directory.glob('*.verdict.json')):
    assert time.monotonic()<until;time.sleep(.002)
   signed_at=time.time_ns()
   while not [e for e in events() if e['event']=='authentication' and e.get('receipt_id')==submit['receipt_id'] and e['target'].endswith('/poll') and e['accepted']]:
    assert time.monotonic()<until;time.sleep(.002)
   auth=next(e for e in events() if e['event']=='authentication' and e.get('receipt_id')==submit['receipt_id'] and e['target'].endswith('/poll') and e['accepted'])
   save(R/'cut-trigger.json',dict(receipt_id=submit['receipt_id'],signed_submit_observed_unix_ns=signed_at,submit_receipt=str(next(directory.glob('*.receipt.json'))),submit_verdict=str(next(directory.glob('*.verdict.json'))),first_poll_authentication=auth,witness_stop_requested_unix_ns=time.time_ns()))
   stop(witness);t.join(60);assert not t.is_alive()
   if error:raise error[0]
   row=result[0]
  else:row=client(label)
  ev=[e for e in events() if e.get('receipt_id')==row['receipt_id']]
  counts={kind:sum(e['event']==kind for e in ev) for kind in ('submit','poll','fetch')}
  row['fixture_counts']=counts
  assert counts['submit']==1
  if label.startswith('normal'):assert row['check']['result']=='PASS' and counts==dict(submit=1,poll=1,fetch=1)
  if label=='pending':assert row['check']['result']=='PASS' and counts['poll']>=2
  if label=='bad-digest':
   assert row['state']=='unverified' and row['check']['result']=='UNVERIFIED'
   package=json.loads((R/label/'client'/'package.json').read_text())
   assert 'digest mismatch' in package['reason'] and (R/label/'client'/'response.http').read_bytes().endswith(b' corrupted')
  if label=='cut':assert row['state']=='unverified' and row['check']['result']=='UNVERIFIED' and counts==dict(submit=1,poll=1,fetch=0)
  rows.append(row);save(R/'results.json',rows);print(json.dumps(row),flush=True)
 recon=subprocess.run([B,'reconcile','--admission-log',str(R/'admissions.jsonl'),'--record-dir',str(R/'receipts')],capture_output=True,text=True);save(R/'reconciliation.json',json.loads(recon.stdout));assert recon.returncode==0
 with urllib.request.urlopen('https://127.0.0.1:4017/state',context=context) as f:state=json.load(f)
 save(R/'final-state.json',state);assert all(e['disabled'] for e in state['credentials'])
 # Measurements come from the binary's session records, not estimated timings.
 measurements=[]
 def ns(text):return int(datetime.fromisoformat(text.replace('Z','+00:00')).timestamp()*1e9)
 for row in rows:
  directory=R/'receipts'/row['receipt_id'];records=[json.loads(p.read_text()) for p in sorted(directory.glob('step-*/*.record.json'))]
  e=json.loads((directory/'evidence.json').read_text());sessions=[]
  for record in records:
   seq=record['detail']['credential_sequence'];checks=seq['dead_checks']
   sessions.append(dict(obtained_at=seq['obtained_at'],confirmed_dead_at=checks[-1]['response_received_at'] if checks and checks[-1]['consecutive_refusals']==2 else None,credential_lifetime_ms=(ns(checks[-1]['response_received_at'])-ns(seq['obtained_at']))/1e6 if checks else None,credential_state=seq['credential_status'],obtain_ms=seq['obtain_ms'],revoke_ms=seq['revoke_ms'],dead_check_window_ms=seq.get('second_consecutive_refusal_ms'),resources=record['resources'],sequence=seq))
  final_response=records[-1]['exchanges'][0].get('response_received_at')
  measurements.append(dict(case=row['case'],sessions=sessions,evidence_delay_after_last_upstream_response_ms=(ns(e['terminal_at'])-ns(final_response))/1e6 if final_response else None,router_peak_rss_mib=max(r['resources']['peak_rss_mb'] for r in records),retention=json.loads((directory/'retention.json').read_text()) if (directory/'retention.json').exists() else None))
 witness_records=[json.loads(p.read_text()) for p in (R/'witness').glob('*.record.json')]
 save(R/'measurements.json',dict(chains=measurements,witness_peak_rss_mib=max(r['resources']['peak_rss_mb'] for r in witness_records if 'resources' in r),provider_requests=0,spend_usd=0))
 save(R/'acceptance.json',dict(criteria={str(n):'PASS' for n in (1,3,4)},all_credentials_disabled=True))
 subprocess.run(['python3','tools/summarize_job_fixture.py',str(R)],check=True)
except Exception as ex:save(R/'failure.json',dict(type=type(ex).__name__,reason=str(ex)));raise
finally:
 for p in reversed(children):stop(p)
 save(R/'shutdown.json',dict(router_port_open=port(8087),witness_port_open=port(7049),fixture_port_open=port(4017)))
print(str(R),flush=True)
