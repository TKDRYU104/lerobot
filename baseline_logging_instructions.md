# ベースライン（初期設定）でのログデータ収集

## 現在の設定状況

✅ **完全な初期設定に復元完了**

- すべてのモーターの P 係数: 16（元の設定）
- wrist_roll の特別な設定: なし
- デッドゾーン処理: なし
- フィルタリング: なし

## ログデータ収集の実行

以下のコマンドでベースライン（初期設定）でのログデータを収集してください：

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

## 重要な操作手順

### 1. 問題の再現を重点的に行う

- **wrist_roll が最も回転しやすい操作を特定**
- その操作を繰り返し実行
- 問題の発生パターンを記録

### 2. 各モーターの個別テスト

- shoulder_pan、shoulder_lift、elbow_flex、wrist_flex、gripper を順番に操作
- どのモーターが wrist_roll の回転を引き起こすかを確認

### 3. 組み合わせ操作のテスト

- 複数のモーターを同時に動かす
- 特に elbow_flex と gripper の組み合わせ（前回の分析で相関が高かった）

## 収集時間

- **最低 5-10 分間**: 十分なデータポイントを収集
- **問題の再現**: wrist_roll が回転する操作を重点的に実行

## 完了後の分析

ログ収集が完了したら、以下のコマンドで分析を実行：

```bash
python analysis/analyze_latest_log.py
```

この分析により、初期設定での問題の詳細な特徴が明らかになります。

## 期待される結果

ベースラインでの分析により以下が明確になります：

1. wrist_roll の不要な回転の頻度と強度
2. 他のモーターとの相関関係
3. 問題を引き起こす具体的な操作パターン
4. 今後の対策の効果を測定するための基準値

この基準データを元に、段階的に対策を実装し、その効果を定量的に評価できます。
