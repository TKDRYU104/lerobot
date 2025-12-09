#!/usr/bin/env python

"""
Replay all recorded motions in sequence.

This script finds all .pkl files in the specified directory and replays them
one by one on the follower arm. Useful for demonstrating multiple motions.

Usage:
    python replay_all.py
    python replay_all.py --directory recordings/
    python replay_all.py --pause 3 --no-calibrate
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
        description="Replay all recorded SO100 motions in sequence"
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
        "--pause",
        type=int,
        default=2,
        help="Pause duration between replays in seconds (default: 2)",
    )
    parser.add_argument(
        "--no-calibrate",
        action="store_true",
        help="Skip calibration (use if already calibrated)",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Loop through all files continuously",
    )
    return parser.parse_args()


def find_pkl_files(directory):
    """Find all .pkl files in the specified directory.

    Args:
        directory: Directory path to search

    Returns:
        List of Path objects for .pkl files, sorted by custom order (conf1-5, anx1-5, then others)
    """
    import re

    dir_path = Path(directory)
    pkl_files = list(dir_path.glob("*.pkl"))

    def sort_key(file_path):
        """Custom sort key for conf/anx files."""
        filename = file_path.stem  # Get filename without extension

        # Match conf1-5
        conf_match = re.match(r'conf(\d+)', filename)
        if conf_match:
            num = int(conf_match.group(1))
            return (0, num)  # Group 0 = conf files

        # Match anx1-5
        anx_match = re.match(r'anx(\d+)', filename)
        if anx_match:
            num = int(anx_match.group(1))
            return (1, num)  # Group 1 = anx files

        # Other files come last, sorted alphabetically
        return (2, filename)

    pkl_files.sort(key=sort_key)

    return pkl_files


def load_recording(pkl_file):
    """Load recording from pickle file with validation.

    Args:
        pkl_file: Path to the pickle file

    Returns:
        Dictionary containing recording data, or None if loading fails
    """
    try:
        with open(pkl_file, "rb") as f:
            data = pickle.load(f)

        # Validate data format
        required_keys = ["fps", "frames", "num_frames"]
        for key in required_keys:
            if key not in data:
                return None

        return data

    except Exception as e:
        print(f"   ⚠️  読み込みエラー: {e}")
        return None


def replay_recording(follower, recording, file_name):
    """Replay a single recording on the follower arm.

    Args:
        follower: Connected SO100Follower instance
        recording: Recording data dictionary
        file_name: Name of the file being replayed
    """
    fps = recording["fps"]
    frames = recording["frames"]

    print(f"   📊 {recording['num_frames']} frames | "
          f"⏱️  {recording.get('duration', 0):.1f}s | "
          f"🎬 {fps} Hz")

    try:
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

        print(f"   ✅ 完了")
        return True

    except Exception as e:
        print(f"   ❌ エラー: {e}")
        return False


def main():
    """Main function."""
    args = parse_args()

    # Find all .pkl files
    pkl_files = find_pkl_files(args.directory)

    if not pkl_files:
        print(f"\n❌ {args.directory} に .pkl ファイルが見つかりませんでした。")
        return

    print(f"\n📁 {len(pkl_files)} 個のファイルが見つかりました:")
    for idx, pkl_file in enumerate(pkl_files, 1):
        print(f"   {idx}. {pkl_file.name}")

    # Initialize follower arm
    config = SO100FollowerConfig(port=args.port)
    follower = SO100Follower(config)

    try:
        # Connect to follower arm
        print(f"\n🔌 フォロワーアームに接続中 ({args.port})...")
        follower.connect(calibrate=not args.no_calibrate)
        print("✅ 接続成功！\n")

        cycle_count = 0
        try:
            while True:
                cycle_count += 1
                if args.loop:
                    print(f"{'='*60}")
                    print(f"🔄 サイクル {cycle_count}")
                    print(f"{'='*60}\n")

                # Replay each file
                for idx, pkl_file in enumerate(pkl_files, 1):
                    print(f"🎬 [{idx}/{len(pkl_files)}] 再生中: {pkl_file.name}")

                    # Load recording
                    recording = load_recording(pkl_file)
                    if recording is None:
                        print(f"   ⏭️  スキップします\n")
                        continue

                    # Replay
                    success = replay_recording(follower, recording, pkl_file.name)

                    # Pause between replays (except after the last one if not looping)
                    if idx < len(pkl_files) or args.loop:
                        print(f"   ⏸️  {args.pause}秒待機中...\n")
                        time.sleep(args.pause)

                # Exit if not looping
                if not args.loop:
                    break

                print(f"\n{'='*60}")
                print(f"✅ サイクル {cycle_count} 完了！次のサイクルを開始します...")
                print(f"{'='*60}\n")

        except KeyboardInterrupt:
            print(f"\n\n⏹️  再生を停止しました。")

        print(f"\n🎉 全ての再生が完了しました！")

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        raise

    finally:
        # Always disconnect
        if follower.is_connected:
            print("\n🔌 フォロワーアームを切断中...")
            follower.disconnect()
            print("✅ 切断完了")


if __name__ == "__main__":
    main()
