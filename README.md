# Cross-Asset Systematic Trading & P&L Dashboard

Python research framework for equity, rates, FX and commodity signals, volatility targeting, portfolio risk limits, transaction costs, lagged signal execution and P&L attribution.

## Run

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
python examples/run_demo.py
streamlit run app.py
```

Backtests on supplied sample data are synthetic and exclude many real-world execution and market-access constraints. No claim of live, investable performance is made. Educational research only.
