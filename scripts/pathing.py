import mapper
import numpy as np
import matplotlib.pyplot as plt
import time
from motor_driver import MotorDriver
from shapely.geometry import Polygon, LineString, MultiLineString
from sklearn.decomposition import PCA


class Pathing:
    def __init__(self, map_file, gps_file):
        # Robot properties
        self.map_file = map_file
        self.gps_file = gps_file
        self.left_val = 0
        self.right_val = 0
        self.blade_val = 0

        self.motors = MotorDriver()

        # Load the map data from the file
        self.boundary = self.load_map_data(self.map_file)

        # position will be of the form (lon, lat)
        self.current_position = self.get_current_gps()

        # Create zigzag path based on the loaded boundary
        self.path = self.generate_zigzag_path()

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
        x, y = point
        poly = self.boundary
        n = len(poly)
        inside = False
        p1x, p1y = poly[0]
        for i in range(n + 1):
            p2x, p2y = poly[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y + 1e-10) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def generate_zigzag_path(self, spacing_meters=0.5):
        if not self.boundary:
            print("No boundary data loaded, cannot generate a path.")
            return []
        
        # wait until robot is inside the boundary
        while True:
            pos = self.get_current_gps()
            if pos and self.is_inside_boundary(pos):
                print("Robot is inside the boundary.")
                start_lon, start_lat = pos
                break
            print("Waiting for robot to be inside the boundary...")
            time.sleep(1)  # wait for a second before checking again
    

        # meters to degrees conversion factors
        avg_lat = np.mean([p[1] for p in self.boundary])
        meter_to_deg_lat = 1 / 111320
        meter_to_deg_lon = 1 / (40075000 * np.cos(np.radians(avg_lat)) / 360)
        

        coords = np.array(self.boundary)
        pca = PCA(n_components=2)
        pca.fit(coords)
        rotated = pca.transform(coords)
        polygon_rotated = Polygon(rotated)

        minx, miny, maxx, maxy = polygon_rotated.bounds
        step = spacing_meters * meter_to_deg_lon

        lines = []
        x = minx
        direction = True
        while x <= maxx:
            if direction:
                line = LineString([(x, miny), (x, maxy)])  # vertical line from miny to maxy
            else:
                line = LineString([(x, maxy), (x, miny)])
            clipped = line.intersection(polygon_rotated)  # clip the line to the polygon
            if not clipped.is_empty:
                if isinstance(clipped, LineString):
                    lines.append(list(clipped.coords))  # add the coordinates of the clipped line
                elif isinstance(clipped, MultiLineString):
                    for subline in clipped:
                        lines.append(list(subline.coords))
            x += step
            direction = not direction
        
        # inverse transform the coordinates back to original space
        rotated_path = [pt for segment in lines for pt in segment]
        path = pca.inverse_transform(rotated_path)
        path = [tuple(pt) for pt in path]

        print(f"Generated zigzag path with {len(path)} points.")
        return path


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




"""
if __name__ == "__main__":
    robot = Pathing('./maps/lawn1.txt', 'output.txt')
    robot.test_grid_movement()
"""    
