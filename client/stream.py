import cv2
import threading
from kivy.clock import Clock
from kivy.graphics.texture import Texture
import time

class StreamReceiver:
    def __init__(self, ip, port, image_widget, on_connect, on_disconnect):
        self.ip = ip
        self.port = port
        self.image_widget = image_widget
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.is_running = False
        self.capture = None
        self.thread = None

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        url = f"tcp://{self.ip}:{self.port}"
        # OpenCV needs to be compiled with ffmpeg to handle tcp stream
        self.capture = cv2.VideoCapture(url)
        
        if self.capture.isOpened():
            Clock.schedule_once(lambda dt: self.on_connect())
        
        while self.is_running and self.capture.isOpened():
            ret, frame = self.capture.read()
            if not ret:
                break
            
            # Flip frame vertically for kivy texture
            buf = cv2.flip(frame, 0).tobytes()
            # Schedule texture update on main UI thread
            Clock.schedule_once(lambda dt, b=buf, s=frame.shape: self._update_texture(b, s))
            
        self.is_running = False
        if self.capture:
            self.capture.release()
        Clock.schedule_once(lambda dt: self.on_disconnect())

    def _update_texture(self, buf, shape):
        if not self.image_widget.texture or self.image_widget.texture.size != (shape[1], shape[0]):
            self.image_widget.texture = Texture.create(size=(shape[1], shape[0]), colorfmt='bgr')
        self.image_widget.texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.image_widget.canvas.ask_update()

    def stop(self):
        self.is_running = False
        if self.capture:
            self.capture.release()
