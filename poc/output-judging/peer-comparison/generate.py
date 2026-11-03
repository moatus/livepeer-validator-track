import os
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_IMPLICIT_TOKEN='1',CUBLAS_WORKSPACE_CONFIG=':4096:8')
import pathlib,json,hashlib,time,datetime,sys,gc
import numpy as np,torch
from diffusers import StableDiffusionPipeline,StableDiffusionXLPipeline,DDIMScheduler
from PIL import Image
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parent;J=ROOT/'judge-score-fingerprinting-poc/2026-10-25';OLD=ROOT/'image-fingerprinting-poc/2026-10-25'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,x):(P/n).write_text(json.dumps(x,indent=2)+'\n')
for name,expected in json.loads((P/'freeze.json').read_text())['files'].items():assert sha(P/name)==expected,name
label=sys.argv[1];assert label in ['sd14','sd15','sdxl'];proto=json.loads((P/'PROTOCOL.json').read_text());torch.set_num_threads(4);torch.backends.cudnn.benchmark=False;torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False;torch.use_deterministic_algorithms(True)
for d in ['raw','normalized','records']:(P/d).mkdir(exist_ok=True)
modeldir=J/'models/sdxl' if label=='sdxl' else OLD/'models'/label
pipe=(StableDiffusionXLPipeline if label=='sdxl' else StableDiffusionPipeline).from_pretrained(modeldir,torch_dtype=torch.float16,variant='fp16',use_safetensors=True,local_files_only=True,**({'add_watermarker':False} if label=='sdxl' else {}));pipe.scheduler=DDIMScheduler.from_config(pipe.scheduler.config if label=='sdxl' else proto['generation']['sd1x']['scheduler']);pipe.to('cuda');pipe.set_progress_bar_config(disable=True)
for c in pipe.components.values():
 if isinstance(c,torch.nn.Module):c.eval()
dump('runtime-'+label+'.json',dict(scheduler=dict(pipe.scheduler.config),safety_checker=type(getattr(pipe,'safety_checker',None)).__name__,watermark=str(getattr(pipe,'watermark',None)),torch=torch.__version__,gpu=torch.cuda.get_device_name()))
for row in json.loads((P/'schedule.json').read_text()):
 if row['model']!=label:continue
 assert time.time()<json.loads((P/'run-start.json').read_text())['deadline_epoch'],'wall/GPU conservative budget deadline'
 key=row['key'];recpath=P/'records'/f'{key}.json';assert not recpath.exists();assert len(list((P/'records').glob('*.attempt')))<240;attempt=P/'records'/f'{key}.attempt';assert not attempt.exists();attempt.write_text(str(time.time()));rec=dict(row,timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='started');t=time.time()
 try:
  size=1024 if label=='sdxl' else 512;latent=torch.randn((1,4,size//8,size//8),generator=torch.Generator('cpu').manual_seed(row['seed']),dtype=torch.float16).to('cuda');rec['latent_sha256']=hashlib.sha256(latent.cpu().numpy().tobytes()).hexdigest()
  with torch.inference_mode():out=pipe(prompt=row['prompt'],negative_prompt='',height=size,width=size,num_inference_steps=25,guidance_scale=7.5,eta=0.,latents=latent,output_type='pil')
  im=out.images[0];raw=P/'raw'/f'{key}.png';im.save(raw);norm=P/'normalized'/f'{key}.png';im.convert('RGB').resize((512,512),Image.Resampling.LANCZOS).save(norm);rec.update(status='ok',raw=str(raw.relative_to(P)),normalized=str(norm.relative_to(P)),raw_sha256=sha(raw),normalized_sha256=sha(norm),black=bool(np.max(np.asarray(im))==0),nsfw=getattr(out,'nsfw_content_detected',None),width=size,height=size)
 except Exception as e:rec.update(status='failed',error=repr(e))
 rec['seconds']=time.time()-t;dump('records/'+key+'.json',rec);print(key,label,rec['status'],round(rec['seconds'],2),flush=True)
del pipe;gc.collect();torch.cuda.empty_cache()
