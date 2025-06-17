import argparse
import time
import csv
from so100_interface import SO100Follower

parser = argparse.ArgumentParser()
parser.add_argument('--port', required=True)
parser.add_argument('--input', required=True)
parser.add_argument('--speed', type=int, default=50)
args = parser.parse_args()

robot = SO100Follower(args.port)

with open(args.input, 'r') as f:
    reader = csv.reader(f)
    header = next(reader)
    data = [list(map(float, row)) for row in reader]

print("[Playback] Playing motion from", args.input)
start_time = time.time()
for t, *angles in data:
    now = time.time() - start_time
    delay = t - now
    if delay > 0:
        time.sleep(delay)
    robot.send_angles(angles, speed=args.speed)

print("[Done] Motion playback complete")