# wrist_roll モーター問題の解決策まとめ

## 問題の概要

SO-100 ロボットアームの wrist_roll モーターが、他のモーターを動かした際に不要な回転を起こす問題が発生していました。

## 実装した解決策

### 1. P 係数の低減

**ファイル**: `lerobot/common/robots/so100_follower/so100_follower.py`

**変更内容**:

```python
def configure(self) -> None:
    with self.bus.torque_disabled():
        self.bus.configure_motors()
        for motor in self.bus.motors:
            self.bus.write("Operating_Mode", motor, OperatingMode.POSITION.value)
            # Set P_Coefficient to lower value to avoid shakiness (Default is 32)
            if motor == "wrist_roll":
                # wrist_rollのP係数をさらに低く設定して応答性を下げる
                self.bus.write("P_Coefficient", motor, 4)  # 通常の1/4
            else:
                self.bus.write("P_Coefficient", motor, 16)
            # Set I_Coefficient and D_Coefficient to default value 0 and 32
            self.bus.write("I_Coefficient", motor, 0)
            self.bus.write("D_Coefficient", motor, 32)
```

**効果**: wrist_roll モーターの応答性を下げることで、不要な動きを抑制

### 2. デッドゾーンの実装

**ファイル**: `lerobot/teleoperate.py`

**変更内容**:

```python
def teleop_loop(...):
    while True:
        loop_start = time.perf_counter()
        action = teleop.get_action()

        # デッドゾーンの実装: wrist_rollの小さな変化を無視する
        wrist_roll_key = "wrist_roll.pos"
        if wrist_roll_key in action:
            # 値の絶対値が閾値（5.0）未満なら0に設定
            if abs(action[wrist_roll_key]) < 5.0:
                action[wrist_roll_key] = 0.0

        # 既存のコード...
```

**効果**: 小さな入力変化やノイズによる不要な動きを防止

### 3. 高度なフィルタリング機能

**新規ファイル**: `lerobot/teleoperate_filtered.py`

**主な機能**:

- **強力なデッドゾーン**: 閾値 20.0 で小さな変化を無視
- **移動平均フィルター**: 過去 10 フレームの平均値を使用して滑らかな動きを実現
- **gripper 連動フィルター**: gripper が動いているときは wrist_roll を固定
- **組み合わせモード**: 上記すべてのフィルターを同時適用

**使用方法**:

```bash
python -m lerobot.teleoperate_filtered \
    --robot.type=so100_follower \
    --robot.port=/dev/tty.usbserial-130 \
    --robot.id=blue \
    --teleop.type=so100_leader \
    --teleop.port=/dev/tty.usbserial-110 \
    --teleop.id=blue \
    --filter_type=combined
```

## 分析ツール

### 1. ロギング機能付きテレオペレーション

**新規ファイル**: `lerobot/teleoperate_logging.py`

**機能**:

- 全モーターの値を CSV ファイルに記録
- リアルタイムで wrist_roll と他のモーターの変化量を表示
- 問題の原因分析のためのデータ収集

### 2. ログデータ分析スクリプト

**新規ファイル**: `analysis/analyze_motor_logs.py`

**機能**:

- モーター間の相関係数計算
- 時系列プロットの生成
- 変化量の相関分析
- 視覚的なグラフと CSV ファイルの出力

### 3. 複数ログファイル比較分析

**新規ファイル**: `analysis/comparison_analysis.py`

**機能**:

- 複数のログファイル間での相関係数の変化を比較
- 統計情報の比較
- 問題パターンの一貫性を検証

## 分析結果

### 相関分析の結果

**1 回目のログ**:

- wrist_roll vs gripper: 0.370（最高相関）
- wrist_roll vs shoulder_lift: 0.125
- wrist_roll vs elbow_flex: 0.086

**2 回目のログ**:

- wrist_roll vs elbow_flex: 0.273（最高相関）
- wrist_roll vs gripper: 0.114
- wrist_roll vs shoulder_lift: -0.191

### 重要な発見

1. **最高相関モーターの変化**: gripper → elbow_flex
2. **相関の変化が大きいモーター**: shoulder_lift（分散 0.0498）
3. **変化量の相関**: すべて 0.05 未満で直接的な因果関係は弱い

## ファイル構成

```
lerobot/
├── teleoperate.py                    # デッドゾーン実装済み
├── teleoperate_logging.py            # ロギング機能付き（新規）
├── teleoperate_filtered.py           # 高度なフィルタリング（新規）
└── common/robots/so100_follower/
    └── so100_follower.py             # P係数低減済み

analysis/
├── analyze_motor_logs.py             # ログ分析スクリプト（新規）
├── comparison_analysis.py            # 比較分析スクリプト（新規）
└── results/                          # 分析結果（グラフ・CSV）

motor_logs/                           # ログファイル保存ディレクトリ
```

## 効果

- wrist_roll モーターの不要な動きが大幅に抑制された
- テレオペレーション時の操作性が向上
- データ分析により問題の根本原因を特定

## 今後の改善案

1. **elbow_flex 連動フィルター**: elbow_flex の動きに基づくフィルタリングの追加
2. **適応的パラメータ調整**: 使用状況に応じた自動パラメータ調整
3. **ハードウェア的な改善**: ケーブル配線やノイズ対策の検討

## 使用推奨

- 通常の使用: `teleoperate.py`（デッドゾーン実装済み）
- 問題が残る場合: `teleoperate_filtered.py`（高度なフィルタリング）
- データ収集が必要: `teleoperate_logging.py`（分析用ログ記録）
