"""JOB-003 canonical primitives. No private-data reads at import."""
import json,hashlib,struct
VERSION='job003-v1'
def canonical(x):
 return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')
def framed(domain,*parts):
 fields=[VERSION.encode(),domain.encode(),*parts]
 return b''.join(struct.pack('>Q',len(p))+p for p in fields)
def digest(domain,data): return hashlib.sha256(framed(domain,data)).hexdigest()
def commit(domain,blind,data): return hashlib.sha256(framed(domain,blind,data)).hexdigest()
def pixels(im):
 im=im.convert('RGB')
 return framed('pixels-RGB-u8-row-major',struct.pack('>II',im.width,im.height),im.tobytes())
def dump(path,x): path.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
