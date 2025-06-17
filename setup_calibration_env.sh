#!/bin/bash

# LeRobot キャリブレーション環境設定スクリプト
# このスクリプトは、ワークスペース内のcalibrationディレクトリを使用するための環境変数を設定します

# 現在のワークスペースのパスを取得
WORKSPACE_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CALIBRATION_PATH="${WORKSPACE_PATH}/calibration"

echo "LeRobot キャリブレーション環境を設定しています..."
echo "ワークスペースパス: ${WORKSPACE_PATH}"
echo "キャリブレーションパス: ${CALIBRATION_PATH}"

# 環境変数を設定
export HF_LEROBOT_CALIBRATION="${CALIBRATION_PATH}"

echo ""
echo "環境変数が設定されました:"
echo "HF_LEROBOT_CALIBRATION=${HF_LEROBOT_CALIBRATION}"
echo ""

# 設定の確認
if [ -d "${CALIBRATION_PATH}" ]; then
    echo "✓ キャリブレーションディレクトリが存在します"
else
    echo "✗ キャリブレーションディレクトリが見つかりません"
    echo "  以下のコマンドでディレクトリを作成してください:"
    echo "  mkdir -p ${CALIBRATION_PATH}/robots ${CALIBRATION_PATH}/teleoperators"
fi

echo ""
echo "使用方法:"
echo "1. このスクリプトをsourceコマンドで実行してください:"
echo "   source setup_calibration_env.sh"
echo ""
echo "2. または、以下の行を ~/.bashrc または ~/.zshrc に追加してください:"
echo "   export HF_LEROBOT_CALIBRATION=\"${CALIBRATION_PATH}\""
echo ""
echo "3. キャリブレーションを実行してください:"
echo "   python -m lerobot.calibrate --robot.type=so100_follower --robot.port=/dev/ttyUSB0 --robot.id=blue"
echo "   python -m lerobot.calibrate --teleop.type=so100_leader --teleop.port=/dev/ttyUSB1 --teleop.id=blue"
