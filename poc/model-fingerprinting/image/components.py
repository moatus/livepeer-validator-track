import pathlib,json,hashlib
from safetensors import safe_open
P=pathlib.Path(__file__).resolve().parent
records={}
for label in ['sd14','sd15']:
 records[label]={}
 for f in sorted((P/'models'/label).rglob('*.safetensors')):
  h=hashlib.sha256();count=0
  with safe_open(f,framework='pt',device='cpu') as sf:
   for key in sorted(sf.keys()):
    x=sf.get_tensor(key);h.update(key.encode());h.update(x.numpy().tobytes());count+=x.numel()
  records[label][str(f.relative_to(P/'models'/label))]=dict(tensor_content_sha256=h.hexdigest(),parameters=count)
comparison={n:records['sd14'][n]['tensor_content_sha256']==records['sd15'][n]['tensor_content_sha256'] for n in records['sd14']}
(P/'component-tensor-identities.json').write_text(json.dumps(dict(records=records,matches=comparison),indent=2));print(comparison)
