import os
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
import pathlib,json,time,hashlib,traceback,sys,resource
import torch
from PIL import Image
from transformers import Qwen2_5_VLForConditionalGeneration,AutoProcessor
P=pathlib.Path(__file__).resolve().parent
protocol=json.loads((P/'PROTOCOL.json').read_text());inputs=json.loads((P/'inputs.json').read_text());axes=protocol['axes']
def parse(raw,requirements):
 x=json.loads(raw.strip());assert isinstance(x,dict) and set(x)==set(axes+['craft','aesthetics']),'keys'
 for a in axes:
  assert (x[a] is None if requirements[a] is None else isinstance(x[a],str) and x[a] in ['no','partial','yes']),a
 for a in ['craft','aesthetics']:assert type(x[a]) is int and 0<=x[a]<=10,a
 return x
if __name__=='__main__':
 start=time.time();torch.set_num_threads(6);torch.manual_seed(904)
 lock=json.loads((P/'model-lock.json').read_text())
 model=Qwen2_5_VLForConditionalGeneration.from_pretrained(P/'model',torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},attn_implementation='sdpa',local_files_only=True).eval()
 processor=AutoProcessor.from_pretrained(P/'model',local_files_only=True,min_pixels=protocol['pixels']['min_pixels'],max_pixels=protocol['pixels']['max_pixels'])
 torch.cuda.reset_peak_memory_stats();load_seconds=time.time()-start
 schedule=[('stability',x,v) for x in inputs['stability'] for v in range(3)]+[('main',x,0) for x in inputs['main']]
 (P/'execution-lock.json').write_text(json.dumps(dict(model_revision=lock['revision'],started_epoch=start,protocol_sha256=hashlib.sha256((P/'PROTOCOL.json').read_bytes()).hexdigest(),code_sha256={n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in ['score.py','analyze.py','verify.py']},dependencies_sha256=hashlib.sha256((P/'requirements.lock').read_bytes()).hexdigest()),indent=2))
 done=set()
 if (P/'raw-responses.jsonl').exists():
  done={(r['stage'],r['key'],r['vote']) for r in map(json.loads,(P/'raw-responses.jsonl').read_text().splitlines())}
 assert len(done)<=280
 for stage,item,vote in schedule:
  if (stage,item['key'],vote) in done:continue
  if time.time()>1792982809 or len(done)>=280:break
  t=time.time();r=dict(stage=stage,key=item['key'],vote=vote,image_sha256=item['image_sha256'],model_revision=lock['revision'],hosted_usd=0)
  try:
   assert hashlib.sha256(pathlib.Path(item['image']).read_bytes()).hexdigest()==item['image_sha256']
   image=Image.open(item['image']).convert('RGB');text=protocol['rubric'].format(prompt=item['prompt'],requirements=json.dumps(item['requirements'],ensure_ascii=False))
   messages=[{'role':'user','content':[{'type':'image'},{'type':'text','text':text}]}]
   chat=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
   batch=processor(text=[chat],images=[image],padding=True,return_tensors='pt').to('cuda')
   r.update(judge_text=text,input_tokens=int(batch.input_ids.shape[1]),image_grid=batch.image_grid_thw.tolist())
   assert batch.input_ids.shape[1]<=protocol['context_limit']
   with torch.inference_mode():out=model.generate(**batch,**{k:v for k,v in protocol['decode'].items() if k!='seed'})
   tokens=out[0,batch.input_ids.shape[1]:].tolist();raw=processor.decode(tokens,skip_special_tokens=True,clean_up_tokenization_spaces=False)
   r.update(raw=raw,output_token_ids=tokens,output_tokens=len(tokens))
   try:r.update(parsed=parse(raw,item['requirements']),status='ok')
   except Exception as e:r.update(status='parse_error',error=repr(e))
   del batch,out
  except Exception as e:r.update(status='runtime_error',error=repr(e),traceback=traceback.format_exc())
  r.update(seconds=time.time()-t,peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved())
  with (P/'raw-responses.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
  done.add((stage,item['key'],vote));print(len(done),stage,item['key'],r['status'],round(r['seconds'],2),flush=True)
  (P/'runtime.json').write_text(json.dumps(dict(load_seconds=load_seconds,process_seconds=time.time()-start,calls=len(done),peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved(),hosted_usd=0,process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),indent=2))
  if r['status']=='runtime_error':break
