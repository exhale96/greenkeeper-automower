import gps_mapper
import numpy as np
import matplotlib.pyplot as plt
import time
from motor_driver import MotorDriver


class Pathing:
    def __init__(self, map_file, gps_file):
        #self.boundary = self.load_map_data(map_file)
        # position will be of the form (lon, lat)
        #self.current_position = (0,0)
        #self.path = self.generate_zigzag_path()
        self.map_file = map_file
        self.gps_file = gps_file
        self.motors = MotorDriver()
        self.left_val = 0
        self.right_val = 0
        self.blade_val = 0
    def load_map_data(self, map_file):
        # map_file contains all lon,lat points
        with open(map_file, 'r') as file:
            lines = file.readlines()
            # list of tuples (lon, lat)
            points = []
            for line in lines:
                points.append(tuple(map(float, line.strip().split(','))))

    def get_current_gps(self):
        with open(self.gps_file, 'r') as file:
            # get the last line of the file which should be the most recent GPS data
            lines = file.readlines()
            if not lines:
                print("No GPS data found in the file.")
                return None
            last_line = lines[-1].strip()
            try:
                parts = last_line.split(',')
                if len(parts) > 6 and parts[0] == '$GNGGA':
                    lon, lat = self.nmea_to_decimal(parts[2], parts[3], parts[4], parts[5])
                    return (lon, lat)
                else:
                    print("Invalid GPS data format.")
                    return None
            except ValueError:
                print("Error parsing GPS data.")
                return None

    def nmea_to_decimal(self, lat_deg, lat_dir, lon_deg, lon_dir):
        """Converts NMEA format to decimal degrees."""
        lat_conv = float(lat_deg[:2]) + float(lat_deg[2:]) / 60.0
        lon_conv = float(lon_deg[:3]) + float(lon_deg[3:]) / 60.0
        
        if lat_dir == 'S':
            lat_conv = -lat_conv
        if lon_dir == 'W':
            lon_conv = -lon_conv
        return round(lon_conv, 7), round(lat_conv, 7)
            
    def is_inside_boundary(self, point):
        pass
    def generate_zigzag_path(self):
        pass
    def move_to_next_point(self, target_point):
        pass
    def reached_target(self):
        pass
    def calculate_motor_speeds(self, current_point, target_point):
        pass
    def correct_position(self):
        pass
    def calculate_distance(self, point1, point2):
        pass
    def follow_path(self):
        pass

    def move_forward(self, duration = 0, speed=0.6):
        if duration > 0:
            self.motors.set_motor(speed, speed*0.93)
            time.sleep(duration)
            self.motors.set_motor(0, 0)
        else:
            self.motors.set_motor(speed, speed*0.93)


    def move_backward(self, duration = 0, speed=0.25):
        if duration > 0:
            self.motors.set_motor(-speed, -speed)
            time.sleep(duration)
            self.motors.set_motor(0, 0)
        else:
            self.motors.set_motor(-speed, -speed)

    def turn_left(self, duration=1, speed=0.58):
        self.motors.set_motor(0, speed)
        time.sleep(duration)
        self.motors.set_motor(0, 0)

    def turn_right(self, duration=1, speed=0.55):
        self.motors.set_motor(speed, 0)
        time.sleep(duration)
        self.motors.set_motor(0, 0)

    def test_grid_movement(self):
        zigzag_steps = 3
        forward_time = 2
        side_step_time = 1
        for z in range(zigzag_steps):
            print(z)
            # Upper zigzag
            if z % 2 == 0:          
                self.move_forward(duration=forward_time)
                
                time.sleep(0.5)
                self.turn_right()
                self.move_forward(duration=side_step_time)
                self.turn_right()
            else:
                self.move_forward(duration=forward_time)
                time.sleep(0.5)
                self.turn_left()
                self.move_forward(duration=side_step_time)
                self.turn_left()





if __name__ == "__main__":
    robot = Pathing('./maps/lawn1.txt', 'output.txt')
    robot.test_grid_movement()
    
