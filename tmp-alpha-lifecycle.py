#!/usr/bin/env python3
"""Frozen Binance listing-lifecycle cross-sectional backtest."""
from __future__ import annotations
import argparse, json, math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import duckdb
import numpy as np
import pandas as pd

ANCHOR=pd.Timestamp('2020-01-01'); DATA_END=pd.Timestamp('2025-12-31')
DEV_START=pd.Timestamp('2020-01-01'); DEV_END=pd.Timestamp('2022-12-31')
OOS_START=pd.Timestamp('2023-01-01'); OOS_END=pd.Timestamp('2025-12-31')
AGE_MIN=90; AGE_MAX=180; LOOKBACK_DAYS=30; HOLD_DAYS=3
MIN_MEDIAN_QUOTE_VOLUME=1_000_000.0
PER_SIDE_COST=0.002
FUNDING_RESERVE_PER_LEG_DAY=0.0005
INDEX_EXCLUSIONS={'BTCDOMUSDT','DEFIUSDT','BLUEBIRDUSDT','FOOTBALLUSDT'}
LEVERAGE_GRID=np.round(np.arange(0.25,2.01,0.05),2)

@dataclass
class Trade:
    decision_date:str; entry_date:str; exit_date:str
    long_symbol:str; short_symbol:str
    long_signal:float; short_signal:float; dispersion:float
    dispersion_gate:bool; eligible_count:int
    median_quote_volume_long:float; median_quote_volume_short:float
    long_entry:float; long_exit:float; short_entry:float; short_exit:float
    gross_unit_return:float

def max_drawdown(values:pd.Series)->float:
    if values.empty:return float('nan')
    a=values.astype(float).to_numpy(); p=np.maximum.accumulate(a); d=a/p-1
    return float(-np.nanmin(d))

def cagr(start:float,end:float,days:int)->float:
    if start<=0 or end<=0 or days<=0:return float('nan')
    return float((end/start)**(365.25/days)-1)

def load_data(path:Path)->pd.DataFrame:
    c=duckdb.connect(str(path),read_only=True)
    q="""SELECT date,symbol,available,quote_volume_usdt,open_price,high_price,low_price,close_price
    FROM daily_availability WHERE date<=DATE '2025-12-31' AND available=TRUE
    AND close_price IS NOT NULL AND open_price IS NOT NULL AND high_price IS NOT NULL
    AND low_price IS NOT NULL AND symbol LIKE '%USDT'"""
    d=c.execute(q).fetch_df(); c.close()
    if d.empty:raise RuntimeError('No OHLCV rows found')
    d['date']=pd.to_datetime(d['date']); d['symbol']=d['symbol'].astype(str)
    m=(d.symbol.str.endswith('USDT') & ~d.symbol.str.contains('SETTLED',regex=False)
       & ~d.symbol.str.contains('_',regex=False) & ~d.symbol.isin(INDEX_EXCLUSIONS))
    d=d.loc[m].copy()
    cols=['quote_volume_usdt','open_price','high_price','low_price','close_price']
    for x in cols:d[x]=pd.to_numeric(d[x],errors='coerce')
    d=d.dropna(subset=cols[1:]); d=d[(d[cols[1:]]>0).all(axis=1)]
    return d.sort_values(['symbol','date']).drop_duplicates(['symbol','date'],keep='last')

def panels(d):
    listing=d.groupby('symbol').date.min(); last=d.groupby('symbol').date.max()
    def pv(x):return d.pivot(index='date',columns='symbol',values=x).sort_index()
    o,h,l,c,v=map(pv,['open_price','high_price','low_price','close_price','quote_volume_usdt'])
    ix=pd.date_range(c.index.min(),DATA_END,freq='D')
    o,h,l,c,v=[x.reindex(ix) for x in [o,h,l,c,v]]
    sig=c/c.shift(LOOKBACK_DAYS)-1; mv=v.rolling(30,min_periods=15).median()
    return listing,last,o,h,l,c,mv,sig

def generate_trades(d):
    listing,last,o,h,l,c,mv,sig=panels(d)
    dates=pd.date_range(ANCHOR,DATA_END-pd.Timedelta(days=HOLD_DAYS+1),freq='3D')
    hist=[]; out=[]; skips={}
    def skip(x):skips.__setitem__(x,skips.get(x,0)+1)
    for dt in dates:
        age=(dt-listing).dt.days
        elig=listing.index[(age>=AGE_MIN)&(age<=AGE_MAX)&(last>=dt)]
        if len(elig)<2:skip('age_universe_lt2');continue
        s=sig.loc[dt,elig].dropna(); med=mv.loc[dt,s.index]; s=s[med>=MIN_MEDIAN_QUOTE_VOLUME]
        if len(s)<2:skip('liquid_universe_lt2');continue
        disp=float(s.std(ddof=0)); prior=[x for t,x in hist if t<dt and t>=dt-pd.Timedelta(days=365)]
        tm=float(np.median(prior)) if len(prior)>=20 else float('nan')
        gate=bool(np.isfinite(tm) and disp>tm); hist.append((dt,disp))
        ls=str(s.idxmax()); ss=str(s.idxmin()); en=dt+pd.Timedelta(days=1); ex=en+pd.Timedelta(days=3)
        vals=[o.at[en,ls],o.at[ex,ls],o.at[en,ss],o.at[ex,ss]]
        if not np.all(np.isfinite(vals)) or np.any(np.asarray(vals)<=0):skip('entry_exit_missing');continue
        le,lx,se,sx=map(float,vals); gross=(lx/le-1)+(1-sx/se)
        out.append(Trade(dt.strftime('%Y-%m-%d'),en.strftime('%Y-%m-%d'),ex.strftime('%Y-%m-%d'),
          ls,ss,float(s[ls]),float(s[ss]),disp,gate,int(len(s)),float(mv.at[dt,ls]),float(mv.at[dt,ss]),
          le,lx,se,sx,float(gross)))
    meta={'rows':int(len(d)),'symbols':int(d.symbol.nunique()),'first_date':str(d.date.min().date()),
      'last_date':str(d.date.max().date()),'trades_generated':len(out),'skip_reasons':skips,'_panels':(o,h,l,c)}
    return out,meta

def summarize(eq,tr,start,end):
    terminal=float(eq.iloc[-1].equity_close); cs=eq.set_index('date').equity_close; ss=eq.set_index('date').equity_stress
    m={'terminal_factor':terminal,'total_return':terminal-1,'cagr':cagr(1,terminal,int((end-start).days+1)),
       'mdd_close':max_drawdown(cs),'mdd_stress':max_drawdown(ss),'trade_count':int(len(tr))}
    yr={}
    for y in range(start.year,end.year+1):
        ys=pd.Timestamp(f'{y}-01-01'); ye=pd.Timestamp(f'{y}-12-31')
        sub=cs[(cs.index>=ys)&(cs.index<=ye)]; stress=ss[(ss.index>=ys)&(ss.index<=ye)]
        if sub.empty:continue
        first=float(cs[cs.index<ys].iloc[-1]) if (cs.index<ys).any() else 1.0
        ext=pd.concat([pd.Series([first],index=[ys-pd.Timedelta(seconds=1)]),stress])
        yr[str(y)]={'factor':float(sub.iloc[-1])/first,'mdd_stress':max_drawdown(ext),
          'trades':int((tr.entry_date.astype(str).str[:4]==str(y)).sum()) if not tr.empty else 0}
    m['yearly']=yr;return m

def simulate(trades,p,lev,gate,start,end,exclude_idx=None,exclude_symbols=None):
    o,h,l,c=p; eqv=1.0; er=[{'date':start,'equity_close':1.0,'equity_stress':1.0}]; tr=[]
    exclude_idx=exclude_idx or set(); exclude_symbols=exclude_symbols or set()
    for i,t in enumerate(trades):
        en=pd.Timestamp(t.entry_date); ex=pd.Timestamp(t.exit_date)
        if en<start or ex>end or i in exclude_idx:continue
        if t.long_symbol in exclude_symbols or t.short_symbol in exclude_symbols:continue
        if gate and not t.dispersion_gate:continue
        base=eqv; ec=lev*2*PER_SIDE_COST; xc=ec; fr=lev*2*FUNDING_RESERVE_PER_LEG_DAY*HOLD_DAYS
        for day in pd.date_range(en,ex,freq='D'):
            lc=c.at[day,t.long_symbol]; sc=c.at[day,t.short_symbol]; ll=l.at[day,t.long_symbol]; sh=h.at[day,t.short_symbol]
            n=max(0,min(HOLD_DAYS,(day-en).days+1)); fd=lev*2*FUNDING_RESERVE_PER_LEG_DAY*n
            cp=lev*((lc/t.long_entry-1)+(1-sc/t.short_entry)) if np.isfinite(lc) and np.isfinite(sc) else 0
            sp=lev*((ll/t.long_entry-1)+(1-sh/t.short_entry)) if np.isfinite(ll) and np.isfinite(sh) else 0
            er.append({'date':day,'equity_close':max(1e-12,base*(1+cp-ec-fd)),
                       'equity_stress':max(1e-12,base*(1+sp-ec-fd))})
        nr=lev*t.gross_unit_return-ec-xc-fr; eqv=max(1e-12,base*(1+nr))
        tr.append({'trade_index':i,**asdict(t),'leverage':lev,'net_return':nr,'equity_before':base,
          'equity_after':eqv,'log_contribution':math.log(eqv/base) if eqv>0 and base>0 else -np.inf})
        er.append({'date':ex,'equity_close':eqv,'equity_stress':eqv})
        if eqv<=1e-10:break
    e=pd.DataFrame(er); e.date=pd.to_datetime(e.date)
    e=e.sort_values('date').groupby('date',as_index=False).agg(equity_close=('equity_close','last'),equity_stress=('equity_stress','min'))
    tdf=pd.DataFrame(tr);return e,tdf,summarize(e,tdf,start,end)

def select_leverage(trades,p,gate):
    rows=[]
    for lev in LEVERAGE_GRID:
        _,_,m=simulate(trades,p,float(lev),gate,DEV_START,DEV_END); yf=[x['factor'] for x in m['yearly'].values()]
        ok=m['mdd_stress']<=.30 and m['trade_count']>=24 and len(yf)>=3 and min(yf)>.80 and m['terminal_factor']>1
        rows.append({'leverage':lev,'terminal_factor':m['terminal_factor'],'mdd_stress':m['mdd_stress'],
          'trade_count':m['trade_count'],'min_year_factor':min(yf) if yf else np.nan,'admissible':ok})
    f=pd.DataFrame(rows); a=f[f.admissible]
    return (0.25 if a.empty else float(a.sort_values(['terminal_factor','leverage'],ascending=[False,True]).iloc[0].leverage)),f

def robustness(trades,p,lev,gate,base):
    if base.empty:return {}
    r={}
    for name,n in [('delete_top5_trades',5),('delete_top10_trades',10)]:
        x=set(base.nlargest(n,'log_contribution').trade_index.astype(int)); r[name]=simulate(trades,p,lev,gate,OOS_START,OOS_END,x)[2]
    z=pd.concat([base[['long_symbol','log_contribution']].rename(columns={'long_symbol':'symbol'}),
      base[['short_symbol','log_contribution']].rename(columns={'short_symbol':'symbol'})]).groupby('symbol').log_contribution.sum().sort_values(ascending=False)
    sy=set(z.head(5).index); r['delete_top5_symbols']={'symbols':sorted(sy),'metrics':simulate(trades,p,lev,gate,OOS_START,OOS_END,exclude_symbols=sy)[2]}
    return r

def evaluate(name,trades,p,gate,out):
    lev,front=select_leverage(trades,p,gate); de,dt,dm=simulate(trades,p,lev,gate,DEV_START,DEV_END)
    oe,ot,om=simulate(trades,p,lev,gate,OOS_START,OOS_END); rb=robustness(trades,p,lev,gate,ot)
    front.to_csv(out/f'{name}_development_leverage_frontier.csv',index=False); de.to_csv(out/f'{name}_development_equity.csv',index=False)
    dt.to_csv(out/f'{name}_development_trades.csv',index=False); oe.to_csv(out/f'{name}_oos_equity.csv',index=False); ot.to_csv(out/f'{name}_oos_trades.csv',index=False)
    yf=[float(x['factor']) for x in om.get('yearly',{}).values()]; logs=[max(0,math.log(max(x,1e-12))) for x in yf]
    conc=max(logs)/sum(logs) if sum(logs)>0 else 1
    gates={'three_year_terminal_ge_1331':om['terminal_factor']>=1331,'stress_mdd_le_40pct':om['mdd_stress']<=.40,
      'at_least_3_calendar_years':len(yf)>=3,'every_year_factor_ge_3':bool(yf) and min(yf)>=3,
      'best_year_log_share_le_50pct':conc<=.50,'delete_top5_terminal_ge_512':rb.get('delete_top5_trades',{}).get('terminal_factor',0)>=512,
      'delete_top10_terminal_gt_1':rb.get('delete_top10_trades',{}).get('terminal_factor',0)>1,'trade_count_ge_60':om['trade_count']>=60}
    return {'name':name,'use_dispersion_gate':gate,'selected_leverage_from_2020_2022':lev,'development':dm,
      'oos_2023_2025':om,'year_log_concentration':conc,'robustness':rb,'gates':gates,'passed':all(gates.values())}

def main():
    a=argparse.ArgumentParser();a.add_argument('--db',required=True);a.add_argument('--out',required=True);x=a.parse_args()
    out=Path(x.out);out.mkdir(parents=True,exist_ok=True);d=load_data(Path(x.db));trades,meta=generate_trades(d);p=meta.pop('_panels')
    pd.DataFrame([asdict(t) for t in trades]).to_csv(out/'all_signal_trades.csv',index=False)
    specs=[evaluate('base',trades,p,False,out),evaluate('dispersion_gate',trades,p,True,out)]; verified=[s for s in specs if s['passed']]
    summary={'research_contract':{'signal':'age 90-180d; 72h decisions; long max 30d return; short min 30d return',
      'liquidity_gate':f'30d median quote volume >= {MIN_MEDIAN_QUOTE_VOLUME}','development':'2020-01-01 to 2022-12-31',
      'oos':'2023-01-01 to 2025-12-31','execution':{'entry':'next UTC daily open','exit':'three days later UTC daily open',
      'per_side_cost':PER_SIDE_COST,'funding_reserve_per_leg_day':FUNDING_RESERVE_PER_LEG_DAY,
      'mdd':'daily close plus conservative same-day long-low/short-high stress'}},'data':meta,'specs':specs,
      'verified_alpha_found':bool(verified),'verified_specs':[s['name'] for s in verified]}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False,default=str))
    lines=['# Frozen listing-lifecycle validation','',f"- Verified alpha found: **{summary['verified_alpha_found']}**",
      f"- Input rows: {meta['rows']:,}",f"- Symbols: {meta['symbols']}",f"- Generated signal trades: {meta['trades_generated']}",'','## Results','']
    for s in specs:
        o=s['oos_2023_2025'];lines += [f"### {s['name']}",f"- Development-selected leverage: {s['selected_leverage_from_2020_2022']:.2f}",
          f"- OOS terminal factor: {o['terminal_factor']:.4f}x",f"- OOS CAGR: {o['cagr']:.2%}",f"- OOS stress MDD: {o['mdd_stress']:.2%}",
          f"- OOS trades: {o['trade_count']}",f"- Passed: **{s['passed']}**",f"- Gates: `{json.dumps(s['gates'],ensure_ascii=False)}`",'']
    (out/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8');print(json.dumps(summary,indent=2,ensure_ascii=False,default=str))
if __name__=='__main__':main()
