# 🌿 GreenKeeper

GreenKeeper is a Raspberry Pi-powered autonomous lawn robot built with computer vision, real-time controls, and a simple GUI for state management. It’s designed to map, patrol, and maintain a lawn area using onboard sensors and smart pathing algorithms. It was designed as a capstone project for Rutgers University New Brunswick, ECE Department. 

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

## 🛠️ Setup

### Prerequisites

- Raspberry Pi 5 (4GB or more)
- Raspberry Pi Camera Module (IMX219 or similar)
- Python 3.11+
- Pygame, OpenCV, PyTorch, YOLOv5, TensorFlow Lite, etc.
- A virtual environment is recommended

### Installation

1. Clone the repo:

```bash
git clone https://github.com/yourusername/greenkeeper.git
cd greenkeeper
