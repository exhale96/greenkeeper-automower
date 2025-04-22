import numpy as np
import matplotlib.pyplot as plt
import time
from datetime import datetime
import subprocess
import sys


class LawnMowerMapping:
    def __init__(self, out_file_path, gps_file_path='../assets/raw_gps.txt', update_interval=0.1):
        # dir to open raw_gps.txt file
        self.gps_file_path = gps_file_path

        # self.path = []
        # self.latitudes = []
        # self.longitudes = []
        self.paused = False

        # file to write to 
        self.out_file_path = out_file_path  
        self.update_interval = update_interval
        

        # Plot initialization code
        # plt.ion()
        # self.fig, self.ax = plt.subplots()
        # self.ax.set_xlabel("Longitude")
        # self.ax.set_ylabel("Latitude")
        # self.ax.set_title("GPS Path Trace")
        # plt.show(block=False)

    # keep reading gps coordinates until program stops
    def read_gps_coordinates(self):
        with open(self.gps_file_path, 'r') as file:
            while True:
                if not self.paused:
                    file.seek(0, 2)
                    line = file.readline().strip()
                    if not line:
                        time.sleep(self.update_interval)
                        continue
                    parts = line.split(',')
                    if len(parts) > 6 and parts[0] == '$GNGGA':
                        print("\nReceived GPS data")
                        print(parts)
                        lon, lat = self.nmea_to_decimal(parts[2], parts[3], parts[4], parts[5])
                        # check if lon and lat are not empty 
                        if lon == '' or lat == '':
                            print("Invalid GPS data received.")
                            continue
                        print(f"Latitude: {lat}, Longitude: {lon}")
                        # self.path.append((lon, lat))
                        # self.latitudes.append(lat)
                        # self.longitudes.append(lon)

                        # save lon,lat to map file used for lawn mower pathing
                        with open(self.out_file_path, 'a') as out_file:
                            out_file.write(f"{lon},{lat}\n")
                time.sleep(self.update_interval)
                # self.update_plot()




    def nmea_to_decimal(self, lat_deg, lat_dir, lon_deg, lon_dir):
        """Converts NMEA format to decimal degrees."""
        lat_conv = float(lat_deg[:2]) + float(lat_deg[2:]) / 60.0
        lon_conv = float(lon_deg[:3]) + float(lon_deg[3:]) / 60.0
        
        if lat_dir == 'S':
            lat_conv = -lat_conv
        if lon_dir == 'W':
            lon_conv = -lon_conv
        return round(lon_conv, 7), round(lat_conv, 7)
    

    def close(self):
        """Close the file and plot."""
        # self.gps_file.close()
        # plt.ioff()
        # plt.close(self.fig)

"""    
    def update_plot(self):

        self.ax.clear()
        padding = 0.0001  # Small padding to ensure the plot isn't too tight
        if self.latitudes and self.longitudes:
            self.ax.set_xlim(min(self.longitudes) - padding, max(self.longitudes) + padding)
            self.ax.set_ylim(min(self.latitudes) - padding, max(self.latitudes) + padding)
            self.ax.set_xlabel("Longitude")
            self.ax.set_ylabel("Latitude")
            self.ax.set_title("GPS Path Trace")
            self.ax.plot([p[0] for p in self.path], [p[1] for p in self.path], 'r-', linewidth=1)
            
            # Mark the most recent coordinate with a blue dot
            if self.path:
                self.ax.plot(self.longitudes[-1], self.latitudes[-1], 'bo', markersize=6, label='Current Position')
                self.ax.legend()
        
        plt.draw()
        plt.pause(self.update_interval)
"""

def main():
    out_file_path = sys.argv[1]
    mapper_inst = LawnMowerMapping(out_file_path=out_file_path)
    mapper_inst.read_gps_coordinates()


if __name__ == "__main__":
    # if no args are passed, use default path
    if len(sys.argv) < 2:
        print("Usage: python mapper.py <output_file_path>")
        sys.exit(1)
    
    # start the mapping process
    main()