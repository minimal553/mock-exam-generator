#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json
import time
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd
import requests

MODULE_PATH=Path(__file__).with_name('tmp-alpha-lifecycle.py')
spec=importlib.util.spec_from_file_location('frozen_lifecycle',MODULE_PATH)
mod=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

API='https://fapi.binance.com/fapi/v1/klines'

def fetch_json(session,params):
    for attempt in range(6):
        r=session.get(API,params=params,timeout=30)
        if r.status_code==200:return r.json()
        if r.status_code in (418,429):
            time.sleep(float(r.headers.get('Retry-After','5'))+attempt*2);continue
        if r.status_code>=500:
            time.sleep(2**attempt);continue
        return []
    return []

def rest_load_data(db_path:Path)->pd.DataFrame:
    con=duckdb.connect(str(db_path),read_only=True)
    listings=con.execute("""
      SELECT symbol, MIN(date) AS listing_date, MAX(date) AS last_date, COUNT(*) AS available_days
      FROM daily_availability
      WHERE available=TRUE AND symbol LIKE '%USDT'
      GROUP BY symbol ORDER BY listing_date, symbol
    """).fetch_df();con.close()
    listings['listing_date']=pd.to_datetime(listings.listing_date)
    listings['last_date']=pd.to_datetime(listings.last_date)
    s=listings.symbol.astype(str)
    mask=(s.str.endswith('USDT') & ~s.str.contains('SETTLED',regex=False)
      & ~s.str.contains('_',regex=False) & ~s.isin(mod.INDEX_EXCLUSIONS))
    listings=listings.loc[mask].copy()
    listings=listings[(listings.last_date-listings.listing_date).dt.days>=94]
    listings=listings[listings.listing_date<=pd.Timestamp('2025-10-02')]
    rows=[];status=[];session=requests.Session()
    for n,r in enumerate(listings.itertuples(index=False),1):
        start=pd.Timestamp(r.listing_date)
        end=min(start+pd.Timedelta(days=185),pd.Timestamp(r.last_date),pd.Timestamp('2025-12-31'))
        params={'symbol':r.symbol,'interval':'1d','startTime':int(start.timestamp()*1000),
          'endTime':int((end+pd.Timedelta(days=1)-pd.Timedelta(milliseconds=1)).timestamp()*1000),'limit':200}
        data=fetch_json(session,params)
        valid=0
        if isinstance(data,list):
            for x in data:
                if not isinstance(x,list) or len(x)<11:continue
                rows.append({'date':pd.to_datetime(int(x[0]),unit='ms'),'symbol':r.symbol,'available':True,
                  'quote_volume_usdt':float(x[7]),'open_price':float(x[1]),'high_price':float(x[2]),
                  'low_price':float(x[3]),'close_price':float(x[4])});valid+=1
        status.append({'symbol':r.symbol,'listing_date':str(start.date()),'last_date':str(pd.Timestamp(r.last_date).date()),
          'requested_end':str(end.date()),'bars':valid})
        if n%50==0:print(f'fetched {n}/{len(listings)} symbols, rows={len(rows)}',flush=True)
        time.sleep(0.10)
    out=pd.DataFrame(rows)
    if out.empty:raise RuntimeError('Official Binance REST returned no lifecycle bars')
    out=out.sort_values(['symbol','date']).drop_duplicates(['symbol','date'],keep='last')
    coverage=pd.DataFrame(status)
    Path('tmp-alpha-results').mkdir(exist_ok=True)
    coverage.to_csv('tmp-alpha-results/data_fetch_coverage.csv',index=False)
    Path('tmp-alpha-results/data_fetch_summary.json').write_text(json.dumps({
      'symbols_considered':int(len(listings)),'symbols_with_bars':int((coverage.bars>0).sum()),
      'symbols_without_bars':int((coverage.bars==0).sum()),'ohlcv_rows':int(len(out)),
      'first_date':str(out.date.min().date()),'last_date':str(out.date.max().date())},indent=2))
    return out

mod.load_data=rest_load_data
mod.main()
