# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

import pandas as pd

try:
    from qlib.contrib.strategy.signal_strategy import BaseSignalStrategy
except ModuleNotFoundError:  # pragma: no cover - fallback for test-only environments
    class BaseSignalStrategy:  # type: ignore[no-redef]
        pass


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


@dataclass
class TurtleDecision:
    action: str
    target_units: int
    unit_size: int
    reference_price: Optional[float]
    stop_price: Optional[float]
    atr: Optional[float]


@dataclass
class _FallbackOrder:
    SELL = 0
    BUY = 1

    stock_id: str
    amount: int
    start_time: pd.Timestamp
    end_time: pd.Timestamp
    direction: int


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


class TurtleStrategy(BaseSignalStrategy):
    @staticmethod
    def _get_order_class():
        try:
            from qlib.backtest.decision import Order

            return Order
        except ModuleNotFoundError:
            return _FallbackOrder

    def _build_orders_from_decisions(self, decision_map, trade_start_time, trade_end_time):
        order_class = self._get_order_class()
        orders = []
        for instrument, decision in decision_map.items():
            if decision.action in {"open", "add"}:
                order = order_class(
                    stock_id=instrument,
                    amount=decision.unit_size,
                    start_time=trade_start_time,
                    end_time=trade_end_time,
                    direction=order_class.BUY,
                )
                if self.trade_exchange.check_order(order):
                    orders.append(order)
            elif decision.action in {"exit", "stop"}:
                amount = self.trade_position.get_stock_amount(code=instrument)
                order = order_class(
                    stock_id=instrument,
                    amount=amount,
                    start_time=trade_start_time,
                    end_time=trade_end_time,
                    direction=order_class.SELL,
                )
                if self.trade_exchange.check_order(order):
                    orders.append(order)
        return orders

    def generate_trade_decision(self, execute_result=None):
        try:
            from qlib.backtest.decision import TradeDecisionWO
        except ModuleNotFoundError:
            return []
        return TradeDecisionWO([], self)
