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
