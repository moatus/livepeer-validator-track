"""One model per process; complete ASR, optional bounded encoder hooks."""
import os
os.environ['TOKENIZERS_PARALLELISM']='false'
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
import argparse,pathlib,json,time,hashlib,subprocess,sys
import numpy as np
import torch
P=pathlib.Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('model',choices=['parakeet','whisper']);p.add_argument('--round',type=int,default=0);p.add_argument('--limit',type=int,default=30);p.add_argument('--split',choices=['calibration','evaluation','all'],default='all');args=p.parse_args()
torch.set_num_threads(4);torch.manual_seed(42);np.random.seed(42)
torch.backends.cudnn.benchmark=False;torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
assert torch.cuda.is_available()
data=[r for r in json.load(open(P/'dataset.json'))['clips'] if args.split=='all' or r['split']==args.split][:args.limit]
start=time.perf_counter()
if args.model=='whisper':
 import whisper
 model=whisper.load_model('medium.en',device='cuda',download_root=str(P/'models')).eval()
 layers=model.encoder.blocks
 def transcribe(path):
  raw=model.transcribe(path,language='en',task='transcribe',temperature=0.0,beam_size=None,best_of=None,fp16=True,word_timestamps=True,condition_on_previous_text=False,verbose=None)
  return raw,raw['text'],[dict(word=w['word'],start=w['start'],end=w['end']) for s in raw['segments'] for w in s.get('words',[])]
else:
 from nemo.collections.asr.models import ASRModel
 from omegaconf import OmegaConf,open_dict
 from huggingface_hub import HfApi,hf_hub_download
 revision=json.load(open(P/'parakeet-model.json'))['revision'] if (P/'parakeet-model.json').exists() else HfApi().model_info('nvidia/parakeet-tdt-0.6b-v3').sha
 path=hf_hub_download('nvidia/parakeet-tdt-0.6b-v3','parakeet-tdt-0.6b-v3.nemo',revision=revision,cache_dir=str(P/'models'))
 model=ASRModel.restore_from(path,map_location='cpu').cuda().eval()
 cfg=model.cfg.decoding
 with open_dict(cfg):
  cfg.strategy='greedy_batch';cfg.compute_timestamps=True;cfg.preserve_alignments=True
  if 'greedy' in cfg:cfg.greedy.use_cuda_graph_decoder=False
 model.change_decoding_strategy(cfg)
 OmegaConf.save(model.cfg,str(P/'parakeet-config.yaml'))
 json.dump(dict(revision=revision,path=path,sha256=hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()),open(P/'parakeet-model.json','w'),indent=2)
 layers=model.encoder.layers
 def transcribe(path):
  h=model.transcribe([path],batch_size=1,timestamps=True,return_hypotheses=True,num_workers=0,verbose=False)
  if isinstance(h,tuple):h=h[0]
  h=h[0];ts=h.timestamp
  words=[dict(word=w.get('word',w.get('text','')),start=float(w['start']),end=float(w['end'])) for w in ts['word']]
  raw=dict(text=h.text,timestamp=ts)
  return raw,h.text,words
load=time.perf_counter()-start
json.dump(dict(model=args.model,round=args.round,load_seconds=load,device=torch.cuda.get_device_name(),torch=torch.__version__,cuda=torch.version.cuda,precision='whisper fp16 / parakeet fp32',pid=os.getpid()),open(P/f'identity-{args.model}-{args.round}-{args.split}.json','w'),indent=2)
# Fixed before any results: 3 relative encoder positions. Eight activation-distribution statistics per point.
indices=[len(layers)//4,len(layers)//2,len(layers)-1]
json.dump(dict(indices=indices,module_classes=[type(layers[i]).__name__ for i in indices],parameter_count=sum(p.numel() for p in model.parameters()),parameter_dtypes=sorted({str(p.dtype) for p in model.parameters()}),seed=42,threads=4),open(P/f'observation-{args.model}.json','w'),indent=2)
(P/f'gpu-{args.model}-{args.round}-{args.split}.txt').write_text(subprocess.check_output(['nvidia-smi'],text=True))
active=False; captured={};diagnostics={};current_duration=0

def hook_for(slot):
 def hook(module,inputs,kwargs,output):
  if not active or slot in captured:return
  x=output[0] if isinstance(output,(tuple,list)) else output
  # both layer adapters return B,T,C; Parakeet unpadded batch=1, Whisper fixed 30s window.
  x=x[0]
  valid=min(x.shape[0],int(np.ceil(current_duration*50))) if args.model=='whisper' else int((~kwargs['pad_mask'][0]).sum().item()) if kwargs.get('pad_mask') is not None else x.shape[0]
  x=x[:valid].float()
  # Dimension-agnostic summaries: distribution moments, channel/time variation, adjacent-frame relation.
  mean=x.mean();std=x.std(unbiased=False);z=(x-mean)/(std+1e-8)
  rms=x.square().mean().sqrt()
  delta=(x[1:]-x[:-1]).square().mean().sqrt()/(rms+1e-8)
  cosine=torch.nn.functional.cosine_similarity(x[1:],x[:-1],dim=-1).mean()
  v=torch.stack([mean,std,z.pow(3).mean(),z.pow(4).mean(),x.mean(0).std(unbiased=False)/(std+1e-8),x.mean(1).std(unbiased=False)/(std+1e-8),delta,cosine])
  captured[slot]=v.detach().cpu().numpy()
  diagnostics[slot]=dict(shape=list(output[0].shape if isinstance(output,(tuple,list)) else output.shape),valid_frames=valid,head=x[:2,:8].detach().cpu().tolist())
 return hook
handles=[layers[i].register_forward_hook(hook_for(j),with_kwargs=True) for j,i in enumerate(indices)]
# Warm-up excluded from timing. All runs are full timestamped inference.
with torch.inference_mode():
 current_duration=data[0]['duration'];transcribe(data[0]['path']);torch.cuda.synchronize()
 output=P/'runs';output.mkdir(exist_ok=True)
 for r in data:
  current_duration=r['duration']
  # Round 0: paired baseline + instrumented, alternated order by clip. Round 1: two instrumented repeats after reload.
  modes=([False,True] if data.index(r)%2==0 else [True,False]) if args.round==0 else [True,True]
  for j,instrument in enumerate(modes):
   dest=output/f'{args.model}-{args.round}-{r["id"]}-{j}.json'
   if dest.exists():continue
   active=instrument;captured.clear();diagnostics.clear()
   for h in handles:h.remove()
   handles=[layers[i].register_forward_hook(hook_for(j),with_kwargs=True) for j,i in enumerate(indices)] if instrument else []
   torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();t=time.perf_counter()
   raw,text,words=transcribe(r['path'])
   torch.cuda.synchronize();elapsed=time.perf_counter()-t
   assert words and all(w['end']>=w['start'] for w in words)
   fp=np.concatenate([captured[k] for k in sorted(captured)]).astype('float32') if instrument else None
   if instrument:assert len(fp)==24
   rec=dict(model=args.model,clip=r['id'],split=r['split'],round=args.round,instrumented=instrument,seconds=elapsed,peak_allocated=torch.cuda.max_memory_allocated(),peak_reserved=torch.cuda.max_memory_reserved(),text=text,words=words,fingerprint=fp.tolist() if instrument else None,raw=raw)
   record_start=time.perf_counter()
   if instrument:dest.with_suffix('.f32').write_bytes(fp.tobytes())
   dest.write_text(json.dumps(rec,default=lambda x:x.item() if hasattr(x,'item') else str(x)))
   record_seconds=time.perf_counter()-record_start
   with open(P/'recording-times.jsonl','a') as timing_file:timing_file.write(json.dumps(dict(file=dest.name,seconds=record_seconds,bytes=dest.stat().st_size))+'\n')
   if instrument and r==data[0]:json.dump(diagnostics,open(P/f'diagnostic-{args.model}-{args.round}-{args.split}.json','w'))
   print(args.model,args.round,r['id'],instrument,round(elapsed,3),len(words),flush=True)
for h in handles:h.remove()
