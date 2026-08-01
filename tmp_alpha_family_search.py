#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,json,math,time,zipfile
from concurrent.futures import ThreadPoolExecutor,as_completed
from dataclasses import dataclass,asdict
from pathlib import Path
import duckdb,numpy as np,pandas as pd,requests

BASE='https://data.binance.vision/data/futures/um/monthly/klines'
ANCHOR=pd.Timestamp('2020-01-01');END=pd.Timestamp('2025-12-31')
TRAIN0=pd.Timestamp('2020-01-01');TRAIN1=pd.Timestamp('2021-12-31')
VAL0=pd.Timestamp('2022-01-01');VAL1=pd.Timestamp('2022-12-31')
OOS0=pd.Timestamp('2023-01-01');OOS1=pd.Timestamp('2025-12-31')
AGE_MIN,AGE_MAX,HOLD=90,180,3
MIN_VOL=1_000_000.;SIDE_COST=.002;FUND=.0005
EXCL={'BTCDOMUSDT','DEFIUSDT','BLUEBIRDUSDT','FOOTBALLUSDT'}
LEV_GRID=np.round(np.arange(.25,2.01,.05),2)
SCORES=['mom7','mom14','mom30','mom60','rev7','rev30','risk_adj_mom30','accel','accel_rev','listing_rev','volume_exhaustion','drawdown_recovery']
KS=[1,3,5]

@dataclass
class T:
    decision_date:str;entry_date:str;exit_date:str;candidate:str
    long_symbols:str;short_symbols:str;gross_unit_return:float;eligible_count:int

def months(a,b):return pd.date_range(pd.Timestamp(a).replace(day=1),pd.Timestamp(b).replace(day=1),freq='MS')
def get(url):
    for n in range(4):
        try:
            r=requests.get(url,timeout=30)
            if r.status_code==200:return r.content
            if r.status_code==404:return None
        except requests.RequestException:pass
        time.sleep(n+1)
    return None

def one_symbol(rec):
    sym,start,last=rec;start=pd.Timestamp(start);end=min(start+pd.Timedelta(days=185),pd.Timestamp(last),END)
    out=[];ok=0
    for m in months(start,end):
        z=get(f'{BASE}/{sym}/1d/{sym}-1d-{m:%Y-%m}.zip')
        if not z:continue
        ok+=1
        try:
            with zipfile.ZipFile(io.BytesIO(z)) as q:
                f=io.TextIOWrapper(q.open(q.namelist()[0]),encoding='utf-8')
                for x in csv.reader(f):
                    if not x or not x[0].isdigit() or len(x)<11:continue
                    raw=int(x[0]);dt=pd.to_datetime(raw,unit='us' if raw>10**14 else 'ms').normalize()
                    if start<=dt<=end:
                        out.append((dt,sym,float(x[1]),float(x[2]),float(x[3]),float(x[4]),float(x[7])))
        except Exception:pass
    return out,{'symbol':sym,'bars':len(out),'files':ok,'start':str(start.date()),'end':str(end.date())}

def load(db,outdir):
    c=duckdb.connect(db,read_only=True)
    x=c.execute("""SELECT symbol,MIN(date) listing_date,MAX(date) last_date FROM daily_availability
      WHERE available=TRUE AND symbol LIKE '%USDT' GROUP BY symbol ORDER BY listing_date""").fetch_df();c.close()
    x.listing_date=pd.to_datetime(x.listing_date);x.last_date=pd.to_datetime(x.last_date);s=x.symbol.astype(str)
    x=x[s.str.endswith('USDT')&~s.str.contains('SETTLED',regex=False)&~s.str.contains('_',regex=False)&~s.isin(EXCL)]
    x=x[(x.last_date-x.listing_date).dt.days>=94];x=x[x.listing_date<=pd.Timestamp('2025-10-02')]
    rec=list(x[['symbol','listing_date','last_date']].itertuples(index=False,name=None));rows=[];stat=[]
    with ThreadPoolExecutor(max_workers=24) as ex:
        fs=[ex.submit(one_symbol,r) for r in rec]
        for n,f in enumerate(as_completed(fs),1):
            a,b=f.result();rows+=a;stat.append(b)
            if n%100==0:print('download',n,len(rec),len(rows),flush=True)
    pd.DataFrame(stat).to_csv(outdir/'coverage.csv',index=False)
    d=pd.DataFrame(rows,columns=['date','symbol','open','high','low','close','quote_volume'])
    if d.empty:raise RuntimeError('no data')
    d=d.sort_values(['symbol','date']).drop_duplicates(['symbol','date']);return d

def pivots(d):
    listing=d.groupby('symbol').date.min();last=d.groupby('symbol').date.max()
    def p(x):return d.pivot(index='date',columns='symbol',values=x).sort_index().reindex(pd.date_range(d.date.min(),END))
    o,h,l,c,v=map(p,['open','high','low','close','quote_volume']);ret=c.pct_change(fill_method=None)
    feat={'r7':c/c.shift(7)-1,'r14':c/c.shift(14)-1,'r30':c/c.shift(30)-1,'r60':c/c.shift(60)-1,
      'vol30':ret.rolling(30,min_periods=20).std(),'vr':v.rolling(7,min_periods=4).median()/v.rolling(30,min_periods=15).median(),
      'dd30':c/c.rolling(30,min_periods=20).max()-1,'medvol':v.rolling(30,min_periods=15).median()}
    first=c.apply(lambda z:z.dropna().iloc[0] if z.notna().any() else np.nan);feat['since']=c.divide(first,axis=1)-1
    return listing,last,o,h,l,c,feat

def zscore(s):
    sd=s.std(ddof=0)
    return (s-s.mean())/sd if np.isfinite(sd) and sd>0 else s*0

def score(name,F):
    if name=='mom7':return F['r7']
    if name=='mom14':return F['r14']
    if name=='mom30':return F['r30']
    if name=='mom60':return F['r60']
    if name=='rev7':return -F['r7']
    if name=='rev30':return -F['r30']
    if name=='risk_adj_mom30':return F['r30']/(F['vol30']+1e-6)
    if name=='accel':return F['r7']-(7/30)*F['r30']
    if name=='accel_rev':return -(F['r7']-(7/30)*F['r30'])
    if name=='listing_rev':return -F['since']
    if name=='volume_exhaustion':return -(zscore(F['r30'])*zscore(np.log(F['vr'].clip(lower=.05,upper=20))))
    if name=='drawdown_recovery':return -F['dd30']
    raise KeyError(name)

def make_trades(d):
    listing,last,o,h,l,c,feat=pivots(d);by={f'{s}_k{k}':[] for s in SCORES for k in KS}
    for dt in pd.date_range(ANCHOR,END-pd.Timedelta(days=4),freq='3D'):
        age=(dt-listing).dt.days;elig=listing.index[(age>=AGE_MIN)&(age<=AGE_MAX)&(last>=dt)]
        if len(elig)<2:continue
        F={k:v.loc[dt,elig] for k,v in feat.items()};liq=F['medvol']>=MIN_VOL
        en=dt+pd.Timedelta(days=1);ex=en+pd.Timedelta(days=3)
        for sn in SCORES:
            sc=score(sn,F).where(liq).dropna()
            for k in KS:
                if len(sc)<2*k:continue
                lo=list(sc.nlargest(k).index);sh=list(sc.nsmallest(k).index)
                bad=False
                for sym in lo+sh:
                    q=[o.at[en,sym],o.at[ex,sym]]
                    if not np.all(np.isfinite(q)) or min(q)<=0:bad=True;break
                if bad:continue
                lr=np.mean([o.at[ex,s]/o.at[en,s]-1 for s in lo]);sr=np.mean([1-o.at[ex,s]/o.at[en,s] for s in sh])
                key=f'{sn}_k{k}';by[key].append(T(str(dt.date()),str(en.date()),str(ex.date()),key,json.dumps(lo),json.dumps(sh),float(lr+sr),len(sc)))
    return by,(o,h,l,c)

def mdd(s):
    a=np.asarray(s,float);return float(-np.min(a/np.maximum.accumulate(a)-1))
def sim(ts,P,lev,a,b,exclude=None):
    o,h,l,c=P;E=1.;eq=[(a,1.,1.)];tr=[];exclude=exclude or set()
    for i,t in enumerate(ts):
        en=pd.Timestamp(t.entry_date);ex=pd.Timestamp(t.exit_date)
        if en<a or ex>b or i in exclude:continue
        L=json.loads(t.long_symbols);S=json.loads(t.short_symbols);base=E;ec=lev*2*SIDE_COST;xc=ec;fr=lev*2*FUND*HOLD
        for day in pd.date_range(en,ex):
            cp=lev*(np.mean([c.at[day,s]/o.at[en,s]-1 for s in L])+np.mean([1-c.at[day,s]/o.at[en,s] for s in S]))
            sp=lev*(np.mean([l.at[day,s]/o.at[en,s]-1 for s in L])+np.mean([1-h.at[day,s]/o.at[en,s] for s in S]))
            fd=lev*2*FUND*min(HOLD,(day-en).days+1);eq.append((day,max(1e-12,base*(1+cp-ec-fd)),max(1e-12,base*(1+sp-ec-fd))))
        nr=lev*t.gross_unit_return-ec-xc-fr;E=max(1e-12,base*(1+nr));tr.append({'i':i,**asdict(t),'net_return':nr,'before':base,'after':E,'log':math.log(E/base)})
        eq.append((ex,E,E))
        if E<1e-10:break
    q=pd.DataFrame(eq,columns=['date','close','stress']);q=q.groupby('date',as_index=False).agg(close=('close','last'),stress=('stress','min'))
    tt=pd.DataFrame(tr);yrs={}
    for y in range(a.year,b.year+1):
        ys=pd.Timestamp(f'{y}-01-01');ye=pd.Timestamp(f'{y}-12-31');sub=q[(q.date>=ys)&(q.date<=ye)]
        if sub.empty:continue
        prev=q[q.date<ys].close.iloc[-1] if (q.date<ys).any() else 1.;yrs[str(y)]={'factor':float(sub.close.iloc[-1]/prev),'mdd':mdd(pd.concat([pd.Series([prev]),sub.stress]))}
    return q,tt,{'terminal':float(q.close.iloc[-1]),'mdd':mdd(q.stress),'trades':len(tt),'yearly':yrs}

def choose_lev(ts,P):
    R=[]
    for lev in LEV_GRID:
        _,_,x=sim(ts,P,float(lev),TRAIN0,TRAIN1);yf=[v['factor'] for v in x['yearly'].values()]
        ok=x['mdd']<=.25 and x['trades']>=20 and len(yf)>=2 and min(yf)>=.85 and x['terminal']>1
        R.append((lev,x['terminal'],x['mdd'],ok))
    z=[r for r in R if r[3]];return (float(max(z,key=lambda r:r[1])[0]) if z else .25),R

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--db',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    d=load(a.db,out);families,P=make_trades(d);selection=[]
    for name,ts in families.items():
        lev,_=choose_lev(ts,P);_,_,v=sim(ts,P,lev,VAL0,VAL1)
        scorev=math.log(max(v['terminal'],1e-12))-1.5*v['mdd'];eligible=v['terminal']>1 and v['mdd']<=.35 and v['trades']>=20
        selection.append({'candidate':name,'leverage':lev,'validation_terminal':v['terminal'],'validation_mdd':v['mdd'],'validation_trades':v['trades'],'selection_score':scorev,'eligible':eligible})
    sel=pd.DataFrame(selection).sort_values(['eligible','selection_score'],ascending=[False,False]);sel.to_csv(out/'candidate_selection.csv',index=False)
    chosen=sel.iloc[0].candidate;lev=float(sel.iloc[0].leverage);ts=families[chosen];q,t,oos=sim(ts,P,lev,OOS0,OOS1)
    q.to_csv(out/'selected_oos_equity.csv',index=False);t.to_csv(out/'selected_oos_trades.csv',index=False)
    top5=set(t.nlargest(5,'log').i.astype(int)) if not t.empty else set();top10=set(t.nlargest(10,'log').i.astype(int)) if not t.empty else set()
    r5=sim(ts,P,lev,OOS0,OOS1,top5)[2];r10=sim(ts,P,lev,OOS0,OOS1,top10)[2]
    yf=[v['factor'] for v in oos['yearly'].values()];logs=[max(0,math.log(max(x,1e-12))) for x in yf];conc=max(logs)/sum(logs) if sum(logs)>0 else 1
    gates={'terminal_ge_1331':oos['terminal']>=1331,'mdd_le_40pct':oos['mdd']<=.4,'each_year_ge_3':bool(yf) and min(yf)>=3,
      'year_log_share_le_50pct':conc<=.5,'delete_top5_ge_512':r5['terminal']>=512,'delete_top10_gt_1':r10['terminal']>1,'trades_ge_60':oos['trades']>=60}
    diag=[]
    for row in selection:
        _,_,xx=sim(families[row['candidate']],P,row['leverage'],OOS0,OOS1);diag.append({'candidate':row['candidate'],'leverage':row['leverage'],'terminal':xx['terminal'],'mdd':xx['mdd'],'trades':xx['trades']})
    pd.DataFrame(diag).sort_values('terminal',ascending=False).to_csv(out/'all_candidates_oos_diagnostic.csv',index=False)
    res={'selected_without_oos':chosen,'selected_leverage':lev,'oos':oos,'delete_top5':r5,'delete_top10':r10,'year_concentration':conc,'gates':gates,'verified':all(gates.values()),
      'candidate_count':len(selection),'data_rows':len(d),'symbols':int(d.symbol.nunique())}
    (out/'family_summary.json').write_text(json.dumps(res,indent=2));(out/'REPORT.md').write_text('# Mechanism family search\n\n'+json.dumps(res,indent=2));print(json.dumps(res,indent=2))
if __name__=='__main__':main()
