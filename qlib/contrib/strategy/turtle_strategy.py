# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

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


@dataclass
class TurtleDecision:
    action: str
    target_units: int
    unit_size: int
    reference_price: Optional[float]
    stop_price: Optional[float]
    atr: Optional[float]


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
