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

# def cleanup():
#     print("Cleaning up... Terminating RTK process.")
#     map_process.terminate()
#     try:
#         map_process.wait(timeout=5)
#     except subprocess.TimeoutExpired:
#         print("Force killing RTK process.")
#         map_process.kill()

# atexit.register(cleanup)

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
    rtk_thread = threading.Thread(target=launch_rtk_loop, daemon=True)
    rtk_thread.start()





if __name__ == "__main__":
    imgsz = 640 # Declares
    pygame.init() #init pygame for arrow-key robot control
    screen = pygame.display.set_mode((imgsz,imgsz))  # Window size
    pygame.display.set_caption("Test Pygame Window")

    motor_driver = MotorDriver()
    speed = 0.5
    blade_speed = 0.3

    rtk_thread = threading.Thread(target=launch_rtk_loop, daemon=True)
    rtk_thread.start()



    ## RC Mode Control Loop ##
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                motor_driver.stop_motors()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    print("Up Arrow Pressed: Move Forward")
                    print("Speed: ", speed)
                    motor_driver.set_motor(-speed, -speed*0.93)
                elif event.key == pygame.K_DOWN:
                    print("Down Arrow Pressed: Move Backward")
                    motor_driver.set_motor(speed, speed)
                elif event.key == pygame.K_LEFT:
                    print("Left Arrow Pressed: Turn Left")
                    motor_driver.set_motor(0, speed)
                elif event.key == pygame.K_RIGHT:
                    print("Right Arrow Pressed: Turn Right")
                    motor_driver.set_motor(speed, 0)
                elif event.key == pygame.K_0:
                    motor_driver.set_blade(blade_speed)
                    print("0 pressed: Activating Blade Motor")
                elif event.key == pygame.K_ESCAPE:
                    motor_driver.stop_motors()
                    pygame.quit()
                    sys.exit()

            elif event.type == pygame.KEYUP:
                if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT,pygame.K_0]:
                    print("Key Released: Stop Motors")
                    motor_driver.stop_motors()

        ##          ##
        annotated_frame, fps = process_frame()
        frame_rotated = np.rot90(annotated_frame, k=-1)
        frame_flipped = cv2.flip(frame_rotated, 1)
        frame_surface = pygame.surfarray.make_surface(frame_flipped)
        screen.blit(frame_surface, (0, 0))

        ## Display FPS in PyGame ##
        font = pygame.font.Font(None, 36)
        fps_text = font.render(f"FPS: {fps:.1f}", True, (255, 255, 255))
        screen.blit(fps_text, (10, 10))

        ## IMU Reading ##
        # yaw = motor_driver.read_imu()

        """
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
        yaw += g['z']*dt"""

        
        # yaw_text = font.render(f"Yaw: {yaw:.2f} degrees", True, (255, 255, 0))
        # print(yaw_text)
        # screen.blit(yaw_text, (252, 610))


        pygame.display.flip() # Update the Display ws
        pygame.time.delay(10) # Delay to limit CPU Usage


        