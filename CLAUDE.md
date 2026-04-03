# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Qlib 是一个面向 AI 的量化投资平台，支持数据准备、模型训练、回测和在线部署等功能。项目采用模块化设计，各组件可独立使用或组合使用。

## 构建和开发命令

### 初始安装
```bash
make install           # 编译 Cython 扩展并安装包
make dev              # 安装完整开发环境（包含 lint、docs、test、rl 等依赖）
```

### 测试
```bash
pytest tests                      # 运行默认测试套件
pytest tests -m "not slow"        # 跳过标记为 slow 的测试
pytest tests/backtest/            # 运行特定模块的测试
pytest tests/path/to/test_file.py # 运行单个测试文件
```

### 代码检查
```bash
make lint          # 运行所有 lint 检查（black、pylint、flake8、mypy、nbqa）
make black         # 仅运行 black 检查
make pylint        # 仅运行 pylint 检查
make flake8       # 仅运行 flake8 检查
make mypy         # 仅运行 mypy 类型检查
```

### 文档
```bash
make docs-gen     # 构建 Sphinx 文档到 public/ 目录
```

### 常用工作流
```bash
qrun examples/benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml  # 运行工作流
python -m qlib.cli.data qlib_data --target_dir ~/.qlib/qlib_data/cn_data --region cn  # 获取数据
```

## 代码架构

### 核心模块

**qlib/data/** - 数据层
- `data.py`: 核心数据接口 `D`，提供数据查询功能
- `ops.py`: 特征操作和计算表达式引擎
- `cache.py`: 内存和磁盘缓存管理
- `storage/`: 底层存储实现
- `dataset/`: 数据集构建工具
- `_libs/`: Cython 扩展模块（rolling, expanding）用于高性能计算

**qlib/model/** - 模型层
- `trainer.py`: 模型训练器
- `base.py`: 模型基类接口
- `ens/`: 模型集成相关
- `interpret/`: 模型解释工具
- `meta/`: 元学习相关

**qlib/backtest/** - 回测引擎
- `executor.py`: 交易执行器
- `exchange.py`: 交易所模拟
- `account.py`: 账户管理
- `position.py`: 持仓管理
- `decision.py`: 交易决策
- `report.py`: 回测报告生成
- `signal.py`: 信号处理

**qlib/strategy/** - 策略层
- `base.py`: 策略基类
- 策略使用信号生成交易决策，由 executor 执行

**qlib/workflow/** - 工作流管理
- `__init__.py`: 主要工作流类 `R`
- `recorder.py`: 实验记录器，用于保存和恢复实验
- `exp.py`, `expm.py`: 实验管理
- `online/`: 在线服务相关工作流

**qlib/rl/** - 强化学习
- `trainer.py`: RL 训练器
- `simulator.py`: 环境模拟器
- `reward.py`: 奖励函数
- `interpreter.py`: 解释器
- `order_execution/`: 订单执行相关 RL 策略
- `strategy/`: RL 策略实现

**qlib/contrib/** - 贡献扩展
- `workflow/`: 工作流扩展
- `model/`: 模型扩展（如各种基准模型）
- `data/`: 数据处理扩展
- `strategy/`: 策略扩展
- `ops/`: 操作扩展
- `eva/`: 评估工具
- `report/`: 报告工具

### 关键设计原则

1. **模块化**: 各组件可独立使用，例如 `qlib.data.D` 可单独使用进行数据查询
2. **表达式引擎**: 使用类似 SQL 的表达式语法定义特征，如 `Ref($close, 1)` 或 `Mean($close, 3)`
3. **工作流驱动**: 通过 YAML 配置文件或代码方式定义完整的研究流程
4. **性能优化**: 使用 Cython 扩展进行高性能计算，支持多层缓存
5. **多种学习范式**: 支持监督学习和强化学习

## 代码规范

### 命名约定
- 函数/模块: `snake_case`
- 类: `PascalCase`
- 常量: `UPPER_CASE`
- 缩进: 4 空格

### 格式化
- 代码格式: `black -l 120`
- 文档字符串: Numpydoc 风格
- 类型注解: 使用 `mypy` 检查（排除 contrib、data、model 等目录）

### 提交信息
遵循 Conventional Commits 格式：
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `refactor`: 重构
- `test`: 测试相关
- `ci`: CI/CD 相关

示例：`fix(backtest): avoid calendar overflow when end_time is missing`

## 测试指南

### 测试文件组织
- 测试文件命名: `test_*.py`
- 测试目录结构: `tests/` 镜像主包结构
  - `tests/backtest/`: 回测模块测试
  - `tests/model/`: 模型测试
  - `tests/rl/`: RL 测试（仅在 Linux 上运行）
  - `tests/dataset_tests/`: 数据集测试
  - `tests/ops/`: 操作测试

### 测试标记
- `slow`: 慢速测试，使用 `pytest -m "not slow"` 跳过
- 非 Linux 平台自动跳过 RL 测试

## Cython 扩展

项目包含两个 Cython 扩展模块：
- `qlib/data/_libs/rolling`: 滚动窗口计算
- `qlib/data/_libs/expanding`: 扩展窗口计算

这些扩展在首次安装时编译，需要 Cython 和 numpy 开发头文件。如果 `.so` 文件不存在，`make install` 会自动编译。

## 配置和初始化

### Qlib 初始化
```python
import qlib
qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region="cn")
```

### 常用配置
- 数据源路径: 通过 `mount_path` 或 `provider_uri` 指定
- 区域: `REG_CN` (中国) 或 `REG_US` (美国)
- 模式: 离线模式（默认）或在线模式

## 工作流运行

### 使用 qrun
```bash
qrun examples/benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml
```

### 使用代码
参考 `examples/workflow_by_code.py` 或 `examples/workflow_by_code.ipynb`

### 调试模式
```bash
python -m pdb qlib/cli/run.py <workflow_config>
```

## 注意事项

1. **Python 版本**: 支持 Python 3.8-3.12
2. **数据准备**: 使用 `python -m qlib.cli.data` 或 `scripts/get_data.py` 准备数据
3. **类型检查**: mypy 排除了大部分核心模块，类型检查主要用于新代码
4. **RL 支持**: RL 功能仅在 Linux 上完全支持
5. **Cython 重新编译**: 修改 `.pyx` 文件后需要删除 `.so` 文件并重新编译
