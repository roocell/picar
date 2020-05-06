#!/usr/local/bin python3

# a python socketio client
# https://blog.miguelgrinberg.com/post/flask-video-streaming-revisited
import socketio
import time, os, io, datetime
from importlib import import_module
import logging
import threading

# to suppress InsecureRequestWarning when using https
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

os.environ['CAMERA'] = "opencv"
os.environ['OPENCV_CAMERA_SOURCE'] = "0"
fps = 30
URL = "https://www.roocell.com:5000"
hb_time = 0

# import camera driver
if os.environ.get('CAMERA'):
    Camera = import_module('camera_' + os.environ['CAMERA']).Camera
else:
    from camera import Camera

# create logger
log = logging.getLogger('client.py')
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)

sio = socketio.Client(engineio_logger=False, logger=False, ssl_verify=False)

@sio.event
def connect():
    print('connection established')
    print('my sid is', sio.sid)
@sio.event
def connect_error():
    print("The connection failed!")
@sio.event
def disconnect():
    print('disconnected from server')

@sio.event
def hb_from_server(data):
    print('hb_from_server with ', data)
    sio.emit('my response', {'response': 'my response'})
    return "OK"
@sio.event
def movement(data):
    log.debug(data)
    # call python to adjust PWM
    return "OK"
@sio.event
def neutral(data):
    log.debug(data)
    # all stop!
    return "OK"

def hb_response(data):
    global hb_time
    milliseconds = int(round((time.time()-hb_time) * 1000))
    print("server returned " + str(data) + " (rt=" + str(milliseconds) +"ms)")

def gen(camera):
    last_tx = 0
    last_sec_log = 0
    while sio.connected:
        sec = int(round((time.time()-last_sec_log)))
        # print a log every second
        if (sec > 1):
            log.debug("sending frames")
            last_sec_log = time.time()
        ms = int(round((time.time()-last_tx) * 1000))
        frame = camera.get_frame()
        if (ms >= 1000/fps):
            try:
                # TODO: need a callback from server here.
                # client is disconncting and there's no attempt
                # to reconnect.
                sio.emit("video_source", frame, namespace='/video')
            except:
                print("server is busy...trying again")
            last_tx = time.time()
            # we should be able to go to sleep until roughly the next frame
            # based on the FPS. would resolve 100% CPU
            # actually not needed because get_frame() waits for an event (but still 40% CPU)
            #time.sleep(950/fps/1000) # 100% CPU -> 50% CPU

    if (sio.connected == False):
        log.debug("stopped sending frames")

#gen(Camera())

log.debug("entering main loop")
while 1:
    while sio.connected == False:
        try:
            print("connecting... ")
            sio.connect(URL, namespaces=['/heartbeat', '/video'])
            camera_thread = threading.Thread(target=gen, args=(Camera(),))
        except:
            print("ERROR: connection refused: check your URL, server running, port forwarding, internet connection, etc")
        time.sleep(1)

    # see if we need to start the camera thread
    if (camera_thread.is_alive() == False):
        log.debug('kicking off camera thread')
        camera_thread.start()

    if (sio.connected == True):
        print("ML: sending hb_from_client")
        hb_time = time.time()
        sio.emit("hb_from_client", {'foo' : 'bar'}, namespace='/heartbeat', callback=hb_response)
        time.sleep(10)
