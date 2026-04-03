# Turtle Benchmark Example Design

## Overview
This spec defines a new benchmark example for the Turtle strategy under `examples/benchmarks`, organized similarly to the existing MA example. The goal is to provide a configuration-driven, benchmark-style entry point that users can read and run with the same mental model as MA, while keeping the Turtle strategy logic inside the strategy layer instead of forcing it into a prediction model.

## Goals
- Add a Turtle benchmark example under `examples/benchmarks`.
- Match the overall usage pattern of the MA benchmark example.
- Provide a runnable layout consisting of a config file, a run script, and a README.
- Keep Turtle rule calculation in `TurtleStrategy`, not in the model output.

## Non-Goals
- Reorganizing the existing MA example directory.
- Adding multiple Turtle example variants in the first iteration.
- Rewriting Turtle logic to depend on predictive model scores.

## Directory Structure
Create a dedicated directory:

- `examples/benchmarks/Turtle/README.md`
- `examples/benchmarks/Turtle/run_turtle_strategy.py`
- `examples/benchmarks/Turtle/workflow_config_turtle.yaml`

The first version should stop here. Do not add extra `simple` or `direct` variants unless the initial example proves insufficient.

## Design Principles
- Follow the benchmark example shape already used by MA.
- Keep the public usage path simple: config + run script + README.
- Keep the strategy semantics honest: the Turtle example may instantiate a model and dataset for workflow compatibility, but the trading logic remains rule-driven.
- Avoid placing Turtle files under the MA directory. The similarity is structural, not thematic.

## Configuration Design
`workflow_config_turtle.yaml` should follow the MA benchmark style and include:

- `qlib_init`
- `market`
- `benchmark`
- `task`
- `port_analysis_config`

The configuration should preserve the `task.model` and `task.dataset` sections to stay compatible with the benchmark workflow shape. However, Turtle strategy execution should not rely on model scores as its trading signal source.

The strategy section should point to `TurtleStrategy` and provide explicit Turtle parameters, including:

- `entry_window`
- `exit_window`
- `atr_window`
- `risk_pct`
- `max_units_per_instrument`
- `max_active_instruments`
- `risk_degree`

## Runtime Flow
`run_turtle_strategy.py` should mirror the MA example flow closely:

1. Initialize Qlib with local benchmark data.
2. Load `workflow_config_turtle.yaml`.
3. Instantiate the configured model and dataset.
4. Run `model.fit(dataset)` for workflow compatibility.
5. Build the strategy config using `TurtleStrategy`.
6. Pass the instantiated model and dataset into the strategy config only as workflow-compatible context.
7. Run the backtest and print or record results.

The important boundary is that `TurtleStrategy` remains responsible for Donchian breakout, ATR, pyramiding, stop-loss, and portfolio constraints. The model is not responsible for producing Turtle trading decisions.

## README Requirements
`README.md` should explicitly cover:

- what this example is
- how it differs from a predictive benchmark
- how to run it
- required data location or initialization prerequisites
- the key Turtle parameters
- current limitations

The README must explicitly say that the example keeps the benchmark workflow shape of MA, but the Turtle strategy itself is rule-based rather than prediction-driven.

## Error Handling and User Expectations
The example should communicate failures clearly:

- If Qlib data is missing, instruct the user to prepare the local data directory first.
- If the local environment is missing compiled Qlib extensions or required runtime dependencies, make it clear that this is an environment issue, not a problem with the example structure.
- If `TurtleStrategy` still has integration limitations relative to full end-to-end backtesting, the README should state that the example reflects the current supported strategy integration path.

## Validation Scope
For this repository context, the first version of “runnable” is defined as:

- the example files are present and coherent
- the configuration structure matches benchmark conventions
- the run script follows the benchmark invocation pattern
- the Turtle parameters are wired consistently to `TurtleStrategy`

Given the current local environment constraints, the implementation should not assume that full end-to-end benchmark execution can be verified locally. The example should still be implemented so that it is structurally runnable in a complete Qlib environment.

## Acceptance Criteria
This design is considered implemented when:

- a new `examples/benchmarks/Turtle/` directory exists
- it contains `README.md`, `run_turtle_strategy.py`, and `workflow_config_turtle.yaml`
- the file organization is benchmark-style and analogous to MA
- the run path uses `TurtleStrategy`
- the documentation clearly explains the rule-driven nature of the example and its runtime prerequisites
