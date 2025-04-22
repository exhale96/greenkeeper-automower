import numpy as np
import time
import sys
import webbrowser
import os

class LawnMowerMapping:
    def __init__(self, out_file_path, gps_file_path='../assets/raw_gps.txt', update_interval=0.1):
        # dir to open raw_gps.txt file
        self.gps_file_path = gps_file_path

        self.path = []
        self.latitudes = []
        self.longitudes = []
        self.paused = False

        # file to write to 
        self.out_file_path = out_file_path  
        self.update_interval = update_interval
        
        # Plot initialization code
        self.html_file = "../assets/live_map/live_map.html"
        self.generate_map()


    # keep reading gps coordinates until program stops
    def read_gps_coordinates(self):
        with open(self.gps_file_path, 'r') as file:
            file.seek(0, os.SEEK_END)
            while True:
                if not self.paused:
                    line = file.readline().strip()
                    if not line:
                        time.sleep(self.update_interval)
                        continue
                    parts = line.split(',')
                    if len(parts) > 6 and parts[0] == '$GNGGA':
                        try:
                            print(f"\nReceived GPS data\n{parts}")
                            lon, lat = self.nmea_to_decimal(parts[2], parts[3], parts[4], parts[5])
                            if lon == '' or lat == '':
                                continue
                            print(f"New point:\nLatitude: {lat}, Longitude: {lon}")
                            self.path.append((lon, lat))
                            self.latitudes.append(lat)
                            self.longitudes.append(lon)
                            # save lon,lat to map file used for lawn mower pathing
                            with open(self.out_file_path, 'a') as out_file:
                                out_file.write(f"{lon},{lat}\n")
                            self.generate_map()
                        except:
                            continue
                time.sleep(self.update_interval)


    def nmea_to_decimal(self, lat_deg, lat_dir, lon_deg, lon_dir):
        """Converts NMEA format to decimal degrees."""
        lat_conv = float(lat_deg[:2]) + float(lat_deg[2:]) / 60.0
        lon_conv = float(lon_deg[:3]) + float(lon_deg[3:]) / 60.0
        
        if lat_dir == 'S':
            lat_conv = -lat_conv
        if lon_dir == 'W':
            lon_conv = -lon_conv
        return round(lon_conv, 7), round(lat_conv, 7)
    
    def generate_map(self):
        if not self.path:
            return
        center_lon, center_lat = self.path[-1]  # current/latest location
        path = ",".join(f"[{lat},{lon}]" for lon, lat in self.path)

        html = f"""<!DOCTYPE html>
    <html>
    <head>
        <title>Live Lawn Mower Map</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="refresh" content="3">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    </head>
    <body>
        <div id="map" style="height: 100vh;"></div>
        <script>
            var map = L.map('map').setView([{center_lat}, {center_lon}], 18);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 22,
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map);
            
            var path = L.polyline([{path}], {{color: 'red'}}).addTo(map);
            var currentMarker = L.circleMarker([{center_lat}, {center_lon}], {{
                color: 'blue',
                radius: 8,
                fillColor: '#00f',
                fillOpacity: 0.8
            }}).addTo(map).bindPopup("Current Location");
            
            map.fitBounds(path.getBounds());
        </script>
    </body>
    </html>"""

        with open(self.html_file, 'w') as f:
            f.write(html)

        if not hasattr(self, 'browser_opened'):
            webbrowser.open('file://' + os.path.realpath(self.html_file))
            self.browser_opened = True


def main():
    out_file_path = sys.argv[1]
    out_file_path = "../assets/maps/" + out_file_path + ".txt"
    mapper_inst = LawnMowerMapping(out_file_path=out_file_path)
    mapper_inst.read_gps_coordinates()


if __name__ == "__main__":
    # if no args are passed, use default path
    if len(sys.argv) < 2:
        print("Usage: python mapper.py <output_file_path>")
        sys.exit(1)
    
    # start the mapping process
    main()