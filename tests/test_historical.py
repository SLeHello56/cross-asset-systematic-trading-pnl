import pytest
from cross_asset.historical import fetch_one
class FakeResponse:
    text='observation_date,SP500\n2025-10-01,6500.0\n2025-10-02,6505.0\n'
    def raise_for_status(self):pass
def test_fred_one_parser(monkeypatch):
    monkeypatch.setattr('cross_asset.historical.requests.get',lambda *a,**kw:FakeResponse())
    d=fetch_one('SP500')
    assert len(d)==2
    assert d.SP500.iloc[-1]==6505
