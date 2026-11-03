import tarfile, pathlib, io, hashlib, json
import soundfile as sf
import numpy as np
P=pathlib.Path(__file__).resolve().parent
out=P/'audio';out.mkdir(exist_ok=True)
rows=[]
with tarfile.open(P/'test-clean.tar.gz') as t:
    texts={}
    for m in t.getmembers():
        if m.name.endswith('.trans.txt'):
            for line in t.extractfile(m).read().decode().splitlines():
                k,v=line.split(' ',1);texts[k]=v
    speakers=sorted({m.name.split('/')[-1].split('-')[0] for m in t.getmembers() if m.name.endswith('.flac')})
    # ten speakers, three qualifying clips each; first four calibration gives 12/18 speaker-disjoint split.
    for speaker in speakers:
        selected=[]
        for m in sorted(t.getmembers(),key=lambda x:x.name):
            if not m.name.endswith('.flac') or m.name.split('/')[-1].split('-')[0]!=speaker:continue
            b=t.extractfile(m).read();a,sr=sf.read(io.BytesIO(b),dtype='float32')
            if sr!=16000:raise ValueError(sr)
            if 5<=len(a)/sr<=20:
                k=pathlib.Path(m.name).stem; f=out/(k+'.wav');sf.write(f,a,16000,subtype='PCM_16')
                selected.append(dict(id=k,speaker=speaker,source=m.name,source_sha256=hashlib.sha256(b).hexdigest(),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),duration=len(a)/sr,text=texts[k],path=str(f)))
            if len(selected)==3:break
        if len(selected)==3:
            split='calibration' if len(rows)<12 else 'evaluation'
            rows.extend(dict(r,split=split) for r in selected)
        if len(rows)==30:break
json.dump(dict(source='https://www.openslr.org/12/',license='CC BY 4.0',archive_sha256=hashlib.sha256((P/'test-clean.tar.gz').read_bytes()).hexdigest(),clips=rows),open(P/'dataset.json','w'),indent=2)
print(len(rows),sum(r['duration'] for r in rows))
