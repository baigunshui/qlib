# Turtle Strategy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a multi-instrument Turtle Trading strategy for Qlib with standard entry, exit, ATR unit sizing, pyramiding, and stop-loss rules, validated primarily by unit tests instead of end-to-end runtime execution.

**Architecture:** Keep all Turtle-specific rule calculation in a small pure-Python module under `qlib.contrib.strategy`, with explicit state objects that can be instantiated directly in tests. Add a thin `TurtleStrategy` adapter that translates Qlib market/context objects into rule-engine inputs and translates rule outputs into `Order` / `TradeDecisionWO` decisions.

**Tech Stack:** Python, pandas, numpy, pytest, Qlib strategy/backtest primitives

---

## File Structure

- Create: `qlib/contrib/strategy/turtle_strategy.py`
  Responsibility: state dataclasses, indicator helpers, rule engine, and the thin `TurtleStrategy` Qlib adapter.
- Modify: `qlib/contrib/strategy/__init__.py`
  Responsibility: export `TurtleStrategy` for the public contrib strategy API.
- Create: `tests/backtest/test_turtle_strategy.py`
  Responsibility: pure unit tests for indicator calculation, state transitions, portfolio constraints, and adapter translation with stubs.

## Task 1: Scaffold indicators and state model

**Files:**
- Create: `qlib/contrib/strategy/turtle_strategy.py`
- Test: `tests/backtest/test_turtle_strategy.py`

- [ ] **Step 1: Write the failing tests for indicators and state defaults**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/backtest/test_turtle_strategy.py -k "donchian or atr or empty_instrument_state" -v`
Expected: FAIL with `ModuleNotFoundError` or missing symbol errors for `qlib.contrib.strategy.turtle_strategy`.

- [ ] **Step 3: Write minimal implementation for indicators and state**

```python
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

import pandas as pd


@dataclass
class TurtleInstrumentState:
    units: int = 0
    entry_price: Optional[float] = None
    last_add_price: Optional[float] = None
    stop_price: Optional[float] = None
    atr: Optional[float] = None


@dataclass
class TurtlePortfolioState:
    cash: float
    instrument_states: Dict[str, TurtleInstrumentState] = field(default_factory=dict)

    def ensure_instrument(self, instrument: str) -> TurtleInstrumentState:
        if instrument not in self.instrument_states:
            self.instrument_states[instrument] = TurtleInstrumentState()
        return self.instrument_states[instrument]


def compute_donchian_channels(
    frame: pd.DataFrame, entry_window: int, exit_window: int
) -> Tuple[pd.Series, pd.Series]:
    upper = frame["high"].shift(1).rolling(entry_window).max()
    lower = frame["low"].shift(1).rolling(exit_window).min()
    return upper, lower


def compute_atr(frame: pd.DataFrame, atr_window: int) -> pd.Series:
    prev_close = frame["close"].shift(1)
    true_range = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - prev_close).abs(),
            (frame["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.rolling(atr_window).mean()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/backtest/test_turtle_strategy.py -k "donchian or atr or empty_instrument_state" -v`
Expected: PASS for all 3 selected tests.

- [ ] **Step 5: Commit**

```bash
git add qlib/contrib/strategy/turtle_strategy.py tests/backtest/test_turtle_strategy.py
git commit -m "test(strategy): scaffold turtle indicators and portfolio state"
```

## Task 2: Implement single-instrument rule transitions

**Files:**
- Modify: `qlib/contrib/strategy/turtle_strategy.py`
- Test: `tests/backtest/test_turtle_strategy.py`

- [ ] **Step 1: Write the failing tests for entry, pyramiding, exit, and stop-loss**

```python
import pandas as pd

from qlib.contrib.strategy.turtle_strategy import TurtleRuleEngine, TurtlePortfolioState


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
    state.stop_price = 10.0
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/backtest/test_turtle_strategy.py -k "opens_new_position or adds_unit or exits_on_channel_break or prioritizes_stop" -v`
Expected: FAIL with missing `TurtleRuleEngine` or `evaluate_instrument`.

- [ ] **Step 3: Write minimal implementation for rule evaluation**

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class TurtleDecision:
    action: str
    target_units: int
    unit_size: int
    reference_price: Optional[float]
    stop_price: Optional[float]
    atr: Optional[float]


class TurtleRuleEngine:
    def __init__(self, entry_window: int, exit_window: int, atr_window: int, risk_pct: float):
        self.entry_window = entry_window
        self.exit_window = exit_window
        self.atr_window = atr_window
        self.risk_pct = risk_pct

    def _compute_unit_size(self, portfolio_value: float, atr_value: float, contract_scale: float) -> int:
        if pd.isna(atr_value) or atr_value <= 0:
            return 0
        return max(int((portfolio_value * self.risk_pct) / (atr_value * contract_scale)), 0)

    def evaluate_instrument(
        self,
        instrument: str,
        frame: pd.DataFrame,
        portfolio_state: TurtlePortfolioState,
        portfolio_value: float,
        contract_scale: float,
        max_units_per_instrument: int,
    ) -> TurtleDecision:
        state = portfolio_state.ensure_instrument(instrument)
        upper, lower = compute_donchian_channels(frame, self.entry_window, self.exit_window)
        atr = compute_atr(frame, self.atr_window)
        latest_close = float(frame["close"].iloc[-1])
        latest_low = float(frame["low"].iloc[-1])
        atr_value = float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else None
        unit_size = self._compute_unit_size(portfolio_value, atr_value, contract_scale) if atr_value else 0

        if atr_value is None or unit_size == 0:
            return TurtleDecision("hold", state.units, 0, None, state.stop_price, atr_value)

        if state.units > 0 and state.stop_price is not None and latest_low <= state.stop_price:
            return TurtleDecision("stop", 0, unit_size, latest_close, None, atr_value)

        if state.units > 0 and not pd.isna(lower.iloc[-1]) and latest_close < float(lower.iloc[-1]):
            return TurtleDecision("exit", 0, unit_size, latest_close, None, atr_value)

        if state.units > 0 and state.last_add_price is not None:
            add_threshold = state.last_add_price + 0.5 * atr_value
            if latest_close >= add_threshold and state.units < max_units_per_instrument:
                return TurtleDecision(
                    "add",
                    state.units + 1,
                    unit_size,
                    latest_close,
                    latest_close - 2 * atr_value,
                    atr_value,
                )

        if state.units == 0 and not pd.isna(upper.iloc[-1]) and latest_close > float(upper.iloc[-1]):
            return TurtleDecision("open", 1, unit_size, latest_close, latest_close - 2 * atr_value, atr_value)

        return TurtleDecision("hold", state.units, unit_size, latest_close, state.stop_price, atr_value)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/backtest/test_turtle_strategy.py -k "opens_new_position or adds_unit or exits_on_channel_break or prioritizes_stop" -v`
Expected: PASS for all 4 selected tests.

- [ ] **Step 5: Commit**

```bash
git add qlib/contrib/strategy/turtle_strategy.py tests/backtest/test_turtle_strategy.py
git commit -m "feat(strategy): implement turtle rule transitions"
```

## Task 3: Implement multi-instrument portfolio constraints and state application

**Files:**
- Modify: `qlib/contrib/strategy/turtle_strategy.py`
- Test: `tests/backtest/test_turtle_strategy.py`

- [ ] **Step 1: Write the failing tests for max positions, cash limits, and state mutation**

```python
import pandas as pd

from qlib.contrib.strategy.turtle_strategy import TurtlePortfolioState, TurtleRuleEngine


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/backtest/test_turtle_strategy.py -k "limits_active_instruments or insufficient or apply_decision_updates_state" -v`
Expected: FAIL with missing `evaluate_portfolio` or `apply_decision`.

- [ ] **Step 3: Write minimal implementation for portfolio-level constraints**

```python
class TurtleRuleEngine:
    ...

    def evaluate_portfolio(
        self,
        instrument_frames: dict,
        portfolio_state: TurtlePortfolioState,
        portfolio_value: float,
        contract_scale: float,
        max_units_per_instrument: int,
        max_active_instruments: int,
    ) -> dict:
        decisions = {}
        active_count = sum(1 for state in portfolio_state.instrument_states.values() if state.units > 0)
        remaining_slots = max(max_active_instruments - active_count, 0)

        for instrument, frame in instrument_frames.items():
            decision = self.evaluate_instrument(
                instrument=instrument,
                frame=frame,
                portfolio_state=portfolio_state,
                portfolio_value=portfolio_value,
                contract_scale=contract_scale,
                max_units_per_instrument=max_units_per_instrument,
            )
            estimated_cost = decision.unit_size * float(frame["close"].iloc[-1]) * contract_scale

            if decision.action == "open":
                if remaining_slots <= 0 or estimated_cost > portfolio_state.cash:
                    decision = TurtleDecision("hold", 0, 0, None, None, decision.atr)
                else:
                    remaining_slots -= 1

            if decision.action == "add" and estimated_cost > portfolio_state.cash:
                decision = TurtleDecision("hold", portfolio_state.ensure_instrument(instrument).units, 0, None, None, decision.atr)

            decisions[instrument] = decision

        return decisions

    def apply_decision(self, instrument: str, decision: TurtleDecision, portfolio_state: TurtlePortfolioState) -> None:
        state = portfolio_state.ensure_instrument(instrument)
        if decision.action in {"exit", "stop"}:
            state.units = 0
            state.entry_price = None
            state.last_add_price = None
            state.stop_price = None
            state.atr = decision.atr
            return
        if decision.action == "open":
            state.units = decision.target_units
            state.entry_price = decision.reference_price
            state.last_add_price = decision.reference_price
            state.stop_price = decision.stop_price
            state.atr = decision.atr
            return
        if decision.action == "add":
            state.units = decision.target_units
            state.last_add_price = decision.reference_price
            state.stop_price = decision.stop_price
            state.atr = decision.atr
            return
        state.atr = decision.atr
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/backtest/test_turtle_strategy.py -k "limits_active_instruments or insufficient or apply_decision_updates_state" -v`
Expected: PASS for all 3 selected tests.

- [ ] **Step 5: Commit**

```bash
git add qlib/contrib/strategy/turtle_strategy.py tests/backtest/test_turtle_strategy.py
git commit -m "feat(strategy): add turtle portfolio constraints and state updates"
```

## Task 4: Add thin Qlib adapter and public export

**Files:**
- Modify: `qlib/contrib/strategy/turtle_strategy.py`
- Modify: `qlib/contrib/strategy/__init__.py`
- Test: `tests/backtest/test_turtle_strategy.py`

- [ ] **Step 1: Write the failing tests for adapter translation and public export**

```python
import pandas as pd

from qlib.contrib.strategy import TurtleStrategy


class _StubPosition:
    def get_stock_amount(self, code):
        return {"A": 200}.get(code, 0)


class _StubExchange:
    def is_stock_tradable(self, **kwargs):
        return True

    def get_deal_price(self, stock_id, **kwargs):
        return {"A": 10.0}.get(stock_id, 10.0)

    def get_factor(self, **kwargs):
        return 1.0

    def round_amount_by_trade_unit(self, amount, factor):
        return int(amount)

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/backtest/test_turtle_strategy.py -k "is_exported or builds_orders" -v`
Expected: FAIL with missing `TurtleStrategy` export or `_build_orders_from_decisions`.

- [ ] **Step 3: Write minimal adapter implementation and export**

```python
from qlib.backtest.decision import Order, TradeDecisionWO
from qlib.contrib.strategy.signal_strategy import BaseSignalStrategy


class TurtleStrategy(BaseSignalStrategy):
    def _build_orders_from_decisions(self, decision_map, trade_start_time, trade_end_time):
        orders = []
        for instrument, decision in decision_map.items():
            if decision.action == "open" or decision.action == "add":
                order = Order(
                    stock_id=instrument,
                    amount=decision.unit_size,
                    start_time=trade_start_time,
                    end_time=trade_end_time,
                    direction=Order.BUY,
                )
                if self.trade_exchange.check_order(order):
                    orders.append(order)
            elif decision.action == "exit" or decision.action == "stop":
                amount = self.trade_position.get_stock_amount(code=instrument)
                order = Order(
                    stock_id=instrument,
                    amount=amount,
                    start_time=trade_start_time,
                    end_time=trade_end_time,
                    direction=Order.SELL,
                )
                if self.trade_exchange.check_order(order):
                    orders.append(order)
        return orders

    def generate_trade_decision(self, execute_result=None):
        return TradeDecisionWO([], self)
```

In `qlib/contrib/strategy/__init__.py`, add:

```python
from .turtle_strategy import TurtleStrategy
```

and include `"TurtleStrategy"` in `__all__`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/backtest/test_turtle_strategy.py -k "is_exported or builds_orders" -v`
Expected: PASS for both selected tests.

- [ ] **Step 5: Run the full targeted test file**

Run: `pytest tests/backtest/test_turtle_strategy.py -v`
Expected: PASS for all Turtle strategy unit tests.

- [ ] **Step 6: Commit**

```bash
git add qlib/contrib/strategy/turtle_strategy.py qlib/contrib/strategy/__init__.py tests/backtest/test_turtle_strategy.py
git commit -m "feat(strategy): add qlib turtle strategy adapter"
```

## Task 5: Final verification and cleanup

**Files:**
- Modify: `qlib/contrib/strategy/turtle_strategy.py`
- Modify: `tests/backtest/test_turtle_strategy.py`
- Modify: `qlib/contrib/strategy/__init__.py`

- [ ] **Step 1: Run focused regression checks**

Run: `pytest tests/backtest/test_turtle_strategy.py tests/backtest/test_soft_topk_strategy.py -v`
Expected: PASS for Turtle tests and no regression in `SoftTopkStrategy` tests.

- [ ] **Step 2: Run style checks on touched files**

Run: `python -m black qlib/contrib/strategy/turtle_strategy.py tests/backtest/test_turtle_strategy.py -l 120 --check`
Expected: PASS with no formatting changes required.

Run: `flake8 qlib/contrib/strategy/turtle_strategy.py tests/backtest/test_turtle_strategy.py --ignore=E501,F541,E266,E402,W503,E731,E203`
Expected: PASS.

- [ ] **Step 3: If a check fails, apply the smallest correction and rerun only the failed command**

```python
# Example of acceptable correction scope:
# - rename an unused local variable
# - split a long assertion across lines
# - remove an unused import
```

- [ ] **Step 4: Commit final polish**

```bash
git add qlib/contrib/strategy/turtle_strategy.py qlib/contrib/strategy/__init__.py tests/backtest/test_turtle_strategy.py
git commit -m "test(strategy): verify turtle strategy implementation"
```

## Self-Review

- Spec coverage checked:
  - multi-instrument support: Task 3
  - standard Turtle rules: Tasks 2 and 3
  - unit-test-first validation: Tasks 1 through 5
  - thin Qlib adapter: Task 4
- Placeholder scan checked:
  - no `TODO`, `TBD`, or deferred implementation markers remain in the plan
- Type consistency checked:
  - `TurtlePortfolioState`, `TurtleInstrumentState`, `TurtleRuleEngine`, `TurtleDecision`, `evaluate_instrument`, `evaluate_portfolio`, and `apply_decision` are named consistently across tasks
