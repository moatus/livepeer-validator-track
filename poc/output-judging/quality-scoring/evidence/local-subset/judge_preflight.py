"""Recheck declared public contracts only. Never uploads or submits inference.

No account/credential provisioning; no keyless demo spending. Evidence is written
under a fresh timestamp so the original discovery evidence is never overwritten.
"""
import pathlib,json,datetime,urllib.request
P=pathlib.Path(__file__).resolve().parent
OUT=P/('preflight-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));OUT.mkdir(exist_ok=False)
endpoint='https://agent.livepeer.org/api/mcp'
queries=[('tools','tools/list',{}),('describe','tools/call',{'name':'describe_capability','arguments':{'name':'nemotron-omni-vision'}}),('pricing','tools/call',{'name':'get_pricing','arguments':{'name':'nemotron-omni-vision','bypass_cache':True}})]
for name,method,params in queries:
 req=urllib.request.Request(endpoint,data=json.dumps(dict(jsonrpc='2.0',id='judge004-readonly-'+name,method=method,params=params)).encode(),headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'})
 try:
  with urllib.request.urlopen(req,timeout=30) as r:body=r.read()
  (OUT/(name+'.raw')).write_bytes(body);print(name,'saved')
 except Exception as e:(OUT/(name+'.error')).write_text(type(e).__name__+': '+str(e));print(name,'failed',type(e).__name__)
print('No inference submitted. Authenticated access and current price bounds must be established separately.')
