import numpy as np
import matplotlib.pyplot as plt
import time
import os
import subprocess
import atexit
from datetime import datetime
import threading

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
                                # check if lon and lat are not empty 
                                if lon == '' or lat == '':
                                    print("Invalid GPS data received.")
                                    continue
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

def launch_rtk_loop():
    global rtk_process
    email = "irc16@scarletmail.rutgers.edu"
    while True:
        print("Launching RTK process...")
        rtk_process = subprocess.Popen([
            "python", "rtk_coords.py", 
            "-u", email, 
            "-p", "none", 
            "rtk2go.com", 
            "2101", 
            "NJ_north_central"
        ])
        rtk_process.wait()  # Wait for it to exit
        print("RTK process exited. Restarting in 5 seconds...")
        time.sleep(5)  # Wait a bit before restarting


def cleanup():
    print("Cleaning up... Terminating RTK process (if running).")
    try:
        if rtk_process.poll() is None:
            rtk_process.terminate()
            rtk_process.wait(timeout=5)
            print("RTK process terminated cleanly.")
    except Exception as e:
        print(f"Could not terminate RTK process: {e}")


atexit.register(cleanup)


if __name__ == "__main__":
    rtk_thread = threading.Thread(target=launch_rtk_loop, daemon=True)
    rtk_thread.start()


    lawn_mower_map = LawnMowerMapping('../assets/raw_gps.txt','../assets/maps/map1.txt', update_interval=0.05)
    lawn_mower_map.read_gps_coordinates()
