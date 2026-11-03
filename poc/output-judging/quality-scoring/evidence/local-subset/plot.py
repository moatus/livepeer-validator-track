import pathlib,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageDraw
P=pathlib.Path(__file__).resolve().parent;res=json.loads((P/'results.json').read_text());labels=['sd14','sd15','sdxl'];names=['pickscore','visual','visual+pickscore','pickscore_image_embedding'];display=['PickScore scalar','Color / edge','Color / edge + scalar','PickScore image embedding']
fig,axs=plt.subplots(1,2,figsize=(12,4.6))
for ax,task in zip(axs,['sd1x','threeway']):
 vals=[res['results'][task][n]['base']['accuracy'] for n in names];cis=np.array([res['results'][task][n]['base']['prompt_cluster_ci95'] for n in names]);ax.bar(np.arange(4),vals,color=['#6799bb','#d59e56','#77a57a','#9a82ac']);ax.errorbar(np.arange(4),vals,yerr=np.array([np.array(vals)-cis[:,0],cis[:,1]-np.array(vals)]),fmt='none',c='black',capsize=4);ax.axhline(res['results'][task]['chance'],c='gray',ls='--');ax.set_xticks(np.arange(4),display,rotation=20,ha='right');ax.set_ylim(0,1.05);ax.set_title('SD1.4 vs SD1.5' if task=='sd1x' else 'Three generators');ax.set_ylabel('Held-out accuracy');
fig.suptitle('Local baselines only — Nemotron unavailable\n95% intervals resample six prompt families');fig.tight_layout();fig.savefig(P/'accuracy.png',dpi=160);plt.close(fig)
# Representative outputs fixed by manifest: first draw for every heldout family, all models.
records=[json.loads(f.read_text()) for f in (P/'records').glob('*.json')];prompts=json.loads((P/'prompts.json').read_text());held=[p for p in prompts if p['split']=='heldout'];W=3*256;H=6*288+48;sheet=Image.new('RGB',(W,H),'white');draw=ImageDraw.Draw(sheet)
for j,l in enumerate(labels):draw.text((j*256+8,10),l,fill='black')
for i,p in enumerate(held):
 for j,l in enumerate(labels):
  r=next(r for r in records if r['prompt_id']==p['id'] and r['label']==l and r['draw']==0);y=48+i*288
  if r['status']=='ok':sheet.paste(Image.open(P/r['normalized']).resize((256,256)),(j*256,y))
  draw.text((j*256+5,y+258),p['family'],fill='black')
sheet.save(P/'contact-sheet.jpg',quality=90)
z=np.load(P/'local-scores.npz');rec={r['key']:r for r in records};fig,axs=plt.subplots(1,2,figsize=(10,4))
for label in labels:
 ix=np.array([i for i,k in enumerate(z['keys']) if z['variants'][i]=='base' and rec[k]['label']==label and not rec[k]['black']]);axs[0].hist(z['pickscore'][ix],bins=15,alpha=.45,label=label);vals=[res['results'][t]['visual+pickscore'][v]['accuracy'] for t in ['sd1x','threeway'] for v in ['base','jpeg75','resize256']]
axs[0].set_xlabel('Raw PickScore (usable images, all splits)');axs[0].legend();axs[1].plot(['base','JPEG75','resize256'],[res['results']['sd1x']['visual+pickscore'][v]['accuracy'] for v in ['base','jpeg75','resize256']],marker='o',label='SD1.x');axs[1].plot(['base','JPEG75','resize256'],[res['results']['threeway']['visual+pickscore'][v]['accuracy'] for v in ['base','jpeg75','resize256']],marker='o',label='3-way');axs[1].set_ylim(0,1);axs[1].set_ylabel('Heldout accuracy; frozen base classifier');axs[1].legend();fig.tight_layout();fig.savefig(P/'robustness-quality.png',dpi=150)
