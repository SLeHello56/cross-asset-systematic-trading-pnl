import numpy as np
import pandas as pd
import pytest
from cross_asset.strategy import synthetic_returns,backtest,performance

def test_gross_limits():
    d=backtest(synthetic_returns(),max_asset_weight=.2,max_gross=.7)
    assert (d.gross_exposure<=.700001).all()
    assert (d[[f'weight_{a}' for a in ['equity','rates','fx','commodity']]].abs()<=.200001).all().all()
def test_no_lookahead_last_bar():
    x=synthetic_returns()
    a=backtest(x)
    changed=x.copy();changed.loc[changed.index[-1],'equity']+=.40
    b=backtest(changed)
    columns=[f'weight_{a}' for a in ['equity','rates','fx','commodity']]
    np.testing.assert_allclose(a.loc[len(a)-1,columns].to_numpy(dtype=float),b.loc[len(b)-1,columns].to_numpy(dtype=float))
def test_costs_reduce_equity():
    x=synthetic_returns()
    a=backtest(x,cost_bps=0)
    b=backtest(x,cost_bps=25)
    assert b.transaction_cost.sum()>0
    assert b.equity_curve.iloc[-1]<a.equity_curve.iloc[-1]
def test_pnl_attribution_reconciles():
    x=backtest(synthetic_returns())
    cols=['pnl_equity','pnl_rates','pnl_fx','pnl_commodity']
    np.testing.assert_allclose(x[cols].sum(axis=1).to_numpy()-x.transaction_cost.to_numpy(),x.net_return.to_numpy())
def test_empty_warmup_no_positions():
    x=backtest(synthetic_returns())
    assert x.gross_exposure.iloc[:40].sum()==0
def test_reversion_differs():
    x=synthetic_returns()
    a=backtest(x,style='momentum');b=backtest(x,style='reversion')
    assert (a.weight_equity==-b.weight_equity).all()
def test_performance():
    x=backtest(synthetic_returns())
    m=performance(x)
    assert m['max_drawdown']<=0
    assert np.isfinite(m['total_return'])
