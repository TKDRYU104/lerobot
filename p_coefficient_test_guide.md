# P 係数段階的低減テストガイド

## 概要

wrist_roll の P 係数を段階的に低減（16→4→2→1）して、最適な安定性と応答性のバランスを見つけるためのテストガイドです。

## 実装されたバージョン

### 1. ベースライン（P 係数 16）

- **ファイル**: 元の`so100_follower.py`
- **設定**: 全モーター P 係数 16
- **結果**: 標準偏差 95.596（制御不能）

### 2. 修正版（P 係数 4）

- **ファイル**: 修正済みの`so100_follower.py`
- **設定**: wrist_roll のみ P 係数 4
- **結果**: 標準偏差 59.976（37.3%改善）

### 3. P 係数 2 版

- **ファイル**: `so100_follower_p2.py`
- **設定**: wrist_roll のみ P 係数 2
- **期待**: さらなる安定化

### 4. P 係数 1 版（最小応答性）

- **ファイル**: `so100_follower_p1.py`
- **設定**: wrist_roll のみ P 係数 1
- **期待**: 最大限の安定化

## テスト手順

### Phase 1: P 係数 2 版のテスト

#### 基本テスト

```bash
# 元のso100_followerを一時的にP係数2版に置き換えてテスト
python -m lerobot.teleoperate_logging \
    --robot.type=so100_follower \
    --robot.port=/dev/tty.usbserial-130 \
    --robot.id=blue \
    --teleop.type=so100_leader \
    --teleop.port=/dev/tty.usbserial-110 \
    --teleop.id=blue \
    --logging_enabled=true
```

#### 評価項目

1. **wrist_roll の安定性**: 標準偏差の測定
2. **応答性**: 意図的な wrist_roll 操作の反応
3. **他のモーターへの影響**: 操作性の変化
4. **全体的な使用感**: 自然な操作感

### Phase 2: P 係数 1 版のテスト

#### 最小応答性テスト

```bash
# P係数1版でのテスト
python -m lerobot.teleoperate_logging \
    --robot.type=so100_follower \
    --robot.port=/dev/tty.usbserial-130 \
    --robot.id=blue \
    --teleop.type=so100_leader \
    --teleop.port=/dev/tty.usbserial-110 \
    --teleop.id=blue \
    --logging_enabled=true
```

#### 注意点

- 応答性が極端に低下する可能性
- 意図的な wrist_roll 操作が困難になる可能性
- 遅延やラグの発生

### Phase 3: 比較分析

#### 各バージョンでの 5 分間テスト

1. **P 係数 16**: ベースライン測定
2. **P 係数 4**: 現在の修正版
3. **P 係数 2**: 中間的な設定
4. **P 係数 1**: 最小応答性

#### 分析スクリプトの実行

```bash
python analysis/analyze_latest_log.py
```

## 評価指標

### 1. 安定性指標

- **標準偏差**: 95.596 → 目標 30.0 以下
- **大きな変化回数**: 242 回 → 目標 50 回以下
- **異常値の割合**: 100% → 目標 10%以下

### 2. 応答性指標

- **意図的操作の反応時間**: <100ms
- **操作精度**: 目標位置への到達精度
- **操作の自然さ**: ユーザビリティ評価

### 3. 総合評価

- **安定性スコア**: (100 - 標準偏差) / 100
- **応答性スコア**: 主観的評価（1-10）
- **総合スコア**: 安定性 × 応答性

## 期待される結果

### P 係数 2 版

- **標準偏差**: 59.976 → 35-45
- **改善率**: 50-60%
- **応答性**: やや低下するが許容範囲

### P 係数 1 版

- **標準偏差**: 35-45 → 20-30
- **改善率**: 70-80%
- **応答性**: 大幅低下の可能性

## 最適値の決定

### 判定基準

1. **標準偏差 30 以下**: 実用的な安定性
2. **応答性スコア 7 以上**: 許容できる操作感
3. **大きな変化 50 回以下**: 十分な制御性

### 推奨される選択

- **P 係数 2**: バランス重視
- **P 係数 1**: 安定性最優先
- **P 係数 4**: 現状維持（既に改善済み）

## 実装手順

### 1. ファイルの置き換え

```bash
# P係数2版をテストする場合
cp lerobot/common/robots/so100_follower/so100_follower_p2.py \
   lerobot/common/robots/so100_follower/so100_follower.py
```

### 2. テスト実行

```bash
python -m lerobot.teleoperate_logging \
    --logging_enabled=true
```

### 3. 分析実行

```bash
python analysis/analyze_latest_log.py
```

### 4. 結果の記録

- 各 P 係数での標準偏差
- 操作感の主観評価
- 推奨設定の決定

## トラブルシューティング

### 応答性が低すぎる場合

- P 係数を 1 段階上げる（1→2、2→4）
- I 係数や D 係数の調整を検討

### 安定性が不十分な場合

- P 係数をさらに下げる
- elbow_flex フィルターとの組み合わせ
- 完全無効化の検討

### 操作感が不自然な場合

- 他のモーターの P 係数も調整
- 全体的なバランスの見直し

このテストにより、wrist_roll の最適な P 係数設定を科学的に決定できます。
