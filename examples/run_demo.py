from cross_asset.strategy import synthetic_returns,backtest,performance
x=backtest(synthetic_returns())
print('Synthetic backtest:',performance(x))
print(x[['date','weight_equity','weight_rates','weight_fx','weight_commodity','net_return']].tail().to_string(index=False))
