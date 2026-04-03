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
