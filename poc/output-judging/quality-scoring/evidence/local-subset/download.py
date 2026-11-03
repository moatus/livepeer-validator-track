import pathlib,json,hashlib,time,os
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN']='1'
P=pathlib.Path(__file__).resolve().parent
os.environ['HF_HOME']=str(P/'hf-cache')
from huggingface_hub import HfApi,snapshot_download
api=HfApi();ids={};locked=json.loads((P/'download-identities.json').read_text()) if (P/'download-identities.json').exists() else {}
for key,repo,patterns in [('sdxl','stabilityai/stable-diffusion-xl-base-1.0',['model_index.json','scheduler/*','tokenizer/*','tokenizer_2/*','text_encoder/config.json','text_encoder/model.fp16.safetensors','text_encoder_2/config.json','text_encoder_2/model.fp16.safetensors','unet/config.json','unet/diffusion_pytorch_model.fp16.safetensors','vae/config.json','vae/diffusion_pytorch_model.fp16.safetensors']),('pickscore','yuvalkirstain/PickScore_v1',['config.json','model.safetensors','pytorch_model.bin','README.md']),('processor','laion/CLIP-ViT-H-14-laion2B-s32B-b79K',['preprocessor_config.json','tokenizer.json','tokenizer_config.json','special_tokens_map.json','vocab.json','merges.txt','config.json'])]:
 revision=locked[key]['revision'] if key in locked else api.model_info(repo).sha;ids[key]=dict(repo=repo,revision=revision);(P/'download-identities.json').write_text(json.dumps(ids,indent=2))
 if key=='sdxl':
  q=json.loads((P/'PROTOCOL.json').read_text());assert q['generators']['sdxl']['revision'] in ['resolve immutable before generation',revision];q['generators']['sdxl']['revision']=revision;(P/'PROTOCOL.json').write_text(json.dumps(q,indent=2)+'\n');(P/'PROTOCOL.json.sha256').write_text(hashlib.sha256((P/'PROTOCOL.json').read_bytes()).hexdigest()+'  PROTOCOL.json\n')
 print('download',key,revision,flush=True)
 snapshot_download(repo,revision=revision,allow_patterns=patterns,local_dir=P/'models'/key,max_workers=3)
 ids[key]['files']={str(p.relative_to(P/'models'/key)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (P/'models'/key).rglob('*') if p.is_file() and '.cache' not in p.parts}
 (P/'download-identities.json').write_text(json.dumps(ids,indent=2));print('ready',key,flush=True)
