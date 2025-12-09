#!/usr/bin/env python

"""
Record SO100 motion with teleoperation (leader to follower).

This script connects to both SO100 leader and follower arms, allows you to move
the leader arm while the follower arm follows in real-time, and records the motion
data to a pickle file for later replay.

Usage:
    python record_with_teleop.py --output my_motion.pkl
    python record_with_teleop.py --leader-port /dev/tty.usbserial-1110 --follower-port /dev/tty.usbserial-1130
    python record_with_teleop.py --fps 60 --no-calibrate
"""

import argparse
import pickle
import time
from pathlib import Path

from lerobot.common.robots.so100_follower import SO100Follower
from lerobot.common.robots.so100_follower.config_so100_follower import SO100FollowerConfig
from lerobot.common.teleoperators.so100_leader import SO100Leader
from lerobot.common.teleoperators.so100_leader.config_so100_leader import SO100LeaderConfig
from lerobot.common.utils.robot_utils import busy_wait


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Record SO100 motion with real-time teleoperation"
    )
    parser.add_argument(
        "--leader-port",
        type=str,
        default="/dev/tty.usbserial-1110",
        help="Leader arm serial port (default: /dev/tty.usbserial-1110)",
    )
    parser.add_argument(
        "--follower-port",
        type=str,
        default="/dev/tty.usbserial-1130",
        help="Follower arm serial port (default: /dev/tty.usbserial-1130)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="recorded_motion.pkl",
        help="Output pickle file path (default: recorded_motion.pkl)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Recording frequency in Hz (default: 30)",
    )
    parser.add_argument(
        "--no-calibrate",
        action="store_true",
        help="Skip calibration (use if already calibrated)",
    )
    return parser.parse_args()


def save_recording(frames, output_path, fps):
    """Save recorded frames to pickle file.

    Args:
        frames: List of frame dictionaries containing timestamp and action
        output_path: Path to save the pickle file
        fps: Recording frequency in Hz
    """
    data = {
        "fps": fps,
        "frames": frames,
        "num_frames": len(frames),
        "duration": frames[-1]["timestamp"] if frames else 0,
        "motor_names": list(frames[0]["action"].keys()) if frames else [],
    }

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "wb") as f:
        pickle.dump(data, f)

    print(f"\nRecording saved to {output_file}")
    print(f"Total frames: {data['num_frames']}")
    print(f"Duration: {data['duration']:.2f}s")
    print(f"Motors: {', '.join(data['motor_names'])}")


def main():
    """Main recording with teleoperation function."""
    args = parse_args()

    # Initialize leader and follower arms
    leader_config = SO100LeaderConfig(port=args.leader_port)
    leader = SO100Leader(leader_config)

    follower_config = SO100FollowerConfig(port=args.follower_port)
    follower = SO100Follower(follower_config)

    # Data storage
    frames = []

    try:
        # Connect to leader arm
        print(f"Connecting to leader arm on {args.leader_port}...")
        leader.connect(calibrate=not args.no_calibrate)
        print("Leader arm connected successfully!")

        # Connect to follower arm
        print(f"Connecting to follower arm on {args.follower_port}...")
        follower.connect(calibrate=not args.no_calibrate)
        print("Follower arm connected successfully!")

        print(f"\nRecording at {args.fps} Hz with real-time teleoperation.")
        print("Move the leader arm and watch the follower follow!")
        print("Press Ctrl+C to stop.\n")

        start_time = time.perf_counter()
        frame_count = 0

        while True:
            loop_start = time.perf_counter()

            # Read leader position
            action = leader.get_action()

            # Send to follower (teleoperation)
            follower.send_action(action)

            # Store frame data for recording
            timestamp = time.perf_counter() - start_time
            frames.append({"timestamp": timestamp, "action": action})

            frame_count += 1

            # Display progress every second
            if frame_count % args.fps == 0:
                print(f"Recorded {frame_count} frames ({timestamp:.1f}s)")

            # Maintain timing
            dt_s = time.perf_counter() - loop_start
            busy_wait(1 / args.fps - dt_s)

    except KeyboardInterrupt:
        print(f"\n\nRecording stopped by user.")

    except Exception as e:
        print(f"\nError during recording: {e}")
        raise

    finally:
        # Always disconnect both arms
        if leader.is_connected:
            print("Disconnecting leader arm...")
            leader.disconnect()

        if follower.is_connected:
            print("Disconnecting follower arm...")
            follower.disconnect()

        # Save data if any frames were recorded
        if frames:
            save_recording(frames, args.output, args.fps)
        else:
            print("No frames recorded.")


if __name__ == "__main__":
    main()
