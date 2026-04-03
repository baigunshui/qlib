import pandas as pd

from qlib.contrib.strategy import TurtleStrategy
from qlib.contrib.strategy.turtle_strategy import (
    TurtlePortfolioState,
    TurtleRuleEngine,
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


def _single_instrument_frame():
    return pd.DataFrame(
        {
            "instrument": ["A"] * 6,
            "high": [10.0, 10.5, 11.0, 12.2, 12.7, 10.0],
            "low": [9.0, 9.2, 9.8, 11.4, 12.0, 8.8],
            "close": [9.5, 10.2, 10.9, 12.0, 12.6, 9.0],
        },
        index=pd.date_range("2020-01-01", periods=6, freq="D"),
    )


def test_rule_engine_opens_new_position_on_breakout():
    engine = TurtleRuleEngine(entry_window=2, exit_window=2, atr_window=2, risk_pct=0.01)
    portfolio = TurtlePortfolioState(cash=100000.0)

    result = engine.evaluate_instrument(
        instrument="A",
        frame=_single_instrument_frame().iloc[:4],
        portfolio_state=portfolio,
        portfolio_value=100000.0,
        contract_scale=1.0,
        max_units_per_instrument=4,
    )

    assert result.action == "open"
    assert result.target_units == 1
    assert result.unit_size > 0


def test_rule_engine_adds_unit_every_half_n():
    engine = TurtleRuleEngine(entry_window=2, exit_window=2, atr_window=2, risk_pct=0.01)
    portfolio = TurtlePortfolioState(cash=100000.0)
    state = portfolio.ensure_instrument("A")
    state.units = 1
    state.entry_price = 12.0
    state.last_add_price = 12.0
    state.stop_price = 8.0
    state.atr = 1.0

    result = engine.evaluate_instrument(
        instrument="A",
        frame=_single_instrument_frame().iloc[:5],
        portfolio_state=portfolio,
        portfolio_value=100000.0,
        contract_scale=1.0,
        max_units_per_instrument=4,
    )

    assert result.action == "add"
    assert result.target_units == 2


def test_rule_engine_exits_on_channel_break():
    engine = TurtleRuleEngine(entry_window=2, exit_window=2, atr_window=2, risk_pct=0.01)
    portfolio = TurtlePortfolioState(cash=100000.0)
    state = portfolio.ensure_instrument("A")
    state.units = 2
    state.entry_price = 12.0
    state.last_add_price = 12.5
    state.stop_price = 8.0
    state.atr = 1.0

    result = engine.evaluate_instrument(
        instrument="A",
        frame=_single_instrument_frame(),
        portfolio_state=portfolio,
        portfolio_value=100000.0,
        contract_scale=1.0,
        max_units_per_instrument=4,
    )

    assert result.action == "exit"
    assert result.target_units == 0


def test_rule_engine_prioritizes_stop_over_add():
    engine = TurtleRuleEngine(entry_window=2, exit_window=2, atr_window=2, risk_pct=0.01)
    portfolio = TurtlePortfolioState(cash=100000.0)
    state = portfolio.ensure_instrument("A")
    state.units = 1
    state.entry_price = 10.0
    state.last_add_price = 10.0
    state.stop_price = 9.5
    state.atr = 1.0

    frame = pd.DataFrame(
        {
            "instrument": ["A"] * 4,
            "high": [10.0, 10.4, 11.2, 11.5],
            "low": [9.7, 9.8, 9.4, 9.3],
            "close": [9.9, 10.2, 10.9, 10.8],
        },
        index=pd.date_range("2020-02-01", periods=4, freq="D"),
    )

    result = engine.evaluate_instrument(
        instrument="A",
        frame=frame,
        portfolio_state=portfolio,
        portfolio_value=100000.0,
        contract_scale=1.0,
        max_units_per_instrument=4,
    )

    assert result.action == "stop"
    assert result.target_units == 0


def _portfolio_frames():
    dates = pd.date_range("2020-03-01", periods=4, freq="D")
    frame_a = pd.DataFrame(
        {"high": [10.0, 10.5, 11.1, 11.8], "low": [9.0, 9.2, 9.7, 10.8], "close": [9.5, 10.0, 11.0, 11.7]},
        index=dates,
    )
    frame_b = pd.DataFrame(
        {"high": [20.0, 20.2, 21.0, 21.8], "low": [18.0, 18.5, 19.2, 20.5], "close": [19.0, 19.8, 20.9, 21.7]},
        index=dates,
    )
    return {"A": frame_a, "B": frame_b}


def test_portfolio_evaluation_limits_active_instruments():
    engine = TurtleRuleEngine(entry_window=2, exit_window=2, atr_window=2, risk_pct=0.01)
    portfolio = TurtlePortfolioState(cash=100000.0)

    decisions = engine.evaluate_portfolio(
        instrument_frames=_portfolio_frames(),
        portfolio_state=portfolio,
        portfolio_value=100000.0,
        contract_scale=1.0,
        max_units_per_instrument=4,
        max_active_instruments=1,
    )

    opened = [code for code, decision in decisions.items() if decision.action == "open"]
    assert len(opened) == 1


def test_portfolio_evaluation_skips_open_when_cash_is_insufficient():
    engine = TurtleRuleEngine(entry_window=2, exit_window=2, atr_window=2, risk_pct=0.50)
    portfolio = TurtlePortfolioState(cash=100.0)

    decisions = engine.evaluate_portfolio(
        instrument_frames={"A": _portfolio_frames()["A"]},
        portfolio_state=portfolio,
        portfolio_value=100.0,
        contract_scale=1000.0,
        max_units_per_instrument=4,
        max_active_instruments=2,
    )

    assert decisions["A"].action == "hold"


def test_apply_decision_updates_state_after_add():
    engine = TurtleRuleEngine(entry_window=2, exit_window=2, atr_window=2, risk_pct=0.01)
    portfolio = TurtlePortfolioState(cash=100000.0)
    state = portfolio.ensure_instrument("A")
    state.units = 1
    state.entry_price = 12.0
    state.last_add_price = 12.0
    state.stop_price = 10.0
    state.atr = 1.0

    decision = engine.evaluate_instrument(
        instrument="A",
        frame=pd.DataFrame(
            {"high": [10.0, 11.0, 12.0, 13.0], "low": [9.0, 10.0, 11.0, 12.0], "close": [9.5, 10.8, 12.0, 12.7]},
            index=pd.date_range("2020-04-01", periods=4, freq="D"),
        ),
        portfolio_state=portfolio,
        portfolio_value=100000.0,
        contract_scale=1.0,
        max_units_per_instrument=4,
    )
    engine.apply_decision("A", decision, portfolio)

    updated = portfolio.ensure_instrument("A")
    assert updated.units == 2
    assert updated.last_add_price == decision.reference_price
    assert updated.stop_price == decision.stop_price


class _StubPosition:
    def get_stock_amount(self, code):
        return {"B": 200}.get(code, 0)


class _StubExchange:
    def check_order(self, order):
        return order.amount > 0


def test_turtle_strategy_is_exported():
    assert TurtleStrategy.__name__ == "TurtleStrategy"


def test_translate_decisions_builds_orders():
    strategy = TurtleStrategy.__new__(TurtleStrategy)
    strategy.trade_exchange = _StubExchange()
    strategy.trade_position = _StubPosition()

    decision_map = {
        "A": type("Decision", (), {"action": "open", "unit_size": 50})(),
        "B": type("Decision", (), {"action": "exit", "unit_size": 0})(),
    }

    orders = strategy._build_orders_from_decisions(
        decision_map=decision_map,
        trade_start_time=pd.Timestamp("2020-05-01"),
        trade_end_time=pd.Timestamp("2020-05-01"),
    )

    assert len(orders) == 2
    assert {order.stock_id for order in orders} == {"A", "B"}
    assert {order.direction for order in orders} == {0, 1}
