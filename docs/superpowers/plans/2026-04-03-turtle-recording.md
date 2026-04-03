# Turtle 回测结果记录实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `examples/benchmarks/Turtle/` 使用 Qlib 标准 `record` 流程保存回测结果，并让用户可以通过 experiment / recorder 查看 Turtle benchmark 的回测分析结果。

**Architecture:** 在 `workflow_config_turtle.yaml` 中增加标准 `record` 段，接入 `SignalRecord`、`SigAnaRecord`、`PortAnaRecord`。`run_turtle_strategy.py` 从“手写 backtest 并打印”调整为“训练 model + 执行 record_temp 记录器”，README 则补充如何查看 experiment / recorder 结果。

**Tech Stack:** Python, YAML, Qlib workflow recorder, Qlib benchmark example structure

---

## File Structure

- Modify: `examples/benchmarks/Turtle/workflow_config_turtle.yaml`
  Responsibility: 增加标准 `record` 段，并将 `<MODEL>`、`<DATASET>`、`*port_analysis_config` 接入记录器配置。
- Modify: `examples/benchmarks/Turtle/run_turtle_strategy.py`
  Responsibility: 改用 recorder 驱动流程，不再只执行 `backtest_loop + print`。
- Modify: `examples/benchmarks/Turtle/README.md`
  Responsibility: 增加“如何查看回测结果”的说明和推荐运行命令。

## Task 1: 为 Turtle 配置补齐标准 record 段

**Files:**
- Modify: `examples/benchmarks/Turtle/workflow_config_turtle.yaml`

- [ ] **Step 1: 写失败检查，确认当前配置还没有 `record` 段**

Run: `rg -n "^\\s*record:" examples/benchmarks/Turtle/workflow_config_turtle.yaml`
Expected: 无输出，退出码非 0，说明当前配置尚未接入 recorder。

- [ ] **Step 2: 对照可工作的 benchmark 配置**

Run: `sed -n '1,120p' examples/benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml`
Expected: 能看到 `record` 段中包含 `SignalRecord`、`SigAnaRecord`、`PortAnaRecord`。

- [ ] **Step 3: 在 Turtle 配置中增加最小可用 record 段**

```yaml
    record:
        - class: SignalRecord
          module_path: qlib.workflow.record_temp
          kwargs:
            model: <MODEL>
            dataset: <DATASET>
        - class: SigAnaRecord
          module_path: qlib.workflow.record_temp
          kwargs:
            ana_long_short: False
            ann_scaler: 252
        - class: PortAnaRecord
          module_path: qlib.workflow.record_temp
          kwargs:
            config: *port_analysis_config
```

- [ ] **Step 4: 运行检查，确认配置已接入 recorder**

Run: `rg -n "record:|SignalRecord|SigAnaRecord|PortAnaRecord" examples/benchmarks/Turtle/workflow_config_turtle.yaml`
Expected: 输出四类关键字对应的行号。

- [ ] **Step 5: Commit**

```bash
git add examples/benchmarks/Turtle/workflow_config_turtle.yaml
git commit -m "feat(example): add turtle recorder config"
```

## Task 2: 重构运行脚本为 record 驱动路径

**Files:**
- Modify: `examples/benchmarks/Turtle/run_turtle_strategy.py`

- [ ] **Step 1: 写失败检查，确认脚本当前仍在手动打印 backtest 结果**

Run: `rg -n "backtest_loop|portfolio_dict|indicator_dict|print\\(\"Portfolio analysis results" examples/benchmarks/Turtle/run_turtle_strategy.py`
Expected: 输出这些关键字所在行，说明脚本仍然走手写回测路径。

- [ ] **Step 2: 写最小目标骨架，明确后续结构**

```python
with R.start(experiment_name="Turtle_Strategy"):
    model = init_instance_by_config(config["task"]["model"])
    dataset = init_instance_by_config(config["task"]["dataset"])
    model.fit(dataset)

    recorder = R.get_recorder()
    for record_config in config["task"]["record"]:
        ...
```

- [ ] **Step 3: 将脚本改为训练 + 执行记录器**

```python
from copy import deepcopy

...
with R.start(experiment_name="Turtle_Strategy"):
    model = init_instance_by_config(config["task"]["model"])
    dataset = init_instance_by_config(config["task"]["dataset"])
    model.fit(dataset)

    recorder = R.get_recorder()
    for record_config in config["task"]["record"]:
        record_config = deepcopy(record_config)
        kwargs = record_config.setdefault("kwargs", {})
        if kwargs.get("model") == "<MODEL>":
            kwargs["model"] = model
        if kwargs.get("dataset") == "<DATASET>":
            kwargs["dataset"] = dataset
        if kwargs.get("config") == "<PORT_ANALYSIS_CONFIG>":
            kwargs["config"] = deepcopy(config["port_analysis_config"])
        record = init_instance_by_config(
            record_config,
            recorder=recorder,
            default_module="qlib.workflow.record_temp",
        )
        record.generate()

    print(f"Experiment: Turtle_Strategy")
    print(f"Recorder ID: {recorder.id}")
```

同时把 YAML 中 `PortAnaRecord` 的 `config` 保持为锚点引用 `*port_analysis_config`，脚本中不再手动调用 `backtest_loop`。

- [ ] **Step 4: 运行语法检查**

Run: `python3 -m py_compile examples/benchmarks/Turtle/run_turtle_strategy.py`
Expected: 成功退出，无语法错误。

- [ ] **Step 5: 运行结构检查，确认旧路径已移除**

Run: `rg -n "backtest_loop|portfolio_dict|indicator_dict|print\\(\"Portfolio analysis results" examples/benchmarks/Turtle/run_turtle_strategy.py`
Expected: 无输出，退出码非 0。

- [ ] **Step 6: Commit**

```bash
git add examples/benchmarks/Turtle/run_turtle_strategy.py
git commit -m "feat(example): switch turtle runner to recorder flow"
```

## Task 3: README 增加结果查看说明

**Files:**
- Modify: `examples/benchmarks/Turtle/README.md`

- [ ] **Step 1: 写失败检查，确认 README 目前没有“查看回测结果”段落**

Run: `rg -n "查看回测结果|Recorder ID|experiment|PortAnaRecord" examples/benchmarks/Turtle/README.md`
Expected: 无输出或仅零星命中，说明 README 还没有完整查看说明。

- [ ] **Step 2: 写最小新增内容**

```markdown
## 查看回测结果
脚本运行后会在 `Turtle_Strategy` 实验下生成 recorder。
回测分析结果由 `PortAnaRecord` 记录。
推荐关注脚本输出中的 recorder id，并通过 Qlib 的 experiment / recorder 接口查看结果。
```

- [ ] **Step 3: 将 README 运行命令和结果查看说明补齐**

```markdown
## 运行方式
```bash
PYTHONPATH=. python examples/benchmarks/Turtle/run_turtle_strategy.py
```

## 查看回测结果
脚本运行后会在 `Turtle_Strategy` 实验下生成 recorder。
回测结果主要由 `PortAnaRecord` 记录。
运行结束后可根据终端输出中的 `Recorder ID` 查看对应实验记录。
如果当前环境不完整，可能会影响端到端记录生成。
```

- [ ] **Step 4: 运行检查，确认 README 已包含新说明**

Run: `rg -n "查看回测结果|Recorder ID|PortAnaRecord|Turtle_Strategy" examples/benchmarks/Turtle/README.md`
Expected: 输出这些关键字对应的行号。

- [ ] **Step 5: Commit**

```bash
git add examples/benchmarks/Turtle/README.md
git commit -m "docs(example): add turtle recorder usage guide"
```

## Task 4: 运行级验证 recorder 路径

**Files:**
- Modify: `examples/benchmarks/Turtle/run_turtle_strategy.py`
- Modify: `examples/benchmarks/Turtle/workflow_config_turtle.yaml`
- Modify: `examples/benchmarks/Turtle/README.md`

- [ ] **Step 1: 实际运行脚本，确认至少进入 experiment / recorder 路径**

Run: `PYTHONPATH=. ./.venv/bin/python examples/benchmarks/Turtle/run_turtle_strategy.py`
Expected: 日志中出现 `Experiment ... starts running`，并在脚本结尾打印 `Recorder ID:`；如果运行环境不足导致端到端失败，也要记录精确报错位置。

- [ ] **Step 2: 如果运行失败，先记录失败点，不做多点并行修复**

```text
允许记录的失败示例：
- 缺少可选模型依赖
- recorder 与 TurtleStrategy 的接口不兼容
- 环境缺少特定运行依赖
```

本步骤要求先收集一条精确失败栈，而不是同时改多个地方。

- [ ] **Step 3: 做最小修正，只处理 record 接入相关问题**

```python
# 可接受修正范围示例：
# - 修正 record 配置引用的键名
# - 修正 init_instance_by_config 调用参数
# - 修正 recorder 输出位置
#
# 不接受：
# - 顺手重写 TurtleStrategy 逻辑
# - 改 unrelated benchmark
```

- [ ] **Step 4: 重新运行脚本，确认 recorder 路径可达**

Run: `PYTHONPATH=. ./.venv/bin/python examples/benchmarks/Turtle/run_turtle_strategy.py`
Expected: 至少看到 experiment / recorder 相关输出；若端到端完成，记录最终输出中的 recorder id。

- [ ] **Step 5: Commit**

```bash
git add examples/benchmarks/Turtle/run_turtle_strategy.py examples/benchmarks/Turtle/workflow_config_turtle.yaml examples/benchmarks/Turtle/README.md
git commit -m "test(example): verify turtle recorder workflow"
```

## Self-Review

- Spec coverage checked:
  - `record` 段补齐：Task 1
  - `run_turtle_strategy.py` 改为记录器驱动：Task 2
  - README 增加查看说明：Task 3
  - 运行级验证 recorder 路径：Task 4
- Placeholder scan checked:
  - 没有保留 `TODO`、`TBD`、`implement later` 等占位说明
- Type consistency checked:
  - `SignalRecord`、`SigAnaRecord`、`PortAnaRecord`、`Turtle_Strategy`、`Recorder ID` 命名在任务中保持一致
