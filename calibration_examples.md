# LeRobot キャリブレーション実行例

このファイルには、ワークスペース内のキャリブレーションディレクトリを使用した具体的な実行例を示します。

## 事前準備

### 1. 環境変数の設定

```bash
# 一時的な設定（現在のセッションのみ）
source setup_calibration_env.sh

# または永続的な設定（推奨）
echo 'export HF_LEROBOT_CALIBRATION="/Users/tkdryu/Documents/NakaLab/lerobot/calibration"' >> ~/.zshrc
source ~/.zshrc
```

### 2. デバイスの接続確認

```bash
# 利用可能なポートを確認
python -m lerobot.find_port

# カメラデバイスを確認
python -m lerobot.find_cameras
```

## キャリブレーション実行例

### SO100 システムのキャリブレーション

#### リーダー側（テレオペレーター）のキャリブレーション

```bash
# SO100 リーダーのキャリブレーション
python -m lerobot.calibrate \
    --teleop.type=so100_leader \
    --teleop.port=/dev/tty.usbmodem58760431551 \
    --teleop.id=blue

# 保存先: calibration/teleoperators/so100_leader/blue.json
```

#### フォロー側（ロボット）のキャリブレーション

```bash
# SO100 フォロワーのキャリブレーション
python -m lerobot.calibrate \
    --robot.type=so100_follower \
    --robot.port=/dev/tty.usbmodem58760431552 \
    --robot.id=blue

# 保存先: calibration/robots/so100_follower/blue.json
```

### SO101 システムのキャリブレーション

#### リーダー側（テレオペレーター）のキャリブレーション

```bash
# SO101 リーダーのキャリブレーション
python -m lerobot.calibrate \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodem58760431553 \
    --teleop.id=red

# 保存先: calibration/teleoperators/so101_leader/red.json
```

#### フォロー側（ロボット）のキャリブレーション

```bash
# SO101 フォロワーのキャリブレーション
python -m lerobot.calibrate \
    --robot.type=so101_follower \
    --robot.port=/dev/tty.usbmodem58760431554 \
    --robot.id=red

# 保存先: calibration/robots/so101_follower/red.json
```

### Koch システムのキャリブレーション

#### リーダー側（テレオペレーター）のキャリブレーション

```bash
# Koch リーダーのキャリブレーション
python -m lerobot.calibrate \
    --teleop.type=koch_leader \
    --teleop.port=/dev/tty.usbmodem58760431555 \
    --teleop.id=green

# 保存先: calibration/teleoperators/koch_leader/green.json
```

#### フォロー側（ロボット）のキャリブレーション

```bash
# Koch フォロワーのキャリブレーション
python -m lerobot.calibrate \
    --robot.type=koch_follower \
    --robot.port=/dev/tty.usbmodem58760431556 \
    --robot.id=green

# 保存先: calibration/robots/koch_follower/green.json
```

## キャリブレーション後の確認

### ファイル構造の確認

```bash
# キャリブレーションファイルの確認
tree calibration/

# 期待される出力例:
# calibration/
# ├── robots/
# │   ├── so100_follower/
# │   │   └── blue.json
# │   ├── so101_follower/
# │   │   └── red.json
# │   └── koch_follower/
# │       └── green.json
# └── teleoperators/
#     ├── so100_leader/
#     │   └── blue.json
#     ├── so101_leader/
#     │   └── red.json
#     └── koch_leader/
#         └── green.json
```

### キャリブレーションファイルの内容確認

```bash
# キャリブレーションファイルの内容を確認
cat calibration/robots/so100_follower/blue.json
cat calibration/teleoperators/so100_leader/blue.json
```

## トラブルシューティング

### よくある問題と解決方法

1. **ポートが見つからない場合**

   ```bash
   # デバイスの接続を確認
   ls /dev/tty.*
   # または
   python -m lerobot.find_port
   ```

2. **権限エラーが発生する場合**

   ```bash
   # ポートへのアクセス権限を確認
   sudo chmod 666 /dev/tty.usbmodem*
   ```

3. **環境変数が設定されていない場合**

   ```bash
   # 環境変数の確認
   echo $HF_LEROBOT_CALIBRATION

   # 再設定
   source setup_calibration_env.sh
   ```

4. **キャリブレーションファイルが見つからない場合**

   ```bash
   # ディレクトリの存在確認
   ls -la calibration/

   # 必要に応じてディレクトリを再作成
   mkdir -p calibration/robots calibration/teleoperators
   ```

## 注意事項

- キャリブレーション実行前に、デバイスが正しく接続されていることを確認してください
- 同じ ID を使用すると既存のキャリブレーションファイルが上書きされます
- 複数のデバイスを使用する場合は、異なる ID を設定することを推奨します
- キャリブレーションファイルはプロジェクトと一緒にバージョン管理することができます
