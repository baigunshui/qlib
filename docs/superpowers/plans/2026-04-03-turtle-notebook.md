# Turtle Notebook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a teaching-oriented `examples/notebook_pynb/workflow_config_turtle.ipynb` that independently defines and runs a complete Turtle workflow with recorder outputs.

**Architecture:** The implementation adds one standalone notebook plus one lightweight JSON-structure test. The notebook follows the existing `examples/notebook_pynb` pattern for setup and execution, but defines `task`, `record`, and `port_analysis_config` inline instead of loading the Turtle benchmark YAML.

**Tech Stack:** Python 3, Jupyter notebook JSON (`.ipynb`), pytest, Qlib workflow/record APIs

---

### Task 1: Create The Notebook Skeleton And Guard Test

**Files:**
- Create: `tests/misc/test_turtle_notebook.py`
- Create: `examples/notebook_pynb/workflow_config_turtle.ipynb`
- Test: `tests/misc/test_turtle_notebook.py`

- [ ] **Step 1: Write the failing structure test**

```python
import json
from pathlib import Path


NOTEBOOK_PATH = Path("examples/notebook_pynb/workflow_config_turtle.ipynb")


def _load_notebook():
    return json.loads(NOTEBOOK_PATH.read_text())


def _sources(notebook):
    return ["".join(cell.get("source", [])) for cell in notebook["cells"]]


def test_turtle_notebook_has_expected_sections_and_is_independent_from_benchmark_yaml():
    notebook = _load_notebook()
    sources = _sources(notebook)
    joined = "\n".join(sources)

    assert notebook["nbformat"] == 4
    assert NOTEBOOK_PATH.exists()
    assert "# workflow_config_turtle Notebook" in joined
    assert "# turtle strategy parameters" in joined
    assert "# run turtle workflow" in joined
    assert "# inspect recorder outputs" in joined
    assert "examples/benchmarks/Turtle/workflow_config_turtle.yaml" not in joined
    assert "TurtleStrategy" in joined
    assert "SignalRecord" in joined
    assert "SigAnaRecord" in joined
    assert "PortAnaRecord" in joined
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/misc/test_turtle_notebook.py -v`
Expected: FAIL with `FileNotFoundError` because `examples/notebook_pynb/workflow_config_turtle.ipynb` does not exist yet.

- [ ] **Step 3: Create the notebook with setup, parameter, config, run, and inspection cells**

```python
import json
from pathlib import Path


def lines(text):
    return [f"{line}\n" for line in text.strip("\n").splitlines()]


def markdown_cell(text):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": lines(text),
    }


def code_cell(text):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": lines(text),
    }


notebook = {
    "cells": [
        markdown_cell(
            """
            # workflow_config_turtle Notebook

            This notebook demonstrates a teaching-oriented Turtle workflow that defines the full task configuration in notebook cells.
            """
        ),
        code_cell(
            """
            # Copyright (c) Microsoft Corporation.
            # Licensed under the MIT License.
            """
        ),
        code_cell(
            """
            import sys, site
            from pathlib import Path

            ################################# NOTE #################################
            #  Please be aware that if colab installs the latest numpy and pyqlib  #
            #  in this cell, users should RESTART the runtime in order to run the  #
            #  following cells successfully.                                       #
            ########################################################################

            try:
                import qlib
            except ImportError:
                ! pip install --upgrade numpy
                ! pip install pyqlib
                if "google.colab" in sys.modules:
                    ! pip install pyyaml==5.4.1
            """
        ),
        code_cell(
            """
            import qlib
            import pandas as pd
            from qlib.constant import REG_CN
            from qlib.tests.data import GetData
            from qlib.utils import exists_qlib_data, flatten_dict, init_instance_by_config
            from qlib.workflow import R
            from qlib.workflow.record_temp import PortAnaRecord, SigAnaRecord, SignalRecord
            """
        ),
        code_cell(
            """
            provider_uri = "~/.qlib/qlib_data/cn_data"

            if not exists_qlib_data(provider_uri):
                print(f"Qlib data is not found in {provider_uri}")
                GetData().qlib_data(target_dir=provider_uri, region=REG_CN)

            qlib.init(provider_uri=provider_uri, region=REG_CN)
            """
        ),
        code_cell(
            """
            market = "csi300"
            benchmark = "SH000300"
            train_period = ("2008-01-01", "2014-12-31")
            valid_period = ("2015-01-01", "2016-12-31")
            test_period = ("2017-01-01", "2020-08-01")
            account = 100000000
            """
        ),
        markdown_cell(
            """
            # turtle strategy parameters

            - `entry_window`: breakout lookback for opening a new position.
            - `exit_window`: channel lookback for closing an existing position.
            - `atr_window`: ATR lookback used for position sizing and stop updates.
            - `risk_pct`: fraction of total capital allocated to each risk unit.
            - `max_units_per_instrument`: maximum pyramid units per instrument.
            - `max_active_instruments`: maximum simultaneous instruments in the portfolio.
            - `risk_degree`: overall capital usage cap for the backtest account.
            """
        ),
        code_cell(
            """
            turtle_kwargs = {
                "signal": "<PRED>",
                "entry_window": 20,
                "exit_window": 10,
                "atr_window": 14,
                "risk_pct": 0.01,
                "max_units_per_instrument": 4,
                "max_active_instruments": 10,
                "risk_degree": 0.95,
            }

            port_analysis_config = {
                "strategy": {
                    "class": "TurtleStrategy",
                    "module_path": "qlib.contrib.strategy",
                    "kwargs": turtle_kwargs,
                },
                "backtest": {
                    "start_time": test_period[0],
                    "end_time": test_period[1],
                    "account": account,
                    "benchmark": benchmark,
                    "exchange_kwargs": {
                        "limit_threshold": 0.095,
                        "deal_price": "close",
                        "open_cost": 0.0005,
                        "close_cost": 0.0015,
                        "min_cost": 5,
                    },
                },
            }

            task = {
                "model": {
                    "class": "LinearModel",
                    "module_path": "qlib.contrib.model.linear",
                    "kwargs": {"estimator": "ols"},
                },
                "dataset": {
                    "class": "DatasetH",
                    "module_path": "qlib.data.dataset",
                    "kwargs": {
                        "handler": {
                            "class": "Alpha158",
                            "module_path": "qlib.contrib.data.handler",
                            "kwargs": {
                                "start_time": train_period[0],
                                "end_time": test_period[1],
                                "fit_start_time": train_period[0],
                                "fit_end_time": train_period[1],
                                "instruments": market,
                            },
                        },
                        "segments": {
                            "train": train_period,
                            "valid": valid_period,
                            "test": test_period,
                        },
                    },
                },
            }

            task["record"] = [
                {"class": "SignalRecord", "kwargs": {"model": "<MODEL>", "dataset": "<DATASET>"}},
                {"class": "SigAnaRecord", "kwargs": {"ana_long_short": False, "ann_scaler": 252}},
                {"class": "PortAnaRecord", "kwargs": {"config": port_analysis_config}},
            ]
            """
        ),
        markdown_cell(
            """
            # run turtle workflow
            """
        ),
        code_cell(
            """
            recorder_id = None

            with R.start(experiment_name="Turtle_Strategy"):
                R.log_params(**flatten_dict(task))

                model = init_instance_by_config(task["model"])
                dataset = init_instance_by_config(task["dataset"])
                model.fit(dataset)

                recorder = R.get_recorder()
                SignalRecord(model, dataset, recorder).generate()
                SigAnaRecord(recorder, ana_long_short=False, ann_scaler=252).generate()
                PortAnaRecord(recorder, port_analysis_config, "day").generate()

                recorder_id = recorder.id
                print("Experiment: Turtle_Strategy")
                print(f"Recorder ID: {recorder_id}")
            """
        ),
        markdown_cell(
            """
            # inspect recorder outputs
            """
        ),
        code_cell(
            """
            recorder = R.get_recorder(recorder_id=recorder_id, experiment_name="Turtle_Strategy")
            print(recorder)

            pred_df = recorder.load_object("pred.pkl")
            report_normal_df = recorder.load_object("portfolio_analysis/report_normal_1day.pkl")
            positions = recorder.load_object("portfolio_analysis/positions_normal_1day.pkl")
            analysis_df = recorder.load_object("portfolio_analysis/port_analysis_1day.pkl")

            print(pred_df.head())
            print(report_normal_df.head())
            print(analysis_df.head())
            positions
            """
        ),
        markdown_cell(
            """
            # next experiments

            Try changing `entry_window`, `exit_window`, or `risk_pct`, then rerun the workflow cell to compare recorder outputs.
            """
        ),
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.8",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 4,
}


output_path = Path("examples/notebook_pynb/workflow_config_turtle.ipynb")
output_path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n")
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/misc/test_turtle_notebook.py -v`
Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit the skeleton and guard test**

```bash
git add tests/misc/test_turtle_notebook.py examples/notebook_pynb/workflow_config_turtle.ipynb
git commit -m "feat(example): add turtle notebook skeleton"
```

### Task 2: Strengthen Teaching Content And Result Inspection

**Files:**
- Modify: `tests/misc/test_turtle_notebook.py`
- Modify: `examples/notebook_pynb/workflow_config_turtle.ipynb`
- Test: `tests/misc/test_turtle_notebook.py`

- [ ] **Step 1: Extend the test to cover inline config details and resilient recorder inspection**

```python
import json
from pathlib import Path


NOTEBOOK_PATH = Path("examples/notebook_pynb/workflow_config_turtle.ipynb")


def _load_notebook():
    return json.loads(NOTEBOOK_PATH.read_text())


def _sources(notebook):
    return ["".join(cell.get("source", [])) for cell in notebook["cells"]]


def test_turtle_notebook_has_expected_sections_and_is_independent_from_benchmark_yaml():
    notebook = _load_notebook()
    sources = _sources(notebook)
    joined = "\n".join(sources)

    assert notebook["nbformat"] == 4
    assert NOTEBOOK_PATH.exists()
    assert "# workflow_config_turtle Notebook" in joined
    assert "# turtle strategy parameters" in joined
    assert "# run turtle workflow" in joined
    assert "# inspect recorder outputs" in joined
    assert "examples/benchmarks/Turtle/workflow_config_turtle.yaml" not in joined
    assert "TurtleStrategy" in joined
    assert "SignalRecord" in joined
    assert "SigAnaRecord" in joined
    assert "PortAnaRecord" in joined


def test_turtle_notebook_defines_workflow_inline_and_handles_missing_artifacts_gracefully():
    notebook = _load_notebook()
    joined = "\n".join(_sources(notebook))

    assert 'task = {' in joined
    assert '"class": "LinearModel"' in joined
    assert '"class": "DatasetH"' in joined
    assert '"class": "Alpha158"' in joined
    assert '"entry_window": 20' in joined
    assert '"exit_window": 10' in joined
    assert '"risk_pct": 0.01' in joined
    assert 'with R.start(experiment_name="Turtle_Strategy"):' in joined
    assert 'artifacts = [' in joined
    assert 'try:' in joined
    assert 'except Exception as exc:' in joined
    assert 'loaded_objects[artifact] = recorder.load_object(artifact)' in joined
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/misc/test_turtle_notebook.py -v`
Expected: FAIL in `test_turtle_notebook_defines_workflow_inline_and_handles_missing_artifacts_gracefully` because the notebook does not yet include resilient artifact loading.

- [ ] **Step 3: Update the notebook to add richer parameter guidance and safer artifact loading**

```python
import json
from pathlib import Path


path = Path("examples/notebook_pynb/workflow_config_turtle.ipynb")
notebook = json.loads(path.read_text())

notebook["cells"][6]["source"] = [
    "# turtle strategy parameters\n",
    "\n",
    "- `entry_window`: the breakout lookback used to open a new long position after a Donchian-channel breakout.\n",
    "- `exit_window`: the shorter exit channel used to close positions when price reverses.\n",
    "- `atr_window`: the ATR lookback used to size each unit and move the protective stop.\n",
    "- `risk_pct`: the fraction of portfolio value risked on each unit before pyramiding.\n",
    "- `max_units_per_instrument`: the maximum number of add-on units allowed for a single instrument.\n",
    "- `max_active_instruments`: the cap on simultaneously active instruments in the portfolio.\n",
    "- `risk_degree`: the overall portfolio capital usage cap applied by the backtest executor.\n",
    "\n",
    "Change these values one at a time so the recorder output stays easy to compare across runs.\n",
]

notebook["cells"][11]["source"] = [
    "recorder = R.get_recorder(recorder_id=recorder_id, experiment_name=\"Turtle_Strategy\")\n",
    "print(recorder)\n",
    "\n",
    "artifacts = [\n",
    "    \"pred.pkl\",\n",
    "    \"portfolio_analysis/report_normal_1day.pkl\",\n",
    "    \"portfolio_analysis/positions_normal_1day.pkl\",\n",
    "    \"portfolio_analysis/port_analysis_1day.pkl\",\n",
    "]\n",
    "\n",
    "loaded_objects = {}\n",
    "for artifact in artifacts:\n",
    "    try:\n",
    "        loaded_objects[artifact] = recorder.load_object(artifact)\n",
    "        print(f\"Loaded {artifact}\")\n",
    "    except Exception as exc:\n",
    "        print(f\"Unable to load {artifact}: {exc}\")\n",
    "\n",
    "if \"pred.pkl\" in loaded_objects:\n",
    "    print(loaded_objects[\"pred.pkl\"].head())\n",
    "\n",
    "if \"portfolio_analysis/report_normal_1day.pkl\" in loaded_objects:\n",
    "    print(loaded_objects[\"portfolio_analysis/report_normal_1day.pkl\"].head())\n",
    "\n",
    "if \"portfolio_analysis/port_analysis_1day.pkl\" in loaded_objects:\n",
    "    print(loaded_objects[\"portfolio_analysis/port_analysis_1day.pkl\"].head())\n",
    "\n",
    "loaded_objects.get(\"portfolio_analysis/positions_normal_1day.pkl\")\n",
]

path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n")
```

- [ ] **Step 4: Run the test and JSON validation to verify it passes**

Run: `pytest tests/misc/test_turtle_notebook.py -v`
Expected: PASS with `2 passed`.

Run: `python3 - <<'PY'\nimport json\nfrom pathlib import Path\npath = Path("examples/notebook_pynb/workflow_config_turtle.ipynb")\nnb = json.loads(path.read_text())\nprint(nb["nbformat"], len(nb["cells"]))\nprint("workflow_config_turtle.yaml" in "\\n".join("".join(c.get("source", [])) for c in nb["cells"]))\nPY`
Expected: first line prints `4` and the cell count, second line prints `False`.

- [ ] **Step 5: Commit the final notebook content**

```bash
git add tests/misc/test_turtle_notebook.py examples/notebook_pynb/workflow_config_turtle.ipynb
git commit -m "feat(example): add turtle notebook example"
```
