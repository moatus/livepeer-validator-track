import os
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN']='1';os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
import pathlib,json,hashlib,time,datetime,argparse,gc
import numpy as np,torch
from diffusers import StableDiffusionPipeline,StableDiffusionXLPipeline,DDIMScheduler
from PIL import Image
P=pathlib.Path(__file__).resolve().parent;OLD=P.parents[1]/'image-fingerprinting-poc/2026-10-25'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,x):(P/n).write_text(json.dumps(x,indent=2)+'\n')
torch.set_num_threads(4);torch.backends.cudnn.benchmark=False;torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False;torch.use_deterministic_algorithms(True)
a=argparse.ArgumentParser();a.add_argument('model',choices=['sd14','sd15','sdxl']);args=a.parse_args();label=args.model
for d in ['raw','normalized','records']:(P/d).mkdir(exist_ok=True)
proto=json.loads((P/'PROTOCOL.json').read_text()); assert len(proto['generators']['sdxl']['revision'])==40
assert hashlib.sha256((P/'PROTOCOL.json').read_bytes()).hexdigest()==(P/'PROTOCOL.json.sha256').read_text().split()[0]
modeldir=P/'models/sdxl' if label=='sdxl' else OLD/'models'/label
if label!='sdxl':
 ids=json.loads((OLD/f'identity-{label}.json').read_text());checks={k:sha(modeldir/k)==v for k,v in ids['files'].items()};assert all(checks.values());dump(f'checkpoint-verification-{label}.json',checks)
pipe=(StableDiffusionXLPipeline if label=='sdxl' else StableDiffusionPipeline).from_pretrained(modeldir,torch_dtype=torch.float16,variant='fp16',use_safetensors=True,local_files_only=True,**({'add_watermarker':False} if label=='sdxl' else {}))
pipe.scheduler=DDIMScheduler.from_config(pipe.scheduler.config if label=='sdxl' else proto['generation']['sd1x']['scheduler']);pipe.to('cuda');pipe.set_progress_bar_config(disable=True)
for c in pipe.components.values():
 if isinstance(c,torch.nn.Module):c.eval()
dump(f'runtime-{label}.json',dict(scheduler=dict(pipe.scheduler.config),safety_checker=type(getattr(pipe,'safety_checker',None)).__name__,watermark=str(getattr(pipe,'watermark',None)),protocol_sha256=sha(P/'PROTOCOL.json'),torch=torch.__version__,cuda=torch.version.cuda,gpu=torch.cuda.get_device_name()))
for p in json.loads((P/'prompts.json').read_text()):
 for draw,seed in enumerate(p['seeds']):
  key=f"{p['id']}-{draw}-{label}";recpath=P/'records'/f'{key}.json'
  if recpath.exists():continue
  # Guard the global attempt cap, including failed requests. No warmup images.
  attempts=list((P/'records').glob('*.attempt'));assert len(attempts)<216
  assert not (P/'records'/f'{key}.attempt').exists(), 'prior attempt without terminal record; never silently reroll'
  (P/'records'/f'{key}.attempt').write_text(str(time.time()))
  rec=dict(key=key,label=label,prompt_id=p['id'],family=p['family'],split=p['split'],seed=seed,draw=draw,timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='started')
  t=time.time()
  try:
   size=1024 if label=='sdxl' else 512
   latent=torch.randn((1,4,size//8,size//8),generator=torch.Generator('cpu').manual_seed(seed),dtype=torch.float16).to('cuda');rec['latent_sha256']=hashlib.sha256(latent.cpu().numpy().tobytes()).hexdigest()
   with torch.inference_mode():out=pipe(prompt=p['prompt'],negative_prompt='',height=size,width=size,num_inference_steps=25,guidance_scale=7.5,eta=0.,latents=latent,output_type='pil')
   im=out.images[0];raw=P/'raw'/f'{key}.png';im.save(raw);norm=P/'normalized'/f'{key}.png';Image.fromarray(np.array(im.convert('RGB').resize((512,512),Image.Resampling.LANCZOS))).save(norm)
   rec.update(status='ok',raw=str(raw.relative_to(P)),normalized=str(norm.relative_to(P)),raw_sha256=sha(raw),normalized_sha256=sha(norm),pixel_sha256=hashlib.sha256(np.asarray(Image.open(norm)).tobytes()).hexdigest(),black=bool(np.max(np.asarray(im))==0),nsfw=getattr(out,'nsfw_content_detected',None),width=size,height=size)
  except Exception as e:rec.update(status='failed',error=type(e).__name__+': '+str(e))
  rec['seconds']=time.time()-t;dump('records/'+key+'.json',rec);print(key,rec['status'],round(rec['seconds'],2),flush=True)
del pipe;gc.collect();torch.cuda.empty_cache();dump('cleanup-'+label+'.json',dict(cuda_allocated=torch.cuda.memory_allocated(),cuda_reserved=torch.cuda.memory_reserved()))
