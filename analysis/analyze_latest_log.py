#!/usr/bin/env python

"""
最新のログファイルを自動分析するスクリプト

このスクリプトは、最新のログファイルを分析し、
前回の結果と比較して問題の変化を調査します。
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from glob import glob
from datetime import datetime

def get_latest_log():
    """最新のログファイルを取得"""
    log_files = glob('motor_logs/motor_log_*.csv')
    if not log_files:
        print("ログファイルが見つかりません。")
        return None
    
    # 最新のファイルを取得
    latest_log = max(log_files, key=os.path.getctime)
    return latest_log

def analyze_wrist_roll_behavior(df):
    """wrist_rollの動作を詳細分析"""
    print("=== wrist_rollの動作分析 ===")
    
    if 'wrist_roll.pos' not in df.columns:
        print("wrist_roll.posが見つかりません。")
        return
    
    # 基本統計
    wrist_roll_data = df['wrist_roll.pos']
    print(f"平均値: {wrist_roll_data.mean():.3f}")
    print(f"標準偏差: {wrist_roll_data.std():.3f}")
    print(f"最大値: {wrist_roll_data.max():.3f}")
    print(f"最小値: {wrist_roll_data.min():.3f}")
    
    # 変化量の分析
    wrist_roll_change = wrist_roll_data.diff().abs()
    print(f"変化量平均: {wrist_roll_change.mean():.3f}")
    print(f"変化量最大: {wrist_roll_change.max():.3f}")
    
    # 大きな変化の回数をカウント
    large_changes = (wrist_roll_change > 10.0).sum()
    very_large_changes = (wrist_roll_change > 50.0).sum()
    print(f"大きな変化(>10.0)の回数: {large_changes}")
    print(f"非常に大きな変化(>50.0)の回数: {very_large_changes}")
    
    # デッドゾーン効果の確認
    small_values = (abs(wrist_roll_data) < 5.0).sum()
    medium_values = ((abs(wrist_roll_data) >= 5.0) & (abs(wrist_roll_data) < 10.0)).sum()
    large_values = (abs(wrist_roll_data) >= 10.0).sum()
    
    total_points = len(wrist_roll_data)
    print(f"\n値の分布:")
    print(f"小さな値(|x|<5.0): {small_values} ({small_values/total_points*100:.1f}%)")
    print(f"中程度の値(5.0≤|x|<10.0): {medium_values} ({medium_values/total_points*100:.1f}%)")
    print(f"大きな値(|x|≥10.0): {large_values} ({large_values/total_points*100:.1f}%)")

def analyze_motor_correlations(df):
    """モーター間の相関を分析"""
    print("\n=== モーター相関分析 ===")
    
    # モーター関連の列のみを抽出
    motor_cols = [col for col in df.columns if '.pos' in col]
    motor_df = df[motor_cols]
    
    # 相関係数を計算
    correlation = motor_df.corr()
    
    if 'wrist_roll.pos' in correlation.columns:
        wrist_roll_corr = correlation['wrist_roll.pos'].drop('wrist_roll.pos')
        print("wrist_rollとの相関係数:")
        for motor, corr in wrist_roll_corr.sort_values(ascending=False).items():
            print(f"  {motor}: {corr:.3f}")

def analyze_trigger_patterns(df):
    """wrist_rollが動くトリガーパターンを分析"""
    print("\n=== トリガーパターン分析 ===")
    
    if 'wrist_roll.pos' not in df.columns:
        return
    
    # 各モーターの変化量を計算
    motor_cols = [col for col in df.columns if '.pos' in col and col != 'wrist_roll.pos']
    
    for motor in motor_cols:
        df[f'{motor}_change'] = df[motor].diff().abs()
    
    df['wrist_roll_change'] = df['wrist_roll.pos'].diff().abs()
    
    # 大きなwrist_roll変化が起きたときの他のモーターの状態
    large_wrist_changes = df[df['wrist_roll_change'] > 10.0]
    
    if len(large_wrist_changes) > 0:
        print(f"大きなwrist_roll変化({len(large_wrist_changes)}回)の際の他のモーター変化量:")
        for motor in motor_cols:
            change_col = f'{motor}_change'
            if change_col in large_wrist_changes.columns:
                avg_change = large_wrist_changes[change_col].mean()
                print(f"  {motor}: 平均{avg_change:.3f}")
    else:
        print("大きなwrist_roll変化は検出されませんでした。")

def compare_with_previous_logs():
    """前回のログと比較"""
    print("\n=== 前回ログとの比較 ===")
    
    log_files = sorted(glob('motor_logs/motor_log_*.csv'))
    if len(log_files) < 2:
        print("比較するログファイルが不足しています。")
        return
    
    # 最新と前回のファイルを比較
    latest_file = log_files[-1]
    previous_file = log_files[-2]
    
    print(f"最新: {os.path.basename(latest_file)}")
    print(f"前回: {os.path.basename(previous_file)}")
    
    # 簡単な統計比較
    latest_df = pd.read_csv(latest_file)
    previous_df = pd.read_csv(previous_file)
    
    if 'wrist_roll.pos' in latest_df.columns and 'wrist_roll.pos' in previous_df.columns:
        latest_std = latest_df['wrist_roll.pos'].std()
        previous_std = previous_df['wrist_roll.pos'].std()
        
        print(f"wrist_roll標準偏差の変化: {previous_std:.3f} → {latest_std:.3f}")
        
        if latest_std < previous_std:
            print("✓ 改善: wrist_rollの変動が減少しました")
        elif latest_std > previous_std:
            print("✗ 悪化: wrist_rollの変動が増加しました")
        else:
            print("→ 変化なし: wrist_rollの変動は同程度です")

def main():
    """メイン関数"""
    print("=== 最新ログファイルの分析 ===")
    
    # 最新のログファイルを取得
    latest_log = get_latest_log()
    if latest_log is None:
        return
    
    print(f"分析対象: {latest_log}")
    
    # CSVファイルを読み込む
    try:
        df = pd.read_csv(latest_log)
        df['elapsed_time'] = df['elapsed_time'].astype(float)
    except Exception as e:
        print(f"ファイル読み込みエラー: {e}")
        return
    
    print(f"データポイント数: {len(df)}")
    print(f"記録時間: {df['elapsed_time'].max():.1f}秒")
    
    # 各種分析を実行
    analyze_wrist_roll_behavior(df)
    analyze_motor_correlations(df)
    analyze_trigger_patterns(df)
    compare_with_previous_logs()
    
    print("\n=== 推奨される次のステップ ===")
    
    # wrist_rollの問題レベルを評価
    if 'wrist_roll.pos' in df.columns:
        wrist_roll_change = df['wrist_roll.pos'].diff().abs()
        large_changes = (wrist_roll_change > 10.0).sum()
        
        if large_changes == 0:
            print("✓ 問題解決: wrist_rollの不要な動きは検出されませんでした")
        elif large_changes < 10:
            print("△ 部分的改善: wrist_rollの問題は軽減されていますが、完全ではありません")
            print("  → P係数をさらに下げる（4→2→1）")
            print("  → デッドゾーンを強化する（10.0→20.0）")
        else:
            print("✗ 問題継続: wrist_rollの問題が継続しています")
            print("  → 完全無効化を検討")
            print("  → ハードウェアの確認")
            print("  → より強力なフィルタリング")

if __name__ == "__main__":
    main()
