#!/usr/bin/env python

"""
複数のログファイルの比較分析スクリプト

このスクリプトは、複数のログファイルを比較して、
wrist_rollモーターの問題の一貫性を調査します。
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from glob import glob

def load_all_logs():
    """すべてのログファイルを読み込む"""
    log_files = glob('motor_logs/motor_log_*.csv')
    if len(log_files) < 2:
        print("比較するには少なくとも2つのログファイルが必要です。")
        return None
    
    log_files.sort()  # ファイル名でソート
    
    logs_data = {}
    for log_file in log_files:
        print(f"読み込み中: {log_file}")
        df = pd.read_csv(log_file)
        df['elapsed_time'] = df['elapsed_time'].astype(float)
        
        # ファイル名から日時を抽出
        filename = os.path.basename(log_file)
        timestamp = filename.replace('motor_log_', '').replace('.csv', '')
        logs_data[timestamp] = df
    
    return logs_data

def compare_correlations(logs_data):
    """複数のログファイル間でwrist_rollの相関係数を比較"""
    correlation_comparison = {}
    
    for timestamp, df in logs_data.items():
        # モーター関連の列のみを抽出
        motor_cols = [col for col in df.columns if '.pos' in col]
        motor_df = df[motor_cols]
        
        # 相関係数を計算
        correlation = motor_df.corr()
        
        if 'wrist_roll.pos' in correlation.columns:
            wrist_roll_corr = correlation['wrist_roll.pos'].drop('wrist_roll.pos')
            correlation_comparison[timestamp] = wrist_roll_corr
    
    # 比較結果をDataFrameに変換
    comparison_df = pd.DataFrame(correlation_comparison)
    
    return comparison_df

def plot_correlation_comparison(comparison_df):
    """相関係数の比較をプロット"""
    # 結果を保存するディレクトリを作成
    os.makedirs('analysis/results', exist_ok=True)
    
    # 相関係数の変化をプロット
    plt.figure(figsize=(12, 8))
    
    for motor in comparison_df.index:
        plt.plot(comparison_df.columns, comparison_df.loc[motor], 
                marker='o', label=motor, linewidth=2)
    
    plt.title('wrist_rollとの相関係数の変化')
    plt.xlabel('ログファイル（時系列）')
    plt.ylabel('相関係数')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('analysis/results/correlation_comparison.png')
    plt.close()
    
    # ヒートマップ
    plt.figure(figsize=(10, 6))
    sns.heatmap(comparison_df, annot=True, cmap='coolwarm', 
                center=0, vmin=-0.5, vmax=0.5)
    plt.title('wrist_rollとの相関係数比較（ヒートマップ）')
    plt.xlabel('ログファイル（時系列）')
    plt.ylabel('モーター')
    plt.tight_layout()
    plt.savefig('analysis/results/correlation_heatmap_comparison.png')
    plt.close()

def analyze_data_statistics(logs_data):
    """各ログファイルの統計情報を分析"""
    stats_data = {}
    
    for timestamp, df in logs_data.items():
        stats = {
            'データポイント数': len(df),
            'wrist_roll平均値': df['wrist_roll.pos'].mean(),
            'wrist_roll標準偏差': df['wrist_roll.pos'].std(),
            'wrist_roll最大値': df['wrist_roll.pos'].max(),
            'wrist_roll最小値': df['wrist_roll.pos'].min(),
            'wrist_roll変化量平均': df['wrist_roll.pos'].diff().abs().mean(),
            'wrist_roll変化量最大': df['wrist_roll.pos'].diff().abs().max()
        }
        stats_data[timestamp] = stats
    
    stats_df = pd.DataFrame(stats_data).T
    
    return stats_df

def main():
    """メイン関数"""
    print("=== 複数ログファイルの比較分析 ===")
    
    # すべてのログファイルを読み込む
    logs_data = load_all_logs()
    if logs_data is None:
        return
    
    print(f"\n分析対象ファイル数: {len(logs_data)}")
    for timestamp in logs_data.keys():
        print(f"  - {timestamp}")
    
    # 相関係数の比較
    print("\n=== 相関係数の比較 ===")
    comparison_df = compare_correlations(logs_data)
    print(comparison_df)
    
    # 相関係数をCSVに保存
    comparison_df.to_csv('analysis/results/correlation_comparison.csv')
    
    # プロット作成
    plot_correlation_comparison(comparison_df)
    
    # 統計情報の分析
    print("\n=== 統計情報の比較 ===")
    stats_df = analyze_data_statistics(logs_data)
    print(stats_df)
    
    # 統計情報をCSVに保存
    stats_df.to_csv('analysis/results/statistics_comparison.csv')
    
    # 主要な発見をまとめる
    print("\n=== 主要な発見 ===")
    
    # 最も相関の高いモーターを特定
    for col in comparison_df.columns:
        max_corr_motor = comparison_df[col].abs().idxmax()
        max_corr_value = comparison_df.loc[max_corr_motor, col]
        print(f"{col}: 最高相関モーター = {max_corr_motor} ({max_corr_value:.3f})")
    
    # 相関の変化が大きいモーターを特定
    correlation_variance = comparison_df.var(axis=1).sort_values(ascending=False)
    print(f"\n相関の変化が大きいモーター:")
    for motor, variance in correlation_variance.head(3).items():
        print(f"  {motor}: 分散 = {variance:.4f}")
    
    print("\n比較分析が完了しました。結果は analysis/results ディレクトリに保存されています。")

if __name__ == "__main__":
    main()
