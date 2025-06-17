import argparse
import time
import csv
from so100_interface import SO100Leader

parser = argparse.ArgumentParser()
parser.add_argument('--port', required=True)
parser.add_argument('--duration', type=float, default=10)
parser.add_argument('--output', required=True)
args = parser.parse_args()

robot = SO100Leader(args.port)
recorded_data = []

print("[Recording] Move the robot for {:.1f} seconds...".format(args.duration))
start = time.time()
while time.time() - start < args.duration:
    t = time.time() - start
    angles = robot.get_angles()
    recorded_data.append([t] + angles)
    time.sleep(0.1)

with open(args.output, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["time"] + [f"joint{i+1}" for i in range(len(recorded_data[0])-1)])
    writer.writerows(recorded_data)

print("[Done] Motion saved to", args.output)
