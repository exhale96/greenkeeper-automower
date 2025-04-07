# 🌿 GreenKeeper

Designed as a capstone project for Rutgers University New Brunswick, ECE Department. GreenKeeper is a Raspberry Pi-powered autonomous lawn robot built with computer vision, real-time controls, and a simple GUI for state management. It’s designed to map, patrol, and maintain a lawn area using onboard sensors and smart pathing algorithms, while avoiding obstacles using models like yolov8n and MiDaS. 

---

## 📸 Features

- Autonomous and remote control modes
- Real-time computer vision using YOLOv5
- Simple Pygame-based user interface
- RC (joystick) and keyboard navigation
- Multiple operational states: Idle, Pathing, Sentry, and more
- TensorFlow and PyTorch model compatibility
- Works on Raspberry Pi 5 with camera input
- Modular architecture for easy extension

---

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
- Pygame, OpenCV, PyTorch, YOLOv5, TensorFlow Lite, etc.
- A virtual environment is recommended

### Installation

This repo is mostly for demonstration purposes, but if you wish to try using the software, these are the required dependancies (almost all can be pip installed easily): 
- pygame, opencv, pytorch, ect.... 

1. Create a Virtual Env & Activate it

```bash
python3 -m venv greenkeeper_project
source greenkeeper_project/bin/activate
```
2. Clone the repo:

```bash
git clone https://github.com/yourusername/greenkeeper.git
cd greenkeeper
```

3. Install all required dependancies by executing "requirements.txt" 

```bash
pip install -r requirements.txt
```


