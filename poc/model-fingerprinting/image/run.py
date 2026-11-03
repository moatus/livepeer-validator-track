import os
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN']='1'
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
import argparse,json,pathlib,time,hashlib,datetime,gc,platform
import numpy as np
import torch
from diffusers import StableDiffusionPipeline,DDIMScheduler
P=pathlib.Path(__file__).resolve().parent
C=json.loads((P/'config.json').read_text()); M=json.loads((P/'manifest.json').read_text())
def dump(path,x): path.write_text(json.dumps(x,indent=2)+'\n')
def sha(b): return hashlib.sha256(b).hexdigest()
def stamp(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
for d in ['runs','fingerprints','images']: (P/d).mkdir(exist_ok=True)
torch.set_num_threads(4)
torch.backends.cudnn.benchmark=False
torch.backends.cuda.matmul.allow_tf32=False
torch.backends.cudnn.allow_tf32=False
torch.use_deterministic_algorithms(True)
class Observer:
 def __init__(self,pipe):
  self.active=False;self.step=-1;self.data={};self.handles=[]
  self.handles.append(pipe.unet.register_forward_pre_hook(self.pre))
  for name in C['layers']:
   self.handles.append(pipe.unet.get_submodule(name).register_forward_hook(self.hook(name)))
 def pre(self,module,args):
  self.step+=1
 def hook(self,name):
  def f(module,args,out):
   if not self.active or self.step not in C['observed_steps']: return
   assert out.shape[0]==2, out.shape
   x=out[1].detach().float()
   assert torch.isfinite(x).all()
   mean=x.mean();std=x.std(unbiased=False);z=(x-mean)/std.clamp_min(1e-8)
   vals=torch.stack([mean,std,x.abs().mean(),x.square().mean().sqrt(),z.pow(3).mean(),z.pow(4).mean()])
   self.data[(self.step,name)]=vals.cpu().numpy()
  return f
 def reset(self,active): self.active=active;self.step=-1;self.data={}
 def vector(self):
  v=np.concatenate([self.data[(s,n)] for s in C['observed_steps'] for n in C['layers']]).astype('<f4')
  assert v.shape==(54,) and np.isfinite(v).all();return v
 def remove(self):
  for h in self.handles:h.remove()

def load(label,phase):
 t=time.perf_counter()
 pipe=StableDiffusionPipeline.from_pretrained(P/'models'/label,torch_dtype=torch.float16,variant='fp16',use_safetensors=True,local_files_only=True)
 pipe.scheduler=DDIMScheduler.from_config(C['scheduler'])
 pipe.to('cuda');pipe.set_progress_bar_config(disable=True)
 for n in ['unet','vae','text_encoder','safety_checker']:
  obj=getattr(pipe,n,None)
  if obj is not None:obj.eval()
 obs=Observer(pipe)
 dump(P/f'load-{label}-{phase}.json',dict(seconds=time.perf_counter()-t,timestamp=stamp(),scheduler=dict(pipe.scheduler.config),components={k:dict(class_name=type(v).__name__,config=(v.config.to_dict() if hasattr(v.config,'to_dict') else dict(v.config)) if hasattr(v,'config') else None) for k,v in pipe.components.items() if k not in ['tokenizer','feature_extractor']}))
 return pipe,obs

def generate(pipe,obs,label,p,seed,tag,active=True,save=True):
 obs.reset(active)
 latent=torch.randn((1,4,64,64),generator=torch.Generator('cpu').manual_seed(seed),dtype=torch.float16).to('cuda')
 latent_hash=sha(latent.cpu().numpy().tobytes())
 torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();t=time.perf_counter()
 with torch.inference_mode():
  out=pipe(prompt=p['prompt'],negative_prompt='',height=512,width=512,num_inference_steps=25,guidance_scale=7.5,eta=0.,latents=latent.clone(),output_type='pil')
 torch.cuda.synchronize();elapsed=time.perf_counter()-t
 memory=dict(allocated=torch.cuda.max_memory_allocated(),reserved=torch.cuda.max_memory_reserved())
 image=out.images[0];image_hash=sha(np.asarray(image).tobytes());key=f"{label}-{p['id']}-{seed}-{tag}"
 vector=obs.vector() if active else None
 write_t=time.perf_counter()
 if save:
  image.save(P/'images'/f'{key}.png')
  if active:vector.tofile(P/'fingerprints'/f'{key}.f32')
  rec=dict(key=key,label=label,prompt_id=p['id'],group=p['group'],split=p['split'],seed=seed,tag=tag,instrumented=active,seconds=elapsed,memory=memory,latent_sha256=latent_hash,image_sha256=image_hash,nsfw=out.nsfw_content_detected,timestamp=stamp(),fingerprint=str(P/'fingerprints'/f'{key}.f32') if active else None,image=str(P/'images'/f'{key}.png'))
  rec['write_seconds']=time.perf_counter()-write_t;dump(P/'runs'/f'{key}.json',rec)
  print(key,round(elapsed,3),flush=True)
 return vector,image_hash

def main():
 a=argparse.ArgumentParser();a.add_argument('label',choices=['sd14','sd15']);a.add_argument('phase',choices=['smoke','calibration','evaluation','reload']);args=a.parse_args()
 if args.phase in ['evaluation','reload']:assert (P/'frozen-classifier.json').exists()
 pipe,obs=load(args.label,args.phase)
 generate(pipe,obs,args.label,M[0],1101,'warmup',save=False)
 if args.phase=='smoke':generate(pipe,obs,args.label,M[0],1101,'smoke')
 elif args.phase in ['calibration','evaluation']:
  for p in M:
   if p['split']!=args.phase:continue
   for seed in p['seeds']:generate(pipe,obs,args.label,p,seed,'first')
  if args.phase=='evaluation':
   # True uninstrumented baselines remove every hook. Recreate only for measured instrumented runs.
   for j,job in enumerate(C['repeat_jobs']):
    p=next(p for p in M if p['id']==job['id']);seed=job['seed']
    for active in ([False,True] if j%2==0 else [True,False]):
     if not active:obs.remove()
     generate(pipe,obs,args.label,p,seed,'timing-instrumented' if active else 'timing-baseline',active)
     if not active:obs=Observer(pipe)
    generate(pipe,obs,args.label,p,seed,'repeat-inprocess')
 elif args.phase=='reload':
  for job in C['repeat_jobs']:
   p=next(p for p in M if p['id']==job['id']);generate(pipe,obs,args.label,p,job['seed'],'repeat-reload')
 obs.remove();del pipe,obs;gc.collect();torch.cuda.empty_cache()
 dump(P/f'complete-{args.label}-{args.phase}.json',dict(timestamp=stamp(),gpu_allocated=torch.cuda.memory_allocated(),gpu_reserved=torch.cuda.memory_reserved()))
if __name__=='__main__': main()
