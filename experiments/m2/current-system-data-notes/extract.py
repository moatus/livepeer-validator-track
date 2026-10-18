"""Collect the fixed P1 window. Read-only requests; credentials stay in memory.

Raw response bytes are losslessly zlib/base64 encoded to avoid duplicating bulk
records. data contains source references, resolved by materialize() offline.
"""
import argparse
import base64
import hashlib
import json
import os
import sys
import time
import zlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
FILE = HERE / 'livepeer-arbitrum-p1-20260717-20261015-v1.json'
GRAPH = 'https://gateway.thegraph.com/api/subgraphs/id/FE63YgkzcpVocxdCEyEYbvjYqEf2kb1A6daMYRxmejYC'
LOG_RPC = 'https://arb1.arbitrum.io/rpc'
STATE_RPC = 'https://arbitrum-one.public.blastapi.io'
BM = '0x35Bcf3c30594191d53231E4FF333E8A770453e40'
TB = '0xa8bB618B1520E284046F3dFc448851A1Ff26e41B'
START, END, T0, T1 = 484622260, 514893852, 1784246400, 1792022400
PINS = {
    484622260: '0xda75086009d5b479166ecb0367f63ed9df73961e8ee42147af4eb700a64463ac',
    514893852: '0xdf674fc2b32f2e7a80b8dadd2fa1a93a49c281087a4c37bf56e651f45bf42ccf',
    505240413: '0xfd734b688cdf7e57c53596077519fb77c499498b67cca19a69eb7f59a83a5814',
    494961555: '0x5c6b4828912edf9abdca8c58dd8ca7649097a1b44810b1fb7a113a2d5a64d3a6',
    484622259: '0x2254139c042c27cb31da42678d4d51aefe42d1b254e6d26c4433a6fcd77034e2',
}
CHECKPOINTS = [484622259, 494961555, 505240413, END]
SIGNATURES = {
 'bondEvents': 'Bond(address,address,address,uint256,uint256)',
 'unbondEvents': 'Unbond(address,address,uint256,uint256,uint256)',
 'rebondEvents': 'Rebond(address,address,uint256,uint256)',
 'transferBondEvents': 'TransferBond(address,address,uint256,uint256,uint256)',
 'withdrawStakeEvents': 'WithdrawStake(address,uint256,uint256,uint256)',
 'winningTicketRedeemedEvents': 'WinningTicketRedeemed(address,address,uint256,uint256,uint256,uint256,bytes)',
}
# Keccak-f[1600], legacy Ethereum padding, not SHA3-256. Standard library only.
RC = [0x1,0x8082,0x800000000000808a,0x8000000080008000,0x808b,0x80000001,
0x8000000080008081,0x8000000000008009,0x8a,0x88,0x80008009,0x8000000a,
0x8000808b,0x800000000000008b,0x8000000000008089,0x8000000000008003,
0x8000000000008002,0x8000000000000080,0x800a,0x800000008000000a,
0x8000000080008081,0x8000000000008080,0x80000001,0x8000000080008008]
ROT = [[0,36,3,41,18],[1,44,10,45,2],[62,6,43,15,61],
       [28,55,25,21,56],[27,20,39,8,14]]
MASK = (1 << 64)-1

def keccak(text):
    raw = text.encode() if isinstance(text, str) else text
    raw += b'\x01'
    raw += b'\0' * ((135 - len(raw)) % 136) + b'\x80'
    a = [0]*25
    rol = lambda v,n: ((v<<n)|(v>>(64-n))) & MASK if n else v
    for offset in range(0,len(raw),136):
        for i in range(17): a[i] ^= int.from_bytes(raw[offset+8*i:offset+8*i+8],'little')
        for rc in RC:
            c = [a[x]^a[x+5]^a[x+10]^a[x+15]^a[x+20] for x in range(5)]
            d = [c[(x-1)%5]^rol(c[(x+1)%5],1) for x in range(5)]
            for x in range(5):
                for y in range(5): a[x+5*y] ^= d[x]
            b = [0]*25
            for x in range(5):
                for y in range(5): b[y+5*((2*x+3*y)%5)] = rol(a[x+5*y],ROT[x][y])
            for x in range(5):
                for y in range(5): a[x+5*y] = b[x+5*y]^((~b[(x+1)%5+5*y])&b[(x+2)%5+5*y])
            a[0] ^= rc
    return '0x'+b''.join(x.to_bytes(8,'little') for x in a)[:32].hex()

TOPICS = {name: keccak(sig) for name,sig in SIGNATURES.items()}

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()

def utc(): return datetime.now(timezone.utc).isoformat()

def response(source):
    return json.loads(zlib.decompress(base64.b64decode(source['raw_response_zlib_base64'])))

def materialize(doc):
    sources = doc['provenance']['sources']
    def result(ref):
        row = response(sources[ref])
        return row.get('data', row.get('result'))
    return {
        'events': {k:[e for ref in refs for e in result(ref)[k]] for k,refs in doc['data']['events'].items()},
        'rounds': [e for ref in doc['data']['rounds'] for e in result(ref)['rounds']],
        'transcoders': {b:[e for ref in refs for e in result(ref)['transcoders']] for b,refs in doc['data']['transcoders'].items()},
        'logs': [e for ref in doc['data']['logs'] for e in result(ref)],
        'rpc_log_decoded': json.loads(zlib.decompress(base64.b64decode(doc['data']['rpc_log_decoded']['zlib_base64']))) if 'rpc_log_decoded' in doc['data'] else [],
        'state': [{**r,'raw':result(r['source'])} for r in doc['data']['state']],
        'headers': {b:result(ref) for b,ref in doc['data']['headers'].items()},
    }

def words(raw): return [int(raw[i:i+64],16) for i in range(2,len(raw),64)]
def address(topic): return '0x'+topic[-40:].lower()

def decode(log):
    name = next(k for k,v in TOPICS.items() if v==log['topics'][0])
    ts,w = log['topics'],words(log['data'])
    a = lambda i: address(ts[i])
    if name=='bondEvents': f={'newDelegate':a(1),'oldDelegate':a(2),'delegator':a(3),'additionalAmount':str(w[0]),'bondedAmount':str(w[1])}
    elif name=='unbondEvents': f={'delegate':a(1),'delegator':a(2),'unbondingLockId':str(w[0]),'amount':str(w[1]),'withdrawRound':str(w[2])}
    elif name=='rebondEvents': f={'delegate':a(1),'delegator':a(2),'unbondingLockId':str(w[0]),'amount':str(w[1])}
    elif name=='transferBondEvents': f={'oldDelegator':a(1),'newDelegator':a(2),'oldUnbondingLockId':str(w[0]),'newUnbondingLockId':str(w[1]),'amount':str(w[2])}
    elif name=='withdrawStakeEvents': f={'delegator':a(1),'unbondingLockId':str(w[0]),'amount':str(w[1]),'withdrawRound':str(w[2])}
    else:
        offset = w[4]
        payload = bytes.fromhex(log['data'][2:])
        size = int.from_bytes(payload[offset:offset+32],'big')
        f={'sender':a(1),'recipient':a(2),'faceValue':str(w[0]),'winProb':str(w[1]),
           'senderNonce':str(w[2]),'recipientRand':str(w[3]),'auxData':'0x'+payload[offset+32:offset+32+size].hex()}
    return name,f


class Collector:
    def __init__(self):
        self.key = os.environ.get('GRAPH_API_KEY')
        if not self.key: raise SystemExit('GRAPH_API_KEY is not set; load the local env file')
        self.sources = {}

    def request(self, endpoint, body, graph=False):
        headers = {'Content-Type':'application/json','User-Agent':'m2-p1-data-notes/1'}
        if graph: headers['Authorization'] = 'Bearer '+self.key
        request = Request(endpoint,data=canonical(body),headers=headers)
        for attempt in range(4):
            try:
                with urlopen(request,timeout=90) as r: raw = r.read()
                parsed = json.loads(raw)
                break
            except Exception as exc:
                # Never print a request, exception text, headers or credentials.
                if attempt == 3: raise RuntimeError('Source unavailable: '+endpoint+' ('+type(exc).__name__+')') from None
                time.sleep(2**attempt)
        ref = 'request-'+str(len(self.sources)+1).zfill(4)
        subset = {k:parsed[k] for k in ('jsonrpc','id','errors','error') if k in parsed}
        if graph and '_meta' in parsed.get('data',{}): subset['_meta'] = parsed['data']['_meta']
        self.sources[ref] = {'endpoint':endpoint,'request':body,'retrieved_utc':utc(),
            'raw_response_sha256':hashlib.sha256(raw).hexdigest(),
            'raw_response_encoding':'zlib+base64; UTF-8 JSON after decompression',
            'raw_response_zlib_base64':base64.b64encode(zlib.compress(raw,9)).decode(),
            'parsed_response_subset':subset}
        time.sleep(.2)
        if parsed.get('errors') or parsed.get('error'):
            raise ValueError('Source returned API error; inspect sanitized provenance '+ref)
        return ref,parsed['data'] if graph else parsed['result']

    def gql(self, query, variables=None):
        return self.request(GRAPH,{'query':query,'variables':variables or {}},True)

    def rpc(self, endpoint, method, params):
        return self.request(endpoint,{'jsonrpc':'2.0','id':1,'method':method,'params':params})

    def pages(self, collection, fields, block, where):
        query = ('query($b:Int!,$last:String!){ '+collection+
            '(block:{number:$b},first:1000,orderBy:id,orderDirection:asc,where:{id_gt:$last'+where+'}){'+fields+'} }')
        refs, rows, cursor = [], [], ''
        while True:
            ref,data = self.gql(query,{'b':block,'last':cursor})
            page = data[collection]
            refs.append(ref); rows.extend(page)
            print(collection,block,len(rows),flush=True)
            if len(page)<1000: return refs,rows
            if page[-1]['id'] <= cursor: raise ValueError('Cursor did not advance')
            cursor = page[-1]['id']

    def logs(self, address, topics, lo, hi):
        try:
            ref,rows = self.rpc(LOG_RPC,'eth_getLogs',[{'address':address,
                'fromBlock':hex(lo),'toBlock':hex(hi),'topics':[topics]}])
            print('logs',lo,hi,len(rows),flush=True)
            return [ref]
        except (ValueError,RuntimeError):
            if lo==hi: raise RuntimeError('Logs refused at single block; stop') from None
            mid = (lo+hi)//2
            return self.logs(address,topics,lo,mid)+self.logs(address,topics,mid+1,hi)

    def collect(self):
        data = {'events':{},'rounds':[],'transcoders':{},'logs':[],'headers':{},'state':[]}
        schema_query = '{ __schema { types { name kind fields { name type { kind name ofType { kind name ofType { kind name } } } } } } _meta { block { number hash } hasIndexingErrors deployment } }'
        schema_ref,schema = self.gql(schema_query)
        if schema['_meta']['hasIndexingErrors']: raise RuntimeError('Subgraph indexing errors; stop')
        for block,expected in PINS.items():
            ref,header = self.rpc(LOG_RPC,'eth_getBlockByNumber',[hex(block),False])
            if header['hash'] != expected: raise RuntimeError('Pinned block hash differs; stop')
            data['headers'][str(block)] = ref
        meta_ref,_ = self.gql('{ _meta(block:{number:514893852}) { block {number hash} hasIndexingErrors deployment } }')
        common = 'id timestamp round{id} transaction{id blockNumber} '
        fields = {
          'bondEvents':'delegator{id} newDelegate{id} oldDelegate{id} additionalAmount bondedAmount',
          'unbondEvents':'delegator{id} delegate{id} amount unbondingLockId withdrawRound',
          'rebondEvents':'delegator{id} delegate{id} amount unbondingLockId',
          'transferBondEvents':'oldDelegator{id} newDelegator{id} amount oldUnbondingLockId newUnbondingLockId',
          'withdrawStakeEvents':'delegator{id} amount unbondingLockId',
          'winningTicketRedeemedEvents':'sender{id} recipient{id} faceValue faceValueUSD winProb senderNonce recipientRand auxData',
        }
        all_events = {}
        for name,field in fields.items():
            refs,rows = self.pages(name,common+field,END,',timestamp_gte:'+str(T0)+',timestamp_lt:'+str(T1))
            data['events'][name] = refs; all_events[name] = rows
        min_round = min(int(e['round']['id']) for rows in all_events.values() for e in rows)
        data['rounds'],_ = self.pages('rounds','id startTimestamp startBlock endBlock length initialized',END,
                                     ',id_gte:"'+str(min_round)+'"')
        transcoders = {}
        for block in CHECKPOINTS:
            refs,rows = self.pages('transcoders','id totalStake active status activationRound deactivationRound feeShare rewardCut',block,'')
            data['transcoders'][str(block)] = refs; transcoders[block] = rows
        for lo in range(START,END+1,1000000):
            hi = min(lo+999999,END)
            data['logs'] += self.logs(BM,[TOPICS[k] for k in fields if k!='winningTicketRedeemedEvents'],lo,hi)
            data['logs'] += self.logs(TB,[TOPICS['winningTicketRedeemedEvents']],lo,hi)
        # Selectors are keccak of pinned BondingManager.sol function signatures.
        def call(block,signature,address=None,purpose='checkpoint'):
            arg = address[2:].rjust(64,'0') if address else ''
            ref,raw = self.rpc(STATE_RPC,'eth_call',[{'to':BM,'data':keccak(signature)[:10]+arg},hex(block)])
            data['state'].append({'block':block,'signature':signature,'address':address,'purpose':purpose,'source':ref})
            return raw
        for block in CHECKPOINTS:
            call(block,'getTotalBonded()')
            for sig in ('getTranscoderPoolSize()','getTranscoderPoolMaxSize()'): call(block,sig)
            ranked = sorted(transcoders[block],key=lambda x:__import__('decimal').Decimal(x['totalStake']),reverse=True)
            for row in ranked[:5 if block==END else 2]: call(block,'getDelegator(address)',row['id'])
        call(END,'unbondingPeriod()')
        # Anchor only old-delegator states needed by TransferBond reconstruction.
        anchors = set()
        for e in all_events['transferBondEvents']:
            pair = (int(e['transaction']['blockNumber'])-1,e['oldDelegator']['id'])
            if pair not in anchors:
                call(*pair[:1],'getDelegator(address)',pair[1],purpose='transfer-old-delegator-before-block')
                anchors.add(pair)
        decoded_logs = []
        for ref in data['logs']:
            for log in response(self.sources[ref])['result']:
                name, fields = decode(log)
                decoded_logs.append({'transaction_hash':log['transactionHash'], 'log_index':str(int(log['logIndex'],16)), 'event':name, 'fields':fields})
        decoded_bytes = canonical(decoded_logs)
        data['rpc_log_decoded'] = {'encoding':'zlib+base64 of UTF-8 JSON; uint256 fields are decimal integer strings',
            'sha256':hashlib.sha256(decoded_bytes).hexdigest(),
            'zlib_base64':base64.b64encode(zlib.compress(decoded_bytes,9)).decode()}
        doc = {
          'capture':{'id':'livepeer-arbitrum-p1-20260717-20261015-v1','chain_id':42161,
              'retrieved_utc':utc(),'window':{'start_block':START,'end_block_inclusive':END,
              'start_timestamp':T0,'end_timestamp_exclusive':T1,'start_utc':'2026-07-17T00:00:00Z',
              'end_utc_exclusive':'2026-10-15T00:00:00Z'},'pinned_hashes':{str(b):h for b,h in PINS.items()},
              'checkpoints':CHECKPOINTS,'schema_source':schema_ref,'subgraph_meta':schema['_meta'],
              'historical_meta_source':meta_ref},
          'units':{'subgraph_token_amounts':'decimal LPT or ETH strings, unchanged',
                   'rpc_log_data':'raw ABI hex plus decoded uint256 decimal integer strings in data.rpc_log_decoded; amounts in wei',
                   'rpc_state':'raw ABI hex; no rounding','faceValueUSD':'indexed USD, secondary settlement series'},
          'definitions':{'label':"today's system (Arbitrum One, pinned window), not a forecast for the litepaper",
              'data':'Source references. materialize() parses losslessly retained raw response bytes; no derived tables.',
              'event_identity':'Subgraph id checked offline against transaction hash plus RPC log index.',
              'round_blocks':'Round startBlock/endBlock/length are Ethereum L1; transactions and pins are Arbitrum L2.',
              'protocol_commit':'46c24fef8c7ccccfb4a55038bd80af7799c904c7',
              'go_livepeer_commit':'9d4f55ecb183b969dbdf1caf0ac25f9c386530fd'},
          'data':data,'provenance':{'sources':self.sources}}
        doc['integrity'] = {'algorithm':'SHA-256, sorted keys, compact separators, ensure_ascii=False, excluding integrity',
                            'content_sha256':hashlib.sha256(canonical(doc)).hexdigest()}
        return doc

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=FILE)
    args = parser.parse_args()
    c = Collector()
    if args.output.exists(): raise SystemExit('Extract already exists; preserve it and choose a new --output path')
    try:
        doc = c.collect()
        raw = canonical(doc)+b'\n'
        if len(raw)>15_000_000: raise RuntimeError('Extract exceeds 15 MB; report before trimming')
        # Do not overwrite an existing frozen artifact.
        with args.output.open('xb') as f: f.write(raw)
        print('Saved',len(raw),'bytes;',doc['integrity']['content_sha256'])
    except Exception as e:
        # Persist sanitized request/response evidence only, never headers/key.
        if c.sources:
            partial=args.output.with_name(args.output.name+'.partial')
            try:
                with partial.open('xb') as f:
                    f.write(canonical({'provenance':{'sources':c.sources}}))
            except FileExistsError:
                raise SystemExit('Collection failed; existing partial evidence preserved') from None
        raise SystemExit(type(e).__name__+': '+str(e)) from None
