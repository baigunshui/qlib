# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Run Turtle strategy benchmark example.
"""

import os
from copy import deepcopy

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

        recorder = R.get_recorder()
        for record_config in config["task"]["record"]:
            record_config = deepcopy(record_config)
            kwargs = record_config.setdefault("kwargs", {})
            if kwargs.get("model") == "<MODEL>":
                kwargs["model"] = model
            if kwargs.get("dataset") == "<DATASET>":
                kwargs["dataset"] = dataset
            record = init_instance_by_config(
                record_config,
                recorder=recorder,
                default_module="qlib.workflow.record_temp",
            )
            record.generate()

        print("Experiment: Turtle_Strategy")
        print(f"Recorder ID: {recorder.id}")
