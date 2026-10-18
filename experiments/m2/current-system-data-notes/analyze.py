"""Offline P1 tables. Decimal arithmetic; no network calls."""
import csv
import hashlib
import json
from collections import defaultdict, Counter
from datetime import datetime, timezone
from decimal import Decimal as D, getcontext
from pathlib import Path
from statistics import median
from extract import FILE, HERE, START, END, T0, T1, PINS, CHECKPOINTS, TOPICS, canonical, materialize, decode

getcontext().prec = 100
ZERO = '0x'+'0'*40
WEI = D(10)**18
DISCLAIMER = 'This is a stake threshold under stated assumptions, not an acquisition cost. The cost of acquiring control stays unknown unless evidence supports it.'


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def load(path=FILE):
    doc = json.loads(Path(path).read_text())
    actual = hashlib.sha256(canonical({k:v for k,v in doc.items() if k!='integrity'})).hexdigest()
    if actual != doc['integrity']['content_sha256']: raise ValueError('Extract integrity differs')
    return doc,materialize(doc)


def words(raw): return [int(raw[i:i+64],16) for i in range(2,len(raw),64)]
def address(topic): return '0x'+topic[-40:].lower()
def identity(e):
    # The Graph id is tx hash + '-' + the decimal, block-wide log index.
    tx,index = e['id'].rsplit('-',1)
    check((tx == e['transaction']['id']), "Validation failed: tx == e['transaction']['id']")
    return tx.lower(),int(index)

def log_identity(e): return e['transactionHash'].lower(),int(e['logIndex'],16)
def day(ts): return datetime.fromtimestamp(ts,timezone.utc).date().isoformat()
def lpt(raw): return D(raw)/WEI


def reconcile(data):
    sg = {identity(e):(name,e) for name,rows in data['events'].items() for e in rows}
    rpc = {log_identity(e):e for e in data['logs']}
    check((len(sg)==sum(map(len,data['events'].values()))), 'Duplicate subgraph identity')
    check((len(rpc)==len(data['logs'])), 'Duplicate RPC identity')
    if sg.keys()!=rpc.keys():
        raise ValueError('STOP: event sets disagree; subgraph-only='+str(len(sg.keys()-rpc.keys()))+' RPC-only='+str(len(rpc.keys()-sg.keys())))
    for key,(name,e) in sg.items():
        log = rpc[key]
        kind,fields = decode(log)
        check((kind==name), 'Validation failed: kind == name')
        check((int(e['transaction']['blockNumber'])==int(log['blockNumber'],16)), "Validation failed: int(e['transaction']['blockNumber']) == int(log['blockNumber'], 16)")
        for field,raw in fields.items():
            if field not in e: continue
            value = e[field]
            if field in ('amount','additionalAmount','bondedAmount','faceValue'):
                if D(value)*WEI != D(raw): raise ValueError('STOP: non-exact decimal/raw amount '+e['id']+' '+field)
            elif field in ('auxData',): check((value.lower()==raw), 'Validation failed: value.lower() == raw')
            elif raw.startswith('0x'):
                check(((value['id'] if value else ZERO).lower()==raw), "Validation failed: (value['id'] if value else ZERO).lower() == raw")
            else: check((int(value)==int(raw)), 'Validation failed: int(value) == int(raw)')
    return sg,rpc


def write(name,rows,columns=None):
    rows=list(rows)
    path=HERE/'tables'/name
    path.parent.mkdir(exist_ok=True)
    cols=columns or list(rows[0])
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=cols);writer.writeheader();writer.writerows(rows)


def amount(name,e):
    return D(e['additionalAmount'] if name=='bondEvents' else e['faceValue'] if name=='winningTicketRedeemedEvents' else e['amount'])


def coverage(data,sg,rpc):
    out=[]
    for lo in list(range(START,END+1,1000000))+[None]:
        hi=min(lo+999999,END) if lo else None
        for name in TOPICS:
            selected=[e for e in data['events'][name] if lo is None or lo<=int(e['transaction']['blockNumber'])<=hi]
            logs=[v for v in data['logs'] if v['topics'][0]==TOPICS[name] and (lo is None or lo<=int(v['blockNumber'],16)<=hi)]
            sf='additionalAmount' if name=='bondEvents' else 'faceValue' if name=='winningTicketRedeemedEvents' else 'amount'
            raw=sum(int(decode(e)[1][sf]) for e in logs)
            s=sum((amount(name,e) for e in selected),D(0))
            check((s*WEI==raw and len(selected)==len(logs)), 'Validation failed: s * WEI == raw and len(selected) == len(logs)')
            out.append({'start_block':lo or 'TOTAL','end_block':hi or 'TOTAL','event':name,
                'subgraph_count':len(selected),'rpc_count':len(logs),'subgraph_amount_tokens':s,
                'rpc_amount_wei':str(raw),'amount_field':sf,'one_to_one':'exact'})
    write('coverage.csv',out)
    # Lossless ABI decoding table, decimal integer strings; original logs remain in extract.
    decoded=[]
    for e in data['logs']:
        name,fields=decode(e)
        decoded.append({'tx_hash':e['transactionHash'],'log_index':int(e['logIndex'],16),'event':name,
                        'block':int(e['blockNumber'],16),'decoded_fields_raw_units':json.dumps(fields,sort_keys=True)})
    write('rpc-decoded.csv',decoded)


def transfer_links(data):
    bytx=defaultdict(list)
    for name,rows in data['events'].items():
        for e in rows: bytx[identity(e)[0]].append((identity(e)[1],name,e))
    links=[];internal=set()
    for transfer in data['events']['transferBondEvents']:
        tx,idx=identity(transfer)
        ordered=sorted(bytx[tx])
        before=[e for i,n,e in ordered if i<idx and n=='unbondEvents' and e['delegator']==transfer['oldDelegator'] and e['unbondingLockId']==transfer['oldUnbondingLockId']]
        after=[e for i,n,e in ordered if i>idx and n=='rebondEvents' and e['delegator']==transfer['newDelegator'] and e['unbondingLockId']==transfer['newUnbondingLockId']]
        if len(before)!=1 or len(after)!=1:
            raise ValueError('Unresolved TransferBond event sequence '+transfer['id'])
        old,new=before[0],after[0]
        check((D(old['amount'])==D(new['amount'])==D(transfer['amount'])), "Validation failed: D(old['amount']) == D(new['amount']) == D(transfer['amount'])")
        internal.update((old['id'],new['id']))
        links.append({'id':transfer['id'],'old_delegator':transfer['oldDelegator']['id'],
            'new_delegator':transfer['newDelegator']['id'],'old_delegate':old['delegate']['id'],
            'new_delegate':new['delegate']['id'],'amount_lpt':transfer['amount'],
            'cross_delegate':old['delegate']!=new['delegate'],'method':'same-transaction ordered Unbond / TransferBond / Rebond, matching delegator and lock ids',
            'unbond_id':old['id'],'rebond_id':new['id'],'unresolved':False})
    return links,internal


def slow_path_changes(data):
    """In-window delegate changes through rebond or a later new-bond-class Bond.

    Matching rebond locks identifies the same stake. The later-Bond comparison
    identifies a sequence for the same delegator, not the source of its funds.
    Neither path is added to instant bond() redelegation or transfer turnover.
    """
    _,internal=transfer_links(data)
    order=lambda e:(int(e['transaction']['blockNumber']),identity(e)[1])
    unbonds=sorted(data['events']['unbondEvents'],key=order)
    locks={(e['delegator']['id'],e['unbondingLockId']):e for e in unbonds if e['id'] not in internal}
    rows=[]
    for name in ('rebondEvents','bondEvents'):
        for event in data['events'][name]:
            if name=='rebondEvents':
                if event['id'] in internal:continue
                unbond=locks.get((event['delegator']['id'],event['unbondingLockId']))
                new=event['delegate']['id'];value=event['amount']
                path='standalone rebond to different delegate'
                basis='same delegator and unbonding lock; same stake'
            else:
                if event['oldDelegate'] and event['oldDelegate']['id']!=ZERO:continue
                earlier=[u for u in unbonds if u['delegator']==event['delegator'] and order(u)<order(event)]
                unbond=earlier[-1] if earlier else None
                new=event['newDelegate']['id'];value=event['additionalAmount']
                path='later new-bond-class Bond to different delegate'
                basis='same delegator; latest preceding in-window unbond; funding is not traced'
            if not unbond or unbond['delegate']['id']==new:continue
            check(order(unbond)<order(event),'Unbond must precede its matched later event')
            rows.append({'path':path,'unbond_id':unbond['id'],'event_id':event['id'],
                'delegator':event['delegator']['id'],'old_delegate':unbond['delegate']['id'],
                'new_delegate':new,'amount_lpt':D(value),'matching_basis':basis,
                'lag_rounds':int(event['round']['id'])-int(unbond['round']['id']),
                'lag_days':D(event['timestamp']-unbond['timestamp'])/86400,
                'withdraw_eligibility_round':unbond['withdrawRound'],'event_round':event['round']['id'],
                'before_withdraw_eligibility':int(event['round']['id'])<int(unbond['withdrawRound']),
                'wait_limit':'seven-round wait applies to withdrawal, not necessarily rebond or a later Bond using other funds'})
    return sorted(rows,key=lambda r:(r['path'],r['event_id']))


def redistribution_threshold(stakes,majority=17):
    """Smallest j fully removed largest donor pools funding majority new nodes.

    All remaining incumbents retain their stake. Unused donor stake stays outside
    eligible nodes. Control and the ability to move every donor token are premises.
    """
    available=D(0)
    for j in range(1,len(stakes)-majority+1):
        available+=stakes[j-1]
        cutoff=majority+j
        required=D(majority)*(stakes[cutoff-1]+D(1)/WEI)
        if available>required:return j,available,cutoff,required
    raise ValueError('No donor subset satisfies the stated redistribution premise')


def movement(data):
    links,internal=transfer_links(data); link_by={e['id']:e for e in links}
    write('transfer-attribution.csv',links)
    # verify.py cross-checks previous-block anchors unless an earlier same-block
    # event touches the old delegator, excluding this transfer's own Unbond.
    movements=[];flow=defaultdict(lambda:[D(0),D(0),0])
    delegators=defaultdict(lambda:[0,D(0)])
    voluntary_locks={}
    lags=[]
    for name,rows in data['events'].items():
        if name=='winningTicketRedeemedEvents':continue
        for e in rows:
            category=name;value=amount(name,e);old=new='';moved=D(0)
            if name=='bondEvents':
                old=(e['oldDelegate'] or {'id':ZERO})['id'];new=e['newDelegate']['id']
                category='new_bond' if old==ZERO else 'top_up' if old==new else 'redelegation'
                moved=D(e['bondedAmount'])-D(e['additionalAmount']) if category=='redelegation' else D(0)
                flow[(new,category)][0]+=value+moved;flow[(new,category)][2]+=1
                if moved:flow[(old,category)][1]+=moved;flow[(old,category)][2]+=1
            elif name=='unbondEvents':
                old=e['delegate']['id'];flow[(old,name)][1]+=value;flow[(old,name)][2]+=1
                if e['id'] not in internal: voluntary_locks[(e['delegator']['id'],e['unbondingLockId'])]=e
            elif name=='rebondEvents':
                new=e['delegate']['id'];flow[(new,name)][0]+=value;flow[(new,name)][2]+=1
            elif name=='transferBondEvents':
                old=link_by[e['id']]['old_delegate'];new=link_by[e['id']]['new_delegate']
                # its component Unbond/Rebond already account for orchestrator flow
            else:
                key=(e['delegator']['id'],e['unbondingLockId'])
                if key in voluntary_locks:
                    unbond=voluntary_locks[key]
                    old=unbond['delegate']['id']
                    lags.append({'delegator':key[0],'lock_id':key[1],'unbond_id':unbond['id'],'withdraw_id':e['id'],
                      'amount_lpt':e['amount'],'lag_rounds':int(e['round']['id'])-int(unbond['round']['id']),
                      'lag_days':D(e['timestamp']-unbond['timestamp'])/86400,
                      'withdraw_eligibility_round':unbond['withdrawRound']})
            actors=[e['delegator']['id']] if 'delegator' in e else [e['oldDelegator']['id'],e['newDelegator']['id']]
            for actor in actors:
                delegators[(actor,category)][0]+=1;delegators[(actor,category)][1]+=value
            movements.append({'id':e['id'],'event':name,'category':category,'day':day(e['timestamp']),
              'round':int(e['round']['id']),'amount_lpt':value,'redelegated_existing_lpt':moved,
              'old_delegate':old,'new_delegate':new,'delegators':','.join(actors),'transfer_component':e['id'] in internal})
    # withdrawals appear after unbonds in collection iteration; both ends within window only.
    write('movement-events.csv',movements)
    orch_counts=defaultdict(lambda:[0,D(0)])
    for m in movements:
        actors=set((m['old_delegate'],m['new_delegate']))-{ZERO,''}
        if not actors and m['category']=='withdrawStakeEvents':actors={'unattributed: unbond outside window'}
        for actor in actors:
            v=orch_counts[(actor,m['category'])];v[0]+=1;v[1]+=m['amount_lpt']
    write('movement-counts-by-orchestrator.csv',[
        {'orchestrator':k[0],'category':k[1],'count':v[0],'event_amount_lpt':v[1],
         'note':'event counts; transfer components overlap; withdrawal has no additional active-pool flow'}
        for k,v in sorted(orch_counts.items())])
    ownership=defaultdict(lambda:[D(0),D(0),0])
    for x in links:
        ownership[x['old_delegator']][1]+=D(x['amount_lpt']);ownership[x['old_delegator']][2]+=1
        ownership[x['new_delegator']][0]+=D(x['amount_lpt']);ownership[x['new_delegator']][2]+=1
    write('transfer-by-delegator.csv',[
        {'delegator':k,'count':v[2],'inflow_lpt':v[0],'outflow_lpt':v[1],'net_lpt':v[0]-v[1]}
        for k,v in sorted(ownership.items())])

    write('unbond-withdraw-lags.csv',lags,columns=['delegator','lock_id','unbond_id','withdraw_id','amount_lpt','lag_rounds','lag_days','withdraw_eligibility_round'])
    for key in ('day','round'):
        grouped=defaultdict(lambda:[0,D(0),D(0),0])
        for m in movements:
            v=grouped[(m[key],m['category'])];v[0]+=1;v[1]+=m['amount_lpt'];v[2]+=m['redelegated_existing_lpt'];v[3]+=m['transfer_component']
        periods=[day(t) for t in range(T0,T1,86400)] if key=='day' else [int(r['id']) for r in data['rounds']]
        for period in periods:
            for cat in ['new_bond','top_up','redelegation','unbondEvents','rebondEvents','transferBondEvents','withdrawStakeEvents']:
                grouped[(period,cat)]
        write('movement-by-'+key+'.csv',[{key:k[0],'category':k[1],'count':v[0],
            'amount_lpt':v[1],'redelegated_existing_lpt':v[2],'transfer_component_count':v[3]} for k,v in sorted(grouped.items())])
    for period in ('day','round'):
        for dimension in ('delegator','orchestrator'):
            group=defaultdict(lambda:[0,D(0),D(0)])
            for m in movements:
                if dimension=='delegator':
                    actors=m['delegators'].split(',')
                    for actor in actors:
                        v=group[(m[period],actor,m['category'])];v[0]+=1;v[1]+=m['amount_lpt'];v[2]+=m['redelegated_existing_lpt']
                else:
                    actors=set((m['old_delegate'],m['new_delegate']))-{ZERO,''}
                    for actor in actors:
                        v=group[(m[period],actor,m['category'])];v[0]+=1;v[1]+=m['amount_lpt'];v[2]+=m['redelegated_existing_lpt']
            write('movement-by-'+period+'-'+dimension+'.csv',[
                {period:k[0],dimension:k[1],'category':k[2],'count':v[0],
                 'event_amount_lpt':v[1],'redelegated_existing_lpt':v[2]}
                for k,v in sorted(group.items())])
    ledger=defaultdict(lambda:[0,D(0),D(0),D(0)])
    for m in movements:
        for actor in m['delegators'].split(','):
            v=ledger[(actor,m['category'])];v[0]+=1
            if m['event'] in ('bondEvents','rebondEvents'):v[1]+=m['amount_lpt']
            elif m['event']=='unbondEvents':v[2]+=m['amount_lpt']
            elif m['event']=='withdrawStakeEvents':v[3]+=m['amount_lpt']
    write('delegator-flows.csv',[
        {'delegator':k[0],'category':k[1],'count':v[0],'bonded_inflow_lpt':v[1],
         'bonded_outflow_lpt':v[2],'net_bonded_lpt':v[1]-v[2],'escrow_withdrawal_lpt':v[3],
         'note':'TransferBond components account for its bonded flow; ownership flow is separate'}
        for k,v in sorted(ledger.items())])
    expected_net=(sum((D(e['additionalAmount']) for e in data['events']['bondEvents']),D(0))
        +sum((D(e['amount']) for e in data['events']['rebondEvents']),D(0))
        -sum((D(e['amount']) for e in data['events']['unbondEvents']),D(0)))
    check((sum((v[0]-v[1] for v in flow.values()),D(0))==expected_net), 'Validation failed: sum((v[0] - v[1] for v in flow.values()), D(0)) == expected_net')
    check((sum((v[1]-v[2] for v in ledger.values()),D(0))==expected_net), 'Validation failed: sum((v[1] - v[2] for v in ledger.values()), D(0)) == expected_net')
    write('movement-by-delegator.csv',[{'delegator':k[0],'category':k[1],'count':v[0],'amount_lpt':v[1]} for k,v in sorted(delegators.items())])
    write('movement-by-orchestrator.csv',[{'orchestrator':k[0],'category':k[1],'count':v[2],'inflow_lpt':v[0],'outflow_lpt':v[1],'net_lpt':v[0]-v[1]} for k,v in sorted(flow.items())])
    write('transfer-orchestrator-flows.csv',[{'id':x['id'],'old_delegate':x['old_delegate'],'new_delegate':x['new_delegate'],
        'amount_lpt':x['amount_lpt'],'net_pool_change_lpt':x['amount_lpt'] if x['cross_delegate'] else '0',
        'note':'already counted in component Unbond and Rebond; do not add again'} for x in links])
    measures=defaultdict(lambda:[0,D(0)])
    for m in movements:
        cat=m['category'];value=m['redelegated_existing_lpt'] if cat=='redelegation' else m['amount_lpt']
        if m['transfer_component']:cat+=' (transfer component)'
        measures[cat][0]+=1;measures[cat][1]+=value
        if m['category']=='redelegation':
            measures['additional_LPT_with_redelegation'][0]+=1
            measures['additional_LPT_with_redelegation'][1]+=m['amount_lpt']
    count=sum(x['cross_delegate'] for x in links)
    measures['transfer_cross_delegate_only']=[count,sum((D(x['amount_lpt']) for x in links if x['cross_delegate']),D(0))]
    denominators={r['block']:lpt(int(r['raw'],16)) for r in data['state'] if r['signature']=='getTotalBonded()'}
    nr=len(data['rounds'])
    out=[]
    for cat,(count,value) in sorted(measures.items()):
        for block in (CHECKPOINTS[0],END):
            for period,scale in [('90-day window',D(1)),('30 days',D(1)/3),('UTC day',D(1)/90),('intersecting round',D(1)/nr)]:
                out.append({'measure':cat,'period':period,'count_or_rate':D(count)*scale,'amount_lpt':value*scale,
                   'denominator_block':block,'getTotalBonded_lpt':denominators[block],
                   'fraction_of_denominator':value*scale/denominators[block],
                   'rounds_including_partial':nr,'whole_UTC_days':90})
    write('movement-rates.csv',out)
    slow=slow_path_changes(data)
    write('slow-path-delegate-changes.csv',slow)
    slow_summary=[]
    for path in sorted({row['path'] for row in slow}):
        selected=[row for row in slow if row['path']==path]
        slow_summary.append({'path':path,'count':len(selected),
            'amount_lpt':sum((row['amount_lpt'] for row in selected),D(0)),
            'min_lag_rounds':min(row['lag_rounds'] for row in selected),
            'max_lag_rounds':max(row['lag_rounds'] for row in selected),
            'before_withdraw_eligibility_count':sum(row['before_withdraw_eligibility'] for row in selected),
            'scope':'separate from instant bond() redelegation; later Bond funding not established'})
    write('slow-path-summary.csv',slow_summary)
    return {'measures':{k:{'count':v[0],'lpt':str(v[1])} for k,v in measures.items()},'transfer_unresolved':0,
            'slow_paths':[{k:str(v) for k,v in row.items()} for row in slow_summary],
            'lag_count':len(lags),'lag_rounds_median':str(median([x['lag_rounds'] for x in lags])) if lags else None}


def threshold(stakes,seats=33,majority=17,declined=0,existing=0):
    # Largest `declined` incumbent ranks decline, then largest `existing`
    # participating incumbent ranks are already coordinated. Fresh nodes displace
    # the lowest needed seats. Incumbent stakes remain fixed.
    m=majority-existing
    cutoff=seats-m+1+declined
    return m,cutoff,stakes[cutoff-1],D(m)*stakes[cutoff-1]+D(m)/WEI


def concentration(data):
    rows=[];summary=[];thresholds=[]
    for block,ops in sorted(data['transcoders'].items(),key=lambda x:int(x[0])):
        ranked=sorted(ops,key=lambda x:(-D(x['totalStake']),x['id']))
        total=sum((D(x['totalStake']) for x in ranked),D(0));cum=D(0)
        stakes=[D(x['totalStake']) for x in ranked]
        for rank,op in enumerate(ranked,1):
            cum+=D(op['totalStake'])
            rows.append({'block':block,'rank':rank,'address':op['id'],'stake_lpt':op['totalStake'],
              'active':op['active'],'status':op['status'],'activation_round':op['activationRound'],
              'deactivation_round':op['deactivationRound'],'fee_share_raw':op['feeShare'],'reward_cut_raw':op['rewardCut'],
              'share_of_all_indexed_transcoder_stake':D(op['totalStake'])/total,
              'cumulative_share':cum/total})
        s={'block':block,'all_indexed_transcoders':len(ops),'positive_stake_transcoders':sum(x>0 for x in stakes),
           'active_flag_count':sum(x['active'] for x in ranked),'total_live_pool_stake_lpt':total,
           'rank_17_lpt':stakes[16],'rank_33_lpt':stakes[32],'rank_100_lpt':stakes[99],
           'top_100_inactive_flag_count':sum(not x['active'] for x in ranked[:100]),
           'top_33_registered_count':sum(x['status']=='Registered' for x in ranked[:33]),
           'lowest_active_flag_stake_lpt':min(D(x['totalStake']) for x in ranked if x['active']),
           'lowest_active_flag_global_rank':max(i+1 for i,x in enumerate(ranked) if x['active'])}
        for target in ('0.333','0.5','0.667'):
            cum=D(0)
            for rank,x in enumerate(stakes,1):
                cum+=x
                if cum/total>=D(target):break
            s['nodes_for_'+target]=rank
        summary.append(s)
        for d in (0,5,10,16):
            for k in ((0,1,3,5) if d==0 else (0,)):
                m,cutoff,stake,value=threshold(stakes,declined=d,existing=k)
                thresholds.append({'block':block,'variant':'new capital' if not d and not k else 'declined seats' if d else 'existing holdings',
                  'declined_ranks':'1..'+str(d) if d else 'none','existing_coordinated_ranks':'1..'+str(k) if k else 'none',
                  'new_nodes':m,'cutoff_original_rank':cutoff,'stake_per_node_exclusive_lpt':stake,
                  'threshold_total_lpt_including_one_wei_per_node':value,
                  'donor_pool_count':'','available_donor_stake_lpt':'',
                  'source_of_stake':'new capital; coordinated existing seat stake excluded from new requirement',
                  'assumptions':'top 33 participating nodes by stake; declined seats pass down; largest k participating incumbents already coordinated; all remaining incumbents fixed; equal new-node stake; 17/33 majority',
                  'disclaimer':DISCLAIMER})
        # Conditional existing-capital redistribution; donor does not already
        # hold a majority of seats in these measured cases.
        j,available,cutoff,value=redistribution_threshold(stakes)
        thresholds.append({'block':block,'variant':'smallest j donor pools redistribution',
          'declined_ranks':'none','existing_coordinated_ranks':'all stake behind original ranks 1..'+str(j)+' is assumed controllable and fully removed',
          'new_nodes':17,'cutoff_original_rank':cutoff,'stake_per_node_exclusive_lpt':stakes[cutoff-1],
          'threshold_total_lpt_including_one_wei_per_node':value,
          'donor_pool_count':j,'available_donor_stake_lpt':available,
          'source_of_stake':'existing stake; unused donor stake stays outside eligible nodes; no new capital',
          'assumptions':"smallest j whose largest-pool stake exceeds 17*(original rank 17+j stake + 1 wei); donor controls and can move all stake of those j pools, which are emptied; other pools unchanged; 17 equally staked new registered nodes; ownership/control not observed; today's seven-round withdrawal wait, instant bond redelegation and transferBond; eligibility can start next round",
          'disclaimer':DISCLAIMER})
    write('stake-concentration.csv',rows);write('stake-summary.csv',summary);write('seat-thresholds.csv',thresholds)
    return [{k:str(v) for k,v in row.items()} for row in summary]


def fees(data):
    tickets=data['events']['winningTicketRedeemedEvents']
    rounds=sorted(data['rounds'],key=lambda x:int(x['id']))
    round_lookup={int(r['id']):r for r in rounds}
    grouped={key:defaultdict(lambda:[0,D(0),D(0)]) for key in ('day','round','sender','recipient')}
    for e in tickets:
        for key,value in [('day',day(e['timestamp'])),('round',int(e['round']['id'])),('sender',e['sender']['id']),('recipient',e['recipient']['id'])]:
            v=grouped[key][value];v[0]+=1;v[1]+=D(e['faceValue']);v[2]+=D(e.get('faceValueUSD','0'))
    for t in range(T0,T1,86400):grouped['day'][day(t)]
    out_round=[]
    for i,r in enumerate(rounds):
        rid=int(r['id']);v=grouped['round'][rid]
        end=int(rounds[i+1]['startTimestamp']) if i+1<len(rounds) else None
        partial=int(r['startTimestamp'])<T0 or end is None or end>T1
        out_round.append({'round':rid,'start_timestamp':r['startTimestamp'],'end_timestamp_exclusive':end,
             'start_L1_block':r['startBlock'],'length_L1_blocks':r['length'],'partial':partial,
             'count':v[0],'fees_eth':v[1],'fees_usd_indexed':v[2]})
    write('fees-by-round.csv',out_round)
    for key in ('day','sender','recipient'):
        write('fees-by-'+key+'.csv',[{key:k,'count':v[0],'fees_eth':v[1],'fees_usd_indexed':v[2]} for k,v in sorted(grouped[key].items())])
    med=median([r['fees_eth'] for r in out_round if not r['partial']])
    spikes=[]
    for row in sorted((r for r in out_round if not r['partial']),key=lambda r:r['fees_eth'],reverse=True)[:5]:
        ts=[e for e in tickets if int(e['round']['id'])==row['round']]
        def dominant(field):
            totals=defaultdict(D)
            for e in ts:totals[e[field]['id']]+=D(e['faceValue'])
            who=max(totals,key=totals.get)
            return who,totals[who]
        recipient,rf=dominant('recipient');sender,sf=dominant('sender')
        spikes.append({**row,'round_start_day':day(row['start_timestamp']),
            'redemption_days':','.join(sorted({day(e['timestamp']) for e in ts})),
            'median_complete_round_eth':med,'ratio_to_median':row['fees_eth']/med if med else 'undefined',
            'dominant_recipient':recipient,'dominant_recipient_eth':rf,'dominant_sender':sender,'dominant_sender_eth':sf,
            'label':'redemptions measure settlement, not jobs or independent customer demand'})
    write('fee-spikes.csv',spikes)
    # Frozen baseline is loaded through its hash-checking reader. No mutable price quote.
    import importlib.util
    spec=importlib.util.spec_from_file_location('p1_snapshot',HERE.parent/'network-snapshot'/'read_snapshot.py')
    reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
    snapshot=reader.load_snapshot()
    old=snapshot['provenance']['sources']['tickets']['data']['events']
    overlap=[e for e in tickets if 1788912000<=e['timestamp']<1791504000]
    ids_old={e['id']:e for e in old};ids_new={e['id']:e for e in overlap}
    overlap_rows=[]
    for field in ('faceValue','faceValueUSD'):
        a=sum((D(e[field]) for e in old),D(0));b=sum((D(e[field]) for e in overlap),D(0))
        overlap_rows.append({'field':field,'snapshot_count':len(old),'p1_count':len(overlap),
            'snapshot_sum':a,'p1_sum':b,'difference':b-a,'snapshot_only_ids':len(ids_old.keys()-ids_new.keys()),
            'p1_only_ids':len(ids_new.keys()-ids_old.keys()),'same_ids':ids_old.keys()==ids_new.keys(),
            'per_event_amounts_exact':all(D(ids_old[k][field])==D(ids_new[k][field]) for k in ids_old.keys()&ids_new.keys()),
            'snapshot_content_sha256':snapshot['integrity']['content_sha256']})
    write('snapshot-overlap.csv',overlap_rows)
    return {'count':len(tickets),'eth':str(sum((D(e['faceValue']) for e in tickets),D(0))),
        'usd_indexed':str(sum((D(e['faceValueUSD']) for e in tickets),D(0))),
        'complete_round_median_eth':str(med),'spikes':[{k:str(v) for k,v in s.items()} for s in spikes],
        'overlap':[{k:str(v) for k,v in r.items()} for r in overlap_rows]}


def state_checks(data):
    out=[]
    for r in data['state']:
        sig=r['signature'];w=words(r['raw']);comparison='not applicable'
        if sig=='getDelegator(address)' and r['purpose']=='checkpoint':
            op=next(o for o in data['transcoders'][str(r['block'])] if o['id']==r['address'])
            comparison=str(D(op['totalStake'])*WEI==D(w[3]))
            if comparison!='True':raise ValueError('STOP: historical stake mismatch')
        out.append({'block':r['block'],'signature':sig,'address':r['address'],
            'purpose':r['purpose'],'raw_uint256_words':json.dumps([str(v) for v in w]),
            'subgraph_pool_stake_exact':comparison})
    write('state-cross-checks.csv',out)


def main():
    doc,data=load();sg,rpc=reconcile(data)
    coverage(data,sg,rpc);state_checks(data)
    result={'label':doc['definitions']['label'],'extract_sha256':doc['integrity']['content_sha256'],
        'event_counts':{k:len(v) for k,v in data['events'].items()},'movement':movement(data),
        'concentration':concentration(data),'fees':fees(data)}
    # Only tables are generated; stdout is a bounded report aid, not a second source.
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
