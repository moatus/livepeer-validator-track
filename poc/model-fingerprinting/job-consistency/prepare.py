import pathlib,json,os,hashlib,datetime
P=pathlib.Path(__file__).resolve().parent
OLD=P.parents[1]/'image-fingerprinting-poc/2026-10-25'
def dump(n,x): (P/n).write_text(json.dumps(x,indent=2)+'\n')
for d in ['private','images','vectors','runs','bundle']: (P/d).mkdir(mode=0o700,exist_ok=True)
triples=[
('a photograph of a red ceramic mug on a wooden table','a photograph of a blue ceramic mug on a wooden table','a photograph of a snowy mountain under stars'),
('a watercolor of one yellow bird on a branch','a watercolor of two yellow birds on a branch','a watercolor of a busy harbor with sailboats'),
('a photograph of a cat sitting to the left of a basket','a photograph of a cat sitting to the right of a basket','a photograph of a steam train in a desert'),
('an oil painting of a green bicycle beside a brick wall','an oil painting of a green motorcycle beside a brick wall','an oil painting of a tropical island at sunset'),
('a studio photograph of a glass bowl filled with apples','a studio photograph of a glass bowl filled with oranges','a studio photograph of a silver wristwatch on velvet'),
('a photograph of a red umbrella on a quiet beach','a photograph of a blue umbrella on a quiet beach','a photograph of an astronaut standing on the moon'),
('a watercolor of three pink flowers in a white vase','a watercolor of five pink flowers in a white vase','a watercolor of a medieval stone castle'),
('a photograph of a dog standing behind a wooden chair','a photograph of a dog standing in front of a wooden chair','a photograph of a waterfall in a green forest'),
('an illustration of a small sailboat on a calm lake','an illustration of a small rowboat on a calm lake','an illustration of colorful hot air balloons above a city'),
('a photograph of a silver spoon next to a white plate','a photograph of a golden spoon next to a white plate','a photograph of a fox walking through snow'),
('a painting of a lighthouse during the day','a painting of a lighthouse during the night','a painting of a bowl of strawberries on a kitchen counter'),
('a photograph of one brown horse in a grassy field','a photograph of two brown horses in a grassy field','a photograph of a modern library filled with books'),
('an illustration of a rabbit wearing a red scarf','an illustration of a rabbit wearing a green scarf','an illustration of a submarine exploring a coral reef'),
('a photograph of a wooden toy car on a blue rug','a photograph of a metal toy car on a blue rug','a photograph of a stone bridge crossing a river'),
('a watercolor of a white house with a round window','a watercolor of a white house with a square window','a watercolor of a violin resting on a concert stage')]
config=json.loads((OLD/'config.json').read_text())
config.update(experiment='JOB-003',classifier='per-job standardized RMS difference; calibration only',model=json.loads((OLD/'models.json').read_text())['sd15'],method='IMG-002-54-v1')
config.pop('repeat_jobs');config.pop('timing_jobs')
dump('config.json',config)
jobs=[]
for i,t in enumerate(triples):
 split='calibration' if i<5 else 'heldout'
 for seed in ([5101,5202] if i<5 else [6303,6404]):
  for v,prompt in zip('ABC',t):
   jobs.append(dict(id=os.urandom(16).hex(),family=i,variant=v,prompt=prompt,seed=seed,split=split,input_blind=os.urandom(32).hex(),output_blind=os.urandom(32).hex()))
# Raw strings differ beyond the effective token window. These are excluded controls.
long='a photograph of a red apple on a table '+ 'with a plain background '*35
for v,prompt in [('X',long+' blue'),('Y',long+' yellow')]:
 jobs.append(dict(id=os.urandom(16).hex(),family=15,variant=v,prompt=prompt,seed=7505,split='collision',input_blind=os.urandom(32).hex(),output_blind=os.urandom(32).hex()))
dump('private/manifest.json',jobs)
protocol=dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),families=15,calibration_families=list(range(5)),heldout_families=list(range(5,15)),seeds={'calibration':[5101,5202],'heldout':[6303,6404]},positive='independent candidate for every ABC job',negative_pairs=[['A','B','close'],['B','A','close'],['A','C','distant'],['C','A','distant']],reload='all ABC, first seed, families 0,1,5,6; 12 jobs',threshold_rule='scale = calibration reference feature population std floored 1e-6; distance = RMS standardized delta; tolerance=max(1e-5,10*max calibration positive including reload); proceed with 54 if all calibration negatives exceed tolerance; otherwise stop for one alternate decision before heldout',collision='two actual generations with equal effective tokens; exclude from fitting',no_zero_tolerance=True)
dump('protocol.json',protocol)
dump('protocol-freeze.json',{n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in ['config.json','private/manifest.json','protocol.json']})
(P/'private/manifest.json').chmod(0o600)
print('Frozen',len(jobs),'private jobs; 15 families plus collision control')
