# Turtle 示例回测结果记录设计

## 概述
本设计文档定义 Turtle benchmark 示例如何接入 Qlib 标准的回测结果记录体系，使用户能够通过 experiment / recorder 查看回测结果，而不是仅依赖脚本运行时在终端打印的数据。

当前 `examples/benchmarks/Turtle/run_turtle_strategy.py` 使用手写 `backtest_loop` 路径执行回测，并直接打印 `portfolio_dict` 和 `indicator_dict`。这种方式可以验证策略是否执行，但没有接入 Qlib 的标准 `record` 流程，因此不利于后续查看、复用和对齐 benchmark 示例习惯。

## 目标
- 让 Turtle benchmark 示例使用 Qlib 标准的结果记录流程。
- 让用户能够通过 experiment / recorder 查看回测分析结果。
- 让 Turtle benchmark 的运行结构更接近仓库中现有 benchmark 示例。
- 在 README 中明确说明如何查看回测结果。

## 非目标
- 不重写 Turtle 策略的交易逻辑。
- 不把 Turtle 策略改造成纯预测驱动策略。
- 不在第一版中扩展自定义导出文件格式。

## 现状问题
当前 Turtle 示例存在两个结构性问题：

1. 运行脚本只手动执行 `backtest_loop` 并打印结果，没有交给 Qlib 的 `record_temp` 体系管理。
2. `workflow_config_turtle.yaml` 没有 `record` 段，因此即使运行成功，也没有标准 recorder 产物可供后续查看。

## 设计原则
- 结果保存应由 Qlib 标准记录器负责，而不是脚本自行打印或另存自定义文件。
- Turtle example 应尽量对齐现有 benchmark 的配置风格，尤其是 `record` 段结构。
- 保持海龟策略本身仍然是规则驱动；接入 recorder 不意味着改变策略语义。

## 配置设计
`workflow_config_turtle.yaml` 应增加标准 `record` 段，结构参考现有 benchmark 配置，优先包含：

- `SignalRecord`
- `SigAnaRecord`
- `PortAnaRecord`

其中：

- `SignalRecord` 记录由 `<MODEL>` 和 `<DATASET>` 对应的信号相关产物；
- `SigAnaRecord` 用于补充信号分析；
- `PortAnaRecord` 使用 `*port_analysis_config` 生成并保存组合回测分析结果。

配置中 `record` 应显式引用：

- `<MODEL>`
- `<DATASET>`
- `*port_analysis_config`

## 运行流程设计
`run_turtle_strategy.py` 应从“手写回测并打印结果”调整为“训练 + 触发记录器”：

1. 初始化 Qlib。
2. 读取 `workflow_config_turtle.yaml`。
3. 启动 `R.start(experiment_name="Turtle_Strategy")`。
4. 实例化并训练 `model`。
5. 实例化 `dataset`。
6. 按配置中的 `record` 顺序执行记录器。
7. 在终端输出 experiment 名称和 recorder id，而不是只打印回测 DataFrame。

这里的职责边界是：

- 回测结果保存由 `SignalRecord` / `SigAnaRecord` / `PortAnaRecord` 负责；
- `run_turtle_strategy.py` 负责驱动这些记录器执行；
- 示例脚本不再自己承担结果持久化职责。

## README 设计
`examples/benchmarks/Turtle/README.md` 应新增“查看回测结果”说明，至少包含：

- 脚本运行后会在 `Turtle_Strategy` 实验下生成 recorder；
- 回测结果主要由 `PortAnaRecord` 记录；
- 用户可通过 experiment / recorder 查看结果；
- 如果当前环境不完整，可能会影响端到端记录生成。

README 不应只说明“怎么运行”，还应说明“运行后去哪里看结果”。

## 兼容风险
本设计的主要兼容风险有两类：

1. `TurtleStrategy` 与标准 `record` 流程的兼容性  
   现有 benchmark 主要面向预测驱动策略，部分记录器可能默认假设 `<MODEL>` / `<DATASET>` 生成的是典型预测信号。Turtle 示例虽然保留了 `model + dataset` 外壳，但其交易决策仍由规则策略驱动，因此实现时需要验证标准记录器是否能与当前策略路径正常协作。

2. 当前脚本路径与标准 benchmark workflow 的差异  
   这次改造的目的就是缩小这部分差异。第一版不要求完全复刻所有 benchmark 细节，但必须保证 recorder 会被真正执行，且用户能够按 Qlib 标准方式查看结果。

## 验证范围
第一版的验证范围应定义为：

- `workflow_config_turtle.yaml` 中存在可用的 `record` 段；
- `run_turtle_strategy.py` 会触发记录器执行；
- 终端输出包含 experiment / recorder 的关键信息；
- README 明确说明如何查看回测结果；
- 在当前本地环境允许的范围内，确认示例结构和调用路径正确。

若本地环境仍受依赖、扩展编译或其他运行条件影响，结构和调用路径的正确性优先于完整端到端回测的绝对通过。

## 验收标准
当满足以下条件时，可认为该设计已实现：

- Turtle 示例配置中新增 `record` 段；
- 运行脚本会触发 Qlib 标准记录器；
- 回测结果不再只停留在终端打印；
- README 清楚说明如何查看 recorder 结果；
- Turtle benchmark 示例在结构上更接近标准 benchmark workflow。
