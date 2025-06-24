# 新しいログデータ収集セッション

## 実行コマンド

以下のコマンドでロギング機能付きテレオペレーションを実行してください：

```bash
python -m lerobot.teleoperate_logging \
    --robot.type=so100_follower \
    --robot.port=/dev/tty.usbserial-130 \
    --robot.id=blue \
    --teleop.type=so100_leader \
    --teleop.port=/dev/tty.usbserial-110 \
    --teleop.id=blue \
    --logging_enabled=true
```

## 問題再現のための操作手順

ログ収集中に以下の操作を行って、wrist_roll の不要な回転を記録してください：

### 1. 基本動作テスト

- 各モーターを個別に動かす
- shoulder_pan、shoulder_lift、elbow_flex、wrist_flex、gripper を順番に操作
- wrist_roll がどのモーターの動きに反応するかを観察

### 2. 組み合わせ動作テスト

- 複数のモーターを同時に動かす
- 特に elbow_flex と gripper の組み合わせ（分析で相関が高かった）
- 日常的な操作パターンを再現

### 3. 意図的な問題再現

- wrist_roll が最も回転しやすい操作を特定
- その操作を繰り返し実行
- 問題の一貫性を確認

## 収集時間の目安

- **最低 5 分間**: 十分なデータポイントを収集
- **様々な操作**: 単調な動きではなく、多様なパターンを試す
- **問題の記録**: wrist_roll が回転したタイミングを覚えておく

## 完了後の手順

ログ収集が完了したら、Ctrl+C でテレオペレーションを終了し、新しいログファイルが生成されたことを確認してください。

その後、分析スクリプトを実行して結果を確認します。
