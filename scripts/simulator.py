import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from shapely.geometry import Polygon, LineString, MultiLineString
from sklearn.decomposition import PCA
import math

def meters_to_degrees(center_lat):
    meter_to_deg_lat = 1 / 111320
    meter_to_deg_lon = 1 / (40075000 * np.cos(np.radians(center_lat)) / 360)
    return meter_to_deg_lat, meter_to_deg_lon

def generate_custom_polygon(center_lat, center_lon):
    # Creates a non-convex polygon to simulate an irregular lawn shape
    meter_to_deg_lat, meter_to_deg_lon = meters_to_degrees(center_lat)
    lat_offset = meter_to_deg_lat * np.array([0, 5, 10, 10, 5, 0, 0])
    lon_offset = meter_to_deg_lon * np.array([0, 0, 2, 8, 10, 10, 0])
    lats = center_lat + lat_offset
    lons = center_lon + lon_offset
    return np.column_stack((lons, lats))

center_lat = 40.5216
center_lon = -74.4604
boundary = generate_custom_polygon(center_lat, center_lon)

# Apply PCA
pca = PCA(n_components=2)
pca.fit(boundary)
rotated = pca.transform(boundary)
polygon_rotated = Polygon(rotated)

# Create vertical zigzag in rotated space
avg_lat = np.mean(boundary[:, 1])
meter_to_deg_lon = 1 / (40075000 * np.cos(np.radians(avg_lat)) / 360)
spacing_meters = 0.5
step = spacing_meters * np.linalg.norm(pca.components_[0]) * meter_to_deg_lon

# Simulate start in bottom-left (minimum x and y)
minx, miny, maxx, maxy = polygon_rotated.bounds
x = minx
lines = []
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
    x += step
    direction = not direction

# Inverse transform path
rotated_path = [pt for segment in lines for pt in segment]
path = pca.inverse_transform(rotated_path)
path_np = np.array(path)

# Animate
fig, ax = plt.subplots(figsize=(10, 8))
ax.plot(boundary[:, 0], boundary[:, 1], 'k--', label='Lawn Boundary')
ax.plot(path_np[:, 0], path_np[:, 1], 'b-', label='Zigzag Path')
robot_dot, = ax.plot([], [], 'ro', label='Robot', markersize=8)

ax.set_title("Animated Zigzag Path on Custom Lawn")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.legend()
ax.grid(True)
ax.set_aspect('equal', adjustable='box')

def init():
    robot_dot.set_data([], [])
    return robot_dot,

def update(frame):
    if frame < len(path_np):
        robot_dot.set_data([path_np[frame][0]], [path_np[frame][1]])
    return robot_dot,

ani = animation.FuncAnimation(fig, update, frames=len(path_np), init_func=init,
                              interval=150, blit=True, repeat=False)
ani.save("../assets/custom_zigzag_sim.gif", writer="pillow", fps=10)
plt.show()
