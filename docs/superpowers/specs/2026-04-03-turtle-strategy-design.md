# Turtle Strategy Design

## Overview
This spec defines a Qlib-based Turtle Trading implementation that is validated primarily through unit tests rather than end-to-end execution. The target is a multi-instrument portfolio strategy. Each instrument follows the standard Turtle rule set independently, while portfolio-level constraints control capital usage and active positions.

The design separates core trading rules from Qlib integration so the algorithm can be verified in a local environment where the full runtime stack is unavailable.

## Goals
- Implement a standard Turtle strategy with entry, exit, ATR-based risk units, pyramiding, and stop-loss.
- Support multiple instruments in one portfolio.
- Make the core logic testable with pure unit tests and mocked strategy integration tests.
- Keep the Qlib-facing layer thin and consistent with existing `qlib.contrib.strategy` patterns.

## Non-Goals
- Running the full backtest workflow locally.
- Building a UI, notebook workflow, or example script in the first iteration.
- Supporting short selling in the first version.

## Architecture
The implementation is split into three layers.

### TurtleRuleEngine
A pure-Python rule engine that receives market history for multiple instruments and the current portfolio state. It computes the next target state per instrument and emits semantic actions such as open, add, hold, exit, or stop.

### TurtlePortfolioState
A state container that tracks each instrument independently. Each instrument state includes at least:
- current units
- entry price
- last add price
- stop price
- latest ATR (`N`)
- pending or derived target units

This layer does not depend on Qlib backtest classes and is designed to be instantiated directly in tests.

### TurtleStrategy
A thin Qlib adapter placed under `qlib.contrib.strategy`. It gathers the historical window for the current trading step, calls `TurtleRuleEngine`, compares the rule output with current holdings, and converts the result into Qlib `Order` and `TradeDecisionWO` objects.

## Trading Rules
The first version uses one explicit rule set to avoid ambiguity.

- Entry: open a long position when price breaks above the Donchian upper channel over `entry_window`.
- Exit: close the entire position when price breaks below the Donchian lower channel over `exit_window`.
- ATR: compute `N` using `atr_window`.
- Unit size: `floor((portfolio_value * risk_pct) / N / contract_scale)`, then round by trade unit where needed.
- Pyramiding: add one unit each time price advances by `0.5 * N`, capped by `max_units_per_instrument`.
- Stop-loss: liquidate the position when price falls `2 * N` below the relevant reference entry or add price.
- Portfolio constraints: enforce `max_active_instruments`; reject new entries or adds when cash is insufficient.

Within a single trading step, action priority is fixed as:
1. stop-loss or channel exit
2. pyramiding
3. new entry

## Data Contract
The core rule layer accepts a multi-instrument DataFrame indexed by `(datetime, instrument)`. Required fields are:
- `close`
- `high`
- `low`

The first implementation should compute Donchian channels and ATR internally. This keeps the interface stable for tests and avoids coupling the rule engine to external precomputed signal columns.

## Qlib Integration Boundary
`TurtleStrategy` should remain a thin adapter.

- It fetches the required history window from Qlib for the current step.
- It transforms the data into the rule-engine input format.
- It uses the rule output to build Qlib buy and sell orders.
- It applies exchange rounding and tradability checks at the integration boundary.

The strategy should not own core Turtle rule calculations beyond orchestration and translation.

## Error Handling
To keep failure modes explicit:

- If the historical window is insufficient, the instrument is skipped for that step.
- If ATR is zero or NaN, the instrument is skipped.
- If required price fields are missing, raise a clear exception instead of silently continuing.
- If rounded trade size becomes zero or cash is insufficient, no order is generated and state remains unchanged.
- If exit and add conditions are both true in the same step, exit wins.

## Test Strategy
Testing is centered on unit tests, not full workflow execution.

### Rule Unit Tests
Use pure tests to validate:
- Donchian channel calculation
- ATR calculation
- breakout entry
- `0.5N` pyramiding
- `2N` stop-loss
- channel exit
- multi-instrument capital allocation
- `max_active_instruments` enforcement
- same-step priority resolution

### State Transition Tests
Construct `TurtlePortfolioState` directly and verify state transitions for one step at a time. Confirm updates to:
- units
- last add price
- stop price
- per-instrument action

### Thin Integration Tests
Use mocks or lightweight stubs to verify that `TurtleStrategy` converts rule-engine output into Qlib decision objects. Do not rely on a full local backtest runtime.

## File Layout
Planned files:

- `qlib/contrib/strategy/turtle_strategy.py`
- `qlib/contrib/strategy/__init__.py`
- `tests/backtest/test_turtle_strategy.py`

## Implementation Constraints
- Follow existing `qlib.contrib.strategy` module style.
- Keep the rule engine and state objects small and independently testable.
- Avoid introducing unrelated refactors in strategy or backtest modules.
- Prefer deterministic tests with hand-crafted price series over fixture-heavy setup.

## Acceptance Criteria
The design is considered implemented when:

- the Turtle strategy supports multiple instruments
- standard Turtle entry, exit, ATR unit sizing, pyramiding, and stop-loss rules are covered by tests
- the core algorithm is validated by unit tests without requiring full local workflow execution
- Qlib integration remains limited to a thin translation layer
