import pathlib,json,hashlib,time,subprocess
from huggingface_hub import HfApi,snapshot_download
P=pathlib.Path(__file__).resolve().parent; O=P.with_name('2026-10-25')
def dump(n,x):(P/n).write_text(json.dumps(x,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
start=time.time(); info=HfApi(token=False).model_info('Qwen/Qwen2.5-VL-7B-Instruct',files_metadata=True)
dump('download-plan.json',dict(repo=info.id,revision=info.sha,files=[dict(name=s.rfilename,size=s.size) for s in info.siblings],started=start))
path=snapshot_download(info.id,revision=info.sha,token=False,local_dir=P/'model',allow_patterns=['*.json','*.safetensors','*.txt','*.jinja','README.md','LICENSE'],max_workers=4)
dump('model-lock.json',dict(repo=info.id,revision=info.sha,download_seconds=time.time()-start,files={str(p.relative_to(path)):sha(p) for p in pathlib.Path(path).rglob('*') if p.is_file() and '.cache' not in p.parts}))
print('download and hashes complete',flush=True)
