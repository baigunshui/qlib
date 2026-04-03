import pandas as pd

from qlib.contrib.strategy.turtle_strategy import (
    TurtleInstrumentState,
    TurtlePortfolioState,
    compute_atr,
    compute_donchian_channels,
)


def test_compute_donchian_channels_excludes_current_bar():
    frame = pd.DataFrame(
        {
            "high": [10.0, 11.0, 12.0, 13.0],
            "low": [8.0, 8.5, 9.0, 9.5],
            "close": [9.0, 10.0, 11.0, 12.0],
        },
        index=pd.date_range("2020-01-01", periods=4, freq="D"),
    )

    upper, lower = compute_donchian_channels(frame, entry_window=3, exit_window=2)

    assert pd.isna(upper.iloc[0])
    assert upper.iloc[3] == 12.0
    assert lower.iloc[3] == 8.5


def test_compute_atr_returns_expected_value():
    frame = pd.DataFrame(
        {
            "high": [10.0, 11.0, 13.0],
            "low": [8.0, 9.0, 10.0],
            "close": [9.0, 10.0, 12.0],
        },
        index=pd.date_range("2020-01-01", periods=3, freq="D"),
    )

    atr = compute_atr(frame, atr_window=2)

    assert round(float(atr.iloc[-1]), 4) == 2.5000


def test_portfolio_state_creates_empty_instrument_state():
    portfolio = TurtlePortfolioState(cash=100000.0)

    state = portfolio.ensure_instrument("SH600519")

    assert state.units == 0
    assert state.entry_price is None
    assert state.last_add_price is None
    assert state.stop_price is None
