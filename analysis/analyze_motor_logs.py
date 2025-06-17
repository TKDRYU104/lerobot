#!/usr/bin/env python

"""
モーターログデータの分析スクリプト

このスクリプトは、teleoperate_loggingで生成されたCSVログファイルを分析し、
wrist_rollモーターと他のモーターの相関関係を調査します。
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from glob import glob

def load_latest_log():
    """最新のログファイルを読み込む"""
    log_files = glob('motor_logs/motor_log_*.csv')
    if not log_files:
        print("ログファイルが見つかりません。")
        sys.exit(1)
    
    # 最新のファイルを取得
    latest_log = max(log_files, key=os.path.getctime)
    print(f"分析対象ファイル: {latest_log}")
    
    # CSVファイルを読み込む
    df = pd.read_csv(latest_log)
    
    # elapsed_timeを数値型に変換
    df['elapsed_time'] = df['elapsed_time'].astype(float)
    
    return df, latest_log

def analyze_correlation(df):
    """相関分析を行う"""
    # モーター関連の列のみを抽出
    motor_cols = [col for col in df.columns if '.pos' in col]
    motor_df = df[motor_cols]
    
    # 相関係数を計算
    correlation = motor_df.corr()
    
    # 結果を保存するディレクトリを作成
    os.makedirs('analysis/results', exist_ok=True)
    
    # 相関係数をCSVに保存
    correlation.to_csv('analysis/results/correlation_matrix.csv')
    
    # wrist_rollとの相関係数を表示
    if 'wrist_roll.pos' in motor_df.columns:
        wrist_roll_corr = correlation['wrist_roll.pos'].sort_values(ascending=False)
        print("\nwrist_roll.posとの相関係数:")
        print(wrist_roll_corr)
        
        # 相関係数をCSVに保存
        wrist_roll_corr.to_csv('analysis/results/wrist_roll_correlation.csv')
    
    # 相関ヒートマップを作成
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
    plt.title('モーター値の相関係数')
    plt.tight_layout()
    plt.savefig('analysis/results/correlation_heatmap.png')
    plt.close()
    
    return correlation

def plot_time_series(df):
    """時系列プロットを作成"""
    # モーター関連の列のみを抽出
    motor_cols = [col for col in df.columns if '.pos' in col]
    
    # 時系列プロット
    plt.figure(figsize=(12, 6))
    for column in motor_cols:
        plt.plot(df['elapsed_time'], df[column], label=column)
    plt.legend()
    plt.title('モーター値の時間変化')
    plt.xlabel('経過時間 (秒)')
    plt.ylabel('モーター値')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('analysis/results/motor_values_time_series.png')
    plt.close()
    
    # wrist_rollのみの時系列プロット
    if 'wrist_roll.pos' in motor_cols:
        plt.figure(figsize=(12, 6))
        plt.plot(df['elapsed_time'], df['wrist_roll.pos'], 'r-', label='wrist_roll.pos')
        plt.title('wrist_rollモーターの時間変化')
        plt.xlabel('経過時間 (秒)')
        plt.ylabel('モーター値')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig('analysis/results/wrist_roll_time_series.png')
        plt.close()

def analyze_motor_movement_impact(df):
    """他のモーターの動きがwrist_rollに与える影響を分析"""
    if 'wrist_roll.pos' not in df.columns:
        print("wrist_roll.posが見つかりません。")
        return
    
    # モーター関連の列のみを抽出（wrist_roll以外）
    other_motor_cols = [col for col in df.columns if '.pos' in col and col != 'wrist_roll.pos']
    
    # 各モーターの変化量を計算
    for motor in other_motor_cols:
        df[f'{motor}_change'] = df[motor].diff().abs()
    
    # wrist_rollの変化量を計算
    df['wrist_roll.pos_change'] = df['wrist_roll.pos'].diff().abs()
    
    # 他のモーターの変化量の合計を計算
    df['other_motors_total_change'] = df[[f'{motor}_change' for motor in other_motor_cols]].sum(axis=1)
    
    # NaNを含む行を削除
    df_clean = df.dropna(subset=['other_motors_total_change', 'wrist_roll.pos_change'])
    
    # 散布図：他のモーターの変化量合計 vs wrist_rollの変化量
    plt.figure(figsize=(10, 6))
    plt.scatter(df_clean['other_motors_total_change'], df_clean['wrist_roll.pos_change'], alpha=0.5)
    plt.title('他のモーターの変化量合計 vs wrist_rollの変化量')
    plt.xlabel('他のモーターの変化量合計')
    plt.ylabel('wrist_rollの変化量')
    plt.grid(True)
    
    # 回帰直線を追加
    if len(df_clean) > 2:  # 少なくとも2点以上のデータが必要
        z = np.polyfit(df_clean['other_motors_total_change'], df_clean['wrist_roll.pos_change'], 1)
        p = np.poly1d(z)
        plt.plot(df_clean['other_motors_total_change'], p(df_clean['other_motors_total_change']), "r--")
        plt.text(0.05, 0.95, f'y = {z[0]:.4f}x + {z[1]:.4f}', transform=plt.gca().transAxes)
    
    plt.tight_layout()
    plt.savefig('analysis/results/motor_change_scatter.png')
    plt.close()
    
    # 各モーターごとの散布図
    plt.figure(figsize=(15, 10))
    for i, motor in enumerate(other_motor_cols):
        # 各モーターごとにNaNを含む行を削除
        motor_df_clean = df.dropna(subset=[f'{motor}_change', 'wrist_roll.pos_change'])
        
        plt.subplot(2, 3, i+1)
        plt.scatter(motor_df_clean[f'{motor}_change'], motor_df_clean['wrist_roll.pos_change'], alpha=0.5)
        plt.title(f'{motor}の変化量 vs wrist_rollの変化量')
        plt.xlabel(f'{motor}の変化量')
        plt.ylabel('wrist_rollの変化量')
        plt.grid(True)
        
        # 回帰直線を追加
        if len(motor_df_clean) > 2:  # 少なくとも2点以上のデータが必要
            z = np.polyfit(motor_df_clean[f'{motor}_change'], motor_df_clean['wrist_roll.pos_change'], 1)
            p = np.poly1d(z)
            plt.plot(motor_df_clean[f'{motor}_change'], p(motor_df_clean[f'{motor}_change']), "r--")
            plt.text(0.05, 0.95, f'y = {z[0]:.4f}x + {z[1]:.4f}', transform=plt.gca().transAxes)
    
    plt.tight_layout()
    plt.savefig('analysis/results/individual_motor_change_scatter.png')
    plt.close()
    
    # 相関係数を計算
    change_cols = [f'{motor}_change' for motor in other_motor_cols] + ['wrist_roll.pos_change', 'other_motors_total_change']
    change_df = df[change_cols].dropna()
    change_corr = change_df.corr()
    
    # 相関ヒートマップを作成
    plt.figure(figsize=(10, 8))
    sns.heatmap(change_corr, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
    plt.title('モーター変化量の相関係数')
    plt.tight_layout()
    plt.savefig('analysis/results/change_correlation_heatmap.png')
    plt.close()
    
    # wrist_rollの変化量との相関係数を表示
    wrist_roll_change_corr = change_corr['wrist_roll.pos_change'].sort_values(ascending=False)
    print("\nwrist_roll.pos_changeとの相関係数:")
    print(wrist_roll_change_corr)
    
    # 相関係数をCSVに保存
    wrist_roll_change_corr.to_csv('analysis/results/wrist_roll_change_correlation.csv')
    
    return change_corr

def main():
    """メイン関数"""
    # 結果ディレクトリを作成
    os.makedirs('analysis/results', exist_ok=True)
    
    # ログデータを読み込む
    df, log_file = load_latest_log()
    
    print(f"データポイント数: {len(df)}")
    print(f"記録されたモーター: {[col for col in df.columns if '.pos' in col]}")
    
    # 相関分析
    print("\n=== 相関分析 ===")
    correlation = analyze_correlation(df)
    
    # 時系列プロット
    print("\n=== 時系列プロット作成 ===")
    plot_time_series(df)
    
    # モーターの動きの影響分析
    print("\n=== モーターの動きの影響分析 ===")
    change_corr = analyze_motor_movement_impact(df)
    
    print("\n分析が完了しました。結果は analysis/results ディレクトリに保存されています。")

if __name__ == "__main__":
    main()
