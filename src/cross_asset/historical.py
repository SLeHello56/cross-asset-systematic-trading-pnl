"""FRED US cross-asset *proxies*, not investable total-return instruments.
Downloads raw observations one series at a time to avoid mixed-frequency zip.
FX DEXUSEU: dollars per euro, Treasury DGS10: percent; WTI: USD/bbl.
"""
from io import StringIO
import pandas as pd
import requests

SERIES={'equity':'SP500','rates':'DGS10','fx':'DEXUSEU','commodity':'DCOILWTICO'}

def fetch_one(series,start='2017-01-01'):
    if series not in SERIES.values():raise ValueError('Unsupported FRED series')
    r=requests.get('https://fred.stlouisfed.org/graph/fredgraph.csv',params={'id':series,'cosd':start},timeout=30)
    r.raise_for_status()
    df=pd.read_csv(StringIO(r.text))
    date_col='observation_date' if 'observation_date' in df else 'DATE'
    if series not in df or date_col not in df:raise ValueError(f'Unexpected response for {series}')
    df=df.rename(columns={date_col:'date',series:series})[['date',series]]
    df['date']=pd.to_datetime(df.date)
    df[series]=pd.to_numeric(df[series],errors='coerce')
    return df.dropna().drop_duplicates('date').sort_values('date')

def historical_proxy_returns(start='2017-01-01',duration_years=7.0):
    """Align to common quote dates. 10y Treasury return is -duration*Δyield only;
    no coupon/carry/convexity. Commodity & FX are spot; all non-investable proxies.
    """
    if duration_years<=0:raise ValueError('Duration must be positive')
    data=[fetch_one(s,start) for s in SERIES.values()]
    merged=data[0]
    for x in data[1:]:merged=merged.merge(x,on='date',how='inner')
    merged=merged.sort_values('date').reset_index(drop=True)
    if len(merged)<80:raise ValueError('Too few aligned historical observations')
    if (merged[['SP500','DEXUSEU','DCOILWTICO']]<=0).any().any():
        raise ValueError('Nonpositive spot quote not supported')
    returns=pd.DataFrame({'date':merged.date,'equity':merged.SP500.pct_change(),
                          'rates':-duration_years*(merged.DGS10.diff()/100),
                          'fx':merged.DEXUSEU.pct_change(),
                          'commodity':merged.DCOILWTICO.pct_change()}).dropna()
    return returns.reset_index(drop=True)
