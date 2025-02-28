# GreenKeeper 
GreenKeeper - Autonomous Lawn Maintenance Robot

Team Members

Ian Christensen

Erik Pacio

Shahvez Siddiqui

John Lim

Advisor: Sasan Haghani, Dana Kristin

Project Overview

GreenKeeper is a budget-friendly, automatic lawn maintenance robot designed to offer an accessible alternative to high-cost commercial models. Our aim is to reduce unnecessary features and installation expenses, making autonomous lawn care affordable and practical for a wider range of users.

🚀 Key Features

Navigation Control: ESP32 microcontroller processes sensor data (ToF, GPS, IMU) for obstacle avoidance and lawn mapping.

Computer Vision: Raspberry Pi with synchronized cameras running machine learning models for grass detection and object recognition.

User App: Real-time lawn status, robot location, and scheduling via Bluetooth and WiFi.

Safety Mechanisms: Immediate shutdown when lifted, rain detection, and obstacle avoidance.

Autonomy: Fully autonomous operation, including scheduled mowing and automatic charging.

🎯 Objectives

Affordability: Final retail price under $1000.

Efficiency: Grass cutting comparable to traditional mowers.

Safety: Reliable systems to protect users, animals, and property.

Terrain Handling: Capable of navigating slopes up to 15% and covering lawns up to 0.25 acres.

📐 System Design

Navigation & Control: ESP32 handles sensor integration and decision-making.

Vision & Processing: Raspberry Pi processes CV models using Python and OpenCV.

Mowing Mechanism: Adjustable blade speed and height based on location and obstacles.

Power Supply: 5000 mAh battery for full lawn coverage.

🛠 Development Workflow

Research: Component selection, GPS-based mapping, OpenCV model training.

Prototyping: Sensor integration, physical build testing, motor and blade calibration.

Software Implementation: Object detection, path planning, app development.

Testing & Debugging: Component validation, safety checks, and performance optimization.

📊 Task Allocation

Hardware Build: Chassis, blade, motor integration.

Electronics & Wiring: Battery management, component wiring.

Software: CV model training, app development.

Testing & Integration: Full system testing, debugging, and adjustments.

🕒 Timeline

Refer to the Gantt chart for detailed milestones, including research, prototyping, software development, and testing phases.

💰 Budget Considerations

Our cost breakdown targets affordability without compromising core functionality, prioritizing essential features over luxury additions.

📘 Future Enhancements

Soil Aeration & Moisture Sensing: For advanced lawn care.

Nutrient Detection: Potential future feature, subject to cost feasibility.

🛠 Tech Stack

Hardware: ESP32, Raspberry Pi, ToF sensors, GPS, motors.

Software: Python, OpenCV, TensorFlow Lite.

App Development: Flutter (with Bluetooth and real-time status updates).

GreenKeeper aims to democratize lawn care by offering an accessible, autonomous solution for those who need it most. This README will evolve alongside the project — stay tuned for updates and contributions!

Let me know if you’d like any adjustments or additions! 🚀

