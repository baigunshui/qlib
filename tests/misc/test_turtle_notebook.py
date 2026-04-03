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
