import serial

class SO100Base:
    def __init__(self, port):
        self.ser = serial.Serial(port, baudrate=115200, timeout=0.1)
    def close(self):
        self.ser.close()

class SO100Leader(SO100Base):
    def get_angles(self):
        self.ser.write(b'GET_ANGLES\n')
        line = self.ser.readline().decode().strip()
        # `1,23.5,45.0,...` のフォーマットを想定
        parts = line.split(',')
        return [float(x) for x in parts]  # 関節角度リスト

class SO100Follower(SO100Base):
    def send_angles(self, angles, speed=50):
        cmd = 'SET_ANGLES,' + ','.join(f'{a:.2f}' for a in angles) + f',SPEED,{speed}\n'
        self.ser.write(cmd.encode())