import cv2
from picamera2 import Picamera2
from ultralytics import YOLO
import torch
import numpy as np

def process_frame():
    # Capture a frame from the camera
    frame = picam2.capture_array()
    frame = cv2.resize(frame, (imgsz, imgsz))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Run YOLO model on the captured frame and store the results
    results = model(frame, imgsz=imgsz, conf=confidence, classes=classes, iou=iou, half=half, agnostic_nms=agnostic_nms)

    # Output the visual detection data, we will draw this on our camera preview window
    annotated_frame = results[0].plot()

    # Get inference time and calculate FPS
    inference_time = results[0].speed['inference']
    fps = 1000 / inference_time  # Convert to milliseconds

    ## MiDaS Depth Calculations (This lags the RC mode heavily, but tbh neither CV model is needed in RC mode) ##
    #img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # Convert the frame for depth estimation
    """input_batch = transform(frame)

    with torch.no_grad():
        prediction = midas(input_batch)

        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=frame.shape[:2],
            mode="bicubic",
            align_corners=False,
        ).squeeze()

    depth_map = prediction.cpu().numpy()
    if results and results[0].boxes is not None:
        for box in results[0].boxes:
            # Get bounding box coordinates
            x1, y1, x2, y2 = box.xyxy[0].int().tolist()

            # Ensure coordinates are within the depth map bounds
            h, w = depth_map.shape
            x1 = max(0, min(x1, w - 1))
            x2 = max(0, min(x2, w - 1))
            y1 = max(0, min(y1, h - 1))
            y2 = max(0, min(y2, h - 1))

            # Get region of depth map for that object
            object_depth_region = depth_map[y1:y2, x1:x2]

            # Avoid empty slices
            if object_depth_region.size == 0:
                continue
            normalized_depth = (depth_map - depth_map.min()) / (depth_map.max() - depth_map.min())

            roi = normalized_depth[y1:y2, x1:x2]
            mean_depth = np.mean(roi)
            print(mean_depth)

            # Create label based on thresholds
            if mean_depth > 0.5:
                proximity = "Very Close!!!"
            elif mean_depth > 0.35:
                proximity = "Somewhat Close"
            elif mean_depth > 0.2:
                proximity = "Medium"
            else:
                proximity = "Far"

            label = f"{proximity} ({mean_depth:.2f})"
        


            # Draw the MiDaS depth text
            # Draw the proximity and depth label for each object (ensure proper positioning)
            text_position = (x1, y1 + 25)  # Position the label just above the bounding box
            cv2.putText(annotated_frame, label, text_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 255, 255), 1, cv2.LINE_AA)"""
    return annotated_frame, fps

# Set up the camera with Picam
picam2 = Picamera2()
picam2.preview_configuration.main.size = (1944, 1944)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

# Setup Vision Models
model = YOLO("/home/green/Desktop/greenkeeper_project/cv_models/yolov8n_ncnn_model", task='detect')
midas = torch.hub.load("intel-isl/MiDaS", "MiDaS_small")
midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
transform = midas_transforms.small_transform
midas.eval()

## Performance Metrics for CV ##
imgsz = 640  # Image size for YOLO processing
confidence = 0.5
classes = None 
iou = 0.75
half = False
agnostic_nms = False

