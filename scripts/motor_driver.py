from gpiozero import PWMOutputDevice, DigitalOutputDevice
import time
import sys
import mpu6050
import pygame
import cv2
import numpy as np
from picamera2 import Picamera2
from computer_vision import process_frame
from mapper import LawnMowerMapping
import subprocess
import atexit
import threading
from camera_manager import CameraManager

camera_manager = CameraManager()
'''
# left motor
PWM1_PIN = 21  # Hardware PWM for speed
DIR1_PIN = 20  # Direction control

# right motor
PWM2_PIN = 6  # Hardware PWM for speed
DIR2_PIN = 5  # Direction control

# Blade motor
PWM3_PIN = 11
FORW = 9
REV = 10

ENCODER_LEFT_A = 7  # GPIO pin for left motor encoder A
ENCODER_LEFT_B = 8  # GPIO pin for left motor encoder B

ENCODER_RIGHT_A = 23  # GPIO pin for right motor encoder A
ENCODER_RIGHT_B = 24  # GPIO pin for right motor encoder B

IMU_SDA = 2 # GPIO Pin for imu SDA
IMU_SCL = 3 # GPUI Pin for imu SCL
'''

"""
# IMU SETUP
IMU = mpu6050.mpu6050(0x68)
IMU_SDA = 2 # GPIO Pin for imu SDA
IMU_SCL = 3 # GPUI Pin for imu SCL
alpha = 0.98
yaw = 0.0
last_time = time.time()"""

class MotorDriver:

    def __init__(self):

        self.pwm_left = PWMOutputDevice(21)  # Left motor PWM pin
        self.dir_left = DigitalOutputDevice(20)  # Left motor direction pin

        self.pwm_right = PWMOutputDevice(6)  # Right motor PWM pin
        self.dir_right = DigitalOutputDevice(5)  # Right motor direction pin

        self.pwm_blade = PWMOutputDevice(11)  # Blade motor PWM pin
        self.forw = DigitalOutputDevice(9)  # Blade motor forward pin
        self.rev = DigitalOutputDevice(10)  # Blade motor reverse pin

        # imu setup
        """self.imu = mpu6050.mpu6050(0x68)
        self.alpha = 0.98
        self.yaw = 0.0
        self.last_time = time.time()
        self.gyro_bias_z = 0
        self.calibrate_gyro()
"""
        

    def calibrate_gyro(self, samples=100):
        bias = 0
        for _ in range(samples):
            bias += self.imu.get_gyro_data()['z']
            time.sleep(0.01)  # adjust based on your loop speed
        self.gyro_bias_z = bias / samples

    def read_imu(self):
        accelerometer_data = self.imu.get_accel_data()
        gyroscope_data = self.imu.get_gyro_data()
        temperature = self.imu.get_temp()
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        corrected_gyro_z = gyroscope_data['z'] - self.gyro_bias_z
        self.yaw += corrected_gyro_z*dt
        return self.yaw

    def set_motor(self, left_speed, right_speed):
        """
        Sets the speed and direction of the left and right motors.
        :param left_speed: Speed from -1 (full reverse) to 1 (full forward).
        :param right_speed: Speed from -1 (full reverse) to 1 (full forward).
        """
        self.dir_left.on() if left_speed > 0 else self.dir_left.off()
        self.pwm_left.value = abs(left_speed)

        self.dir_right.on() if right_speed > 0 else self.dir_right.off()
        self.pwm_right.value = abs(right_speed)
        
    def set_blade(self, blade_speed):
        """
        Controls the blade motor speed and direction.
        :param blade_speed: Speed from -1 (full reverse) to 1 (full forward).
        """
        if blade_speed > 0:
            self.forw.on()
            self.rev.off()
            self.pwm_blade.value = abs(blade_speed)
        elif blade_speed < 0:
            self.forw.off()
            self.rev.on()
            self.pwm_blade.value = abs(blade_speed)
        else:
            self.forw.off()
            self.rev.off()
            self.pwm_blade.value = 0

    def stop_motors(self):
        '''Stop all motors'''
        self.set_motor(0, 0)
        self.set_blade(0)

def launch_rtk_loop():
    global mapper_process

    while True:
        print("Launching mapper process...")
        mapper_process = subprocess.Popen([
            "python", "mapper.py"
        ])
        mapper_process.wait()  # Wait for it to exit
        print("RTK process exited. Restarting in 5 seconds...")
        time.sleep(5)  # Wait a bit before restarting

def cleanup():
    print("Cleaning up... Terminating RTK process (if running).")
    try:
        if mapper_process.poll() is None:
            mapper_process.terminate()
            mapper_process.wait(timeout=5)
            print("RTK process terminated cleanly.")
    except Exception as e:
        print(f"Could not terminate RTK process: {e}")


atexit.register(cleanup)

if __name__ == "__main__":
    ...


        