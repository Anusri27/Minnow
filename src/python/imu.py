#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import zmq
import time
import math
import signal
from collections import deque
from threading import Thread
import flatbuffers
#generated by flatc
import topics.nav.imu
#IMU-specific scripts
from em7180 import EM7180_Master

class Publisher:
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_signal)
        self.data_queue = deque(maxlen=1)
        self.zmq_context = zmq.Context()
        #setup IMU
        self.MAG_RATE       = 100  # Hz
        self.ACCEL_RATE     = 200  # Hz
        self.GYRO_RATE      = 200  # Hz
        self.BARO_RATE      = 50   # Hz
        self.Q_RATE_DIVISOR = 3    # 1/3 gyro rate
        self.em7180 = EM7180_Master(MAG_RATE, ACCEL_RATE, GYRO_RATE, BARO_RATE, Q_RATE_DIVISOR)
        if not self.em7180.begin():
            print('IMU initialization error!')
            print(self.em7180.getErrorString())
            exit(1)

    def exit_signal(self, sig, frame):
        print('You pressed Ctrl+C!')
        sys.exit(0)

    def run(self):
        socket = self.zmq_context.socket(zmq.PUB)
        socket.connect("tcp://127.0.0.1:5556")

        count = 0
        while True:
            count += 1

            self.em7180.checkEventStatus()

            if self.em7180.gotError():
                print('IMU runtime error: ' + self.em7180.getErrorString())
                exit(1)

            if (self.em7180.gotQuaternion()):
                qw, qx, qy, qz = self.em7180.readQuaternion()
                roll  = math.atan2(2.0 * (qw * qx + qy * qz), qw * qw - qx * qx - qy * qy + qz * qz)
                pitch = -math.asin(2.0 * (qx * qz - qw * qy))
                yaw   = math.atan2(2.0 * (qx * qy + qw * qz), qw * qw + qx * qx - qy * qy - qz * qz)

                pitch *= 180.0 / math.pi
                yaw   *= 180.0 / math.pi
                yaw   += 13.8 # Declination at Danville, California is 13 degrees 48 minutes and 47 seconds on 2014-04-04
                if yaw < 0: yaw   += 360.0  # Ensure yaw stays between 0 and 360
                roll  *= 180.0 / math.pi
                print('roll, pitch, yaw: {}'.format(roll,pitch,yaw))

            if self.em7180.gotAccelerometer():
                ax,ay,az = self.em7180.readAccelerometer()
                print('accel: {}'.format(ax,ay,az))

            if self.em7180.gotGyrometer():
                gx,gy,gz = self.em7180.readGyrometer()
                print('gyro: {}'.format(gx,gy,gz))

            if self.em7180.gotBarometer():
                pressure, temperature = self.em7180.readBarometer()
                print('baro:')
                print('  temperature: {}'.format(temperature))
                print('  temperature: {} mbar'.format(pressure))

            time.sleep(.001)

if __name__ == "__main__":
    pub = Publisher()
    pub.run()
