import os
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN']='1';os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
import pathlib,json,io,hashlib,time,gc
import numpy as np,torch
import datetime
from PIL import Image
from transformers import AutoProcessor,AutoModel
P=pathlib.Path(__file__).resolve().parent
torch.set_num_threads(4);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
def visual(im):
 a=np.asarray(im,dtype=np.float64)/255;lum=a@np.array([.2126,.7152,.0722]);sat=a.max(2)-a.min(2)
 return np.r_[a.mean((0,1)),a.std((0,1)),lum.mean(),lum.std(),np.abs(np.diff(lum,axis=1)).mean(),np.abs(np.diff(lum,axis=0)).mean(),sat.mean(),sat.std()]
def variant(im,name):
 if name=='jpeg75':
  b=io.BytesIO();im.save(b,format='JPEG',quality=75);b.seek(0);return Image.open(b).convert('RGB')
 if name=='resize256':return im.resize((256,256),Image.Resampling.LANCZOS).resize((512,512),Image.Resampling.LANCZOS)
 return im
prompts={p['id']:p for p in json.loads((P/'prompts.json').read_text())};records=sorted([json.loads(f.read_text()) for f in (P/'records').glob('*.json')],key=lambda r:r['key']);valid=[r for r in records if r['status']=='ok']
assert len(records)==216,'score only after all scheduled generation attempts'
processor=AutoProcessor.from_pretrained(P/'models/processor',local_files_only=True)
model=AutoModel.from_pretrained(P/'models/pickscore',local_files_only=True,use_safetensors=(P/'models/pickscore/model.safetensors').exists()).eval().to('cuda')
keys=[];scalar=[];emb=[];txt=[];features=[];variants=[];start=time.time();started_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
with torch.inference_mode():
 for r in valid:
  im=Image.open(P/r['normalized']).convert('RGB')
  text=processor(text=[prompts[r['prompt_id']]['prompt']],padding=True,truncation=True,max_length=77,return_tensors='pt').to('cuda')
  tf=model.get_text_features(**text);tf=tf/tf.norm(dim=-1,keepdim=True)
  for name in ['base','jpeg75','resize256']:
   image=variant(im,name);inputs=processor(images=image,return_tensors='pt').to('cuda');vf=model.get_image_features(**inputs);vf=vf/vf.norm(dim=-1,keepdim=True)
   raw=(model.logit_scale.exp()*(tf@vf.T)).item()
   keys.append(r['key']);variants.append(name);scalar.append(raw);emb.append(vf.float().cpu().numpy()[0]);txt.append(tf.float().cpu().numpy()[0]);features.append(visual(image))
  print(r['key'],round(scalar[-3],4),flush=True)
np.savez_compressed(P/'local-scores.npz',keys=np.array(keys),variants=np.array(variants),pickscore=np.array(scalar),image_embedding=np.array(emb),text_embedding=np.array(txt),visual=np.array(features))
(P/'score-runtime.json').write_text(json.dumps(dict(started_at=started_at,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),script_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),torch=torch.__version__,precision=str(next(model.parameters()).dtype),model=type(model).__name__,model_config=model.config.to_dict(),logit_scale_exp=model.logit_scale.exp().item(),seconds=time.time()-start,valid_images=len(valid),scored_variants=len(keys)),indent=2))
del model;gc.collect();torch.cuda.empty_cache()
