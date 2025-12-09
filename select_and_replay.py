#!/usr/bin/env python

"""
Select and replay recorded motions from a menu.

This script scans for .pkl files in the current directory (or specified directory),
displays them in a numbered menu, and allows you to select which one to replay.

Usage:
    python select_and_replay.py
    python select_and_replay.py --directory recordings/
    python select_and_replay.py --loop --no-calibrate
"""

import argparse
import pickle
import time
from pathlib import Path

from lerobot.common.robots.so100_follower import SO100Follower
from lerobot.common.robots.so100_follower.config_so100_follower import SO100FollowerConfig
from lerobot.common.utils.robot_utils import busy_wait


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Select and replay recorded SO100 motion from a menu"
    )
    parser.add_argument(
        "--port",
        type=str,
        default="/dev/tty.usbserial-1130",
        help="Follower arm serial port (default: /dev/tty.usbserial-1130)",
    )
    parser.add_argument(
        "--directory",
        type=str,
        default=".",
        help="Directory to search for .pkl files (default: current directory)",
    )
    parser.add_argument(
        "--no-calibrate",
        action="store_true",
        help="Skip calibration (use if already calibrated)",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Loop the selected replay continuously",
    )
    return parser.parse_args()


def find_pkl_files(directory):
    """Find all recording files in the specified directory.

    Args:
        directory: Directory path to search

    Returns:
        List of Path objects sorted by custom order (conf*, anx*, then others)
    """
    import re

    dir_path = Path(directory)
    recording_files = []

    for entry in dir_path.iterdir():
        if not entry.is_file():
            continue

        # Recordings saved without extension (e.g., anx6) should be included.
        if entry.suffix == ".pkl" or re.match(r"(?:anx|conf)\d+$", entry.name):
            recording_files.append(entry)

    def sort_key(file_path):
        """Custom sort key for conf/anx files."""
        filename = file_path.stem if file_path.suffix == ".pkl" else file_path.name

        # Match conf*
        conf_match = re.match(r'conf(\d+)', filename)
        if conf_match:
            num = int(conf_match.group(1))
            return (0, num)  # Group 0 = conf files

        # Match anx*
        anx_match = re.match(r'anx(\d+)', filename)
        if anx_match:
            num = int(anx_match.group(1))
            return (1, num)  # Group 1 = anx files

        # Other files come last, sorted alphabetically
        return (2, filename)

    recording_files.sort(key=sort_key)

    return recording_files


def load_recording_info(pkl_file):
    """Load basic info from a recording file without full validation.

    Args:
        pkl_file: Path to the pickle file

    Returns:
        Dictionary with basic info, or None if loading fails
    """
    try:
        with open(pkl_file, "rb") as f:
            data = pickle.load(f)
        return {
            "num_frames": data.get("num_frames", "?"),
            "duration": data.get("duration", 0),
            "fps": data.get("fps", "?"),
        }
    except Exception:
        return None


def display_menu(pkl_files):
    """Display a menu of available recordings.

    Args:
        pkl_files: List of Path objects for .pkl files

    Returns:
        Selected file index, or None if cancelled
    """
    print("\n" + "="*60)
    print("📁 利用可能な記録ファイル")
    print("="*60 + "\n")

    for idx, pkl_file in enumerate(pkl_files, 1):
        info = load_recording_info(pkl_file)
        if info:
            print(f"  [{idx}] {pkl_file.name}")
            print(f"      📊 {info['num_frames']} frames | "
                  f"⏱️  {info['duration']:.1f}s | "
                  f"🎬 {info['fps']} Hz")
        else:
            print(f"  [{idx}] {pkl_file.name} (読み込みエラー)")
        print()

    print("="*60)

    while True:
        try:
            choice = input(f"\n再生するファイルを選択してください [1-{len(pkl_files)}] (qで終了): ").strip()

            if choice.lower() == 'q':
                return None

            choice_num = int(choice)
            if 1 <= choice_num <= len(pkl_files):
                return choice_num - 1
            else:
                print(f"❌ 1から{len(pkl_files)}の間の数字を入力してください。")
        except ValueError:
            print("❌ 有効な数字を入力してください。")
        except KeyboardInterrupt:
            print("\n\n終了します。")
            return None


def load_recording(pkl_file):
    """Load recording from pickle file with validation.

    Args:
        pkl_file: Path to the pickle file

    Returns:
        Dictionary containing recording data

    Raises:
        ValueError: If the pickle file has invalid format
    """
    with open(pkl_file, "rb") as f:
        data = pickle.load(f)

    # Validate data format
    required_keys = ["fps", "frames", "num_frames"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Invalid recording file: missing '{key}'")

    print(f"\n✅ 読み込み完了: {pkl_file.name}")
    print(f"   フレーム数: {data['num_frames']}")
    print(f"   再生時間: {data.get('duration', 0):.2f}秒")
    print(f"   周波数: {data['fps']} Hz")

    return data


def replay_recording(follower, recording, loop_mode):
    """Replay the recording on the follower arm.

    Args:
        follower: Connected SO100Follower instance
        recording: Recording data dictionary
        loop_mode: Whether to loop continuously
    """
    fps = recording["fps"]
    frames = recording["frames"]

    replay_count = 0
    try:
        while True:
            replay_count += 1
            print(f"\n🎬 再生中 (iteration {replay_count})...")

            for idx, frame in enumerate(frames):
                loop_start = time.perf_counter()

                # Send action to follower
                action = frame["action"]
                follower.send_action(action)

                # Display progress every second
                if (idx + 1) % fps == 0:
                    progress = (idx + 1) / len(frames) * 100
                    print(f"   進捗: {idx + 1}/{len(frames)} frames ({progress:.1f}%)")

                # Maintain original timing
                dt_s = time.perf_counter() - loop_start
                busy_wait(1 / fps - dt_s)

            print(f"✅ 再生完了！")

            # Exit if not looping
            if not loop_mode:
                break

            # Brief pause between loops
            print("   ⏸️  2秒後に次のループを開始...")
            time.sleep(2)

    except KeyboardInterrupt:
        print(f"\n\n⏹️  再生を停止しました。")


def main():
    """Main function."""
    args = parse_args()

    # Find all .pkl files
    pkl_files = find_pkl_files(args.directory)

    if not pkl_files:
        print(f"\n❌ {args.directory} に .pkl ファイルが見つかりませんでした。")
        return

    # Display menu and get selection
    selected_idx = display_menu(pkl_files)

    if selected_idx is None:
        print("\n👋 終了します。")
        return

    selected_file = pkl_files[selected_idx]

    # Load recording
    try:
        recording = load_recording(selected_file)
    except Exception as e:
        print(f"\n❌ 記録の読み込みエラー: {e}")
        return

    # Initialize follower arm
    config = SO100FollowerConfig(port=args.port)
    follower = SO100Follower(config)

    try:
        # Connect to follower arm
        print(f"\n🔌 フォロワーアームに接続中 ({args.port})...")
        follower.connect(calibrate=not args.no_calibrate)
        print("✅ 接続成功！")

        # Replay
        replay_recording(follower, recording, args.loop)

    except Exception as e:
        print(f"\n❌ 再生エラー: {e}")
        raise

    finally:
        # Always disconnect
        if follower.is_connected:
            print("\n🔌 フォロワーアームを切断中...")
            follower.disconnect()
            print("✅ 切断完了")


if __name__ == "__main__":
    main()
