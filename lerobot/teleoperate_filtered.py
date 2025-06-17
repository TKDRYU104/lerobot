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
Script to control a robot from teleoperation with advanced wrist_roll filtering.
This version implements multiple filtering techniques to prevent unwanted wrist_roll movement.

Example:

```shell
python -m lerobot.teleoperate_filtered \
    --robot.type=so100_follower \
    --robot.port=/dev/tty.usbserial-130 \
    --robot.id=blue \
    --teleop.type=so100_leader \
    --teleop.port=/dev/tty.usbserial-110 \
    --teleop.id=blue \
    --filter_type=combined
```
"""

import logging
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pprint import pformat
from typing import List

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


class FilterType(str, Enum):
    NONE = "none"  # フィルタリングなし
    DEADZONE = "deadzone"  # 強力なデッドゾーンのみ
    MOVING_AVERAGE = "moving_average"  # 移動平均フィルターのみ
    GRIPPER_LINKED = "gripper_linked"  # gripperが動いているときはwrist_rollを固定
    COMBINED = "combined"  # すべてのフィルターを組み合わせる


@dataclass
class TeleoperateFilteredConfig:
    teleop: TeleoperatorConfig
    robot: RobotConfig
    # Limit the maximum frames per second.
    fps: int = 60
    teleop_time_s: float | None = None
    # Display all cameras on screen
    display_data: bool = False
    # フィルタリングの種類
    filter_type: FilterType = FilterType.COMBINED
    # デッドゾーンの閾値
    deadzone_threshold: float = 20.0
    # 移動平均フィルターのウィンドウサイズ
    moving_average_window: int = 10
    # gripperの変化量の閾値
    gripper_change_threshold: float = 5.0


class WristRollFilter:
    """wrist_rollモーターの値をフィルタリングするクラス"""
    
    def __init__(self, config: TeleoperateFilteredConfig):
        self.config = config
        self.filter_type = config.filter_type
        self.deadzone_threshold = config.deadzone_threshold
        self.moving_average_window = config.moving_average_window
        self.gripper_change_threshold = config.gripper_change_threshold
        
        # 移動平均フィルター用の履歴
        self.wrist_roll_history: List[float] = []
        
        # gripper連動フィルター用の前回の値
        self.prev_gripper_value = None
        self.prev_wrist_roll_value = None
        
        print(f"フィルタータイプ: {self.filter_type}")
        if self.filter_type in [FilterType.DEADZONE, FilterType.COMBINED]:
            print(f"デッドゾーン閾値: {self.deadzone_threshold}")
        if self.filter_type in [FilterType.MOVING_AVERAGE, FilterType.COMBINED]:
            print(f"移動平均ウィンドウサイズ: {self.moving_average_window}")
        if self.filter_type in [FilterType.GRIPPER_LINKED, FilterType.COMBINED]:
            print(f"gripper変化量閾値: {self.gripper_change_threshold}")
    
    def apply_filter(self, action: dict[str, float]) -> dict[str, float]:
        """アクションにフィルターを適用する"""
        wrist_roll_key = "wrist_roll.pos"
        gripper_key = "gripper.pos"
        
        if wrist_roll_key not in action:
            return action
        
        # 元の値を保存
        original_value = action[wrist_roll_key]
        filtered_value = original_value
        
        # フィルタータイプに応じてフィルタリングを適用
        if self.filter_type == FilterType.NONE:
            return action
        
        # デッドゾーンフィルター
        if self.filter_type in [FilterType.DEADZONE, FilterType.COMBINED]:
            if abs(filtered_value) < self.deadzone_threshold:
                filtered_value = 0.0
        
        # 移動平均フィルター
        if self.filter_type in [FilterType.MOVING_AVERAGE, FilterType.COMBINED]:
            self.wrist_roll_history.append(filtered_value)
            if len(self.wrist_roll_history) > self.moving_average_window:
                self.wrist_roll_history.pop(0)
            
            filtered_value = sum(self.wrist_roll_history) / len(self.wrist_roll_history)
        
        # gripper連動フィルター
        if self.filter_type in [FilterType.GRIPPER_LINKED, FilterType.COMBINED] and gripper_key in action:
            current_gripper_value = action[gripper_key]
            
            if self.prev_gripper_value is not None and self.prev_wrist_roll_value is not None:
                gripper_change = abs(current_gripper_value - self.prev_gripper_value)
                
                # gripperが大きく動いている場合、wrist_rollの値を前回の値に固定
                if gripper_change > self.gripper_change_threshold:
                    filtered_value = self.prev_wrist_roll_value
                    print(f"gripper変化量: {gripper_change:.2f} > {self.gripper_change_threshold} → wrist_roll固定")
            
            # 現在の値を保存
            self.prev_gripper_value = current_gripper_value
        
        # フィルタリング後の値を保存
        self.prev_wrist_roll_value = filtered_value
        
        # フィルタリング後の値をアクションに設定
        action[wrist_roll_key] = filtered_value
        
        # フィルタリング前後の値を表示（デバッグ用）
        if abs(original_value - filtered_value) > 1.0:
            print(f"wrist_roll: {original_value:.2f} → {filtered_value:.2f}")
        
        return action


def teleop_loop(
    teleop: Teleoperator,
    robot: Robot,
    fps: int,
    wrist_roll_filter: WristRollFilter,
    display_data: bool = False,
    duration: float | None = None,
):
    display_len = max(len(key) for key in robot.action_features)
    start = time.perf_counter()
    
    while True:
        loop_start = time.perf_counter()
        action = teleop.get_action()
        
        # wrist_rollフィルターを適用
        action = wrist_roll_filter.apply_filter(action)
        
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
            return

        # フィルタリング情報の表示行数を考慮
        extra_lines = 1 if wrist_roll_filter.filter_type in [FilterType.GRIPPER_LINKED, FilterType.COMBINED] else 0
        move_cursor_up(len(action) + 5 + extra_lines)


@draccus.wrap()
def teleoperate_filtered(cfg: TeleoperateFilteredConfig):
    init_logging()
    logging.info(pformat(asdict(cfg)))
    if cfg.display_data:
        _init_rerun(session_name="teleoperation")

    teleop = make_teleoperator_from_config(cfg.teleop)
    robot = make_robot_from_config(cfg.robot)
    
    # wrist_rollフィルターを作成
    wrist_roll_filter = WristRollFilter(cfg)

    teleop.connect()
    robot.connect()

    try:
        teleop_loop(
            teleop,
            robot,
            cfg.fps,
            wrist_roll_filter,
            display_data=cfg.display_data,
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
    teleoperate_filtered()
