import streamlit as st
import pandas as pd
from cross_asset.strategy import synthetic_returns,validate_returns,backtest,performance,ASSETS
from cross_asset.historical import historical_proxy_returns
st.set_page_config(page_title='Cross-Asset Trading & P&L',layout='wide')
st.title('Cross-Asset Systematic Trading & P&L Dashboard')
st.caption('Educational long/short research — synthetic sample, user CSV, or FRED non-investable market proxies.')
source=st.radio('Input data',['Synthetic demo','Upload daily returns CSV','Fetch FRED historical proxies (internet)'])
if source=='Upload daily returns CSV':
    upload=st.file_uploader('Upload date,equity,rates,fx,commodity — simple daily returns in decimal',type=['csv'])
    if upload is None:st.stop()
    data=pd.read_csv(upload)
elif source.startswith('Fetch'):
    try: data=historical_proxy_returns()
    except Exception as e:st.error(f'Historical fetch unavailable: {e}');st.stop()
    st.warning('FRED underlying proxies are not tradeable total returns: S&P index, Treasury yield duration approximation, spot EUR/USD and WTI; interpretation limited.')
else:data=synthetic_returns()
a,b,c=st.columns(3)
style=a.selectbox('Signal',['momentum','reversion'])
lookback=b.slider('Signal lookback (days)',10,100,30)
cost=c.slider('Turnover cost (bps)',0.,20.,2.)
target=st.slider('Diagonal volatility proxy target, annualized',.02,.30,.10,.01)
max_weight=st.slider('Max absolute weight per asset',.05,.50,.25,.05)
try:
    result=backtest(data,lookback=lookback,cost_bps=cost,target_vol=target,max_asset_weight=max_weight,style=style)
    stats=performance(result)
    cols=st.columns(4)
    for col,(name,value) in zip(cols,stats.items()):
        col.metric(name.replace('_',' ').title(),f'{value:.2%}' if name in ('total_return','annualized_vol','max_drawdown','total_cost_return_points') else f'{value:.2f}')
    st.line_chart(result.set_index('date').equity_curve)
    st.subheader('Gross asset P&L contributions (daily return units)')
    st.line_chart(result.set_index('date')[[f'pnl_{a}' for a in ASSETS]].cumsum())
    st.subheader('Risk limits and position weights')
    st.line_chart(result.set_index('date')[[f'weight_{a}' for a in ASSETS]])
    st.dataframe(result.tail(15),hide_index=True)
    st.download_button('Download full backtest CSV',data=result.to_csv(index=False),file_name='cross_asset_backtest.csv')
except (ValueError,KeyError) as e:st.error(str(e))
