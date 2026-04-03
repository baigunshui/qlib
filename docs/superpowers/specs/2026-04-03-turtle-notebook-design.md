# Turtle Notebook 示例设计

## 概述
本设计文档定义一个新的海龟策略 notebook 示例，放置于 `examples/notebook_pynb/workflow_config_turtle.ipynb`。该示例参考现有 `examples/notebook_pynb` 下 notebook 的整体组织方式，但定位为教学导向的完整 workflow 示例：读者可以在一个 notebook 中完成环境准备、任务配置、策略参数理解、实验运行以及 recorder 结果查看，而不需要依赖 `examples/benchmarks/Turtle/workflow_config_turtle.yaml`。

## 目标
- 在 `examples/notebook_pynb` 下新增独立的 `workflow_config_turtle.ipynb`。
- 示例内容应采用 notebook 风格组织，兼顾可运行性与教学性。
- notebook 独立定义 Turtle workflow 所需配置，不依赖现有 benchmark YAML。
- notebook 应形成完整 Qlib workflow，包括 `qlib.init`、模型训练、record 生成和 recorder 结果查看。
- notebook 应明确解释 Turtle 关键参数与回测流程的关系。

## 非目标
- 不重构现有 `examples/benchmarks/Turtle` 目录。
- 不新增第二套 Turtle YAML 配置文件。
- 不在 notebook 中重写 `TurtleStrategy` 的内部算法实现。
- 不把 notebook 做成仅展示策略逻辑、但缺少标准 Qlib recorder 的半成品示例。

## 文件与命名
新增文件：

- `examples/notebook_pynb/workflow_config_turtle.ipynb`

命名遵循现有 `examples/notebook_pynb/workflow_config_*.ipynb` 风格，便于用户在同一目录下按模型或策略主题查找示例。

## 设计原则
- 对齐现有 notebook 示例的使用习惯：一个文件内既包含说明，也包含可执行代码。
- 以教学为优先，关键配置和关键参数应在 notebook 中显式展开，而不是隐藏在外部 YAML 中。
- 保持 workflow 完整，避免只演示局部策略逻辑。
- 与现有 Turtle benchmark 在核心命名上保持一致，例如 `TurtleStrategy`、`entry_window`、`exit_window` 等，降低迁移成本。
- 说明范围聚焦于“如何在 Qlib workflow 中使用 Turtle 策略”，不扩展为策略源码解析文档。

## Notebook 结构
notebook 建议按以下章节组织：

1. 标题与目标
   说明这是一个 Turtle strategy 的教学型 workflow notebook，展示从初始化到 recorder 查看的完整流程。

2. 环境准备
   导入依赖、处理 notebook 路径、检查本地 Qlib 数据、执行 `qlib.init(...)`。

3. 基础实验设置
   显式定义市场、benchmark、时间区间、账户资金等基础参数。

4. Turtle 策略参数说明
   通过 markdown 解释海龟策略关键参数的含义和作用范围。

5. 构建任务配置
   在 notebook 中直接定义 `model`、`dataset`、`record` 和 `port_analysis_config`。

6. 运行实验并生成 recorder
   使用 `R.start(...)` 执行 `model.fit(dataset)`，再生成 `SignalRecord`、`SigAnaRecord` 和 `PortAnaRecord`。

7. 查看结果
   展示 experiment 名、recorder id，并给出读取结果或指标的示例。

8. 可调参数建议
   简要指出哪些参数适合继续调整和扩展实验。

## 配置与数据流设计
notebook 内应直接定义完整 `task_config`，而不是从 `examples/benchmarks/Turtle/workflow_config_turtle.yaml` 读取。该配置至少包括：

- `model`
- `dataset`
- `record`
- `port_analysis_config`

其中：

- `model` 继续使用简单、稳定的基础模型以产出 workflow 所需的预测分数，优先选择与现有 Turtle benchmark 一致的 `LinearModel`。
- `dataset` 在 notebook 内展开 `DatasetH + Alpha158` 的配置，使读者可以直接看到训练和测试区间。
- `record` 显式列出 `SignalRecord`、`SigAnaRecord`、`PortAnaRecord`，保持与其他 benchmark notebook 一致的 recorder 结构。
- `port_analysis_config.strategy` 使用 `qlib.contrib.strategy.TurtleStrategy`，并在 `kwargs` 中直接配置 Turtle 关键参数。

数据流建议保持为：

1. 检查并初始化本地 Qlib 数据环境。
2. 定义实验基础参数与 `task_config`。
3. 实例化 `model` 与 `dataset`。
4. 执行 `model.fit(dataset)`。
5. 依次生成 `SignalRecord`、`SigAnaRecord`、`PortAnaRecord`。
6. 输出并读取 recorder 结果。

关键边界如下：

- notebook 的教学重点是展示 Turtle 策略如何接入 Qlib workflow。
- `TurtleStrategy` 负责海龟规则相关的仓位管理和交易逻辑。
- notebook 解释策略参数，但不复制或改写 `TurtleStrategy` 内部实现。

## Turtle 参数说明要求
notebook 应显式解释以下参数：

- `entry_window`
- `exit_window`
- `atr_window`
- `risk_pct`
- `max_units_per_instrument`
- `max_active_instruments`
- `risk_degree`

说明重点应是这些参数对策略行为和组合约束的影响，而不是泛泛罗列名称。解释应放在独立 markdown 单元中，方便读者先理解参数，再运行代码。

## 错误处理与用户预期
notebook 应对以下常见失败场景给出清晰、可执行的提示：

- 如果本地 `~/.qlib/qlib_data/cn_data` 不存在或不完整，应提示用户先准备数据，或按现有 notebook 方式给出下载指引。
- 如果运行环境缺少必要依赖或 Qlib 编译扩展，应在 notebook 顶部保留与现有 notebook 风格一致的安装或重启说明。
- 如果实验完成但部分分析产物未生成，notebook 至少应展示 experiment 名、recorder id 和可读取的基础结果，而不是假设所有 artifact 都必然存在。

用户预期应明确为：

- 这是一个教学导向的完整 workflow notebook；
- 它可以独立阅读和执行；
- 它不是 Turtle benchmark YAML 的 notebook 封装层；
- 它展示的是标准 Qlib 实验流程中的 Turtle 用法，而不是纯策略源码教程。

## 验证范围
第一版实现的验证重点如下：

- notebook 文件位于 `examples/notebook_pynb/`，命名符合现有风格；
- notebook 同时包含 markdown 说明与可执行代码；
- notebook 不依赖 `examples/benchmarks/Turtle/workflow_config_turtle.yaml`；
- notebook 可以按完整 workflow 组织 `qlib.init`、训练、record 生成和结果查看；
- notebook 清晰解释 Turtle 参数和实验步骤之间的关系。

实现阶段不要求在设计文档中承诺额外的衍生文档、配套 YAML 或目录重构。

## 验收标准
当满足以下条件时，可认为该设计已实现：

- 新增 `examples/notebook_pynb/workflow_config_turtle.ipynb`；
- notebook 结构清晰，包含标题说明、环境准备、参数说明、配置定义、实验运行和结果查看；
- notebook 中的 workflow 配置独立定义，不读取 `examples/benchmarks/Turtle/workflow_config_turtle.yaml`；
- notebook 能产出标准 Qlib recorder 结果；
- notebook 对 Turtle 关键参数的含义和作用给出明确说明；
- 该示例整体风格与 `examples/notebook_pynb` 现有 notebook 保持一致，同时具备更强的教学导向。
