#!/usr/bin/env python3
"""Frozen BCLX-R M→Q intermediate-fact test using SQD Portal raw Aave V3 logs."""
from __future__ import annotations
import argparse
import csv
import json
import math
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests
from eth_utils import keccak
from scipy.stats import fisher_exact

POOL = '0x794a61358d6845594f94dc1db02a252b5b4814ad'
CHAINS = {
    'arbitrum': {'slug':'arbitrum-one','start':7_740_000,'end':391_361_693,'address_file':'AaveV3Arbitrum.sol'},
    'optimism': {'slug':'optimism-mainnet','start':4_365_693,'end':142_662_943,'address_file':'AaveV3Optimism.sol'},
    'polygon': {'slug':'polygon-mainnet','start':25_825_996,'end':77_909_957,'address_file':'AaveV3Polygon.sol'},
    'avalanche': {'slug':'avalanche-mainnet','start':11_970_000,'end':70_593_220,'address_file':'AaveV3Avalanche.sol'},
}
EVENT_SIGS = {
    'Supply':'Supply(address,address,address,uint256,uint16)',
    'Borrow':'Borrow(address,address,address,uint256,uint8,uint256,uint16)',
    'Withdraw':'Withdraw(address,address,address,uint256)',
    'Repay':'Repay(address,address,address,uint256,bool)',
    'LiquidationCall':'LiquidationCall(address,address,address,uint256,uint256,address,bool)',
    'FlashLoan':'FlashLoan(address,address,address,uint256,uint8,uint256,uint16)',
}
TOPIC_TO_EVENT = {'0x'+keccak(text=s).hex(): n for n,s in EVENT_SIGS.items()}
TOPICS = list(TOPIC_TO_EVENT)
WINDOW_BLOCKS = 1_000_000
LABEL_DAYS = [7,30,90]
DATA_END = pd.Timestamp('2025-10-01', tz='UTC')
CANDIDATE_CUTOFF = DATA_END - pd.Timedelta(days=90)
STABLE_KEYS = ('USDC','USDT','DAI','GHO','FRAX','LUSD','SUSD','MAI','USDE','USDS','PYUSD','RLUSD','USD0','USDBC','USDCE','USDT0')


def addr_word(x: str) -> str:
    return '0x' + x[-40:].lower()

def words(data: str) -> list[str]:
    x = data[2:] if data.startswith('0x') else data
    return [x[i:i+64] for i in range(0,len(x),64) if len(x[i:i+64])==64]

def uint(w: str) -> int:
    return int(w,16) if w else 0

def parse_blocks(text: str) -> list[dict[str,Any]]:
    text=text.strip()
    if not text: return []
    try:
        obj=json.loads(text)
        return obj if isinstance(obj,list) else [obj]
    except json.JSONDecodeError:
        out=[]
        for line in text.splitlines():
            line=line.strip()
            if not line: continue
            try: out.append(json.loads(line))
            except json.JSONDecodeError: pass
        return out

def request_portal(session: requests.Session, url: str, payload: dict[str,Any]) -> requests.Response:
    for attempt in range(8):
        try:
            r=session.post(url,json=payload,headers={'content-type':'application/json','accept-encoding':'gzip'},timeout=240)
        except requests.RequestException:
            time.sleep(min(30,2**attempt)); continue
        if r.status_code==429:
            time.sleep(float(r.headers.get('retry-after','5'))+attempt); continue
        if r.status_code in (500,502,503,504):
            time.sleep(min(30,2**attempt)); continue
        return r
    raise RuntimeError(f'Portal request failed after retries: {url}')

def decode_log(chain: str, block: int, timestamp: int, log: dict[str,Any]) -> dict[str,Any] | None:
    ts=log.get('topics') or []
    if not ts: return None
    event=TOPIC_TO_EVENT.get(str(ts[0]).lower())
    if not event: return None
    w=words(str(log.get('data','0x')))
    row={'chain':chain,'block':int(block),'timestamp':int(timestamp),'tx_hash':str(log.get('transactionHash','')).lower(),
         'log_index':int(log.get('logIndex',0)),'event':event,'reserve':'','user':'','on_behalf':'','counterparty':'',
         'amount':0,'collateral_asset':'','debt_asset':''}
    try:
        if event=='Supply':
            row['reserve']=addr_word(ts[1]); row['on_behalf']=addr_word(ts[2]); row['user']=addr_word(w[0]); row['amount']=uint(w[1])
        elif event=='Borrow':
            row['reserve']=addr_word(ts[1]); row['on_behalf']=addr_word(ts[2]); row['user']=addr_word(w[0]); row['amount']=uint(w[1])
        elif event=='Repay':
            row['reserve']=addr_word(ts[1]); row['user']=addr_word(ts[2]); row['on_behalf']=row['user']; row['counterparty']=addr_word(ts[3]); row['amount']=uint(w[0])
        elif event=='Withdraw':
            row['reserve']=addr_word(ts[1]); row['user']=addr_word(ts[2]); row['on_behalf']=row['user']; row['counterparty']=addr_word(ts[3]); row['amount']=uint(w[0])
        elif event=='LiquidationCall':
            row['collateral_asset']=addr_word(ts[1]); row['debt_asset']=addr_word(ts[2]); row['user']=addr_word(ts[3]); row['on_behalf']=row['user']; row['amount']=uint(w[0]); row['reserve']=row['debt_asset']
        elif event=='FlashLoan':
            row['counterparty']=addr_word(ts[1]); row['reserve']=addr_word(ts[2]) if len(ts)>2 else ''; row['user']=addr_word(w[0]) if w else ''
    except (IndexError,ValueError,TypeError):
        return None
    return row

def extract_chain(name: str, cfg: dict[str,Any], raw_dir: Path) -> dict[str,Any]:
    out=raw_dir/f'{name}_events.csv'
    fields=['chain','block','timestamp','tx_hash','log_index','event','reserve','user','on_behalf','counterparty','amount','collateral_asset','debt_asset']
    total=0; counts=defaultdict(int); session=requests.Session(); url=f"https://portal.sqd.dev/datasets/{cfg['slug']}/finalized-stream"
    with out.open('w',newline='',encoding='utf-8') as f:
        wr=csv.DictWriter(f,fieldnames=fields); wr.writeheader()
        windows=0
        for a0 in range(int(cfg['start']),int(cfg['end'])+1,WINDOW_BLOCKS):
            chunk_end=min(int(cfg['end']),a0+WINDOW_BLOCKS-1); cur=a0; repeats=0
            while cur<=chunk_end:
                payload={'type':'evm','fromBlock':cur,'toBlock':chunk_end,
                    'fields':{'block':{'number':True,'timestamp':True},'log':{'address':True,'topics':True,'data':True,'transactionHash':True,'logIndex':True}},
                    'logs':[{'address':[POOL],'topic0':TOPICS}]}
                r=request_portal(session,url,payload)
                if r.status_code==204: break
                if r.status_code!=200: raise RuntimeError(f"{name} {cur}-{chunk_end} HTTP {r.status_code}: {r.text[:500]}")
                blocks=parse_blocks(r.text)
                if not blocks: break
                last=cur-1
                for b in blocks:
                    header=b.get('header') or {}; bn=int(header.get('number',-1)); bt=int(header.get('timestamp',0) or 0); last=max(last,bn)
                    for lg in b.get('logs',[]) or []:
                        row=decode_log(name,bn,bt,lg)
                        if row:
                            wr.writerow(row); total+=1; counts[row['event']]+=1
                if last<cur: break
                cur=last+1; repeats+=1
                if repeats>50: raise RuntimeError(f'{name}: excessive continuation at {a0}-{chunk_end}')
                time.sleep(.55)
            windows+=1
            if windows%25==0: print(f'{name}: windows={windows}, events={total}, block={chunk_end}',flush=True)
    return {'chain':name,'events':total,'counts':dict(counts),'file':str(out)}

def fetch_asset_map(chain: str, filename: str) -> dict[str,dict[str,Any]]:
    url=f'https://raw.githubusercontent.com/aave-dao/aave-address-book/main/src/{filename}'
    r=requests.get(url,timeout=60); r.raise_for_status(); text=r.text
    addresses={m.group(1):'0x'+m.group(2).lower() for m in re.finditer(r'address internal constant ([A-Za-z0-9_]+)_UNDERLYING\s*=\s*0x([0-9A-Fa-f]{40})',text)}
    decimals={m.group(1):int(m.group(2)) for m in re.finditer(r'uint8 internal constant ([A-Za-z0-9_]+)_DECIMALS\s*=\s*(\d+)',text)}
    out={}
    for sym,a in addresses.items():
        u=sym.upper(); stable=any(k in u for k in STABLE_KEYS)
        out[a]={'chain':chain,'symbol':sym,'decimals':decimals.get(sym),'stable':stable}
    return out

def has_future(arr: np.ndarray | None, t: int, days: int) -> bool:
    if arr is None or len(arr)==0: return False
    i=int(np.searchsorted(arr,t,side='right'))
    return i<len(arr) and int(arr[i])<=t+days*86400

def build_chain_borrows(chain: str, event_file: Path, assets: dict[str,dict[str,Any]]) -> pd.DataFrame:
    d=pd.read_csv(event_file,dtype={'tx_hash':str,'event':str,'reserve':str,'user':str,'on_behalf':str,'collateral_asset':str,'debt_asset':str})
    if d.empty: return pd.DataFrame()
    d['timestamp']=pd.to_numeric(d.timestamp,errors='coerce').fillna(0).astype(np.int64)
    d['log_index']=pd.to_numeric(d.log_index,errors='coerce').fillna(0).astype(int)
    d['amount']=pd.to_numeric(d.amount,errors='coerce').fillna(0).astype(object)
    d['asset_symbol']=d.reserve.map(lambda x:assets.get(str(x).lower(),{}).get('symbol','UNKNOWN'))
    d['stable']=d.reserve.map(lambda x:bool(assets.get(str(x).lower(),{}).get('stable',False)))
    flash_txs=set(d.loc[d.event.eq('FlashLoan'),'tx_hash'])
    b=d[(d.event=='Borrow') & d.stable].copy().reset_index(drop=True); b['borrow_id']=np.arange(len(b)); b['candidate']=False; b['candidate_reserve']=''; b['candidate_symbol']=''
    s=d[(d.event=='Supply') & ~d.stable].copy()
    if not b.empty and not s.empty:
        pairs=b[['borrow_id','tx_hash','on_behalf','log_index']].merge(s[['tx_hash','on_behalf','log_index','reserve','asset_symbol']],on=['tx_hash','on_behalf'],suffixes=('_b','_s'))
        pairs=pairs[pairs.log_index_s>pairs.log_index_b].sort_values(['borrow_id','log_index_s']).drop_duplicates('borrow_id')
        pairs=pairs[~pairs.tx_hash.isin(flash_txs)]
        if not pairs.empty:
            idx=pairs.borrow_id.astype(int).to_numpy(); b.loc[idx,'candidate']=True; b.loc[idx,'candidate_reserve']=pairs.reserve.to_numpy(); b.loc[idx,'candidate_symbol']=pairs.asset_symbol.to_numpy()
    b=b.sort_values(['on_behalf','timestamp','log_index']).reset_index(drop=True)
    b['prior_borrows']=b.groupby('on_behalf').cumcount(); b['year']=pd.to_datetime(b.timestamp,unit='s',utc=True).dt.year; b['date']=pd.to_datetime(b.timestamp,unit='s',utc=True)
    b['log_amount']=np.log1p(b.amount.map(float).clip(lower=0))
    rep=defaultdict(list); liq=defaultdict(list); wd=defaultdict(list)
    for r in d[d.event=='Repay'].itertuples(index=False): rep[(str(r.on_behalf),str(r.reserve))].append(int(r.timestamp))
    for r in d[d.event=='LiquidationCall'].itertuples(index=False): liq[str(r.on_behalf)].append(int(r.timestamp))
    for r in d[d.event=='Withdraw'].itertuples(index=False): wd[(str(r.on_behalf),str(r.reserve))].append(int(r.timestamp))
    rep={k:np.asarray(sorted(v),dtype=np.int64) for k,v in rep.items()}; liq={k:np.asarray(sorted(v),dtype=np.int64) for k,v in liq.items()}; wd={k:np.asarray(sorted(v),dtype=np.int64) for k,v in wd.items()}
    for days in LABEL_DAYS:
        rv=[];lv=[];wv=[]
        for r in b.itertuples(index=False):
            t=int(r.timestamp); u=str(r.on_behalf); reserve=str(r.reserve); cr=str(r.candidate_reserve)
            rv.append(has_future(rep.get((u,reserve)),t,days)); lv.append(has_future(liq.get(u),t,days)); wv.append(bool(r.candidate) and has_future(wd.get((u,cr)),t,days))
        b[f'repay{days}']=rv; b[f'liquid{days}']=lv; b[f'withdraw_candidate{days}']=wv; b[f'delever{days}']=b[f'repay{days}']|b[f'liquid{days}']
    b=b[b.date<=CANDIDATE_CUTOFF].copy()
    b['chain']=chain
    return b

def match_pairs(b: pd.DataFrame, label: str, controls_per: int=5) -> pd.DataFrame:
    cand=b[b.candidate].copy(); ctrl=b[~b.candidate].copy(); rows=[]
    groups={k:g for k,g in ctrl.groupby(['chain','reserve','year'])}
    for r in cand.itertuples(index=False):
        g=groups.get((r.chain,r.reserve,r.year))
        if g is None or g.empty: continue
        g=g[g.on_behalf!=r.on_behalf]
        if g.empty: continue
        amount=np.abs(g.log_amount.to_numpy(float)-float(r.log_amount)); days=np.abs((g.timestamp.to_numpy(np.int64)-int(r.timestamp))/86400.0)
        score=amount + .002*days + .05*np.abs(g.prior_borrows.to_numpy(float)-float(r.prior_borrows))
        k=min(controls_per,len(g)); sel=np.argpartition(score,k-1)[:k] if k<len(g) else np.arange(len(g)); chosen=g.iloc[sel]
        cval=float(bool(getattr(r,label))); m=float(chosen[label].astype(float).mean())
        rows.append({'chain':r.chain,'candidate_borrow_id':int(r.borrow_id),'candidate_user':r.on_behalf,'year':int(r.year),
                     'reserve':r.reserve,'candidate_asset':r.candidate_symbol,'candidate_value':cval,'control_mean':m,'pair_diff':cval-m,
                     'controls':k,'candidate_timestamp':int(r.timestamp),'candidate_log_amount':float(r.log_amount)})
    return pd.DataFrame(rows)

def bootstrap_lcb(x: np.ndarray, seed: int=20260801, reps: int=5000) -> tuple[float,float,float]:
    x=np.asarray(x,float); x=x[np.isfinite(x)]
    if len(x)==0:return math.nan,math.nan,math.nan
    rng=np.random.default_rng(seed); means=np.empty(reps)
    for i in range(reps): means[i]=rng.choice(x,size=len(x),replace=True).mean()
    return float(x.mean()),float(np.quantile(means,.05)),float(np.quantile(means,.95))

def rate_stats(df: pd.DataFrame, label: str) -> dict[str,Any]:
    if df.empty:return {'n':0}
    cand=df[df.candidate][label].astype(int); ctrl=df[~df.candidate][label].astype(int)
    table=[[int(cand.sum()),int(len(cand)-cand.sum())],[int(ctrl.sum()),int(len(ctrl)-ctrl.sum())]]
    _,p=fisher_exact(table,alternative='greater') if len(cand) and len(ctrl) else (math.nan,math.nan)
    return {'n_candidate':len(cand),'n_control':len(ctrl),'candidate_rate':float(cand.mean()) if len(cand) else math.nan,
            'control_rate':float(ctrl.mean()) if len(ctrl) else math.nan,'risk_difference':float(cand.mean()-ctrl.mean()) if len(cand) and len(ctrl) else math.nan,
            'fisher_one_sided_p':float(p)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); args=ap.parse_args(); out=Path(args.out); out.mkdir(parents=True,exist_ok=True); raw=out/'raw'; raw.mkdir(exist_ok=True)
    extraction=[]; all_assets={}; borrows=[]
    for chain,cfg in CHAINS.items():
        amap=fetch_asset_map(chain,cfg['address_file']); all_assets[chain]=amap
        extraction.append(extract_chain(chain,cfg,raw))
        x=build_chain_borrows(chain,raw/f'{chain}_events.csv',amap)
        if not x.empty: borrows.append(x)
    B=pd.concat(borrows,ignore_index=True) if borrows else pd.DataFrame()
    if B.empty: raise RuntimeError('No stablecoin Borrow events decoded')
    asset_rows=[]
    for ch,m in all_assets.items():
        for a,z in m.items(): asset_rows.append({'chain':ch,'address':a,**z})
    pd.DataFrame(asset_rows).to_csv(out/'asset_map.csv',index=False)
    pd.DataFrame(extraction).to_json(out/'extraction_summary.json',orient='records',indent=2)
    keep=['chain','block','timestamp','date','tx_hash','log_index','reserve','asset_symbol','on_behalf','amount','log_amount','prior_borrows','year','candidate','candidate_reserve','candidate_symbol']+[f'{x}{d}' for d in LABEL_DAYS for x in ['repay','liquid','withdraw_candidate','delever']]
    B[keep].to_csv(out/'stable_borrow_cohort.csv',index=False)
    labels=['repay7','repay30','repay90','liquid30','liquid90','delever30','delever90']
    results={'contract':{'development':'2022-2023','selection':'2024','final':'2025','candidate':'stablecoin Borrow followed in same tx by non-stable Supply for same debtor; Borrow log precedes Supply; FlashLoan tx excluded','primary_label':'delever90','matching':'chain + stable reserve + calendar year; nearest log amount, time, prior borrow count; five controls','right_censor_cutoff':str(CANDIDATE_CUTOFF)},
             'extraction':extraction,'borrow_counts':{'total':int(len(B)),'candidate':int(B.candidate.sum()),'control':int((~B.candidate).sum()),'by_year':B.groupby(['year','candidate']).size().rename('n').reset_index().to_dict('records')},'labels':{},'primary':{},'gates':{}}
    for lab in labels:
        P=match_pairs(B,lab); P.to_csv(out/f'matched_{lab}.csv',index=False)
        yearly=[]
        for y,g in P.groupby('year'):
            mean,lcb,ucb=bootstrap_lcb(g.pair_diff.to_numpy(),seed=20260801+int(y)); yearly.append({'year':int(y),'n':len(g),'effect':mean,'lcb5':lcb,'ucb95':ucb})
        overall=bootstrap_lcb(P.pair_diff.to_numpy()) if not P.empty else (math.nan,math.nan,math.nan)
        results['labels'][lab]={'unmatched':rate_stats(B,lab),'matched_n':int(len(P)),'matched_effect':overall[0],'matched_lcb5':overall[1],'matched_ucb95':overall[2],'yearly':yearly}
    P=match_pairs(B,'delever90'); top_users=set(P.candidate_user.value_counts().head(10).index) if not P.empty else set(); trimmed=P[~P.candidate_user.isin(top_users)].copy(); tr=bootstrap_lcb(trimmed.pair_diff.to_numpy(),seed=20260802)
    yr={int(x['year']):x for x in results['labels']['delever90']['yearly']}
    dev=P[P.year.isin([2022,2023])]; sel=P[P.year==2024]; fin=P[P.year==2025]
    devb=bootstrap_lcb(dev.pair_diff.to_numpy(),seed=20260803); selb=bootstrap_lcb(sel.pair_diff.to_numpy(),seed=20260804); finb=bootstrap_lcb(fin.pair_diff.to_numpy(),seed=20260805)
    gates={
      'candidate_count_ge_100':int(B.candidate.sum())>=100,
      'matched_candidate_count_ge_100':len(P)>=100,
      'each_2023_2025_candidate_count_ge_20':all(int((P.year==y).sum())>=20 for y in [2023,2024,2025]),
      'development_effect_positive':devb[0]>0,
      'selection_2024_effect_positive':selb[0]>0,
      'final_2025_effect_positive':finb[0]>0,
      'final_2025_lcb5_positive':finb[1]>0,
      'combined_2024_2025_lcb5_positive':bootstrap_lcb(P[P.year.isin([2024,2025])].pair_diff.to_numpy(),seed=20260806)[1]>0,
      'delete_top10_users_effect_positive':tr[0]>0,
    }
    results['primary']={'development':{'n':len(dev),'effect':devb[0],'lcb5':devb[1]},'selection_2024':{'n':len(sel),'effect':selb[0],'lcb5':selb[1]},'final_2025':{'n':len(fin),'effect':finb[0],'lcb5':finb[1]},'trim_top10_users':{'n':len(trimmed),'effect':tr[0],'lcb5':tr[1]},'top10_users':sorted(top_users)}
    results['gates']=gates; results['mq_verified']=all(gates.values())
    (out/'summary.json').write_text(json.dumps(results,indent=2,default=str))
    report=['# Frozen BCLX-R M→Q Test','',f"- M→Q verified: **{results['mq_verified']}**",f"- Stable Borrow events: {len(B):,}",f"- Strict atomic debt-funded-long candidates: {int(B.candidate.sum()):,}",f"- Matched primary candidates: {len(P):,}",'', '## Primary deleveraging effect']
    for k,v in results['primary'].items(): report.append(f"- {k}: n={v.get('n')}, effect={v.get('effect')}, LCB5={v.get('lcb5')}")
    report += ['','## Gates',json.dumps(gates,indent=2)]
    (out/'REPORT.md').write_text('\n'.join(report))
    print(json.dumps({'mq_verified':results['mq_verified'],'borrow_counts':results['borrow_counts'],'primary':results['primary'],'gates':gates},indent=2,default=str))

if __name__=='__main__': main()
