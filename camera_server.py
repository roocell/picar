# from https://github.com/miguelgrinberg/flask-video-streaming
import time
from base_camera import BaseCamera

class Camera(BaseCamera):
    frame = bytes()

    @staticmethod
    def frames():
        while True:
            time.sleep(1)
            yield Camera.frame
