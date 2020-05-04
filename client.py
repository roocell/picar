#!/usr/local/bin python3

# a python socketio client
# https://blog.miguelgrinberg.com/post/flask-video-streaming-revisited
import socketio
import time, os
from importlib import import_module

# import camera driver
if os.environ.get('CAMERA'):
    Camera = import_module('camera_' + os.environ['CAMERA']).Camera
else:
    from camera import Camera


URL = "http://www.roocell.com:5000"
connected = 0
hb_time = 0

sio = socketio.Client()

@sio.event
def connect():
    global connected
    connected = 1
    print('connection established')
    print('my sid is', sio.sid)
@sio.event
def connect_error():
    global connected
    connected = 0
    print("The connection failed!")
@sio.event
def disconnect():
    global connected
    connected = 0
    print('disconnected from server')

@sio.event
def hb_from_server(data):
    print('hb_from_server with ', data)
    sio.emit('my response', {'response': 'my response'})
    return "OK"

def hb_response(data):
    global hb_time
    milliseconds = int(round((time.time()-hb_time) * 1000))
    print("server returned " + str(data) + " (rt=" + str(milliseconds) +"ms)")


def background_task(my_argument):
    # do some background work here!
    # this is background work while the client is connecting
    print("my background task " + str(my_argument) + " while socketio does it's thing")
    sio.sleep(2)
    print("my background task says: yo!")
    pass

def gen(camera):
    while True:
        frame = camera.get_frame()
        print("sending frame")
        try:
            sio.emit("video_source", frame, namespace='/video')
        except:
            print("server is busy...trying again")


sio.start_background_task(background_task, 123)
while connected == 0:
    try:
        print("connecting... " + str(connected))
        sio.connect(URL, namespaces=['/heartbeat', '/video'])
    except:
        print("ERROR: connection refused: check your URL, server running, port forwarding, internet connection, etc")
    time.sleep(1)

gen(Camera())

print("entering main loop")
while 1:
    print("ML: sending hb_from_client")
    hb_time = time.time()
    sio.emit("hb_from_client", {'foo' : 'bar'}, namespace='/heartbeat', callback=hb_response)
    time.sleep(10)
