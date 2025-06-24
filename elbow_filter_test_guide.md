# elbow_flex 連動フィルターのテストガイド

## 概要

elbow_flex と wrist_roll の強い負の相関（-0.253）に基づいて開発された、高度なフィルタリングシステムのテストガイドです。

## 実装された機能

### 1. elbow_flex 変化量監視

- elbow_flex の変化量を常時監視
- 閾値を超えた場合に wrist_roll をフィルタリング

### 2. 適応的閾値調整

- 過去 100 フレームの統計に基づいて閾値を自動調整
- 平均 + 1.5 標準偏差を新しい閾値として設定

### 3. フィルター強度調整

- 0.0-1.0 の範囲でフィルタリング強度を設定
- 前回値との補間によるスムーズなフィルタリング

### 4. リアルタイム統計表示

- フィルタリング率の表示
- 現在の閾値の表示
- 詳細なフィルタリング理由の表示

## テスト手順

### 基本テスト（デフォルト設定）

```bash
python -m lerobot.teleoperate_elbow_filter \
    --robot.type=so100_follower \
    --robot.port=/dev/tty.usbserial-130 \
    --robot.id=blue \
    --teleop.type=so100_leader \
    --teleop.port=/dev/tty.usbserial-110 \
    --teleop.id=blue
```

**デフォルト設定**:

- elbow_threshold: 2.0
- wrist_deadzone: 5.0
- filter_strength: 0.8
- adaptive_threshold: true

### 強力フィルタリングテスト

```bash
python -m lerobot.teleoperate_elbow_filter \
    --robot.type=so100_follower \
    --robot.port=/dev/tty.usbserial-130 \
    --robot.id=blue \
    --teleop.type=so100_leader \
    --teleop.port=/dev/tty.usbserial-110 \
    --teleop.id=blue \
    --elbow_threshold=1.0 \
    --wrist_deadzone=10.0 \
    --filter_strength=0.9
```

### 軽量フィルタリングテスト

```bash
python -m lerobot.teleoperate_elbow_filter \
    --robot.type=so100_follower \
    --robot.port=/dev/tty.usbserial-130 \
    --robot.id=blue \
    --teleop.type=so100_leader \
    --teleop.port=/dev/tty.usbserial-110 \
    --teleop.id=blue \
    --elbow_threshold=3.0 \
    --wrist_deadzone=3.0 \
    --filter_strength=0.5
```

### 固定閾値テスト

```bash
python -m lerobot.teleoperate_elbow_filter \
    --robot.type=so100_follower \
    --robot.port=/dev/tty.usbserial-130 \
    --robot.id=blue \
    --teleop.type=so100_leader \
    --teleop.port=/dev/tty.usbserial-110 \
    --teleop.id=blue \
    --adaptive_threshold=false \
    --elbow_threshold=2.5
```

## テスト項目

### 1. elbow_flex 動作テスト

- **目的**: elbow_flex を動かした際の wrist_roll の反応を確認
- **手順**:
  1. elbow_flex を大きく動かす
  2. フィルタリングメッセージの確認
  3. wrist_roll の動きが抑制されているかチェック

### 2. 他のモーター動作テスト

- **目的**: elbow_flex 以外のモーターでの影響を確認
- **手順**:
  1. shoulder_pan、shoulder_lift、wrist_flex、gripper を個別に動かす
  2. wrist_roll への影響を観察
  3. 不要なフィルタリングが発生していないかチェック

### 3. 複合動作テスト

- **目的**: 複数のモーターを同時に動かした際の動作確認
- **手順**:
  1. elbow_flex + gripper の同時操作
  2. shoulder 系 + elbow_flex の同時操作
  3. 全モーターの複合動作

### 4. 適応的閾値テスト

- **目的**: 適応的閾値調整の効果確認
- **手順**:
  1. 最初の閾値を記録
  2. 5 分間の操作を実行
  3. 最終閾値との比較
  4. 閾値の変化が適切かチェック

## 評価指標

### 1. フィルタリング効果

- **wrist_roll の標準偏差**: ベースライン（95.596）からの改善度
- **大きな変化の回数**: >10.0 の変化回数の削減
- **フィルタリング率**: 適切な範囲（10-30%程度）での動作

### 2. 操作性

- **レスポンス**: 意図的な wrist_roll 操作の応答性
- **自然さ**: 他のモーター操作への影響の少なさ
- **予測可能性**: フィルタリング動作の一貫性

### 3. 適応性

- **閾値調整**: 使用パターンに応じた適切な調整
- **安定性**: 閾値の過度な変動がないこと
- **収束性**: 適切な値への収束

## 期待される結果

### 成功指標

1. **wrist_roll 標準偏差**: 95.596 → 30.0 以下
2. **大きな変化回数**: 242 回 → 50 回以下
3. **フィルタリング率**: 15-25%の範囲
4. **操作遅延**: 感知できない程度（<50ms）

### 注意点

- elbow_flex の意図的な操作が阻害されていないか
- 他のモーターの操作性に悪影響がないか
- フィルタリングが過度に強すぎないか

## トラブルシューティング

### フィルタリングが強すぎる場合

- `elbow_threshold`を大きくする（2.0 → 3.0）
- `filter_strength`を小さくする（0.8 → 0.6）

### フィルタリングが弱すぎる場合

- `elbow_threshold`を小さくする（2.0 → 1.5）
- `wrist_deadzone`を大きくする（5.0 → 8.0）

### 適応的閾値が不安定な場合

- `adaptive_threshold=false`で固定閾値を使用
- 手動で適切な閾値を設定

このテストにより、elbow_flex 連動フィルターの効果を定量的に評価できます。
