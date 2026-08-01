#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import requests

POOL='0x794a61358d6845594f94dc1db02a252b5b4814ad'
BORROW='0xb3d084820fb1a9decffb176436bd02558d15fac9b0ddfed8c465bc7359d7dce0'
NETWORKS={
  'arbitrum':('arbitrum-one',7_740_000),
  'optimism':('optimism-mainnet',4_365_693),
  'polygon':('polygon-mainnet',25_825_996),
  'avalanche':('avalanche-mainnet',11_970_000),
}
OUT=Path('sqd-probe-results');OUT.mkdir(exist_ok=True)

def parse_blocks(text:str):
    text=text.strip()
    if not text:return []
    try:
        obj=json.loads(text)
        return obj if isinstance(obj,list) else [obj]
    except json.JSONDecodeError:
        out=[]
        for line in text.splitlines():
            line=line.strip()
            if line:
                try: out.append(json.loads(line))
                except json.JSONDecodeError: pass
        return out

results={}
for name,(slug,start) in NETWORKS.items():
    base=f'https://portal.sqd.dev/datasets/{slug}'
    rec={'slug':slug,'metadata':None,'windows':[]}
    try:
        m=requests.get(base+'/metadata',timeout=30)
        rec['metadata']={'status':m.status_code,'body':m.text[:2000]}
    except Exception as e:
        rec['metadata']={'exception':repr(e)}
    for a in range(start,start+200_000,50_000):
        b=a+49_999
        payload={'type':'evm','fromBlock':a,'toBlock':b,
          'fields':{'block':{'number':True,'timestamp':True},
                    'log':{'address':True,'topics':True,'data':True,'transactionHash':True,'logIndex':True}},
          'logs':[{'address':[POOL],'topic0':[BORROW]}]}
        try:
            r=requests.post(base+'/stream',json=payload,headers={'content-type':'application/json','accept-encoding':'gzip'},timeout=120)
            blocks=parse_blocks(r.text) if r.status_code==200 else []
            logs=sum(len(x.get('logs',[])) for x in blocks if isinstance(x,dict))
            last=max((x.get('header',{}).get('number',-1) for x in blocks if isinstance(x,dict)),default=None)
            rec['windows'].append({'from':a,'to':b,'status':r.status_code,'blocks':len(blocks),'logs':logs,'last_block':last,'body_prefix':r.text[:500]})
        except Exception as e:
            rec['windows'].append({'from':a,'to':b,'exception':repr(e)})
    results[name]=rec
    (OUT/f'{name}.json').write_text(json.dumps(rec,indent=2))
summary={'networks':{},'all_metadata_ok':True,'networks_with_logs':0}
for n,r in results.items():
    mok=r.get('metadata',{}).get('status')==200
    total=sum(int(x.get('logs',0) or 0) for x in r['windows'])
    summary['networks'][n]={'metadata_ok':mok,'borrow_logs_sample':total,'statuses':[x.get('status') for x in r['windows']]}
    summary['all_metadata_ok'] &= mok
    summary['networks_with_logs'] += int(total>0)
summary['qualified_for_full_extract']=summary['all_metadata_ok'] and summary['networks_with_logs']>=3
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
