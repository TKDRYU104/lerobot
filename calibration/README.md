# LeRobot キャリブレーションファイル

このディレクトリには、LeRobot プロジェクトで使用するロボット（フォロー側）とテレオペレーター（リーダー側）のキャリブレーションファイルが保存されます。

## ディレクトリ構造

```
calibration/
├── robots/           # フォロー側ロボットのキャリブレーション
│   ├── so100_follower/
│   ├── so101_follower/
│   ├── koch_follower/
│   └── [その他のロボット]/
└── teleoperators/    # リーダー側テレオペレーターのキャリブレーション
    ├── so100_leader/
    ├── so101_leader/
    ├── koch_leader/
    └── [その他のテレオペレーター]/
```

## 使用方法

### 1. 環境変数の設定

このワークスペース内の calibration ディレクトリを使用するために、以下の環境変数を設定してください：

```bash
export HF_LEROBOT_CALIBRATION="/Users/tkdryu/Documents/NakaLab/lerobot/calibration"
```

### 2. キャリブレーションの実行

#### フォロー側ロボットのキャリブレーション例

```bash
# SO100 フォロワーのキャリブレーション
python -m lerobot.calibrate \
    --robot.type=so100_follower \
    --robot.port=/dev/tty.usbmodem58760431551 \
    --robot.id=blue

# SO100 フォロワーのキャリブレーション （こちらの方がおすすめ）
# こちらはポートを直接指定しない場合の例
# その場合、デフォルトのポートが使用されます
python -m lerobot.calibrate \
    --robot.type=so100_follower --robot.port=/dev/tty.usbserial-130 \
    --robot.id=blue

# SO101 フォロワーのキャリブレーション
python -m lerobot.calibrate \
    --robot.type=so101_follower \
    --robot.port=/dev/tty.usbmodem58760431551 \
    --robot.id=blue

# SO101 フォロワーのキャリブレーション （こちらの方がおすすめ）
# こちらはポートを直接指定しない場合の例
# その場合、デフォルトのポートが使用されます
python -m lerobot.calibrate \
    --robot.type=so101_follower --robot.port=/dev/tty.usbserial-130 \
    --robot.id=blue

```

#### リーダー側テレオペレーターのキャリブレーション例

```bash
# SO100 リーダーのキャリブレーション
python -m lerobot.calibrate \
    --teleop.type=so100_leader \
    --teleop.port=/dev/tty.usbmodem58760431551 \
    --teleop.id=blue

# SO100 リーダーのキャリブレーション （こちらの方がおすすめ）
# こちらはポートを直接指定しない場合の例
# その場合、デフォルトのポートが使用されます
python -m lerobot.calibrate \
    --teleop.type=so100_leader --teleop.port=/dev/tty.usbserial-110 \
    --teleop.id=blue

# SO101 リーダーのキャリブレーション
python -m lerobot.calibrate \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodem58760431551 \
    --teleop.id=blue
```

### 3. キャリブレーションファイルの確認

キャリブレーション完了後、以下のようなファイルが生成されます：

```
calibration/
├── robots/
│   └── so100_follower/
│       └── blue.json    # IDが"blue"の場合
└── teleoperators/
    └── so100_leader/
        └── blue.json    # IDが"blue"の場合
```

## 注意事項

- キャリブレーションファイルは各デバイスの ID ごとに個別に保存されます
- 同じ種類のデバイスでも、異なる ID を使用することで複数の設定を管理できます
- キャリブレーションファイルは JSON 形式で保存され、モーターの位置情報などが含まれます
