# Turtle Benchmark 示例设计

## 概述
本设计文档定义一个新的海龟策略 benchmark 示例，放置于 `examples/benchmarks` 下，整体组织方式参考现有的 MA 示例。目标是提供一套配置驱动、结构清晰、便于阅读和后续运行的 benchmark 示例入口，同时保持海龟策略的核心交易逻辑仍然位于策略层，而不是被强行塞进预测模型输出中。

## 目标
- 在 `examples/benchmarks` 下新增海龟策略 benchmark 示例。
- 保持与 MA benchmark 示例相近的使用方式和目录组织。
- 提供一套由配置文件、运行脚本和 README 组成的完整示例结构。
- 保持海龟规则计算由 `TurtleStrategy` 负责，而不是由模型输出海龟交易信号。

## 非目标
- 不调整现有 MA 示例目录结构。
- 第一版不增加多个海龟示例变体。
- 不把海龟策略重写为依赖预测分数驱动的策略。

## 目录结构
新增一个独立目录：

- `examples/benchmarks/Turtle/README.md`
- `examples/benchmarks/Turtle/run_turtle_strategy.py`
- `examples/benchmarks/Turtle/workflow_config_turtle.yaml`

第一版到此为止，不额外增加 `simple`、`direct` 等变体；除非后续证明当前示例不足以支撑使用。

## 设计原则
- 目录结构和运行入口遵循 MA benchmark 的整体风格。
- 对外使用路径保持简单，即“配置文件 + 运行脚本 + README”。
- 保持语义清晰：海龟示例可以为了 workflow 兼容性实例化 model 和 dataset，但交易逻辑本身仍然是规则驱动。
- 不把海龟示例放进 MA 目录中。两者相似的是组织方式，不是策略主题。

## 配置设计
`workflow_config_turtle.yaml` 应保持与 MA benchmark 类似的结构，至少包含：

- `qlib_init`
- `market`
- `benchmark`
- `task`
- `port_analysis_config`

其中，配置仍保留 `task.model` 和 `task.dataset`，以保持与 benchmark workflow 外形一致；但海龟策略执行时不应依赖模型分数作为交易信号来源。

策略部分应指向 `TurtleStrategy`，并显式暴露海龟策略关键参数，包括：

- `entry_window`
- `exit_window`
- `atr_window`
- `risk_pct`
- `max_units_per_instrument`
- `max_active_instruments`
- `risk_degree`

## 运行链路
`run_turtle_strategy.py` 应尽量贴近 MA 示例的执行流程：

1. 初始化本地 Qlib 数据环境。
2. 加载 `workflow_config_turtle.yaml`。
3. 实例化配置中的 model 和 dataset。
4. 执行 `model.fit(dataset)`，用于保持 workflow 外形兼容。
5. 构造 `TurtleStrategy` 对应的策略配置。
6. 将实例化后的 model 和 dataset 作为 workflow 兼容上下文传入策略配置。
7. 执行 backtest，并打印或记录结果。

这里的关键边界是：

- `TurtleStrategy` 负责 Donchian 突破、ATR、加仓、止损和组合约束等海龟规则。
- model 不负责生成海龟交易决策。

## README 要求
`README.md` 至少应明确说明以下内容：

- 这个示例是什么
- 它与预测驱动 benchmark 的差异
- 如何运行
- 所需数据目录或初始化前置条件
- 海龟策略关键参数说明
- 当前限制

README 必须明确写出：该示例在 workflow 外形上参考 MA benchmark，但海龟策略本身是规则驱动，而不是预测驱动。

## 错误处理与用户预期
该示例应对常见失败情况给出清晰说明：

- 如果本地没有 Qlib 数据，应提示用户先准备本地数据目录。
- 如果本地环境缺少 Qlib 编译扩展或必要运行依赖，应明确说明这是环境问题，而不是示例结构问题。
- 如果 `TurtleStrategy` 当前与完整端到端回测仍存在集成限制，README 应明确写明该示例反映的是当前支持的策略集成路径。

## 验证范围
在当前仓库上下文中，第一版“可运行”的定义是：

- 示例文件完整且彼此一致；
- 配置结构符合 benchmark 约定；
- 运行脚本遵循 benchmark 示例调用方式；
- 海龟参数能够一致地传递给 `TurtleStrategy`。

考虑到当前本地环境限制，实现时不应假设可以在本地完整验证端到端 benchmark 执行；但示例本身仍应按照完整 Qlib 环境下可运行的结构来设计和实现。

## 验收标准
当满足以下条件时，可认为该设计已实现：

- 存在新的 `examples/benchmarks/Turtle/` 目录；
- 目录中包含 `README.md`、`run_turtle_strategy.py` 和 `workflow_config_turtle.yaml`；
- 文件组织方式为 benchmark 风格，并与 MA 示例在结构上保持类比；
- 运行路径使用 `TurtleStrategy`；
- 文档明确说明该示例是规则驱动，并写清运行前提与限制。
