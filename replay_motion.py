#!/usr/bin/env python

"""
Replay recorded SO100 motion on follower arm.

This script loads a pickle file containing recorded motion data and replays it
on an SO100 follower arm, maintaining the original timing and joint positions.

Usage:
    python replay_motion.py --input recorded_motion.pkl
    python replay_motion.py --input my_motion.pkl --port /dev/tty.usbserial-1130
    python replay_motion.py --input my_motion.pkl --loop --no-calibrate
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
        description="Replay recorded SO100 motion on follower arm"
    )
    parser.add_argument(
        "--port",
        type=str,
        default="/dev/tty.usbserial-1130",
        help="Follower arm serial port (default: /dev/tty.usbserial-1130)",
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input pickle file path containing recorded motion",
    )
    parser.add_argument(
        "--no-calibrate",
        action="store_true",
        help="Skip calibration (use if already calibrated)",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Loop the replay continuously",
    )
    return parser.parse_args()


def load_recording(input_path):
    """Load recording from pickle file.

    Args:
        input_path: Path to the pickle file

    Returns:
        Dictionary containing recording data

    Raises:
        FileNotFoundError: If the input file doesn't exist
        ValueError: If the pickle file has invalid format
    """
    input_file = Path(input_path)

    if not input_file.exists():
        raise FileNotFoundError(f"Recording file not found: {input_file}")

    with open(input_file, "rb") as f:
        data = pickle.load(f)

    # Validate data format
    required_keys = ["fps", "frames", "num_frames"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Invalid recording file: missing '{key}'")

    print(f"\nLoaded recording from {input_file}")
    print(f"Frames: {data['num_frames']}")
    print(f"Duration: {data.get('duration', 0):.2f}s")
    print(f"FPS: {data['fps']}")
    print(f"Motors: {', '.join(data.get('motor_names', []))}")

    return data


def main():
    """Main replay function."""
    args = parse_args()

    # Load recording
    try:
        recording = load_recording(args.input)
    except Exception as e:
        print(f"Error loading recording: {e}")
        return

    # Initialize follower arm
    config = SO100FollowerConfig(port=args.port)
    follower = SO100Follower(config)

    try:
        # Connect to follower arm
        print(f"\nConnecting to follower arm on {args.port}...")
        follower.connect(calibrate=not args.no_calibrate)
        print("Connected successfully!")

        fps = recording["fps"]
        frames = recording["frames"]

        # Replay loop
        replay_count = 0
        while True:
            replay_count += 1
            print(f"\nReplaying motion (iteration {replay_count})...")

            for idx, frame in enumerate(frames):
                loop_start = time.perf_counter()

                # Send action to follower
                action = frame["action"]
                follower.send_action(action)

                # Display progress every second
                if (idx + 1) % fps == 0:
                    progress = (idx + 1) / len(frames) * 100
                    print(f"Progress: {idx + 1}/{len(frames)} frames ({progress:.1f}%)")

                # Maintain original timing
                dt_s = time.perf_counter() - loop_start
                busy_wait(1 / fps - dt_s)

            print(f"Replay complete!")

            # Exit if not looping
            if not args.loop:
                break

            # Brief pause between loops
            print("Pausing 2 seconds before next loop...")
            time.sleep(2)

    except KeyboardInterrupt:
        print(f"\n\nReplay stopped by user.")

    except Exception as e:
        print(f"\nError during replay: {e}")
        raise

    finally:
        # Always disconnect
        if follower.is_connected:
            print("Disconnecting follower arm...")
            follower.disconnect()


if __name__ == "__main__":
    main()
