#!/usr/bin/env python3
from __future__ import annotations
import csv
import importlib.util
import io
import json
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import duckdb
import pandas as pd
import requests

MODULE_PATH=Path(__file__).with_name('tmp-alpha-lifecycle.py')
spec=importlib.util.spec_from_file_location('frozen_lifecycle',MODULE_PATH)
mod=importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)

BASE='https://data.binance.vision/data/futures/um/monthly/klines'

def month_starts(start,end):
    return pd.date_range(pd.Timestamp(start).replace(day=1),pd.Timestamp(end).replace(day=1),freq='MS')

def get_zip(url):
    for attempt in range(5):
        try:
            r=requests.get(url,timeout=30)
            if r.status_code==200:return r.content,200
            if r.status_code==404:return None,404
            if r.status_code in (418,429) or r.status_code>=500:
                time.sleep(1.5*(attempt+1));continue
            return None,r.status_code
        except requests.RequestException:
            time.sleep(1.5*(attempt+1))
    return None,-1

def parse_zip(content,symbol,start,end):
    rows=[]
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            name=z.namelist()[0]
            text=io.TextIOWrapper(z.open(name),encoding='utf-8')
            for x in csv.reader(text):
                if not x or not x[0].strip().isdigit() or len(x)<11:continue
                raw=int(x[0]);unit='us' if raw>10**14 else 'ms'
                dt=pd.to_datetime(raw,unit=unit)
                if dt<start or dt>end:continue
                rows.append({'date':dt.normalize(),'symbol':symbol,'available':True,
                  'quote_volume_usdt':float(x[7]),'open_price':float(x[1]),'high_price':float(x[2]),
                  'low_price':float(x[3]),'close_price':float(x[4])})
    except Exception:
        return []
    return rows

def fetch_symbol(rec):
    symbol,start,last=rec
    start=pd.Timestamp(start);end=min(start+pd.Timedelta(days=185),pd.Timestamp(last),pd.Timestamp('2025-12-31'))
    rows=[];ok=0;missing=0;codes={}
    for m in month_starts(start,end):
        url=f'{BASE}/{symbol}/1d/{symbol}-1d-{m:%Y-%m}.zip'
        content,code=get_zip(url);codes[str(code)]=codes.get(str(code),0)+1
        if content:
            ok+=1;rows.extend(parse_zip(content,symbol,start,end))
        else:missing+=1
    return rows,{'symbol':symbol,'listing_date':str(start.date()),'last_date':str(pd.Timestamp(last).date()),
      'requested_end':str(end.date()),'bars':len(rows),'monthly_files_ok':ok,'monthly_files_missing':missing,
      'status_codes':json.dumps(codes,sort_keys=True)}

def vision_load_data(db_path:Path)->pd.DataFrame:
    con=duckdb.connect(str(db_path),read_only=True)
    listings=con.execute("""
      SELECT symbol, MIN(date) AS listing_date, MAX(date) AS last_date, COUNT(*) AS available_days
      FROM daily_availability
      WHERE available=TRUE AND symbol LIKE '%USDT'
      GROUP BY symbol ORDER BY listing_date, symbol
    """).fetch_df();con.close()
    listings['listing_date']=pd.to_datetime(listings.listing_date);listings['last_date']=pd.to_datetime(listings.last_date)
    s=listings.symbol.astype(str)
    mask=(s.str.endswith('USDT') & ~s.str.contains('SETTLED',regex=False)
      & ~s.str.contains('_',regex=False) & ~s.isin(mod.INDEX_EXCLUSIONS))
    listings=listings.loc[mask].copy()
    listings=listings[(listings.last_date-listings.listing_date).dt.days>=94]
    listings=listings[listings.listing_date<=pd.Timestamp('2025-10-02')]
    records=list(listings[['symbol','listing_date','last_date']].itertuples(index=False,name=None))
    rows=[];status=[]
    with ThreadPoolExecutor(max_workers=24) as ex:
        futures=[ex.submit(fetch_symbol,r) for r in records]
        for n,f in enumerate(as_completed(futures),1):
            rr,ss=f.result();rows.extend(rr);status.append(ss)
            if n%50==0:print(f'fetched {n}/{len(records)} symbols, rows={len(rows)}',flush=True)
    out=pd.DataFrame(rows)
    coverage=pd.DataFrame(status).sort_values('symbol')
    Path('tmp-alpha-results').mkdir(exist_ok=True)
    coverage.to_csv('tmp-alpha-results/data_fetch_coverage.csv',index=False)
    if out.empty:
        Path('tmp-alpha-results/data_fetch_summary.json').write_text(json.dumps({'symbols_considered':len(records),
          'status_code_counts':coverage.status_codes.value_counts().to_dict()},indent=2))
        raise RuntimeError('Binance Vision monthly archives returned no lifecycle bars')
    out=out.sort_values(['symbol','date']).drop_duplicates(['symbol','date'],keep='last')
    Path('tmp-alpha-results/data_fetch_summary.json').write_text(json.dumps({
      'symbols_considered':int(len(listings)),'symbols_with_bars':int((coverage.bars>0).sum()),
      'symbols_without_bars':int((coverage.bars==0).sum()),'ohlcv_rows':int(len(out)),
      'monthly_files_ok':int(coverage.monthly_files_ok.sum()),'monthly_files_missing':int(coverage.monthly_files_missing.sum()),
      'first_date':str(out.date.min().date()),'last_date':str(out.date.max().date())},indent=2))
    return out

mod.load_data=vision_load_data
mod.main()
