import os,sys
sys.dont_write_bytecode=True
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN']='1';os.environ['HF_HUB_OFFLINE']='1';os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
import pathlib,json,time,datetime,hashlib,importlib.util,argparse,gc
import numpy as np
import torch
from diffusers import StableDiffusionPipeline,DDIMScheduler
from common import *
P=pathlib.Path(__file__).resolve().parent;OLD=P.parents[1]/'image-fingerprinting-poc/2026-10-25'
C=json.loads((P/'config.json').read_text());J=json.loads((P/'private/requests.json').read_text())
# Read-only reuse of the exact prior observer implementation; never call its load/generate/main.
spec=importlib.util.spec_from_file_location('precedent',OLD/'run.py');prev=importlib.util.module_from_spec(spec);spec.loader.exec_module(prev)
Observer=prev.Observer
torch.set_num_threads(4);torch.backends.cudnn.benchmark=False;torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False;torch.use_deterministic_algorithms(True)
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def main():
 a=argparse.ArgumentParser();a.add_argument('phase',choices=['calibration','calibration-reload','heldout','heldout-reload','collision']);args=a.parse_args();phase=args.phase
 if phase.startswith('heldout'): assert (P/'frozen-rule.json').exists()
 if phase=='heldout': assert not list((P/'runs').glob('*-heldout-*.json'))
 t=time.perf_counter()
 pipe=StableDiffusionPipeline.from_pretrained(OLD/'models/sd15',torch_dtype=torch.float16,variant='fp16',use_safetensors=True,local_files_only=True)
 pipe.scheduler=DDIMScheduler.from_config(C['scheduler']);pipe.to('cuda');pipe.set_progress_bar_config(disable=True)
 for name in ['unet','vae','text_encoder','safety_checker']:
  obj=getattr(pipe,name,None)
  if obj is not None:obj.eval()
 obs=Observer(pipe)
 dump(P/f'load-{phase}.json',dict(timestamp=stamp(),seconds=time.perf_counter()-t,scheduler=dict(pipe.scheduler.config),torch=torch.__version__,cuda=torch.version.cuda,diffusers=__import__('diffusers').__version__))
 if phase=='collision': selected=[j for j in J if j['split']=='collision']
 elif phase.endswith('reload'):
  fs=[0,1] if phase.startswith('calibration') else [5,6]
  selected=[j for j in J if j['family'] in fs and j['seed'] in [5101,6303]]
 else:selected=[j for j in J if j['split']==phase]
 toks=[]
 for j in selected:
  full=pipe.tokenizer(j['prompt'],truncation=False)['input_ids']
  effective=pipe.tokenizer(j['prompt'],padding='max_length',max_length=77,truncation=True,return_tensors='pt')['input_ids'][0].tolist()
  if phase!='collision':assert len(full)<=77
  toks.append(dict(id=j['id'],full_length=len(full),effective_ids=effective))
 if phase=='collision':assert toks[0]['effective_ids']==toks[1]['effective_ids'] and selected[0]['prompt']!=selected[1]['prompt']
 elif not phase.endswith('reload'):
  for family in sorted(set(j['family'] for j in selected)):
   ts=[t['effective_ids'] for t,j in zip(toks,selected) if j['family']==family and j['seed']==selected[0]['seed']]
   assert len({tuple(t) for t in ts})==3
 dump(P/f'private/tokens-{phase}.json',toks)
 for j in selected:
  roles=['reload'] if phase.endswith('reload') else (['control'] if phase=='collision' else ['reference','candidate'])
  for role in roles:
   key=f"{j['id']}-{phase}-{role}"; assert not (P/'runs'/f'{key}.json').exists()
   obs.reset(True)
   latent=torch.randn((1,4,64,64),generator=torch.Generator('cpu').manual_seed(j['seed']),dtype=torch.float16).to('cuda')
   lh=hashlib.sha256(latent.cpu().numpy().tobytes()).hexdigest()
   torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();start=time.perf_counter()
   with torch.inference_mode():out=pipe(prompt=j['prompt'],negative_prompt='',height=512,width=512,num_inference_steps=25,guidance_scale=7.5,eta=0.,latents=latent.clone(),output_type='pil')
   torch.cuda.synchronize();seconds=time.perf_counter()-start
   v=obs.vector();im=out.images[0];oc=commit('output',bytes.fromhex(j['output_blind']),pixels(im))
   v.tofile(P/'vectors'/f'{key}.f32');im.save(P/'images'/f'{key}.png')
   rec=dict(id=j['id'],family=j['family'],variant=j['variant'],seed=j['seed'],split=j['split'],phase=phase,role=role,key=key,seconds=seconds,latent_sha256=lh,output_commitment=oc,pixel_digest=digest('pixel-content',pixels(im)),nsfw=out.nsfw_content_detected,peak_allocated=torch.cuda.max_memory_allocated(),timestamp=stamp())
   dump(P/'runs'/f'{key}.json',rec);print(phase,role,len(list((P/'runs').glob('*.json'))),round(seconds,3),flush=True)
 obs.remove();del obs,pipe;gc.collect();torch.cuda.empty_cache();dump(P/f'complete-{phase}.json',dict(timestamp=stamp(),allocated=torch.cuda.memory_allocated(),reserved=torch.cuda.memory_reserved()))
if __name__=='__main__':main()
