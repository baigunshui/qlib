# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from importlib import import_module


_EXPORTS = {
    "TopkDropoutStrategy": ".signal_strategy",
    "WeightStrategyBase": ".signal_strategy",
    "EnhancedIndexingStrategy": ".signal_strategy",
    "TWAPStrategy": ".rule_strategy",
    "SBBStrategyBase": ".rule_strategy",
    "SBBStrategyEMA": ".rule_strategy",
    "SoftTopkStrategy": ".cost_control",
    "MAStrategy": ".ma_strategy",
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(_EXPORTS[name], package=__name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
