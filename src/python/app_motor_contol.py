#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
import zmq
import time
# minnow comms
from minnow_comms.minnow_app_threaded import App
# flatbuffer serialization
import flatbuffers
# generated by flatc
import topics.nav.imu
import topics.motor.command
# motor control library
from minnow_motor_control.HeadingControl import *
from minnow_motor_control.SurgeSpeedControl import *
from minnow_motor_control.PitchControl import *

class MotorControl(App):
    def __init__(self):
        super().__init__()
        self.setup_subscribers()
        # setup flatbuffers
        self.fb_builder = flatbuffers.Builder(1024)
        # setup motor controllers
        self.speed_control_system = speed_controller()
        self.heading_control_system = heading_controller()
        self.pitch_control_system = pitch_controller()
        # variables
        self.nav_imu_msg = None

        # This is for standalone troubleshooting of the python code ---------------------
        self.desired_speed = 0.0
        self.desired_heading = 280     # between 0 - 360
        self.desired_pitch = 0.0       # Pitch down is positive

        self.current_speed = 0.0
        self.current_heading = 120
        self.current_pitch = 0.0
        # -------------------------------------------------------------------------------

        # Setting desired heading, speed, pitch and depth
        self.heading_control_system.DesiredHeading(self.desired_heading) # this should be called only when desired heading is altered
        self.pitch_control_system.DesiredPitch(self.desired_pitch) # this should be called only when desired heading is altered

    def setup_subscribers(self):
        self.subscribe('nav.imu', self.nav_imu_callback)    # subscribe to imu messages

    def nav_imu_callback(self, msg):
        self.nav_imu_msg = topics.nav.imu.imu.GetRootAsimu(msg, 0)

    def process(self):
        if self.nav_imu_msg is not None:
            self.current_heading = self.nav_imu_msg.Yaw()
            self.current_pitch = self.nav_imu_msg.Pitch()
            print('current hdg',self.current_heading)
            print('current pitch',self.current_pitch)

        # Run speed controller
        (speed_contrl_thrust)=self.speed_control_system.update(self.desired_speed)
        print("Lower thrust after speed controller: %f" % speed_contrl_thrust)

        # Run pitch controller
        (pitch_mixed_speed_thrust,upper_thrust)=self.pitch_control_system.update(self.current_pitch,speed_contrl_thrust)
        print("Lower thrust after pitch controller: %f" % pitch_mixed_speed_thrust)

        # Run heading controller
        (hdg_port_thrust,hdg_stbd_thrust)=self.heading_control_system.update(self.current_heading,pitch_mixed_speed_thrust)
        
        #print(hdg_differential_thrust)
        print("Heading control port thrust: %f" % hdg_port_thrust)
        print("Heading control stbd thrust: %f" % hdg_stbd_thrust)
        print("Pitch control Upper thrust: %f" % upper_thrust)
        print('')

        topics.motor.command.commandStart(self.fb_builder)
        topics.motor.command.commandAddTime(self.fb_builder, time.time())
        topics.motor.command.commandAddMotor1Command(self.fb_builder, hdg_port_thrust)
        topics.motor.command.commandAddMotor2Command(self.fb_builder, hdg_stbd_thrust)
        topics.motor.command.commandAddMotor3Command(self.fb_builder, -1*upper_thrust)
        motor_msg = topics.motor.command.commandEnd(self.fb_builder)
        self.fb_builder.Finish(motor_msg)
        bin_motor_msg = self.fb_builder.Output()
        self.publish(b'motor.command' + b' ' + bin_motor_msg)

        time.sleep(0.1)

if __name__ == "__main__":
    app = MotorControl()
    app.run()
