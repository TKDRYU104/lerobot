# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Script to control a robot from teleoperation with motor value logging.
This version logs all motor values to a CSV file for analysis.

Example:

```shell
python -m lerobot.teleoperate_logging \
    --robot.type=so100_follower \
    --robot.port=/dev/tty.usbserial-130 \
    --robot.id=blue \
    --teleop.type=so100_leader \
    --teleop.port=/dev/tty.usbserial-110 \
    --teleop.id=blue \
    --logging_enabled=true
```
"""

import csv
import logging
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pprint import pformat

import draccus
import numpy as np
import rerun as rr

from lerobot.common.cameras.opencv.configuration_opencv import OpenCVCameraConfig  # noqa: F401
from lerobot.common.cameras.realsense.configuration_realsense import RealSenseCameraConfig  # noqa: F401
from lerobot.common.robots import (  # noqa: F401
    Robot,
    RobotConfig,
    koch_follower,
    make_robot_from_config,
    so100_follower,
    so101_follower,
)
from lerobot.common.teleoperators import (
    Teleoperator,
    TeleoperatorConfig,
    make_teleoperator_from_config,
)
from lerobot.common.utils.robot_utils import busy_wait
from lerobot.common.utils.utils import init_logging, move_cursor_up
from lerobot.common.utils.visualization_utils import _init_rerun

from .common.teleoperators import gamepad, koch_leader, so100_leader, so101_leader  # noqa: F401


@dataclass
class TeleoperateLoggingConfig:
    teleop: TeleoperatorConfig
    robot: RobotConfig
    # Limit the maximum frames per second.
    fps: int = 60
    teleop_time_s: float | None = None
    # Display all cameras on screen
    display_data: bool = False
    # Enable motor value logging
    logging_enabled: bool = True
    # Directory to save log files
    log_dir: str = "motor_logs"


def teleop_loop(
    teleop: Teleoperator,
    robot: Robot,
    fps: int,
    display_data: bool = False,
    logging_enabled: bool = True,
    log_dir: str = "motor_logs",
    duration: float | None = None,
):
    display_len = max(len(key) for key in robot.action_features)
    start = time.perf_counter()
    
    # ロギングの設定
    csv_writer = None
    csv_file = None
    
    if logging_enabled:
        # ログディレクトリの作成
        os.makedirs(log_dir, exist_ok=True)
        
        # ログファイル名の設定
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = os.path.join(log_dir, f"motor_log_{timestamp}.csv")
        
        # CSVファイルの作成とヘッダーの書き込み
        csv_file = open(log_filename, 'w', newline='')
        fieldnames = ['timestamp', 'elapsed_time'] + list(robot.action_features.keys())
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        csv_writer.writeheader()
        
        print(f"モーター値のログを {log_filename} に記録しています...")
    
    # 前回の値を保存する辞書
    prev_action = None
    
    try:
        while True:
            loop_start = time.perf_counter()
            action = teleop.get_action()
            
            # デッドゾーンの実装: wrist_rollの小さな変化を無視する
            wrist_roll_key = "wrist_roll.pos"
            if wrist_roll_key in action:
                # 値の絶対値が閾値（5.0）未満なら0に設定
                if abs(action[wrist_roll_key]) < 5.0:
                    action[wrist_roll_key] = 0.0
            
            # ロギング
            if logging_enabled and csv_writer is not None:
                current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                elapsed_time = time.perf_counter() - start
                
                # ログデータの作成
                log_data = {
                    'timestamp': current_time,
                    'elapsed_time': f"{elapsed_time:.3f}"
                }
                
                # アクションデータの追加
                for key, value in action.items():
                    log_data[key] = value
                
                # 変化量の計算と表示（デバッグ用）
                if prev_action is not None and wrist_roll_key in action and wrist_roll_key in prev_action:
                    wrist_roll_change = action[wrist_roll_key] - prev_action[wrist_roll_key]
                    other_motors_change = 0
                    for key, value in action.items():
                        if key != wrist_roll_key and key in prev_action:
                            other_motors_change += abs(value - prev_action[key])
                    
                    print(f"wrist_roll変化量: {wrist_roll_change:.2f}, 他モーター変化量合計: {other_motors_change:.2f}")
                
                # CSVに書き込み
                csv_writer.writerow(log_data)
                
                # 現在の値を保存
                prev_action = action.copy()
            
            if display_data:
                observation = robot.get_observation()
                for obs, val in observation.items():
                    if isinstance(val, float):
                        rr.log(f"observation_{obs}", rr.Scalar(val))
                    elif isinstance(val, np.ndarray):
                        rr.log(f"observation_{obs}", rr.Image(val), static=True)
                for act, val in action.items():
                    if isinstance(val, float):
                        rr.log(f"action_{act}", rr.Scalar(val))

            robot.send_action(action)
            dt_s = time.perf_counter() - loop_start
            busy_wait(1 / fps - dt_s)

            loop_s = time.perf_counter() - loop_start

            print("\n" + "-" * (display_len + 10))
            print(f"{'NAME':<{display_len}} | {'NORM':>7}")
            for motor, value in action.items():
                print(f"{motor:<{display_len}} | {value:>7.2f}")
            print(f"\ntime: {loop_s * 1e3:.2f}ms ({1 / loop_s:.0f} Hz)")

            if duration is not None and time.perf_counter() - start >= duration:
                break

            move_cursor_up(len(action) + 5 + (2 if prev_action is not None else 0))  # 変化量表示の分も考慮
    finally:
        # CSVファイルを閉じる
        if logging_enabled and csv_file is not None:
            csv_file.close()
            print(f"ログファイルを保存しました: {log_filename}")


@draccus.wrap()
def teleoperate_logging(cfg: TeleoperateLoggingConfig):
    init_logging()
    logging.info(pformat(asdict(cfg)))
    if cfg.display_data:
        _init_rerun(session_name="teleoperation")

    teleop = make_teleoperator_from_config(cfg.teleop)
    robot = make_robot_from_config(cfg.robot)

    teleop.connect()
    robot.connect()

    try:
        teleop_loop(
            teleop,
            robot,
            cfg.fps,
            display_data=cfg.display_data,
            logging_enabled=cfg.logging_enabled,
            log_dir=cfg.log_dir,
            duration=cfg.teleop_time_s
        )
    except KeyboardInterrupt:
        pass
    finally:
        if cfg.display_data:
            rr.rerun_shutdown()
        teleop.disconnect()
        robot.disconnect()


if __name__ == "__main__":
    teleoperate_logging()
