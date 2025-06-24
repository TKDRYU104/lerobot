# 簡単テスト手順 - wrist_roll 問題の解決策テスト

## 現在利用可能な解決策

### 1. elbow_flex フィルター（推奨）

最も効果的で使いやすい解決策

### 2. P 係数低減

ハードウェア設定の変更

### 3. 完全無効化

確実だが機能を失う

## 手順 1: elbow_flex フィルターのテスト

### ステップ 1: 実行

```bash
python -m lerobot.teleoperate_elbow_filter \
    --robot.type=so100_follower \
    --robot.port=/dev/tty.usbserial-130 \
    --robot.id=blue \
    --teleop.type=so100_leader \
    --teleop.port=/dev/tty.usbserial-110 \
    --teleop.id=blue
```

### ステップ 2: 動作確認

1. **elbow_flex を大きく動かす** → wrist_roll の動きが抑制されるかチェック
2. **他のモーターを動かす** → 正常に動作するかチェック
3. **画面の統計を確認** → フィルタリング率が 15-25%程度かチェック

### ステップ 3: 効果の確認

- wrist_roll の不要な回転が減っているか
- 操作感が自然か
- フィルタリングメッセージが適切に表示されるか

## 手順 2: P 係数 2 版のテスト（より高度）

### ステップ 1: ファイルのバックアップ

```bash
cp lerobot/common/robots/so100_follower/so100_follower.py \
   lerobot/common/robots/so100_follower/so100_follower_backup.py
```

### ステップ 2: P 係数 2 版に置き換え

```bash
cp lerobot/common/robots/so100_follower/so100_follower_p2.py \
   lerobot/common/robots/so100_follower/so100_follower.py
```

### ステップ 3: テスト実行

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

### ステップ 4: 元に戻す

```bash
cp lerobot/common/robots/so100_follower/so100_follower_backup.py \
   lerobot/common/robots/so100_follower/so100_follower.py
```

## 手順 3: 完全無効化（最も確実）

### 実行

```bash
python -m lerobot.teleoperate_wrist_disabled \
    --robot.type=so100_follower \
    --robot.port=/dev/tty.usbserial-130 \
    --robot.id=blue \
    --teleop.type=so100_leader \
    --teleop.port=/dev/tty.usbserial-110 \
    --teleop.id=blue
```

### 確認

- wrist_roll が常に 0.0 に固定されるか
- [DISABLED]マークが表示されるか
- 他のモーターは正常に動作するか

## 推奨テスト順序

### 1. まず elbow_flex フィルターを試す

- 最も使いやすく効果的
- ファイル変更不要
- リアルタイムで効果確認可能

### 2. 効果が不十分なら P 係数 2 版

- より強力な安定化
- ファイル置き換えが必要
- バックアップを忘れずに

### 3. 最後の手段として完全無効化

- 100%確実だが機能を失う
- 緊急時の対処法

## トラブルシューティング

### エラーが出る場合

1. **ポート番号を確認** → `/dev/tty.usbserial-130`と`/dev/tty.usbserial-110`
2. **ロボットの接続を確認** → ケーブルとバッテリー
3. **権限を確認** → `sudo`が必要な場合あり

### 効果が感じられない場合

1. **elbow_flex フィルター** → `--elbow_threshold=1.0`で強化
2. **P 係数版** → P 係数 1 版を試す
3. **完全無効化** → 確実な解決

## 次のステップ

### 効果があった場合

1. **ログデータを収集** → `--logging_enabled=true`
2. **分析を実行** → `python analysis/analyze_latest_log.py`
3. **効果を定量化** → 標準偏差の改善を確認

### さらなる改善が必要な場合

1. **複数の解決策を組み合わせ**
2. **設定の微調整**
3. **GitHub イシューでの相談**

まずは**elbow_flex フィルター**から試してみてください！
