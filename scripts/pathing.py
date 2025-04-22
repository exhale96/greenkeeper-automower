import numpy as np
import matplotlib.pyplot as plt
import time
from shapely.geometry import Point, Polygon, LineString, MultiLineString
from sklearn.decomposition import PCA
import math
import sys
from motor_driver import MotorDriver

class Pathing:
    def __init__(self, map_file, gps_file='../assets/raw_gps.txt'):
        # Robot properties
        self.map_file = map_file
        self.gps_file = gps_file
        self.blade_val = 0
        self.motors = MotorDriver()
        self.boundary = self.load_map_data(self.map_file)
        self.start_gps = None # position will be of the form (lon, lat)
        self.boundary_polygon = Polygon(self.boundary)

        # Create zigzag path based on the loaded boundary
        self.path = None

    def create_path(self, spacing_meters=0.5):
        self.path = self.generate_zigzag_path(spacing_meters)

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
        meter_to_deg_lon = 1 / (40075000 * np.cos(np.radians(avg_lat)) / 360)
        

        coords = np.array(self.boundary)
        pca = PCA(n_components=2)
        pca.fit(coords)
        rotated = pca.transform(coords)
        polygon_rotated = Polygon(rotated)

        # Transform the start GPS to PCA space
        start_point_rotated = pca.transform([self.start_gps])[0]
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
        rotated_path = [pt for segment in lines for pt in segment]
        path = pca.inverse_transform(rotated_path)
        path = [tuple(pt) for pt in path]

        print(f"Generated zigzag path with {len(path)} points.")
        return path


    def follow_path(self, align_threshold=5, distance_threshold=0.25):
        for i in range(len(self.path) - 1):
            target = self.path[i + 1]
            while True:
                current = self.get_current_gps()
                if not current:
                    continue
                dist = self.calculate_distance(current, target)
                if dist < distance_threshold:
                    self.motors.set_motor(0, 0)
                    break
                yaw = self.motors.read_imu()
                bearing = self.calculate_bearing(current, target)
                l_speed, r_speed = self.heading_correction(yaw, bearing)
                self.motors.set_motor(l_speed, r_speed)
                time.sleep(0.1)


    def heading_correction(self, current, target, base=0.3, max_corr=0.1):
        diff = self.normalize_angle(target - current)
        corr = max(min(diff / 45, 1), -1)
        left = base - corr * max_corr
        right = base + corr * max_corr
        return max(min(left, 1), 0), max(min(right, 1), 0)

    def calculate_bearing(self, point1, point2):
        lon1, lat1 = map(math.radians, point1)
        lon2, lat2 = map(math.radians, point2)
        dlon = lon2 - lon1
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        return (math.degrees(math.atan2(x, y)) + 360) % 360

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
    

def main():
    map_file = sys.argv[1]
    pathing_inst = Pathing(map_file=map_file)
    


if __name__ == "__main__":
    # if no args are passed, use default path
    if len(sys.argv) < 2:
        print("Usage: python pathing.py <output_file_path>")
        sys.exit(1)
    
    # start the mapping process
    main()


