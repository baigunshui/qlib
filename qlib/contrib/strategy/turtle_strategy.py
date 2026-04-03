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
