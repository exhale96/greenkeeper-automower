from picamera2 import Picamera2
import time
import threading

class CameraManager:
    def __init__(self):
        self.picam2 = None
        self.lock = threading.Lock()
        
        

    def init_camera(self):
        """Initialize the camera."""
        if self.picam2 is None:
            self.picam2 = Picamera2()
            self.picam2.preview_configuration.main.size = (1920, 1080)
            self.picam2.preview_configuration.main.format = "RGB888"
            self.picam2.preview_configuration.align()
            self.picam2.configure("preview")
            self.picam2.start()
            print("Camera initialized!!!! BITCH")

    def stop_camera(self):
        """Stop the camera if it's running."""
        if self.picam2 is not None:
            self.picam2.stop()
            time.sleep(0.5)
            self.picam2.close()
            
            self.picam2 = None
            print("Camera stopped.")
    

    def get_camera(self):
        """Return the camera object."""
        return self.picam2
