# Turtle Benchmark 示例实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `examples/benchmarks/Turtle/` 下新增一套与 MA 组织方式相近的海龟策略 benchmark 示例，包含配置文件、运行脚本和中文 README。

**Architecture:** 示例目录采用 benchmark 风格的“README + workflow_config + run 脚本”结构。`workflow_config_turtle.yaml` 保持与 MA benchmark 相似的外形，`run_turtle_strategy.py` 复用 MA 风格的初始化和执行流程，而海龟规则仍由 `TurtleStrategy` 在策略层负责。

**Tech Stack:** Python, YAML, Qlib benchmark workflow, pytest（仅在可行范围内做结构验证）

---

## File Structure

- Create: `examples/benchmarks/Turtle/README.md`
  Responsibility: 说明示例用途、运行方式、参数含义和环境限制。
- Create: `examples/benchmarks/Turtle/workflow_config_turtle.yaml`
  Responsibility: 提供与 benchmark 风格一致的 Qlib 初始化、task、strategy 和 backtest 配置。
- Create: `examples/benchmarks/Turtle/run_turtle_strategy.py`
  Responsibility: 初始化 Qlib、读取配置、实例化 model/dataset、挂接 `TurtleStrategy` 并执行回测。

## Task 1: 建立 Turtle benchmark 目录与 README

**Files:**
- Create: `examples/benchmarks/Turtle/README.md`

- [ ] **Step 1: 先写 README 内容草稿**

```markdown
# Turtle Benchmark 示例

## 简介
该示例提供一个与 MA benchmark 结构相近的海龟策略示例入口，目录包含配置文件、运行脚本和说明文档。

## 运行方式
```bash
python examples/benchmarks/Turtle/run_turtle_strategy.py
```

## 前置条件
- 已准备本地 Qlib 数据目录 `~/.qlib/qlib_data/cn_data`
- 本地环境能够完成 Qlib 初始化
- 若缺少编译扩展或运行依赖，需先补齐环境

## 关键参数
- `entry_window`
- `exit_window`
- `atr_window`
- `risk_pct`
- `max_units_per_instrument`
- `max_active_instruments`
- `risk_degree`

## 说明
该示例在 workflow 外形上参考 MA benchmark，但海龟策略本身是规则驱动，而不是预测驱动。
```

- [ ] **Step 2: 检查 README 文件当前不存在**

Run: `test ! -f examples/benchmarks/Turtle/README.md && echo missing`
Expected: 输出 `missing`

- [ ] **Step 3: 用最小内容创建 README**

```markdown
# Turtle Benchmark 示例

## 简介
该示例提供一个与 MA benchmark 结构相近的海龟策略 benchmark 入口，目录包含配置文件、运行脚本和说明文档。

## 运行方式
```bash
python examples/benchmarks/Turtle/run_turtle_strategy.py
```

## 前置条件
- 已准备本地 Qlib 数据目录 `~/.qlib/qlib_data/cn_data`
- 本地环境能够完成 Qlib 初始化
- 若缺少 Qlib 编译扩展或必要运行依赖，需要先修复环境

## 关键参数
- `entry_window`：入场突破窗口
- `exit_window`：离场突破窗口
- `atr_window`：ATR 计算窗口
- `risk_pct`：每次建仓的风险比例
- `max_units_per_instrument`：单标的最大加仓单位数
- `max_active_instruments`：组合内最大活跃标的数
- `risk_degree`：组合资金使用比例

## 说明与限制
该示例在 workflow 外形上参考 MA benchmark，但海龟策略本身是规则驱动，而不是预测驱动。
在当前本地环境中，如果缺少完整 Qlib 运行依赖或编译扩展，可能无法完成端到端回测。
```

- [ ] **Step 4: 检查 README 已创建且包含关键段落**

Run: `rg -n "运行方式|前置条件|关键参数|规则驱动" examples/benchmarks/Turtle/README.md`
Expected: 输出对应行号，证明 README 已包含运行方式、前置条件、参数说明和规则驱动说明。

- [ ] **Step 5: Commit**

```bash
git add examples/benchmarks/Turtle/README.md
git commit -m "docs(example): add turtle benchmark README"
```

## Task 2: 编写 benchmark 配置文件

**Files:**
- Create: `examples/benchmarks/Turtle/workflow_config_turtle.yaml`

- [ ] **Step 1: 先写配置内容草稿**

```yaml
qlib_init:
    provider_uri: "~/.qlib/qlib_data/cn_data"
    region: cn
market: &market csi300
benchmark: &benchmark SH000300
port_analysis_config:
    strategy:
        class: TurtleStrategy
        module_path: qlib.contrib.strategy
        kwargs:
            signal:
                - <MODEL>
                - <DATASET>
            entry_window: 20
            exit_window: 10
            atr_window: 14
            risk_pct: 0.01
            max_units_per_instrument: 4
            max_active_instruments: 10
            risk_degree: 0.95
```

- [ ] **Step 2: 检查配置文件当前不存在**

Run: `test ! -f examples/benchmarks/Turtle/workflow_config_turtle.yaml && echo missing`
Expected: 输出 `missing`

- [ ] **Step 3: 创建最小可读配置**

```yaml
qlib_init:
    provider_uri: "~/.qlib/qlib_data/cn_data"
    region: cn

market: &market csi300
benchmark: &benchmark SH000300

port_analysis_config: &port_analysis_config
    strategy:
        class: TurtleStrategy
        module_path: qlib.contrib.strategy
        kwargs:
            signal:
                - <MODEL>
                - <DATASET>
            entry_window: 20
            exit_window: 10
            atr_window: 14
            risk_pct: 0.01
            max_units_per_instrument: 4
            max_active_instruments: 10
            risk_degree: 0.95
    backtest:
        start_time: 2017-01-01
        end_time: 2020-08-01
        account: 100000000
        benchmark: *benchmark
        exchange_kwargs:
            limit_threshold: 0.095
            deal_price: close
            open_cost: 0.0005
            close_cost: 0.0015
            min_cost: 5

task:
    model:
        class: LinearModel
        module_path: qlib.contrib.model.linear
        kwargs:
            estimator: ols
    dataset:
        class: DatasetH
        module_path: qlib.data.dataset
        kwargs:
            handler:
                class: Alpha158
                module_path: qlib.contrib.data.handler
                kwargs:
                    start_time: 2008-01-01
                    end_time: 2020-08-01
                    fit_start_time: 2008-01-01
                    fit_end_time: 2014-12-31
                    instruments: *market
```

- [ ] **Step 4: 校验配置文件包含关键结构**

Run: `rg -n "qlib_init|port_analysis_config|TurtleStrategy|entry_window|task:" examples/benchmarks/Turtle/workflow_config_turtle.yaml`
Expected: 输出对应关键节点行号。

- [ ] **Step 5: Commit**

```bash
git add examples/benchmarks/Turtle/workflow_config_turtle.yaml
git commit -m "feat(example): add turtle benchmark workflow config"
```

## Task 3: 编写运行脚本

**Files:**
- Create: `examples/benchmarks/Turtle/run_turtle_strategy.py`

- [ ] **Step 1: 先写运行脚本骨架**

```python
import os
import yaml
import qlib

from qlib.constant import REG_CN
from qlib.tests.data import GetData
from qlib.utils import init_instance_by_config
from qlib.workflow import R
```

- [ ] **Step 2: 检查运行脚本当前不存在**

Run: `test ! -f examples/benchmarks/Turtle/run_turtle_strategy.py && echo missing`
Expected: 输出 `missing`

- [ ] **Step 3: 创建最小运行脚本**

```python
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Run Turtle strategy benchmark example.
"""

import os

import qlib
import yaml
from qlib.constant import REG_CN
from qlib.tests.data import GetData
from qlib.utils import init_instance_by_config
from qlib.workflow import R


if __name__ == "__main__":
    provider_uri = "~/.qlib/qlib_data/cn_data"
    GetData().qlib_data(target_dir=provider_uri, region=REG_CN, exists_skip=True)
    qlib.init(provider_uri=provider_uri, region=REG_CN)

    config_path = os.path.join(os.path.dirname(__file__), "workflow_config_turtle.yaml")
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    with R.start(experiment_name="Turtle_Strategy"):
        model = init_instance_by_config(config["task"]["model"])
        dataset = init_instance_by_config(config["task"]["dataset"])
        model.fit(dataset)

        from qlib.backtest import get_strategy_executor
        from qlib.backtest.backtest import backtest_loop

        strategy_config = config["port_analysis_config"]["strategy"]
        strategy_config["kwargs"]["signal"] = (model, dataset)

        executor_config = {
            "class": "SimulatorExecutor",
            "module_path": "qlib.backtest.executor",
            "kwargs": {
                "time_per_step": "day",
                "generate_portfolio_metrics": True,
            },
        }

        backtest_config = config["port_analysis_config"]["backtest"]
        strategy, executor = get_strategy_executor(
            start_time=backtest_config["start_time"],
            end_time=backtest_config["end_time"],
            strategy=strategy_config,
            executor=executor_config,
            benchmark=backtest_config["benchmark"],
            account=backtest_config["account"],
            exchange_kwargs=backtest_config["exchange_kwargs"],
        )

        portfolio_dict, indicator_dict = backtest_loop(
            start_time=backtest_config["start_time"],
            end_time=backtest_config["end_time"],
            trade_strategy=strategy,
            trade_executor=executor,
        )

        print("Portfolio analysis results:")
        for key, value in portfolio_dict.items():
            print(f"{key}:")
            print(value[0])

        print("\nIndicator analysis:")
        for key, value in indicator_dict.items():
            print(f"{key}:")
            print(value[0])
```

- [ ] **Step 4: 只做结构校验，不做端到端运行**

Run: `python3 -m py_compile examples/benchmarks/Turtle/run_turtle_strategy.py`
Expected: 命令成功，无语法错误输出。

- [ ] **Step 5: Commit**

```bash
git add examples/benchmarks/Turtle/run_turtle_strategy.py
git commit -m "feat(example): add turtle benchmark runner"
```

## Task 4: 对齐示例文档与配置语义

**Files:**
- Modify: `examples/benchmarks/Turtle/README.md`
- Modify: `examples/benchmarks/Turtle/workflow_config_turtle.yaml`
- Modify: `examples/benchmarks/Turtle/run_turtle_strategy.py`

- [ ] **Step 1: 写一个最小检查脚本，验证三文件术语一致**

```bash
rg -n "TurtleStrategy|entry_window|workflow_config_turtle.yaml|规则驱动" \
  examples/benchmarks/Turtle/README.md \
  examples/benchmarks/Turtle/workflow_config_turtle.yaml \
  examples/benchmarks/Turtle/run_turtle_strategy.py
```

- [ ] **Step 2: 运行检查并记录当前不一致项**

Run:

```bash
rg -n "TurtleStrategy|entry_window|workflow_config_turtle.yaml|规则驱动" \
  examples/benchmarks/Turtle/README.md \
  examples/benchmarks/Turtle/workflow_config_turtle.yaml \
  examples/benchmarks/Turtle/run_turtle_strategy.py
```

Expected: 三个文件都能命中至少一个关键字；若缺少，则在下一步补齐。

- [ ] **Step 3: 做最小修正，补齐缺失说明**

```markdown
README 中应出现：
- `workflow_config_turtle.yaml`
- `TurtleStrategy`
- “规则驱动”

YAML 中应出现：
- `TurtleStrategy`
- `entry_window`

运行脚本中应出现：
- `workflow_config_turtle.yaml`
- `Turtle_Strategy`
```

- [ ] **Step 4: 重新运行检查，确认一致**

Run:

```bash
rg -n "TurtleStrategy|entry_window|workflow_config_turtle.yaml|规则驱动" \
  examples/benchmarks/Turtle/README.md \
  examples/benchmarks/Turtle/workflow_config_turtle.yaml \
  examples/benchmarks/Turtle/run_turtle_strategy.py
```

Expected: 三个文件均能被匹配到相应关键字。

- [ ] **Step 5: Commit**

```bash
git add examples/benchmarks/Turtle/README.md examples/benchmarks/Turtle/workflow_config_turtle.yaml examples/benchmarks/Turtle/run_turtle_strategy.py
git commit -m "docs(example): align turtle benchmark example files"
```

## Task 5: 最终检查

**Files:**
- Modify: `examples/benchmarks/Turtle/README.md`
- Modify: `examples/benchmarks/Turtle/workflow_config_turtle.yaml`
- Modify: `examples/benchmarks/Turtle/run_turtle_strategy.py`

- [ ] **Step 1: 检查示例目录完整**

Run: `find examples/benchmarks/Turtle -maxdepth 1 -type f | sort`
Expected: 输出且只包含 `README.md`、`run_turtle_strategy.py`、`workflow_config_turtle.yaml`。

- [ ] **Step 2: 再做一次脚本语法检查**

Run: `python3 -m py_compile examples/benchmarks/Turtle/run_turtle_strategy.py`
Expected: 成功退出，无错误输出。

- [ ] **Step 3: 检查 YAML 可被读取**

Run:

```bash
python3 - <<'PY'
import yaml
from pathlib import Path
path = Path("examples/benchmarks/Turtle/workflow_config_turtle.yaml")
with path.open("r") as f:
    data = yaml.safe_load(f)
print(sorted(data.keys()))
PY
```

Expected: 输出包含 `benchmark`、`market`、`port_analysis_config`、`qlib_init`、`task`。

- [ ] **Step 4: 提交最终检查结果**

```bash
git add examples/benchmarks/Turtle/README.md examples/benchmarks/Turtle/workflow_config_turtle.yaml examples/benchmarks/Turtle/run_turtle_strategy.py
git commit -m "test(example): verify turtle benchmark example structure"
```

## Self-Review

- Spec coverage checked:
  - 新目录与三文件结构：Task 1, 2, 3
  - benchmark 风格配置：Task 2
  - MA 风格运行链路：Task 3
  - README 说明与限制：Task 1, 4
  - 结构级验证：Task 5
- Placeholder scan checked:
  - 没有保留 `TODO`、`TBD`、`implement later` 等占位内容
- Type consistency checked:
  - `TurtleStrategy`、`workflow_config_turtle.yaml`、`entry_window` 等命名在全部任务中保持一致
