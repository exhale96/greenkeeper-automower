# <img src="assets/images/GreenKeeper_logo.png" alt="GreenKeeper Icon" width="40"/> GreenKeeper

Designed as a capstone project for Rutgers University New Brunswick, ECE Department. GreenKeeper is a Raspberry Pi-powered autonomous lawn robot built with computer vision, real-time controls, and a simple GUI for state management. It’s designed to map, patrol, and maintain a lawn area using onboard sensors and smart pathing algorithms, while avoiding obstacles using models like yolov8n and MiDaS. 
![](assets/images/gkgifnano.gif)
## 📸 Features

- Autonomous and remote control modes
- Real-time computer vision using YOLOv8n
- Simple Pygame-based menu & user interface
- Multiple operational states: Idle, RC, Pathing, Sentry, and more
- Modular architecture for easy extension

## 🛠️ Hardware & Software Setup

### Hardware Used:

- Raspberry Pi 5 (4GB)
- Raspberry Pi Active Cooling Module
- Raspberry Pi Camera Module v2
- 12v 9Ah SLA Battery
- 12v -> 5v/5A DC/DC converter
- Dual Brushed DC Motor Driver + 2 BDC Motors
- Singular BLDC Motor Driver + 1 BLDC Motor (*note: ~1500 RPM Minimum)
- Wheels (3-D Printed), Chasis, Assembly Parts, Wire

### Installation

This repo is mostly for demonstration purposes, but if you wish to try using the software for yourself here is how you can get it set up easily:

1. Create a Virtual Env & Activate it

```bash
python -m venv greenkeeper
source greenkeeper/bin/activate
```
2. Clone the repo:

```bash
git clone https://github.com/exhale96/greenkeeper-automower
cd greenkeeper-automower
```

3. Install all required dependancies by executing "requirements.txt" 

```bash
pip install -r requirements.txt
```
4. Install MiDaS into the environment by following the steps here: 

- https://pytorch.org/hub/intelisl_midas_v2/

