import pathlib,json,random,hashlib,datetime
P=pathlib.Path(__file__).resolve().parent
def dump(n,x):(P/n).write_text(json.dumps(x,indent=2)+'\n')
texts=[
('observatory','A watercolor of a mountain observatory beneath a violet evening sky.'),
('teapot','A porcelain teapot decorated with tiny blue leaves on a linen tablecloth, product photography.'),
('otter','A river otter resting on a smooth rock beside reeds, wildlife photograph.'),
('library','An old library aisle with a rolling wooden ladder and warm lamps, architectural photograph.'),
('violin','A violin and bow resting in an open velvet lined case, still life oil painting.'),
('canyon','A winding river through a sandstone canyon viewed from above at sunrise.'),
('mushroom','A macro photograph of a small mushroom under fallen autumn leaves.'),
('astronaut','A whimsical ceramic astronaut figurine tending a miniature garden, studio photo.'),
('tram','A vintage turquoise tram crossing a cobbled square on a rainy morning.'),
('pears','Three ripe pears in a shallow ceramic bowl, charcoal and pastel drawing.'),
('telescope','A brass telescope beside a round attic window, detailed pencil illustration.'),
('lagoon','A tropical lagoon with a wooden footbridge and distant limestone cliffs, travel photograph.'),
('weaving','Close view of colorful wool being woven on a hand loom, documentary photograph.'),
('fox','A fox curled up beneath a snow covered pine tree, storybook illustration.'),
('greenhouse','A sunlit greenhouse filled with hanging ferns and a stone path.'),
('camera','A vintage film camera beside a folded map on a wooden desk, studio photograph.'),
('waterfall','A small waterfall flowing over dark basalt into a misty forest pool.'),
('origami','An origami crane made of patterned orange paper on a black surface, photograph.'),
('harp','A golden harp in a quiet marble room lit by a high window, oil painting.'),
('radish','Fresh radishes with leafy tops on a kitchen cutting board, food photography.'),
('lighthouse','A striped lighthouse on a rocky headland during a calm pink sunset, watercolor.'),
('terrarium','A glass terrarium with moss and smooth pebbles on a bookshelf, product photograph.'),
('badger','A badger walking along a woodland path in soft morning light, wildlife photograph.'),
('diner','An empty retro diner with mint booths and a tiled floor, interior photograph.'),
('accordion','A red accordion on a wooden chair beside a curtain, still life painting.'),
('dunes','Wind sculpted sand dunes with a single curving trail at dawn, landscape photograph.'),
('dragonfly','A macro photograph of a dragonfly perched on a blade of grass covered in dew.'),
('clayhouse','A miniature clay cottage with a moss roof, handcrafted stop motion style.'),
('ferry','A small passenger ferry approaching a quiet misty harbor, documentary photograph.'),
('plums','Purple plums scattered on cream fabric, soft pastel still life.'),
('compass','An antique compass on a weathered sailing chart, detailed ink illustration.'),
('glacier','A blue glacier meeting a still alpine lake beneath overcast skies, photograph.'),
('pottery','Hands shaping a clay bowl on a pottery wheel, documentary photograph.'),
('hedgehog','A hedgehog nestled beside fallen apples in a garden, storybook illustration.'),
('courtyard','A quiet courtyard with tiled arches and a central stone fountain, architectural photograph.'),
('typewriter','A manual typewriter beside a cup of tea on an oak desk, studio photograph.'),
('cavern','A limestone cavern with a clear underground pool, dramatic landscape photograph.'),
('kite','A diamond shaped patchwork kite above a grassy hill, paper collage illustration.'),
('cello','A cello resting beside a tall arched window in an empty rehearsal room, oil painting.'),
('artichoke','An artichoke and a halved lemon on a slate board, food photography.')]
rng=random.Random(7007); prompts=[]; schedule=[]; groups=[]; labels={}
for i,(family,text) in enumerate(texts):
 pid=f'q{i:02d}';split='calibration' if i<20 else 'heldout';seeds=[730000+i*10+j for j in range(6)]
 prompts.append(dict(id=pid,split=split,family=family,prompt=text,seeds=seeds))
 ids=[]
 for j,model in enumerate(['sd14']*4+['sd15','sdxl']):
  key=f'im{len(schedule):03d}'; ids.append(key);schedule.append(dict(key=key,prompt_id=pid,prompt=text,model=model,seed=seeds[j]))
 # heldout operator role fixed per block; order shuffled independently on each job
 role=(i-20)//5 if i>=20 else rng.randrange(4)
 order=list(range(4));rng.shuffle(order)
 for condition in ['honest','close','broad','jpeg75']:
  members=ids[:4].copy()
  if condition in ['close','broad']:members[role]=ids[4 if condition=='close' else 5]
  if condition=='jpeg75':members[role]=members[role]+'j'
  gid=f'g{len(groups):03d}';groups.append(dict(group=gid,prompt_id=pid,split=split,condition=condition,members=[members[j] for j in order],roles=order))
  labels[gid]=dict(substitute_slot=order.index(role) if condition in ['close','broad'] else None,substitute_role=role if condition in ['close','broad'] else None)
base=json.loads(pathlib.Path('/home/mav/repos/livepeer/research/judge-score-fingerprinting-2026-10-25/evidence/local-subset/PROTOCOL.json').read_text())
dump('prompts.json',prompts);dump('schedule.json',schedule);dump('groups.json',groups);dump('labels.json',labels)
dump('PROTOCOL.json',dict(experiment='CONSENSUS-007',private=True,frozen_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),generation=base['generation'],generators=base['generators'],attempt_cap=240,seed_design='six unique independent seeds per prompt; no matched seed reuse; no rerolls',distance='cosine float64; normalize vectors; clip cosine distance to [0,2]',score='minimum distance to other three / max(median three pairwise distances of remaining trio,1e-12)',epsilon=1e-12,tie='exact maximum ties abstain',threshold='each representation independently: max of 20 honest calibration group maxima; strict exceedance; incomplete calibration blocks evaluation',calibration_target='nominal 1/21 approximately 5% under exchangeability; not production false alarm validation',representations=['frozen RPA1024 mean64 nonoverlapping64px patches, checkpoint normalization','frozen PickScore image embedding; no text'],missing='failed, black or safety-flagged images excluded; any incomplete group invalid and no decision; all scheduled denominators retained',jpeg='one fixed honest role per prompt, JPEG75 subsampling2; unchanged thresholds',repeated='four disjoint five-prompt heldout blocks; substitute role0,1,2,3 by block; per-role arithmetic mean score, rank-only; complete blocks only; no alarm calibration',examples='first heldout honest group; first heldout close and broad; plus first correctly detected and first missed substitute per representation and condition if any, deduplicate; no visual selection',limits=['one GPU simulation, not deployed orchestrators','native SDXL1024 vs SD1x512 confound','relative consistency, not model identity or dishonesty','paired groups not independent','scientific review pending'],budget=dict(wall_minutes=75,gpu_hours=1,hosted_spend=0),interval='Wilson95 descriptive binomial intervals over20 prompts; paired conditions; no population certification'))
