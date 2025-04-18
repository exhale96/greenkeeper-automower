from gpiozero import PWMOutputDevice, DigitalOutputDevice, Button, Device
import time
import sys
import mpu6050
#import pygame
#import cv2
import numpy as np
#from picamera2 import Picamera2
#from computer_vision import process_frame
#from mapper import LawnMowerMapping
#from camera_manager import CameraManager
from threading import Lock


"""
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




# IMU SETUP
IMU = mpu6050.mpu6050(0x68)
IMU_SDA = 2 # GPIO Pin for imu SDA
IMU_SCL = 3 # GPUI Pin for imu SCL
alpha = 0.98
yaw = 0.0
last_time = time.time()
"""

class Encoder:
    def __init__(self, pin_a, pin_b=None, ticks_per_revolution=374):
        self.pin_a = Button(pin_a, pull_up=True)  # Use bounce_time to avoid multiple counts
        self.pin_b = Button(pin_b, pull_up=True) if pin_b is not None else None
        self.ticks = 0
        self.lock = Lock()
        self.last_time = time.time()
        self.last_tick_count = 0
        self.ticks_per_revolution = ticks_per_revolution

        self.pin_a.when_pressed = self._increment

    def _increment(self):
        with self.lock:
            self.ticks += 1

    def reset(self):
        with self.lock:
            self.ticks = 0
            self.last_tick_count = 0
            self.last_time = time.time()

    def get_ticks(self):
        with self.lock:
            return self.ticks

    def get_rpm(self):
        with self.lock:
            now = time.time()
            dt = now - self.last_time
            if dt == 0:
                return 0.0
            tick_diff = self.ticks - self.last_tick_count
            self.last_tick_count = self.ticks
            self.last_time = now
        revolutions_per_sec = tick_diff / self.ticks_per_revolution / dt
        return revolutions_per_sec * 60  # convert to RPM
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
        self.imu = mpu6050.mpu6050(0x68)
        self.alpha = 0.98
        self.yaw = 0.0
        self.last_time = time.time()
        self.gyro_bias_z = 0
        self.calibrate_gyro()

        ENCODER_LEFT_A = 7  # GPIO pin for left motor encoder A
        ENCODER_LEFT_B = 8  # GPIO pin for left motor encoder B

        ENCODER_RIGHT_A = 23  # GPIO pin for right motor encoder A
        ENCODER_RIGHT_B = 24  # GPIO pin for right motor encoder B
                # encoder setup
        self.left_encoder = Encoder(ENCODER_LEFT_A, ENCODER_LEFT_B)
        self.right_encoder = Encoder(ENCODER_RIGHT_A, ENCODER_RIGHT_B)


        

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
        self.yaw = self.yaw % 360  # Normalize
        return self.yaw

    def get_wheel_speeds(self):
        left_rpm = self.left_encoder.get_rpm()
        right_rpm = self.right_encoder.get_rpm()
        return left_rpm, right_rpm

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

    def move_forward_with_heading(self, target_angle):
        current_angle = self.read_imu()
        error = ((current_angle - target_angle + 180) % 360) - 180
        base_speed = 0.3
        correction = 0.075

        if abs(error) <= 1:
            self.set_motor(-base_speed, -base_speed)
        elif error > 1:
            self.set_motor(-base_speed, -base_speed + correction)
        else:
            self.set_motor(-base_speed + correction, -base_speed)

    def move_backward_with_heading(self, target_angle):
        current_angle = self.read_imu()
        error = ((current_angle - target_angle + 180) % 360) - 180
        base_speed = -0.3
        correction = 0.1

        if abs(error) <= 3:
            self.set_motor(base_speed, base_speed)
        elif error > 3:
            self.set_motor(base_speed + correction, base_speed - correction)
        else:
            self.set_motor(base_speed - correction, base_speed + correction)

    def turn_left(self, angle=90):
        
        start_angle = self.read_imu()
        target_angle = (start_angle + angle) % 360
        print(f"Starting angle: {start_angle}")
        print(f"Target angle: {target_angle}")
        while True:
            current_angle = self.read_imu()
            diff = ((current_angle - target_angle + 180) % 360) - 180
            print(f"Current angle: {current_angle}")
            print(f"Difference: {diff}")
            if abs(diff) <= 3:
                self.stop_motors()
                break
            self.set_motor(0, 0.1)
            time.sleep(0.1)

    def turn_right(self, angle=90):
        start_angle = self.read_imu()
        target_angle = (start_angle - angle) % 360
        print(f"Starting angle: {start_angle}")
        print(f"Target angle: {target_angle}")
        while True:
            current_angle = self.read_imu()
            diff = ((current_angle - target_angle + 180) % 360) - 180
            print(f"Current angle: {current_angle}")
            print(f"Difference: {diff}")
            if abs(diff) <= 3:
                self.stop_motors()
                break
            self.set_motor(0.1, 0)
            time.sleep(0.1)


if __name__ == "__main__":
    driver = MotorDriver()

    """
    RUN_TIME_SEC = 5
    print(f"Running motors at 10% speed for {RUN_TIME_SEC} seconds...")
    driver.set_motor(0.1, 0.1)

    start_time = time.time()
    try:
        while time.time() - start_time < RUN_TIME_SEC:
            left_rpm, right_rpm = driver.get_wheel_speeds()
            print(f"Left RPM: {left_rpm:.2f}, Right RPM: {right_rpm:.2f}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Interrupted.")

    driver.stop_motors()
    print("Motors stopped.")"""

    # print("Testing IMU-based right turn...")
    # driver.turn_right_to_90()
    # time.sleep(1)

    # print("Testing IMU-based forward movement again...")
    # for _ in range(20):
    #     driver.move_forward_with_heading(initial_angle)
    #     time.sleep(0.1)
    # driver.stop_motors()
    # time.sleep(1)
    # driver.stop_motors()
    



    """
    print("Testing IMU-based right turn...")
    driver.turn_right_to_90()
    time.sleep(2)
    """

    #driver.stop_motors()
    #time.sleep(2)

    # print("IMU test sequence complete.")


        