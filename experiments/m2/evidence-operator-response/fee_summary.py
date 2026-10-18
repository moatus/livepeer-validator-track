"""Selected frozen P1 summaries only. Offline; no extraction or full P1 analysis."""
import hashlib,json,sys
from pathlib import Path
from decimal import Decimal,getcontext
from statistics import median
from collections import defaultdict
getcontext().prec=100
HERE=Path(__file__).resolve().parent
P1=HERE.parent/'current-system-data-notes'
sys.path.insert(0,str(P1))
from extract import materialize,T0,T1

def summary():
    path=P1/'livepeer-arbitrum-p1-20260717-20261015-v1.json';raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!='b69e2b0949953b348470c772b4fc46f9c6510e37e3fb17b5f959a9fc7529d1c8':raise ValueError('Frozen P1 file changed')
    doc=json.loads(raw)
    actual=hashlib.sha256(json.dumps({k:v for k,v in doc.items() if k!='integrity'},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    if actual!='9f1a8e13b628f68ab65a2a796bc344e455cbbadc55f68221daf39bf75c49c414':raise ValueError('P1 content changed')
    data=materialize(doc);tickets=data['events']['winningTicketRedeemedEvents'];rounds=sorted(data['rounds'],key=lambda r:int(r['id']));sums=defaultdict(int);counts=defaultdict(int)
    for t in tickets:
        wei=Decimal(t['faceValue'])*10**18
        if wei!=int(wei):raise ValueError('Nonintegral wei')
        sums[int(t['round']['id'])]+=int(wei);counts[int(t['round']['id'])]+=1
    complete=[];partial=[]
    for i,r in enumerate(rounds):
        rid=int(r['id']);end=int(rounds[i+1]['startTimestamp']) if i+1<len(rounds) else None
        if int(r['startTimestamp'])<T0 or end is None or end>T1:partial.append(rid)
        else:complete.append(rid)
    med=median([Decimal(sums[r])/10**18 for r in complete]);rank=sorted(complete,key=lambda r:(-sums[r],r))[:5]
    out=dict(file_sha256=hashlib.sha256(raw).hexdigest(),content_sha256=actual,window='2026-07-17T00:00:00Z inclusive to 2026-10-15T00:00:00Z exclusive',blocks=[484622260,514893852],unit='ETH; faceValue wei / 10^18; redemption round, all recipients',tickets=len(tickets),total_eth=str(Decimal(sum(sums.values()))/10**18),intersecting_rounds=len(rounds),complete_rounds=len(complete),partial_excluded=partial,complete_median_eth=str(med),top5=[dict(round=r,count=counts[r],eth=str(Decimal(sums[r])/10**18),ratio_to_median=str(Decimal(sums[r])/10**18/med)) for r in rank])
    assert out['tickets']==15263 and out['total_eth']=='58.547073107487179205'
    assert out['complete_rounds']==100 and out['intersecting_rounds']==102
    assert med==Decimal('0.342115455886838978')
    assert rank==[4317,4321,4322,4320,4323] and sums[4317]==6529159045912707051 and counts[4317]==8
    return out
if __name__=='__main__':print(json.dumps(summary(),indent=2))
