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
テレオペレーションスクリプト（elbow_flex連動フィルター版）

このスクリプトは、elbow_flexの動きに連動してwrist_rollをフィルタリングし、
強い負の相関（-0.253）による不要な回転を防止します。

Example:

```shell
python -m lerobot.teleoperate_elbow_filter \
    --robot.type=so100_follower \
    --robot.port=/dev/tty.usbserial-130 \
    --robot.id=blue \
    --teleop.type=so100_leader \
    --teleop.port=/dev/tty.usbserial-110 \
    --teleop.id=blue \
    --elbow_threshold=2.0 \
    --wrist_deadzone=5.0
```
"""

import logging
import time
from dataclasses import asdict, dataclass
from pprint import pformat
from typing import Optional

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
class TeleoperateElbowFilterConfig:
    teleop: TeleoperatorConfig
    robot: RobotConfig
    # Limit the maximum frames per second.
    fps: int = 60
    teleop_time_s: float | None = None
    # Display all cameras on screen
    display_data: bool = False
    # elbow_flexの変化量閾値（この値を超えるとwrist_rollを固定）
    elbow_threshold: float = 2.0
    # wrist_rollのデッドゾーン閾値
    wrist_deadzone: float = 5.0
    # フィルタリングの強度（0.0-1.0、1.0が最強）
    filter_strength: float = 0.8
    # 適応的閾値を使用するかどうか
    adaptive_threshold: bool = True


class ElbowFlexFilter:
    """elbow_flexの動きに連動してwrist_rollをフィルタリングするクラス"""
    
    def __init__(self, config: TeleoperateElbowFilterConfig):
        self.config = config
        self.elbow_threshold = config.elbow_threshold
        self.wrist_deadzone = config.wrist_deadzone
        self.filter_strength = config.filter_strength
        self.adaptive_threshold = config.adaptive_threshold
        
        # 前回の値を保存
        self.prev_elbow_value: Optional[float] = None
        self.prev_wrist_value: Optional[float] = None
        
        # 適応的閾値用の統計
        self.elbow_changes_history = []
        self.max_history_size = 100
        
        # フィルタリング統計
        self.total_frames = 0
        self.filtered_frames = 0
        
        print("=== elbow_flex連動フィルター ===")
        print(f"elbow_flex閾値: {self.elbow_threshold}")
        print(f"wrist_rollデッドゾーン: {self.wrist_deadzone}")
        print(f"フィルター強度: {self.filter_strength}")
        print(f"適応的閾値: {self.adaptive_threshold}")
        print("=" * 40)
    
    def update_adaptive_threshold(self, elbow_change: float):
        """適応的閾値の更新"""
        if not self.adaptive_threshold:
            return
        
        self.elbow_changes_history.append(elbow_change)
        if len(self.elbow_changes_history) > self.max_history_size:
            self.elbow_changes_history.pop(0)
        
        # 過去の変化量の統計に基づいて閾値を調整
        if len(self.elbow_changes_history) >= 10:
            mean_change = np.mean(self.elbow_changes_history)
            std_change = np.std(self.elbow_changes_history)
            # 平均 + 1.5標準偏差を新しい閾値とする
            new_threshold = mean_change + 1.5 * std_change
            # 急激な変化を避けるため、徐々に調整
            self.elbow_threshold = 0.9 * self.elbow_threshold + 0.1 * new_threshold
    
    def apply_filter(self, action: dict[str, float]) -> dict[str, float]:
        """elbow_flex連動フィルターを適用"""
        elbow_key = "elbow_flex.pos"
        wrist_key = "wrist_roll.pos"
        
        if elbow_key not in action or wrist_key not in action:
            return action
        
        current_elbow = action[elbow_key]
        current_wrist = action[wrist_key]
        
        self.total_frames += 1
        
        # 初回は前回値を設定して終了
        if self.prev_elbow_value is None:
            self.prev_elbow_value = current_elbow
            self.prev_wrist_value = current_wrist
            return action
        
        # elbow_flexの変化量を計算
        elbow_change = abs(current_elbow - self.prev_elbow_value)
        
        # 適応的閾値の更新
        self.update_adaptive_threshold(elbow_change)
        
        # フィルタリングの判定
        should_filter = False
        filter_reason = ""
        
        # 1. elbow_flexの大きな変化をチェック
        if elbow_change > self.elbow_threshold:
            should_filter = True
            filter_reason = f"elbow変化量: {elbow_change:.2f} > {self.elbow_threshold:.2f}"
        
        # 2. wrist_rollのデッドゾーンをチェック
        elif abs(current_wrist) < self.wrist_deadzone:
            action[wrist_key] = 0.0
            filter_reason = f"デッドゾーン: |{current_wrist:.2f}| < {self.wrist_deadzone}"
        
        # フィルタリングを実行
        if should_filter:
            self.filtered_frames += 1
            
            # フィルター強度に応じて前回値との補間
            if self.prev_wrist_value is not None:
                filtered_wrist = (1.0 - self.filter_strength) * current_wrist + \
                               self.filter_strength * self.prev_wrist_value
            else:
                filtered_wrist = current_wrist
            
            action[wrist_key] = filtered_wrist
            
            print(f"フィルタリング適用: {current_wrist:.2f} → {filtered_wrist:.2f} ({filter_reason})")
        
        # 前回値を更新
        self.prev_elbow_value = current_elbow
        self.prev_wrist_value = action[wrist_key]
        
        return action
    
    def get_statistics(self) -> dict:
        """フィルタリング統計を取得"""
        if self.total_frames == 0:
            return {"filter_rate": 0.0, "total_frames": 0, "filtered_frames": 0}
        
        return {
            "filter_rate": self.filtered_frames / self.total_frames,
            "total_frames": self.total_frames,
            "filtered_frames": self.filtered_frames,
            "current_threshold": self.elbow_threshold
        }


def teleop_loop(
    teleop: Teleoperator, 
    robot: Robot, 
    fps: int, 
    elbow_filter: ElbowFlexFilter,
    display_data: bool = False, 
    duration: float | None = None
):
    display_len = max(len(key) for key in robot.action_features)
    start = time.perf_counter()
    
    while True:
        loop_start = time.perf_counter()
        action = teleop.get_action()
        
        # elbow_flex連動フィルターを適用
        action = elbow_filter.apply_filter(action)
        
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
        
        # フィルタリング統計を表示
        stats = elbow_filter.get_statistics()
        print(f"\ntime: {loop_s * 1e3:.2f}ms ({1 / loop_s:.0f} Hz)")
        print(f"filter: {stats['filtered_frames']}/{stats['total_frames']} ({stats['filter_rate']*100:.1f}%)")
        if elbow_filter.adaptive_threshold:
            print(f"threshold: {stats['current_threshold']:.2f}")

        if duration is not None and time.perf_counter() - start >= duration:
            return

        move_cursor_up(len(action) + 7)


@draccus.wrap()
def teleoperate_elbow_filter(cfg: TeleoperateElbowFilterConfig):
    init_logging()
    logging.info(pformat(asdict(cfg)))
    if cfg.display_data:
        _init_rerun(session_name="teleoperation_elbow_filter")

    teleop = make_teleoperator_from_config(cfg.teleop)
    robot = make_robot_from_config(cfg.robot)
    
    # elbow_flex連動フィルターを作成
    elbow_filter = ElbowFlexFilter(cfg)

    teleop.connect()
    robot.connect()

    try:
        teleop_loop(
            teleop, 
            robot, 
            cfg.fps, 
            elbow_filter,
            display_data=cfg.display_data, 
            duration=cfg.teleop_time_s
        )
    except KeyboardInterrupt:
        pass
    finally:
        # 最終統計を表示
        final_stats = elbow_filter.get_statistics()
        print(f"\n=== 最終統計 ===")
        print(f"総フレーム数: {final_stats['total_frames']}")
        print(f"フィルタリング回数: {final_stats['filtered_frames']}")
        print(f"フィルタリング率: {final_stats['filter_rate']*100:.1f}%")
        if elbow_filter.adaptive_threshold:
            print(f"最終閾値: {final_stats['current_threshold']:.2f}")
        
        if cfg.display_data:
            rr.rerun_shutdown()
        teleop.disconnect()
        robot.disconnect()


if __name__ == "__main__":
    teleoperate_elbow_filter()
