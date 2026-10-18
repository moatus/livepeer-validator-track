"""Offline verifier with independently fixed ABI, boundary and threshold anchors."""
import base64
import hashlib
import json
import zlib
from copy import deepcopy
from decimal import Decimal as D
from pathlib import Path
from tempfile import TemporaryDirectory
from extract import FILE, HERE, PINS, END, START, T0, T1, TOPICS, SIGNATURES, keccak, canonical, response
from analyze import load, decode, identity, log_identity, reconcile, words, threshold, transfer_links, slow_path_changes, redistribution_threshold, WEI

TOPIC_FIXTURES = {
 'bondEvents':'0xe5917769f276ddca9f2ee7c6b0b33e1d1e1b61008010ce622c632dd20d168a23',
 'unbondEvents':'0x2d5d98d189bee5496a08db2a5948cb7e5e786f09d17d0c3f228eb41776c24a06',
 'rebondEvents':'0x9f5b64cc71e1e26ff178caaa7877a04d8ce66fde989251870e80e6fbee690c17',
 'transferBondEvents':'0xf136b986590e86cf1abd7b6600186a7a1178ad3cbbdf0f3312e79f6214a2a567',
 'withdrawStakeEvents':'0x1340f1a8f3d456a649e1a12071dfa15655e3d09252131d0f980c3b405cc8dd2e',
 'winningTicketRedeemedEvents':'0xc389eb51ed006dbf2528507f010efdf5225ea596e1e1741d74f550dab1925ee7',
}
# Hand decoding: the indexed topics end in the three 20-byte addresses below.
# The two 32-byte data words are 0x56bc75e2d63100000 = 100 * 10^18
# and 0x2086ac2c90a014b98d2 = 9599999850487277656274.
EVENT_TX = '0x03ccb0b05778af79c82104865bdcbac421fe6e97367a081314ec4384b72bbd0c'
EVENT_LOG_INDEX = 12
EVENT_FIELDS = {
    'newDelegate':'0xaa1dd0958b7c5c5a49550315c9511a53c4d65fba',
    'oldDelegate':'0xaa1dd0958b7c5c5a49550315c9511a53c4d65fba',
    'delegator':'0xc14335b2d233215512fc7c7218fbf56dfe9d9a8e',
    'additionalAmount':'100000000000000000000',
    'bondedAmount':'9599999850487277656274',
}
BOUNDARY = (4330,1788851681,25931085)
# First/last events on each side, ordered timestamp then L2 block then log index.
BOUNDARY_EVENTS = [
    ('0x55d3f6ac0e23dcf93cc084f3a90735548d69e5eae52bd779da355cafebd872d0-0',1784246410,4270),
    ('0x133b0b16c9ebfea26e32c0a54c1c574aa427c2d78d8bbee029e54971738b47d3-6',1788850735,4329),
    ('0x058875bacb6899cc7bf965f89d661f13e7ba45755289a9c1ef0888067e4a8472-6',1788851790,4330),
    ('0x4fd84ec83d63dc6cb9d5d97ec1e6b3c3c8b699fdc42649bcac8b462ddd7efc46-1',1792020793,4371),
]
END_RANK17_ADDRESS = '0x104a7ca059a35fd4def5ecb16600b2caa1fe1361'
END_RANK17_LPT = '379659.360603855438925991'
# Hand multiplication: 10*s = 3796593.606038554389259910;
# 7*s = 2657615.524226988072481937;
# sum = 6454209.130265542461741847, then add 17 wei.
END_BASE_THRESHOLD_LPT = '6454209.130265542461741864'
# Independent end-checkpoint redistribution anchor: two donor pools exceed the
# required stake at original rank 19; neither donor already holds 17 seats.
END_REDISTRIBUTION = (2, D('8563354.934939629961370029'), 19,
                      D('6206912.316848201439881046'))
TRANSFER_ANCHOR_COUNTS = {'compared':1382,'excluded':9,'mismatches':0}
EXPECTED_CONTENT_SHA256 = '9f1a8e13b628f68ab65a2a796bc344e455cbbadc55f68221daf39bf75c49c414'


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def check_transfer_anchors(data):
    anchors={(r['block'],r['address'].lower()):words(r['raw'])
             for r in data['state'] if r['purpose']=='transfer-old-delegator-before-block'}
    order=lambda e:(int(e['transaction']['blockNumber']),identity(e)[1])
    touches={}
    for name,events in data['events'].items():
        if name=='winningTicketRedeemedEvents':continue
        for event in events:
            actors=([event['oldDelegator']['id'],event['newDelegator']['id']]
                    if name=='transferBondEvents' else [event['delegator']['id']])
            for actor in actors:touches.setdefault(actor.lower(),[]).append((order(event),event['id']))
    unbonds={(identity(e)[0],e['delegator']['id'].lower(),e['unbondingLockId']):e
             for e in data['events']['unbondEvents']}
    counts={'compared':0,'excluded':0,'mismatches':0}
    for event in data['events']['transferBondEvents']:
        block,index=order(event);old=event['oldDelegator']['id'].lower()
        unbond=unbonds[(identity(event)[0],old,event['oldUnbondingLockId'])]
        # The transfer's own Unbond is required and does not invalidate its
        # pre-block delegate. Any other earlier touch in that block does.
        prior=[ident for position,ident in touches[old]
               if position[0]==block and position<(block,index) and ident!=unbond['id']]
        if prior:
            counts['excluded']+=1
            continue
        check((block-1,old) in anchors,'Missing previous-block transfer anchor')
        anchor_delegate='0x'+format(anchors[(block-1,old)][2],'040x')
        counts['compared']+=1
        if anchor_delegate!=unbond['delegate']['id'].lower():counts['mismatches']+=1
    check(counts==TRANSFER_ANCHOR_COUNTS,'Previous-block anchor comparison counts differ')
    return counts


def check_anchors(data,sg,rpc):
    key=(EVENT_TX,EVENT_LOG_INDEX)
    check((decode(rpc[key])==('bondEvents',EVENT_FIELDS)), "Validation failed: decode(rpc[key]) == ('bondEvents', EVENT_FIELDS)")
    kind,e=sg[key]
    check((kind=='bondEvents'), "Validation failed: kind == 'bondEvents'")
    for f,v in EVENT_FIELDS.items():
        if f.endswith('Amount'):check((D(e[f])*WEI==D(v)), 'Validation failed: D(e[f]) * WEI == D(v)')
        else:check((e[f]['id']==v), "Validation failed: e[f]['id'] == v")
    check((e['timestamp']==1789163883 and int(e['transaction']['blockNumber'])==504186248), "Validation failed: e['timestamp'] == 1789163883 and int(e['transaction']['blockNumber']) == 504186248")
    r=next(r for r in data['rounds'] if int(r['id'])==BOUNDARY[0])
    check(((int(r['id']),r['startTimestamp'],int(r['startBlock']))==BOUNDARY), "Validation failed: (int(r['id']), r['startTimestamp'], int(r['startBlock'])) == BOUNDARY")
    events=sorted([e for rows in data['events'].values() for e in rows],
                  key=lambda e:(e['timestamp'],int(e['transaction']['blockNumber']),identity(e)[1]))
    before=[e for e in events if e['timestamp']<BOUNDARY[1]]
    after=[e for e in events if e['timestamp']>=BOUNDARY[1]]
    for e,anchor in zip([before[0],before[-1],after[0],after[-1]],BOUNDARY_EVENTS):
        check(((e['id'],e['timestamp'],int(e['round']['id']))==anchor), "Validation failed: (e['id'], e['timestamp'], int(e['round']['id'])) == anchor")
    ranked=sorted(data['transcoders'][str(END)],key=lambda x:(-D(x['totalStake']),x['id']))
    check((ranked[16]['id']==END_RANK17_ADDRESS), "Validation failed: ranked[16]['id'] == END_RANK17_ADDRESS")
    check((D(ranked[16]['totalStake'])==D(END_RANK17_LPT)), "Validation failed: D(ranked[16]['totalStake']) == D(END_RANK17_LPT)")
    check((threshold([D(r['totalStake']) for r in ranked])[3]==D(END_BASE_THRESHOLD_LPT)), "Validation failed: threshold([D(r['totalStake']) for r in ranked])[3] == D(END_BASE_THRESHOLD_LPT)")

    check(redistribution_threshold([D(r['totalStake']) for r in ranked])==END_REDISTRIBUTION,
          'End-checkpoint redistribution constant differs')


def verify():
    doc,data=load()
    check((doc['integrity']['content_sha256']==EXPECTED_CONTENT_SHA256), "Validation failed: doc['integrity']['content_sha256'] == EXPECTED_CONTENT_SHA256")
    check(({k:len(v) for k,v in data['events'].items()}=={'bondEvents':605,'unbondEvents':2670,'rebondEvents':1466,'transferBondEvents':1391,'withdrawStakeEvents':1186,'winningTicketRedeemedEvents':15263}), "Validation failed: {k: len(v) for k, v in data['events'].items()} == {'bondEvents': 605, 'unbondEvents': 2670, 'rebondEvents': 1466, 'transferBondEvents': 1391, 'withdrawStakeEvents': 1186, 'winningTicketRedeemedEvents': 15263}")
    check((TOPICS==TOPIC_FIXTURES), 'Validation failed: TOPICS == TOPIC_FIXTURES')
    check((keccak('Transfer(address,address,uint256)')=='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'), "Validation failed: keccak('Transfer(address,address,uint256)') == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'")
    for row in doc['provenance']['sources'].values():
        raw=zlib.decompress(base64.b64decode(row['raw_response_zlib_base64']))
        check((hashlib.sha256(raw).hexdigest()==row['raw_response_sha256']), "Validation failed: hashlib.sha256(raw).hexdigest() == row['raw_response_sha256']")
        # All request URLs are the fixed unkeyed endpoints. Headers are not retained.
        check((row['endpoint'] in ('https://arb1.arbitrum.io/rpc','https://arbitrum-one.public.blastapi.io',
          'https://gateway.thegraph.com/api/subgraphs/id/FE63YgkzcpVocxdCEyEYbvjYqEf2kb1A6daMYRxmejYC')), "Validation failed: row['endpoint'] in ('https://arb1.arbitrum.io/rpc', 'https://arbitrum-one.public.blastapi.io', 'https://gateway.thegraph.com/api/subgraphs/id/FE63YgkzcpVocxdCEyEYbvjYqEf2kb1A6daMYRxmejYC')")
        check(('Authorization' not in row and 'headers' not in row), "Validation failed: 'Authorization' not in row and 'headers' not in row")
    for block,h in PINS.items():
        check((data['headers'][str(block)]['hash']==h), "Validation failed: data['headers'][str(block)]['hash'] == h")
    check((doc['capture']['pinned_hashes']=={str(k):v for k,v in PINS.items()}), "Validation failed: doc['capture']['pinned_hashes'] == {str(k): v for k, v in PINS.items()}")
    check((doc['capture']['subgraph_meta']['hasIndexingErrors'] is False), "Validation failed: doc['capture']['subgraph_meta']['hasIndexingErrors'] is False")
    check((doc['capture']['subgraph_meta']['deployment']=='QmRX3dyH6DgftucraNNQ8szgP625VhVP7XCubFbchQuJDw'), "Validation failed: doc['capture']['subgraph_meta']['deployment'] == 'QmRX3dyH6DgftucraNNQ8szgP625VhVP7XCubFbchQuJDw'")
    for name,refs in doc['data']['events'].items():
        last=''
        for ref in refs:
            source=doc['provenance']['sources'][ref]
            check((source['request']['variables']=={'b':END,'last':last}), "Validation failed: source['request']['variables'] == {'b': END, 'last': last}")
            query=source['request']['query']
            check(('first:1000' in query and 'orderBy:id' in query and 'orderDirection:asc' in query), "Validation failed: 'first:1000' in query and 'orderBy:id' in query and ('orderDirection:asc' in query)")
            check(('timestamp_gte:1784246400' in query and 'timestamp_lt:1792022400' in query), "Validation failed: 'timestamp_gte:1784246400' in query and 'timestamp_lt:1792022400' in query")
            check(('block:{number:$b}' in query and 'id_gt:$last' in query), "Validation failed: 'block:{number:$b}' in query and 'id_gt:$last' in query")
            rows=response(source)['data'][name]
            check((all(e['id']>last for e in rows)), "Validation failed: all((e['id'] > last for e in rows))")
            check(([e['id'] for e in rows]==sorted(e['id'] for e in rows)), "Validation failed: [e['id'] for e in rows] == sorted((e['id'] for e in rows))")
            if rows:last=rows[-1]['id']
    for b,refs in doc['data']['transcoders'].items():
        last=''
        for ref in refs:
            source=doc['provenance']['sources'][ref]
            check((source['request']['variables']=={'b':int(b),'last':last}), "Validation failed: source['request']['variables'] == {'b': int(b), 'last': last}")
            rows=response(source)['data']['transcoders']
            check((all(e['id']>last for e in rows)), "Validation failed: all((e['id'] > last for e in rows))")
            if rows:last=rows[-1]['id']
    for rows in data['events'].values():
        for e in rows:
            check((T0<=e['timestamp']<T1), "Validation failed: T0 <= e['timestamp'] < T1")
            check((START<=int(e['transaction']['blockNumber'])<=END), "Validation failed: START <= int(e['transaction']['blockNumber']) <= END")
    # Prove complete contiguous coverage for both raw-log filters, not just matching totals.
    for contract in ('0x35bcf3c30594191d53231e4ff333e8a770453e40','0xa8bb618b1520e284046f3dfc448851a1ff26e41b'):
        chunks=[]
        for ref in doc['data']['logs']:
            source=doc['provenance']['sources'][ref]
            filt=source['request']['params'][0]
            if filt['address'].lower()!=contract:continue
            a,b=int(filt['fromBlock'],16),int(filt['toBlock'],16)
            check((b-a+1<=1000000), 'Validation failed: b - a + 1 <= 1000000')
            chunks.append((a,b))
        cursor=START
        for a,b in sorted(chunks):check((a==cursor), 'Validation failed: a == cursor');cursor=b+1
        check((cursor==END+1), 'Validation failed: cursor == END + 1')
    rounds=sorted(data['rounds'],key=lambda r:int(r['id']))
    check((rounds[0]['startTimestamp']<=T0<rounds[1]['startTimestamp']), "Validation failed: rounds[0]['startTimestamp'] <= T0 < rounds[1]['startTimestamp']")
    check((rounds[-1]['startTimestamp']<T1), "Validation failed: rounds[-1]['startTimestamp'] < T1")
    check(([int(r['id']) for r in rounds]==list(range(int(rounds[0]['id']),int(rounds[-1]['id'])+1))), "Validation failed: [int(r['id']) for r in rounds] == list(range(int(rounds[0]['id']), int(rounds[-1]['id']) + 1))")
    for e in [e for rows in data['events'].values() for e in rows]:
        i=int(e['round']['id'])-int(rounds[0]['id'])
        check((e['timestamp']>=rounds[i]['startTimestamp']), "Validation failed: e['timestamp'] >= rounds[i]['startTimestamp']")
        if i+1<len(rounds):check((e['timestamp']<rounds[i+1]['startTimestamp']), "Validation failed: e['timestamp'] < rounds[i + 1]['startTimestamp']")
    historical=response(doc['provenance']['sources'][doc['capture']['historical_meta_source']])['data']['_meta']
    check((historical['hasIndexingErrors'] is False and historical['block']['number']==END), "Validation failed: historical['hasIndexingErrors'] is False and historical['block']['number'] == END")
    sg,rpc=reconcile(data)
    expected_raw={(e['transaction_hash'],int(e['log_index'])):(e['event'],e['fields']) for e in data['rpc_log_decoded']}
    check((hashlib.sha256(canonical(data['rpc_log_decoded'])).hexdigest()==doc['data']['rpc_log_decoded']['sha256']), "Validation failed: hashlib.sha256(canonical(data['rpc_log_decoded'])).hexdigest() == doc['data']['rpc_log_decoded']['sha256']")
    check((len(expected_raw)==len(rpc)), 'Validation failed: len(expected_raw) == len(rpc)')
    check((all(expected_raw[k]==decode(log) for k,log in rpc.items())), 'Validation failed: all((expected_raw[k] == decode(log) for k, log in rpc.items()))')
    links,internal=transfer_links(data)
    check((all(not e['unresolved'] for e in links)), "Validation failed: all((not e['unresolved'] for e in links))")
    # Synthetic constant stakes [9,8,7,6,5] and a 3-of-5 majority:
    # 3 newcomers each need >7: minimum integer-wei example 21 LPT + 3 wei.
    n,rank,cutoff,total=threshold([D(9),D(8),D(7),D(6),D(5)],seats=5,majority=3)
    check(((n,rank,cutoff,total)==(3,3,D(7),D('21.000000000000000003'))), "Validation failed: (n, rank, cutoff, total) == (3, 3, D(7), D('21.000000000000000003'))")
    # If rank 1 is already coordinated, two newcomers each need >6.
    check((threshold([D(9),D(8),D(7),D(6),D(5)],seats=5,majority=3,existing=1)==(2,4,D(6),D('12.000000000000000002'))), "Validation failed: threshold([D(9), D(8), D(7), D(6), D(5)], seats=5, majority=3, existing=1) == (2, 4, D(6), D('12.000000000000000002'))")
    for row in data['state']:
        w=words(row['raw'])
        if row['signature']=='unbondingPeriod()':check((w==[7]), 'Validation failed: w == [7]')
        if row['signature']=='getDelegator(address)' and row['purpose']=='checkpoint':
            op=next(o for o in data['transcoders'][str(row['block'])] if o['id']==row['address'])
            check((D(op['totalStake'])*WEI==w[3]), "Validation failed: D(op['totalStake']) * WEI == w[3]")
    overlap=[e for e in data['events']['winningTicketRedeemedEvents'] if 1788912000<=e['timestamp']<1791504000]
    check((len(overlap)==4947), 'Validation failed: len(overlap) == 4947')
    check((sum((D(e['faceValue']) for e in overlap),D(0))==D('11.998719486500145860')), "Validation failed: sum((D(e['faceValue']) for e in overlap), D(0)) == D('11.998719486500145860')")
    check((sum((D(e['faceValueUSD']) for e in overlap),D(0))==D('31127.7394837736766048862027292859291538')), "Validation failed: sum((D(e['faceValueUSD']) for e in overlap), D(0)) == D('31127.7394837736766048862027292859291538')")
    check_anchors(data,sg,rpc)
    anchors=check_transfer_anchors(data)
    slow=slow_path_changes(data)
    expected_slow={
        'standalone rebond to different delegate':(3,D('339.525'),2),
        'later new-bond-class Bond to different delegate':(7,D('320278.299237065757191033'),2),
    }
    for kind,expected in expected_slow.items():
        selected=[r for r in slow if r['path']==kind]
        actual=(len(selected),sum((r['amount_lpt'] for r in selected),D(0)),
                sum(r['before_withdraw_eligibility'] for r in selected))
        check(actual==expected,'Slow-path constant differs: '+kind)
    with TemporaryDirectory(prefix='p1-verify-') as tmp:
        path=Path(tmp)/'tampered.json'
        changed=deepcopy(doc);changed['capture']['chain_id']=1
        path.write_text(json.dumps(changed))
        try:load(path)
        except ValueError:pass
        else:raise AssertionError('Tampered extract accepted')
    print('PASS: integrity, every raw response hash, fixed pins, query pagination, log-range coverage and event windows.')
    print('PASS: '+str(len(sg))+' events match one-to-one with RPC; every shared ABI field and amount exact.')
    print('PASS: transfer ordering, historical pool stake, unbonding period, slow paths, threshold constants and tamper rejection.')
    print('PASS: previous-block anchors: 1382 compared, 9 excluded, 0 mismatches.')


if __name__=='__main__':verify()
