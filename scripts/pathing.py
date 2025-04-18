import mapper
import numpy as np
import matplotlib.pyplot as plt
import time
from motor_driver import MotorDriver
from shapely.geometry import Point, Polygon, LineString, MultiLineString
from sklearn.decomposition import PCA
import math

class Pathing:
    def __init__(self, map_file, gps_file):
        # Robot properties
        self.map_file = map_file
        self.gps_file = gps_file
        self.left_val = 0
        self.right_val = 0
        self.blade_val = 0
        self.motors = MotorDriver()
        self.boundary = self.load_map_data(self.map_file)
        self.start_gps = None # position will be of the form (lon, lat)
        self.boundary_polygon = Polygon(self.boundary)

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
            if len(points) < 5:
                return None
            return points


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
        return self.boundary_polygon.contains(Point(point)) or self.boundary_polygon.touches(Point(point))


    def generate_zigzag_path(self, spacing_meters=0.5):
        if not self.boundary:
            print("No boundary data loaded, cannot generate a path.")
            return []
        
        # wait until robot is inside the boundary
        while True:
            pos = self.get_current_gps()
            if pos and self.is_inside_boundary(pos):
                print("Robot is inside the boundary.")
                self.start_gps = pos # set starting point
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

        # Transform the start GPS to PCA space
        start_point_rotated = pca.transform([self.start_gps])(0)
        start_x = start_point_rotated[0]


        minx, miny, maxx, maxy = polygon_rotated.bounds
        step = spacing_meters * np.linalg.norm(pca.components_[0]) * meter_to_deg_lon  # convert meters to PCA space step size

        x = minx
        while x + step < start_x:
            x += step


        lines = []
        x = minx
        direction = True
        while x <= maxx:
            line = LineString([(x, miny), (x, maxy)]) if direction else LineString([(x, maxy), (x, miny)])
            clipped = line.intersection(polygon_rotated)
            if not clipped.is_empty:
                if isinstance(clipped, LineString):
                    lines.append(list(clipped.coords))
                elif isinstance(clipped, MultiLineString):
                    for subline in clipped.geoms:
                        lines.append(list(subline.coords))
            # move to the next step
            x += step
            direction = not direction
        
        # inverse transform the coordinates back to original space
        rotated_path = [pt for segment in lines for pt in (segment if direction else segment[::-1])]
        path = pca.inverse_transform(rotated_path)
        path = [tuple(pt) for pt in path]

        print(f"Generated zigzag path with {len(path)} points.")
        return path


    def move_to_next_point(self, target_point):
        print(f"Moving towards target point: {target_point}")
        align_theshold = 10 # degrees
        dist_threshold = 0.2 # meters

        previous_point = None


        self.move_forward()

        while True:
            current_point = self.get_current_gps()
            if current_point is None:
                continue
            if previous_point is None:
                previous_point = current_point
                continue
            
            current_heading = self.calculate_bearing(previous_point, current_point)
            target_heading = self.calculate_bearing(current_point, target_point)
            heading_diff = self.normalize_angle(target_heading - current_heading)
            print(f"Heading: current {current_heading:.1f}°, target {target_heading:.1f}°, diff {heading_diff:.1f}°")

            # turn if needed
            if abs(heading_diff) > align_theshold:
                if heading_diff > 0:
                    # turn right
                    self.turn_right(duration=0.4)
                else:
                    self.turn_left(duration=0.4)
            else:
                self.move_forward()
                while True:
                    current_point = self.get_current_gps()
                    if current_point is None:
                        continue
                    dist = self.calculate_distance(current_point, target_point)
                    print(f"Current distance to target: {dist:.2f} meters")
                    if dist < dist_threshold:
                        self.motors.set_motor(0,0)
                        print("Arrived at target.")
                        return
                    time.sleep(0.5)
            

            dist = self.calculate_distance(current_point, target_point)
            print(f"Current position: {current_point}, Distance to target: {dist:.2f} meters")
            if dist < 0.3:
                self.motors.set_motor(0, 0)  # Stop the motors when close to the target
                break
            time.sleep(0.5)

    def calculate_bearing(self, point1, point2):
        lon1, lat1 = map(math.radians, point1)
        lon2, lat2 = map(math.radians, point2)
        dlon = lon2 - lon1
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dlon))
        bearing = math.degrees(math.atan2(x, y))
        return (bearing + 360) % 360    # degree is from 0 to 360

    def normalize_angle(self, angle):
        angle = (angle + 180) % 360 - 180
        return angle
    
    def calculate_distance(self, point1, point2):
        lat1, lon1 = point1[1], point1[0]
        lat2, lon2 = point2[1], point2[0]
        r = 6371000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return r * c
    
    def follow_path(self):
        print("Starting to follow the zigzag path...")
        for target_point in self.path:
            self.move_to_next_point(target_point)  # Move towards the target point


    def move_forward(self, speed=0.3):
        self.motors.set_motor(speed, speed*0.93)


    def move_backward(self, speed=0.3):
        self.motors.set_motor(-speed, -speed)

    def turn_left(self, speed=0.3):
        self.motors.set_motor(0, speed)


    def turn_right(self, speed=0.3):
        self.motors.set_motor(speed, 0)


"""
if __name__ == "__main__":
    robot = Pathing('./maps/lawn1.txt', 'output.txt')
    robot.test_grid_movement()
"""    
