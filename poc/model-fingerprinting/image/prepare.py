import json, pathlib, datetime, urllib.request, hashlib
P=pathlib.Path(__file__).resolve().parent

def dump(n,x): (P/n).write_text(json.dumps(x,indent=2)+'\n')
groups=[('calibration','tableware',['A blue ceramic teapot on a wooden table','A glass bowl filled with green apples']),('calibration','mountains',['Snow covered mountains beneath a clear sky','A winding trail on a rocky mountain']),('calibration','cats',['An orange cat sleeping on a cushion','A gray kitten sitting beside a window']),('calibration','libraries',['A quiet library with wooden bookshelves','A reading room with a desk and a green lamp']),('calibration','geometric',['A watercolor illustration of colorful geometric shapes','A paper collage of circles and triangles']),('evaluation','boats',['A small sailboat on a calm blue lake','A red fishing boat resting in a harbor']),('evaluation','forests',['Sunlight passing through a pine forest','A mossy log in a green woodland']),('evaluation','birds',['A robin perched on a garden fence','A white heron standing beside a pond']),('evaluation','kitchens',['A bright kitchen with copper pans','A rustic kitchen with a stone floor']),('evaluation','botanical',['A botanical watercolor of wildflowers','An ink illustration of fern leaves']),('evaluation','bicycles',['A yellow bicycle leaning against a brick wall','A vintage bicycle beside a country road']),('evaluation','deserts',['Sand dunes under a pink evening sky','A cactus in a wide rocky desert']),('evaluation','dogs',['A golden dog playing in a grassy field','A small brown dog resting on a rug']),('evaluation','workshops',['A tidy woodworking workshop with hand tools','An artists studio with brushes and blank canvases']),('evaluation','fantasy',['A storybook illustration of a floating garden','A whimsical illustration of a tiny tree house'])]
manifest=[]
for split,group,prompts in groups:
 for prompt in prompts:
  i=len(manifest); manifest.append(dict(id=f'p{i:02}',split=split,group=group,prompt=prompt,seeds=([1101,2202] if split=='calibration' else [3303,4404])))
dump('manifest.json',manifest)
config=dict(experiment='IMG-002',frozen_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),steps=25,guidance_scale=7.5,height=512,width=512,negative_prompt='',precision='float16',batch_size=1,observed_steps=[0,12,24],layers=['down_blocks.1.resnets.1','mid_block.resnets.1','up_blocks.2.resnets.1'],branch='conditional: CFG batch index 1; unconditional index 0 excluded',features=['mean','std_population','mean_absolute','rms','standardized_third_moment','standardized_fourth_moment'],feature_count=54,fingerprint_bytes=216,scheduler=dict(_class_name='DDIMScheduler',num_train_timesteps=1000,beta_start=0.00085,beta_end=0.012,beta_schedule='scaled_linear',clip_sample=False,set_alpha_to_one=False,steps_offset=1,prediction_type='epsilon',timestep_spacing='leading',rescale_betas_zero_snr=False),eta=0.0,classifier='nearest centroid; pooled within-class population std floor 1e-6; no selection',repeat_jobs=[dict(id=f'p{i:02}',seed=(1101 if i<10 else 3303)) for i in [0,2,4,6,8,10,14,18,22,28]],timing_jobs='same 10 balanced prompt/seed jobs; alternate baseline/instrumented order per pair; one warmup per load')
dump('config.json',config)
models={}
for label,repo in [('sd14','CompVis/stable-diffusion-v1-4'),('sd15','stable-diffusion-v1-5/stable-diffusion-v1-5')]:
 with urllib.request.urlopen('https://huggingface.co/api/models/'+repo) as r: info=json.load(r)
 models[label]=dict(repo=repo,revision=info['sha'])
dump('models.json',models)
dump('protocol-freeze.json',{n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in ['config.json','manifest.json','models.json']})
print(models)
