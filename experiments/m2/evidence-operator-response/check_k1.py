"""Bounded local fixture inspection; does not authenticate delivery or judge semantics."""
import hashlib,json,resource,struct,subprocess,sys,time,zlib
from pathlib import Path
HERE=Path(__file__).resolve().parent

def decode(path):
    resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
    from PIL import Image, __version__
    if __version__!='12.3.0': raise ValueError('Requires Pillow==12.3.0')
    with Image.open(path) as im:
        if im.format!='PNG':raise ValueError('Not PNG')
        im.verify()
    with Image.open(path) as im:
        im.load();print(json.dumps({'decoder':'Pillow '+__version__,'width':im.width,'height':im.height,'format':im.format}))

def inspect(path):
    # Length checked before reading. Decode runs with hard address-space and wall limits.
    size=path.stat().st_size
    if size>1048576:raise ValueError('Input exceeds 1 MiB; unknown, do not enlarge ceiling')
    raw=path.read_bytes();start=time.monotonic()
    if raw[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('PNG signature')
    pos=8;chunks=[];ihdr=None
    while pos<len(raw):
        if pos+12>len(raw):raise ValueError('Truncated chunk')
        n=struct.unpack('>I',raw[pos:pos+4])[0];kind=raw[pos+4:pos+8];end=pos+12+n
        if end>len(raw):raise ValueError('Truncated payload')
        payload=raw[pos+8:pos+8+n];crc=struct.unpack('>I',raw[pos+8+n:end])[0]
        if zlib.crc32(kind+payload)!=crc:raise ValueError('CRC')
        chunks.append(kind.decode('ascii'))
        if kind==b'IHDR':ihdr=struct.unpack('>II',payload[:8])
        pos=end
    if chunks[0]!='IHDR' or chunks[-1]!='IEND' or chunks.count('IHDR')!=1 or chunks.count('IEND')!=1:raise ValueError('Chunk framing')
    p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--decode',str(path)],capture_output=True,text=True,timeout=2,check=True)
    obs=json.loads(p.stdout)
    if ihdr!=(obs['width'],obs['height']):raise ValueError('Decoder disagreement; unknown')
    elapsed=time.monotonic()-start
    if elapsed>2:raise ValueError('Total inspection exceeded 2 sec; unknown')
    return dict(path=str(path.relative_to(HERE)),sha256=hashlib.sha256(raw).hexdigest(),bytes=size,chunks=chunks,**obs,k1=obs['width']==512 and obs['height']==512,inspection_seconds=elapsed,memory_limit_bytes=268435456,decoder_timeout_seconds=2)

def main():
    if len(sys.argv)>1 and sys.argv[1]=='--decode':decode(Path(sys.argv[2]));return
    bundle=json.loads((HERE/'fixtures/bundle.json').read_text());rows=[]
    for c in bundle['cases']:
        row=inspect(HERE/c['output_path'])
        if row['sha256']!=c['output_sha256']:raise ValueError('Changed fixture bytes')
        row['case']=c['case'];rows.append(row)
    print(json.dumps({'observations':rows,'limits':'Local byte checks only; custody, accepted terms and job/node identities stipulated; no delivery authentication or empirical error-rate claim.'},indent=2))
if __name__=='__main__':main()
