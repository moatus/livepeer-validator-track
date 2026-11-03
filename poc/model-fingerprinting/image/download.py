import os
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN']='1'
from huggingface_hub import snapshot_download
from pathlib import Path
P=Path(__file__).resolve().parent
import json,hashlib,time
models=json.loads((P/'models.json').read_text())
for label,m in models.items():
 t=time.time()
 path=snapshot_download(m['repo'],revision=m['revision'],token=False,local_dir=P/'models'/label,allow_patterns=['*.json','tokenizer/*','*/*.fp16.safetensors','README.md'],ignore_patterns=['scheduler/.ipynb_checkpoints/*'])
 hashes={str(f.relative_to(path)):hashlib.sha256(f.read_bytes()).hexdigest() for f in __import__('pathlib').Path(path).rglob('*') if f.is_file() and '.cache' not in str(f)}
 (P/f'identity-{label}.json').write_text(json.dumps(dict(**m,files=hashes,download_seconds=time.time()-t),indent=2))
 print(label,'downloaded',flush=True)
