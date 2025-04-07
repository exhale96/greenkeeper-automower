import numpy as np
import matplotlib.pyplot as plt
import time
import os

class LawnMowerMapping:
    def __init__(self, file_path, out_file_path, update_interval=1):
        self.file_path = file_path
        self.update_interval = update_interval
        self.path = []
        self.latitudes = []
        self.longitudes = []
        self.paused = False
        self.out_file_path = out_file_path

        # Initialize plot
        plt.ion()
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel("Longitude")
        self.ax.set_ylabel("Latitude")
        self.ax.set_title("GPS Path Trace")
        print("Press 'p' to pause/resume the map update.")

    def read_gps_coordinates(self):
        """Reads new GPS coordinates from the file."""
        with open(self.file_path, 'r') as file:
            while True:
                try:
                    if not self.paused:
                        line = file.readline().strip()
                        if not line:
                            time.sleep(self.update_interval)
                            continue
                        try:
                            parts = line.split(',')
                            if len(parts) > 6 and parts[0] == '$GNGGA':
                                print("Received GPS data")
                                print(parts)
                                lon, lat = self.nmea_to_decimal(parts[2], parts[3], parts[4], parts[5])
                                print(f"Latitude: {lat}, Longitude: {lon}")
                                self.path.append((lon, lat))
                                self.latitudes.append(lat)
                                self.longitudes.append(lon)
                                # save lon,lat to map file used for lawn mower pathing
                                with open(self.out_file_path, 'a') as out_file:
                                    out_file.write(f"{lon},{lat}\n")

                        except ValueError:
                            continue
                    
                    self.update_plot()
                    self.check_pause()
                except FileNotFoundError:
                    print(f"File {self.file_path} not found. Waiting for file to be created.")
                    time.sleep(self.update_interval)
                except KeyboardInterrupt:
                    print("Stopping the lawn map update.")
                    break
        plt.ioff()
        plt.show()

    def nmea_to_decimal(self, lat_deg, lat_dir, lon_deg, lon_dir):
        """Converts NMEA format to decimal degrees."""
        lat_conv = float(lat_deg[:2]) + float(lat_deg[2:]) / 60.0
        lon_conv = float(lon_deg[:3]) + float(lon_deg[3:]) / 60.0
        
        if lat_dir == 'S':
            lat_conv = -lat_conv
        if lon_dir == 'W':
            lon_conv = -lon_conv
        return round(lon_conv, 7), round(lat_conv, 7)
    

    def update_plot(self):
        """Updates the plot with the latest GPS data."""
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

    def check_pause(self):
        """Checks if the user wants to pause/resume the updates."""
        if plt.waitforbuttonpress(0.1):  # Wait for a key press event
            key = input("Press 'p' to pause/resume: ")
            if key.lower() == 'p':
                self.paused = not self.paused
                print("Paused" if self.paused else "Resumed")

if __name__ == "__main__":
    curr_path = os.path.dirname(os.path.realpath(__file__))
    lawn_mower_map = LawnMowerMapping('output.txt','./maps/map1.txt', update_interval=0.1)
    lawn_mower_map.read_gps_coordinates()
