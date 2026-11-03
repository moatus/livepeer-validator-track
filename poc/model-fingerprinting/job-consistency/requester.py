"""Private trusted requester: create expected commitments BEFORE inference."""
import pathlib,json
from common import *
P=pathlib.Path(__file__).resolve().parent
C=json.loads((P/'config.json').read_text());jobs=json.loads((P/'private/manifest.json').read_text())
profile={k:C[k] for k in ['model','height','width','precision','batch_size','steps','scheduler','guidance_scale','eta','negative_prompt']}
for j in jobs:
 spec=dict(version=VERSION,prompt=j['prompt'],seed=j['seed'],profile=profile,output_format='RGB-u8-512x512; PNG delivery',other_inputs=[],tokenization='CLIPTokenizer pinned model tokenizer; max_length=77; truncation=True; padding=max_length; attention mask not passed by stock pipeline')
 j['input_commitment']=commit('input',bytes.fromhex(j['input_blind']),canonical(spec))
 j['settings_commitment']=digest('settings',canonical(dict(profile=profile,seed=j['seed'],output_format=spec['output_format'])))
 j['request_spec']=spec
 j['model_profile']=digest('model-profile',canonical(profile))
dump(P/'private/requests.json',jobs);(P/'private/requests.json').chmod(0o600)
print('Committed',len(jobs),'requests before generation')
