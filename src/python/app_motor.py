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
import topics.motor.command
import topics.motor.value
# PWM library
from Adafruit_BBIO import PWM

class Motor(App):
    def __init__(self):
        super().__init__()
        self.setup_subscribers()
        # setup flatbuffers
        self.fb_builder = flatbuffers.Builder(1024)
        # variables
        self.motor_command_msg = None
        self.motor_1_command = 0.0
        self.motor_2_command = 0.0
        self.motor_3_command = 0.0
        #setup motors
        self.pwm_freq = 8000.0                                                  #8000 Hz max for BlueRobotics ESC
        self.pwm_stop = 1500                                                    #motor esc stops at 1500 microseconds
        PWM.start("P9_21", self.pwm_stop/(1e6/self.pwm_freq), self.pwm_freq)    #motor 1 beaglebone PWM pin
        PWM.start("P9_22", self.pwm_stop/(1e6/self.pwm_freq), self.pwm_freq)    #motor 2 beaglebone PWM pin
        PWM.start("P9_16", self.pwm_stop/(1e6/self.pwm_freq), self.pwm_freq)    #motor 3 beaglebone PWM pin
        #check BlueRobotics website for current draw - https://bluerobotics.com/store/thrusters/t100-t200-thrusters/t200-thruster/
        #limit ourselves to ~6.5A
        self.pwm_min = 1275                                                     #max reverse microseconds pwm value
        self.pwm_max = 1725                                                     #max forward microseconds pwm value
        self.pwm_deadband = 40                                                  #deadband around 1500 microseconds of 40 microseconds
        self.command_min = -80.0
        self.command_max = 80.0
        self.command_deadband = 2.0
        time.sleep(10.0)

    def setup_subscribers(self):
        self.subscribe('motor.command', self.motor_command_callback)    # subscribe to motor command messages

    def motor_command_callback(self, msg):
        self.motor_command_msg = topics.motor.command.command.GetRootAscommand(msg, 0)
        self.motor_1_command = self.motor_command_msg.Motor1Command()
        self.motor_2_command = self.motor_command_msg.Motor2Command()
        self.motor_3_command = self.motor_command_msg.Motor3Command()

    def exit_signal(self, sig, frame):
        print('You pressed Ctrl+C!')
        PWM.stop("P9_21")
        PWM.stop("P9_22")
        PWM.stop("P9_16")
        PWM.cleanup()
        super().exit_signal()

    def map_command_to_pwm(self, command):
        if abs(command) <= self.command_deadband:                               #stop vehicle if command is within command deadband
            return self.pwm_stop/(1e6/self.pwm_freq)
        else:
            command_scale = (command - self.command_min)/(self.command_max - self.command_min)
            min_val = self.pwm_min/(1e6/self.pwm_freq)
            max_val = self.pwm_max/(1e6/self.pwm_freq)
            pwm_val = command_scale*(max_val - min_val) + min_val
            pwm_val_us = pwm_val*(1e6/self.pwm_freq)
            if abs(pwm_val_us - self.pwm_stop) <= self.pwm_deadband:            #if pwm mapping is within pwm deadband, push outside pwm deadband
                if abs(pwm_val_us - (self.pwm_stop - self.pwm_deadband)) < abs(pwm_val_us - (self.pwm_stop + self.pwm_deadband)):
                    pwm_val = (self.pwm_stop-40)/(1e6/self.pwm_freq)
                else:
                    pwm_val = (self.pwm_stop+40)/(1e6/self.pwm_freq)
            return pwm_val

    def process(self):
        # limit motor commands and map to pwm values
        if self.motor_1_command < self.command_min:
            self.motor_1_command = self.command_min
        if self.motor_1_command > self.command_max:
            self.motor_1_command = self.command_max
        motor_1_pwm = self.map_command_to_pwm(self.motor_1_command)
        if self.motor_2_command < self.command_min:
            self.motor_2_command = self.command_min
        if self.motor_2_command > self.command_max:
            self.motor_2_command = self.command_max
        motor_2_pwm = self.map_command_to_pwm(self.motor_2_command)
        if self.motor_3_command < self.command_min:
            self.motor_3_command = self.command_min
        if self.motor_3_command > self.command_max:
            self.motor_3_command = self.command_max
        motor_3_pwm = self.map_command_to_pwm(self.motor_3_command)
        #set duty cycles
        PWM.set_duty_cycle("P9_21", motor_1_pwm)
        PWM.set_duty_cycle("P9_22", motor_2_pwm)
        PWM.set_duty_cycle("P9_16", motor_3_pwm)

        topics.motor.value.valueStart(self.fb_builder)
        topics.motor.value.valueAddTime(self.fb_builder, time.time())
        topics.motor.value.valueAddMotor1Value(self.fb_builder, motor_1_pwm)
        topics.motor.value.valueAddMotor2Value(self.fb_builder, motor_2_pwm)
        topics.motor.value.valueAddMotor3Value(self.fb_builder, motor_3_pwm)

        print('Motor 1 value: {:6.3f}'.format(motor_1_pwm))
        print('Motor 2 value: {:6.3f}'.format(motor_2_pwm))
        print('Motor 3 value: {:6.3f}'.format(motor_3_pwm))
        print('')

        value_msg = topics.motor.value.valueEnd(self.fb_builder)
        self.fb_builder.Finish(value_msg)
        bin_value_msg = self.fb_builder.Output()
        self.publish(b'motor.value' + b' ' + bin_value_msg)

        time.sleep(0.01)

if __name__ == "__main__":
    app = Motor()
    app.run()
