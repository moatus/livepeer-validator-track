"""Generate profile evidence samples from retained real local router captures.
Usage: python3 tools/generate_evidence_samples.py RUN_DIRECTORY
No signing seeds are read; the captures supply genuine witness signatures.
"""
import pathlib,json,copy,shutil,subprocess,tempfile,sys,re
R=pathlib.Path(sys.argv[1]);S=pathlib.Path('samples/evidence');B=str(pathlib.Path('target/release/witness').resolve())
def load(p):return json.loads(p.read_text())
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def source(name):
 d=R/name/'client';return [load(d/'package.json'),(d/'request.http').read_bytes(),(d/'response.http').read_bytes()]
a=source('full-disclosure-fixture-success');b=source('credential-hidden-success');un=source('full-disclosure-fixture-off-allowlist')
trust=load(R/'full-disclosure-fixture-success/client/trust.json')
other=load(R/'credential-hidden-success/client/trust.json')
trust['witnesses']+=other['witnesses'];trust['operators']+=other['operators']
cases={}
def case(name,base=a,result='FAIL',link=None):
 profile=base[0].get('receipt',{}).get('verdict',{}).get('profile') if result=='PASS' or link in ('session','operator_identity','destination','request_match','forwarded_headers','response_delivery') else None
 value=copy.deepcopy(base)+[copy.deepcopy(trust),{'result':result,'link':link,'profile':profile}];cases[name]=value;return value
case('normal-a',result='PASS');case('normal-b',b,result='PASS')
c=case('body',link='request_match');c[1]=c[1].replace(b'"pong"',b'"ping"')
c=case('header-added',link='forwarded_headers');c[1]=c[1].replace(b'\r\n\r\n',b'\r\nX-Client-Added: yes\r\n\r\n',1)
c=case('header-changed',link='forwarded_headers');c[1]=c[1].replace(b'X-Client-Note: first',b'X-Client-Note: other')
c=case('response-body',link='response_delivery');c[2]=c[2].replace(b'fixture pong',b'fixture ping')
c=case('response-status',link='response_delivery');c[2]=c[2].replace(b'HTTP/1.1 200',b'HTTP/1.1 201',1)
c=case('response-type',link='response_delivery');c[2]=c[2].replace(b'application/json',b'application/text',1)
c=case('operator',link='operator_identity');c[3]['operators']=[b[0]['witness_key_id']]
c=case('witness',link='witness_signature');c[0]['receipt']['verdict']['mode']='edited-with-original-signature'
c=case('receipt-swap',link='receipt_match');c[0]=copy.deepcopy(b[0])
c=case('receipt-swap-outer-rewritten',link='receipt_match');c[0]=copy.deepcopy(b[0]);c[0]['receipt_id']=a[0]['receipt_id'];c[4]['profile']=b[0]['receipt']['verdict']['profile']
c=case('untrusted-witness',b,link='witness_signature');c[3]['witnesses']=[c[3]['witnesses'][0]]
c=case('old-operator-statement',b,link='operator_identity');c[0]['operator_statement']=copy.deepcopy(a[0]['operator_statement'])
c=case('nonce-with-old-receipt',link='forwarded_headers');c[1]=c[1].replace(b'\r\n\r\n',b'\r\nX-Client-Nonce: 8c1869b78f5e4a41a5ee32f6f6b866d2\r\n\r\n',1)
case('no-nonce-old-matching-receipt',result='PASS');case('unverified',un,result='UNVERIFIED')
c=case('destination-host',link='destination');c[3]['server_name']='other.example'
c=case('destination-path',link='destination');c[3]['path']='/other/path'
c=case('pending',link='evidence_pending');c[0]['state']='pending'
c=case('unverified-null-receipt',un,link='evidence');c[0]['receipt']=None
# Universal forgery, no signing key: A = identity, R = identity, S = 0.
c=case('identity-key-forgery',link='witness_signature')
identity='01'+'00'*31
c[0]['receipt']['verdict']['verifier_pub']=identity
c[0]['receipt']['verdict']['sig']=identity+'00'*32
c[0]['witness_key_id']=identity
c[3]['witnesses']=[{'label':'TEST ONLY: small-order identity; never trust','public_key':identity,'profiles':['full-disclosure-fixture']}]
c=case('request-signed-length',link='request_match');c[1]=re.sub(rb'Content-Length: (\d+)',rb'Content-Length: +\1',c[1],count=1)
c=case('response-signed-length',link='response_delivery');c[2]=re.sub(rb'Content-Length: (\d+)',rb'Content-Length: +\1',c[2],count=1)
c=case('request-bare-lf',result='PASS');head,body=c[1].split(b'\r\n\r\n',1);c[1]=head.replace(b'\r\n',b'\n')+b'\n\n'+body
c=case('response-bare-lf',result='PASS');head,body=c[2].split(b'\r\n\r\n',1);c[2]=head.replace(b'\r\n',b'\n')+b'\n\n'+body
c=case('response-short-status',link='receipt_match');c[2]=c[2].replace(b'HTTP/1.1 200',b'HTTP/1.1 20',1)
c=case('response-non-utf8-header',link='receipt_match');c[2]=c[2].replace(b'\r\n\r\n',b'\r\nX-Unused: \xff\r\n\r\n',1)
c=case('request-non-utf8-header',link='request_match');c[1]=c[1].replace(b'\r\n\r\n',b'\r\nX-Unused: \xff\r\n\r\n',1)
case('full-disclosure-receipt',a,result='PASS')
case('credential-hidden-receipt',b,result='PASS')
for name,base,rejected in [('full-disclosure-profile-not-accepted',a,'credential-hidden'),('credential-hidden-profile-not-accepted',b,'full-disclosure-fixture')]:
 c=case(name,base,link='session')
 for w in c[3]['witnesses']:w['profiles']=[rejected]
c=case('session-swap',link='inclusion');c[0]['receipt']['verdict']=copy.deepcopy(b[0]['receipt']['verdict'])
for profile,base in [('full-disclosure',a),('credential-hidden',b)]:
 c=case(profile+'-altered-request',base,link='request_match');c[1]=c[1].replace(b'"pong"',b'"ping"')
 c=case(profile+'-altered-response',base,link='response_delivery');c[2]=c[2].replace(b'fixture pong',b'fixture ping')
 c=case(profile+'-wrong-trust-server',base,link='destination');c[3]['server_name']='another.example'
 c=case(profile+'-receipt-swap',base,link='receipt_match');c[0]=copy.deepcopy(b[0] if base is a else a[0])
 c=case(profile+'-session-swap',base,link='inclusion');c[0]['receipt']['verdict']=copy.deepcopy((b[0] if base is a else a[0])['receipt']['verdict'])
for name,base,changed in [('full-disclosure-profile-edit',a,'credential-hidden'),('credential-hidden-profile-edit',b,'full-disclosure-fixture')]:
 c=case(name,base,link='witness_signature');c[0]['receipt']['verdict']['profile']=changed
# The hidden placement is part of the authenticated exchange record.
if (R/'x-api-key-success/client/package.json').exists():
 x=source('x-api-key-success')
 xt=load(R/'x-api-key-success/client/trust.json')
 trust['witnesses']+=xt['witnesses'];trust['operators']+=xt['operators']
 # Earlier cases took their own policy copies.
 for value in cases.values():
  value[3]['witnesses']+=copy.deepcopy(xt['witnesses'])
  value[3]['operators']+=copy.deepcopy(xt['operators'])
 case('x-api-key-receipt',x,result='PASS')
 c=case('x-api-key-altered-request',x,link='request_match');c[1]=c[1].replace(b'"pong"',b'"ping"')
 c=case('x-api-key-altered-response',x,link='response_delivery');c[2]=c[2].replace(b'fixture pong',b'fixture ping')
 c=case('x-api-key-wrong-trust-server',x,link='destination');c[3]['server_name']='another.example'
 c=case('x-api-key-receipt-swap',x,link='receipt_match');c[0]=copy.deepcopy(b[0])
 c=case('x-api-key-session-swap',x,link='inclusion');c[0]['receipt']['verdict']=copy.deepcopy(b[0]['receipt']['verdict'])
 c=case('x-api-key-profile-not-accepted',x,link='session')
 for w in c[3]['witnesses']:w['profiles']=['full-disclosure-fixture']
 c=case('x-api-key-profile-edit',x,link='witness_signature');c[0]['receipt']['verdict']['profile']='full-disclosure-fixture'
 c=case('x-api-key-placement-edit',x,link='inclusion');c[0]['receipt']['record']['request']['withheld']['header']='authorization'

# These labelled TEST ONLY signatures test offline metadata policy, not TLS
# witnessing. They never substitute for genuine positive fixture captures.
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
seed=Ed25519PrivateKey.generate()
pub=seed.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def resign(value):
 package=value[0];receipt=package['receipt'];verdict=receipt['verdict']
 verdict['root']=__import__('hashlib').sha256(canonical(receipt['record'])).hexdigest()
 verdict['verifier_pub']=pub;package['witness_key_id']=pub
 verdict.pop('sig',None);verdict['sig']=seed.sign(canonical(verdict)).hex()
 value[3]['witnesses']=[{'label':'TEST ONLY: metadata policy; re-signed fixture record; no new TLS observation','public_key':pub,'profiles':[verdict['profile']]}]
for name in ('withheld-empty-range','withheld-under-full-disclosure','withheld-unknown-header','withheld-missing-header'):
 c=case(name,b,link='inclusion' if name=='withheld-missing-header' else 'session')
 withheld=c[0]['receipt']['record']['request']['withheld']
 if name=='withheld-empty-range':withheld['end']=withheld['start']
 elif name=='withheld-under-full-disclosure':c[0]['receipt']['verdict']['profile']='full-disclosure-fixture';c[4]['profile']='full-disclosure-fixture'
 elif name=='withheld-unknown-header':withheld['header']='cookie'
 else:del withheld['header']
 resign(c)
S.mkdir(parents=True,exist_ok=True);results=[]
for name,(package,req,res,policy,expected) in cases.items():
 d=S/name;d.mkdir(exist_ok=True);save(d/'package.json',package);(d/'request.http').write_bytes(req);(d/'response.http').write_bytes(res);save(d/'trust.json',policy);save(d/'expected.json',expected)
 fresh=pathlib.Path(tempfile.mkdtemp(prefix='tlsw-p30-generated-',dir='/tmp'))
 for p in d.iterdir():shutil.copyfile(p,fresh/p.name)
 cmd=[B,'check','--evidence','package.json','--client-request','request.http','--client-response','response.http','--trust-list','trust.json']
 p=subprocess.run(cmd,cwd=fresh,text=True,capture_output=True);got=json.loads(p.stdout);actual={'result':got['result'],'link':got.get('link'),'profile':got.get('profile')}
 assert actual==expected,(name,actual,expected,p.stderr)
 assert (p.returncode==0)==(expected['result']=='PASS')
 results.append({'case':name,'expected':expected,'actual':actual,'output':got,'returncode':p.returncode,'clean_directory':str(fresh),'files':sorted(x.name for x in fresh.iterdir())})
save(R/'sample-generation.json',results);print(json.dumps({'cases':len(results),'matched':len(results)}))
