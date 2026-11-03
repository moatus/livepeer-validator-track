import os
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',CUBLAS_WORKSPACE_CONFIG=':4096:8')
import pathlib,sys,json,hashlib,time,io,gc
import numpy as np,torch
from PIL import Image
from transformers import AutoProcessor,AutoModel
P=pathlib.Path(__file__).resolve().parent;J=P.parent/'judge-score-fingerprinting-poc/2026-10-25';F=P.parent/'external-verification-tests-2026-10-26/forensic-screen'
sys.path.insert(0,str(F/'sources/rpa-code'));from models.cnn import build_model
def dump(n,x):(P/n).write_text(json.dumps(x,indent=2)+'\n')
for n,h in json.loads((P/'freeze.json').read_text())['files'].items():assert hashlib.sha256((P/n).read_bytes()).hexdigest()==h
start=time.time();torch.set_num_threads(4);torch.use_deterministic_algorithms(True);torch.backends.cudnn.benchmark=False;torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
records=[json.loads(f.read_text()) for f in sorted((P/'records').glob('*.json'))];assert len(records)==240
rows=[r for r in records if r['status']=='ok' and not r['black'] and not any(r.get('nsfw') or [])]
# JPEG only prescribed honest slot; variants retain anonymous IDs
jkeys={m[:-1] for g in json.loads((P/'groups.json').read_text()) if g['condition']=='jpeg75' for m in g['members'] if m.endswith('j')}
inputs=[]
for r in rows:
 inputs.append((r['key'],P/r['normalized'],False))
 if r['key'] in jkeys:inputs.append((r['key']+'j',P/r['normalized'],True))
def pixels(path,jpeg):
 im=Image.open(path).convert('RGB');assert im.size==(512,512)
 if jpeg:
  b=io.BytesIO();im.save(b,format='JPEG',quality=75,subsampling=2);b.seek(0);im=Image.open(b).convert('RGB');(P/'nuisance').mkdir(exist_ok=True);im.save(P/'nuisance'/(path.stem+'j.png'))
 return np.array(im,copy=True)
c=torch.load(F/'dragon_25class.pt',map_location='cpu',weights_only=True);model=build_model(c['config'],len(c['class_names']));model.load_state_dict(c['model']);model.eval().cuda();mean=c['channel_mean'].float().cuda().view(1,3,1,1);std=c['channel_std'].float().cuda().view(1,3,1,1)
rpa=[]
with torch.inference_mode():
 for key,path,jpeg in inputs:
  x=torch.from_numpy(pixels(path,jpeg)).permute(2,0,1).float().cuda()/255;patches=x.unfold(1,64,64).unfold(2,64,64).permute(1,2,0,3,4).reshape(64,3,64,64);f=model.features((patches-mean)/std).mean(0).cpu().numpy();assert f.shape==(1024,) and np.isfinite(f).all();rpa.append(f)
del model,c;gc.collect();torch.cuda.empty_cache()
processor=AutoProcessor.from_pretrained(J/'models/processor',local_files_only=True);model=AutoModel.from_pretrained(J/'models/pickscore',local_files_only=True,use_safetensors=True).eval().cuda();pick=[]
with torch.inference_mode():
 for key,path,jpeg in inputs:
  x=processor(images=Image.fromarray(pixels(path,jpeg)),return_tensors='pt').to('cuda');f=model.get_image_features(**x);f=(f/f.norm(dim=-1,keepdim=True)).float().cpu().numpy()[0];assert np.isfinite(f).all();pick.append(f)
np.savez_compressed(P/'features.npz',keys=np.array([x[0] for x in inputs]),rpa=np.array(rpa),pickscore=np.array(pick));dump('extraction.json',dict(seconds=time.time()-start,rows=len(inputs),valid_images=len(rows),rpa_dimension=1024,pickscore_dimension=len(pick[0]),finite=True,interface='RGB512 arrays only, no text or labels',peak_cuda_bytes=torch.cuda.max_memory_allocated()))
