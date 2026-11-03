import os
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
import pathlib,sys,json,hashlib,time,io
import numpy as np
from PIL import Image,ImageFilter
import torch
P=pathlib.Path(__file__).resolve().parent; SRC=P.parents[1]/'judge-score-fingerprinting-poc/2026-10-25'
sys.path.insert(0,str(P/'sources/rpa-code'))
from models.cnn import build_model

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,x):(P/n).write_text(json.dumps(x,indent=2)+'\n')
def variant(im,v):
 if v=='jpeg85':
  b=io.BytesIO();im.save(b,format='JPEG',quality=85,subsampling=2);b.seek(0);return Image.open(b).convert('RGB')
 if v=='resize256':return im.resize((256,256),Image.Resampling.LANCZOS).resize((512,512),Image.Resampling.LANCZOS)
 return im

def residual(im):
 a=np.asarray(im,dtype=np.float64)/255.;g=a@np.array([.2126,.7152,.0722]);blur=np.asarray(im.filter(ImageFilter.GaussianBlur(1)),dtype=np.float64)/255.;r=a-blur
 stats=np.r_[r.mean((0,1)),r.std((0,1)),np.mean(np.abs(r),(0,1)),np.mean(r**4,(0,1))]
 g=g-g.mean();power=np.abs(np.fft.fftshift(np.fft.fft2(g*np.outer(np.hanning(512),np.hanning(512)))))**2
 f=np.fft.fftshift(np.fft.fftfreq(512));yy,xx=np.meshgrid(f,f);rad=np.sqrt(xx**2+yy**2);ang=(np.arctan2(yy,xx)+np.pi)%(2*np.pi)
 power=power/(power.sum()+1e-30);edges=np.linspace(0,np.sqrt(.5),25)
 radial=[np.log10(power[(rad>=edges[i])&(rad<edges[i+1])].mean()+1e-20) for i in range(24)]
 sector=[np.log10(power[(rad>=.25)&(ang>=i*np.pi/2)&(ang<(i+1)*np.pi/2)].mean()+1e-20) for i in range(4)]
 return np.r_[stats,radial,sector]

def visual(im):
 a=np.asarray(im,dtype=np.float64)/255;lum=a@np.array([.2126,.7152,.0722]);sat=a.max(2)-a.min(2)
 return np.r_[a.mean((0,1)),a.std((0,1)),lum.mean(),lum.std(),np.abs(np.diff(lum,axis=1)).mean(),np.abs(np.diff(lum,axis=0)).mean(),sat.mean(),sat.std()]

def main():
 torch.set_num_threads(4);torch.use_deterministic_algorithms(True);torch.backends.cudnn.benchmark=False;torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
 start=time.time();c=torch.load(P/'dragon_25class.pt',map_location='cpu',weights_only=True);model=build_model(c['config'],len(c['class_names']));model.load_state_dict(c['model']);model.eval().cuda();mean=c['channel_mean'].float().cuda().view(1,3,1,1);std=c['channel_std'].float().cuda().view(1,3,1,1)
 dump('checkpoint-settings.json',dict(config=c['config'],classes=c['class_names'],mean=mean.flatten().tolist(),std=std.flatten().tolist(),feature_dim=model.feature_dim,torch=torch.__version__,numpy=np.__version__,precision='float32',device=torch.cuda.get_device_name()))
 def learned(pixels):
  x=torch.from_numpy(np.array(pixels,copy=True)).permute(2,0,1).float().cuda()/255
  patches=x.unfold(1,64,64).unfold(2,64,64).permute(1,2,0,3,4).reshape(64,3,64,64)
  with torch.inference_mode():return model.features((patches-mean)/std).mean(0).cpu().numpy()
 records=sorted([json.loads(f.read_text()) for f in (SRC/'records').glob('*.json')],key=lambda r:r['key']);rows=[r for r in records if r['status']=='ok' and not r['black'] and not any(r.get('nsfw') or [])];assert len(rows)==215
 dump('manifest.json',rows)
 smoke=[]
 for split in ['train','calibration']:
  for label in ['sd14','sd15']:
   r=next(r for r in rows if r['split']==split and r['label']==label);im=Image.open(SRC/r['normalized']).convert('RGB');a=np.asarray(im);assert a.shape==(512,512,3) and hashlib.sha256(a.tobytes()).hexdigest()==r['pixel_sha256']
   f=learned(a);g=learned(a.copy());res=residual(im);assert f.shape==(1024,) and np.isfinite(f).all() and np.array_equal(f,g) and res.shape==(40,) and np.isfinite(res).all()
   smoke.append(dict(key=r['key'],split=split,shape=list(a.shape),pixel_hash=r['pixel_sha256'],feature_hash=hashlib.sha256(f.tobytes()).hexdigest(),repeat_exact=True,residual_dim=40))
 dump('smoke.json',dict(passed=True,examples=smoke,interface='uint8 RGB arrays only; no path, prompt, label or text passed to learned()',seconds=time.time()-start))
 # Smoke completed before any main-pass feature extraction.
 arrays={n:[] for n in ['learned','residual','visual','key','variant']}
 for r in rows:
  im=Image.open(SRC/r['normalized']).convert('RGB');assert im.size==(512,512)
  for v in (['base','jpeg85','resize256'] if r['split']=='heldout' else ['base']):
   img=variant(im,v);arrays['learned'].append(learned(np.asarray(img)));arrays['residual'].append(residual(img));arrays['visual'].append(visual(img));arrays['key'].append(r['key']);arrays['variant'].append(v)
 np.savez_compressed(P/'features.npz',**{n:np.array(v) for n,v in arrays.items()})
 dump('extraction-runtime.json',dict(seconds=time.time()-start,peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),images=len(rows),feature_rows=len(arrays['key']),gpu_hours=(time.time()-start)/3600,smoke_preceded_main=True))
if __name__=='__main__':main()
