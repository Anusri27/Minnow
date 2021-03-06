#!/usr/bin/env python
import time
import math
import numpy as np
from minnow_low_level_control.controlconfig import * 

class heading_controller:
    def __init__(self, prev_hdg_error=0, hdg_error_integral=0):
        self.hdg_kp = config_hdg_kp
        self.hdg_ki = config_hdg_ki
        self.hdg_kd = config_hdg_kd
        self.max_hdg_error_integral=config_max_hdg_error_integral
        
        self.prev_hdg_error=prev_hdg_error
        self.hdg_error_integral=hdg_error_integral
        self.desired_heading=0.0
        self.error=0.0
    
    def update(self,current_heading,speed_thrust):
        self.hdg_error = self.desired_heading - current_heading
        print('control heading',current_heading)
        print('desired heading',self.desired_heading)
        # if abs(self.hdg_error) > 180:
        # 	self.hdg_error = -self.hdg_error
        
        # Setting the integral of the error
        self.hdg_error_integral = self.hdg_error_integral + self.hdg_error
        if self.hdg_error_integral > self.max_hdg_error_integral:
            self.hdg_error_integral = self.max_hdg_error_integral
        if self.hdg_error_integral < -self.max_hdg_error_integral:
            self.hdg_error_integral = -self.max_hdg_error_integral
        
        hdg_p_value = self.hdg_kp * self.hdg_error
        hdg_i_value = self.hdg_ki * (self.hdg_error_integral)
        hdg_d_value = self.hdg_kd * (self.hdg_error - self.prev_hdg_error)
        hdg_differential_thrust = hdg_p_value + hdg_i_value + hdg_d_value
        
        # mixing speed thrust and diff thrust
        print(hdg_differential_thrust)
        hdg_port_thrust = speed_thrust + 0.5 *hdg_differential_thrust
        hdg_stbd_thrust = speed_thrust - 0.5 *hdg_differential_thrust
        print(hdg_port_thrust, hdg_stbd_thrust)
        if (speed_thrust + 0.5 *hdg_differential_thrust) > config_max_motor_thrust:
            hdg_differential_thrust_correction = (speed_thrust + 0.5 *hdg_differential_thrust) - config_max_motor_thrust
            # print(hdg_differential_thrust_correction)
            hdg_port_thrust = hdg_port_thrust - hdg_differential_thrust_correction
            hdg_stbd_thrust = hdg_stbd_thrust - hdg_differential_thrust_correction
        
        #elif (speed_thrust + 0.5 *hdg_differential_thrust) < config_min_motor_thrust:
            #hdg_differential_thrust_correction = (speed_thrust + 0.5 *hdg_differential_thrust) - config_min_motor_thrust
            # print(hdg_differential_thrust_correction)
            #hdg_port_thrust = hdg_port_thrust - hdg_differential_thrust_correction
            #hdg_stbd_thrust = hdg_stbd_thrust - hdg_differential_thrust_correction
        
        # motor safelty limits
        if hdg_port_thrust > config_max_motor_thrust:
            hdg_port_thrust = config_max_motor_thrust
        if hdg_stbd_thrust > config_max_motor_thrust:
            hdg_stbd_thrust = config_max_motor_thrust
        if hdg_port_thrust < config_min_motor_thrust:
            hdg_port_thrust = config_min_motor_thrust
        if hdg_stbd_thrust < config_min_motor_thrust:
            hdg_stbd_thrust = config_min_motor_thrust
            
        # For error deravative 
        self.prev_hdg_error = self.hdg_error
        
        return(hdg_differential_thrust,hdg_port_thrust,hdg_stbd_thrust)
    
    def DesiredHeading(self,desired_heading):
        self.desired_heading = desired_heading
        self.hdg_error_integral=0
        self.prev_hdg_error=0








	# print(speed_controller.speed_contrl_port_thrust)






hdg_contrl_port_thrust = 50
hdg_contrl_port_thrust = 0
