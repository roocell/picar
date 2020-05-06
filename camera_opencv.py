# from https://github.com/miguelgrinberg/flask-video-streaming

import os
import cv2
from base_camera import BaseCamera


class Camera(BaseCamera):
    video_source = 0

    def __init__(self):
        if os.environ.get('OPENCV_CAMERA_SOURCE'):
            Camera.set_video_source(int(os.environ['OPENCV_CAMERA_SOURCE']))
        super(Camera, self).__init__()

    @staticmethod
    def set_video_source(source):
        Camera.video_source = source

    @staticmethod
    def frames():
        # https://docs.opencv.org/3.4/d4/d15/group__videoio__flags__base.html
        camera = cv2.VideoCapture(Camera.video_source)

        # smaller video allows more FPS and is more stable
        # TODO: work on shrinking frame size
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)

        if not camera.isOpened():
            raise RuntimeError('Could not start camera.')

        while True:
            # read current frame
            _, img = camera.read()

            # encode as a jpeg image and return it
            yield cv2.imencode('.jpg', img)[1].tobytes()
