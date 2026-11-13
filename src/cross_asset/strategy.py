"""Long/short signal backtesting on aligned DAILY simple-return series.
Illustrative notional returns; using 1-bar shifted indicators and costs.
"""
import numpy as np
import pandas as pd
ASSETS=['equity','rates','fx','commodity']

def synthetic_returns(n=520,seed=29):
    if n<100:raise ValueError('At least 100 days for sample')
    rng=np.random.default_rng(seed)
    corr=np.array([[1,.05,.18,.25],[.05,1,-.10,-.02],[.18,-.10,1,.15],[.25,-.02,.15,1]])
    z=rng.standard_normal((n,4))@np.linalg.cholesky(corr).T
    daily=np.array([.009,.003,.005,.016])
    drift=np.array([.00025,.00007,.00001,.00015])
    returns=drift+daily*z
    df=pd.DataFrame(returns,columns=ASSETS)
    df.insert(0,'date',pd.bdate_range('2023-01-02',periods=n))
    return df

def validate_returns(data):
    if 'date' not in data or any(a not in data for a in ASSETS):
        raise ValueError('Required CSV columns: date,equity,rates,fx,commodity')
    d=data.copy()
    d['date']=pd.to_datetime(d['date'],errors='raise')
    d=d.sort_values('date').reset_index(drop=True)
    if d.date.duplicated().any():raise ValueError('Duplicate dates not allowed')
    for a in ASSETS: d[a]=pd.to_numeric(d[a],errors='coerce')
    if d[ASSETS].isna().any().any() or not np.isfinite(d[ASSETS].to_numpy()).all():
        raise ValueError('All return entries must be finite')
    if (d[ASSETS]<=-1).any().any():raise ValueError('Simple returns must be greater than -100%')
    return d

def backtest(data,lookback=30,vol_lookback=40,cost_bps=2.0,max_asset_weight=.25,
             max_gross=1.0,target_vol=.10,style='momentum'):
    """Momentum/reversion signals with next-bar positions and diagonal-vol targeting.

    Signal computed using [t-lookback+1,t], position for t+1 is signal[t].
    Scale uses only t-1 observed returns. Limits max notional at <= constraints.
    Vol estimate ignores cross-asset correlation; no claims of exact VaR.
    """
    if lookback<2 or vol_lookback<2 or cost_bps<0 or max_asset_weight<=0 or max_gross<=0 or target_vol<=0:
        raise ValueError('Invalid strategy parameters')
    if style not in ('momentum','reversion'):raise ValueError('Unknown strategy')
    df=validate_returns(data)
    ret=df[ASSETS]
    trailing=np.log1p(ret).rolling(lookback,min_periods=lookback).sum()
    signal=np.sign(trailing).replace(0,0.0)
    if style=='reversion':signal=-signal
    signal=signal.shift(1).fillna(0.0)       # position taken at t uses only info through t-1
    vols=ret.rolling(vol_lookback,min_periods=vol_lookback).std().shift(1)*np.sqrt(252)
    base=signal*min(max_asset_weight,max_gross/len(ASSETS))
    diag_vol=np.sqrt(((base*vols)**2).sum(axis=1))
    ratio=(target_vol/diag_vol.replace(0,np.nan)).clip(upper=1.0).fillna(0.0)
    weights=base.mul(ratio,axis=0).fillna(0.0)
    # Enforce gross cap exactly when only some assets trade
    gross=weights.abs().sum(axis=1)
    scale=(max_gross/gross.replace(0,np.nan)).clip(upper=1.0).fillna(1.0)
    weights=weights.mul(scale,axis=0)
    turnover=weights.diff().fillna(weights).abs().sum(axis=1)
    cost=turnover*cost_bps/10000
    contribution=weights*ret
    gross_ret=contribution.sum(axis=1)
    net=gross_ret-cost
    df=df.assign(gross_return=gross_ret,transaction_cost=cost,turnover=turnover,
                 net_return=net,equity_curve=(1+net).cumprod(),
                 gross_exposure=weights.abs().sum(axis=1))
    for asset in ASSETS:
        df[f'weight_{asset}']=weights[asset]
        df[f'pnl_{asset}']=contribution[asset]
    return df

def performance(backtested):
    r=backtested.net_return.to_numpy(dtype=float)
    if len(r)<2:raise ValueError('Need at least 2 observations')
    if (r<=-1).any():raise ValueError('Invalid net return less than -100%')
    wealth=np.cumprod(1+r)
    peaks=np.maximum.accumulate(np.r_[1.0,wealth])[1:]
    vol=float(np.std(r,ddof=1)*np.sqrt(252))
    return {'total_return':float(wealth[-1]-1),
            'annualized_vol':vol,
            'sharpe_zero_rf':float(np.mean(r)*252/vol) if vol>0 else float('nan'),
            'max_drawdown':float(np.min(wealth/peaks-1)),
            'total_cost_return_points':float(backtested.transaction_cost.sum())}
