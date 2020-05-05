# from https://github.com/miguelgrinberg/flask-video-streaming
import time, io
from base_camera import BaseCamera

class Camera(BaseCamera):
    imgs = [open(f + '.jpg', 'rb').read() for f in ['1', '2', '3']]

    stream = None

    if stream is None:
        stream = imgs[0]

    def set(self, frame):
        Camera.stream = frame
    def get(self):
        return Camera.stream

    @staticmethod
    def frames():
        while True:
            if Camera.stream is None:
                yield Camera.imgs[int(time.time()) % 3]
            else:
                yield Camera.stream
