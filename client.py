#!/usr/local/bin python3

# a python socketio client
# https://blog.miguelgrinberg.com/post/flask-video-streaming-revisited
import socketio
import time, os, io, datetime, sys
from importlib import import_module
import logging
from threading import Thread

# we want to run a flask app here as well to serve up the location page
# this app will get the location from a cellphone and then emit that info
# to the server
from flask import Flask, jsonify, render_template, request, send_from_directory
import json
import apikeys
import flask_socketio

# things needed to control raspi I/O
import atexit

# to suppress InsecureRequestWarning when using https
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

os.environ['CAMERA'] = "opencv"
os.environ['OPENCV_CAMERA_SOURCE'] = "0"
os.environ['FPS'] = "1"
fps = int(os.environ['FPS'])
URL = "https://www.roocell.com:5000"

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

# instantiate app and flask socketio
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
fsio = flask_socketio.SocketIO(app)

#=============================================================
# location routes w/ socketio
@app.route('/location')
def location():
    return render_template('location.html', key = apikeys.google_map_api)
@fsio.on('update_location', namespace='/updatelocation')
def updatelocation(message):
    print("======================================")
    print("location received, forwarding to server")
    # TODO: json.loads doesnt' get all the decimal places.
    data = json.loads(message['data'])
    print(data)
    loc = {"latitude":data['latitude'], "longitude":data['longitude']}
    # emit back to web client so it can update location on it's page
    fsio.emit('location_updated', loc, namespace="/updatelocation")
    # relay location to server
    sio.emit('location_updated', loc, namespace="/serverupdatelocation")
    return "OK"

@fsio.on('connect', namespace='/updatelocation')
def connect():
    print("flask client connected")
    return "OK"

# ============================================
# Camera events
camera_thread = None
@sio.event
def connect():
    global camera_thread
    print('connection established')
    print('my sid is', sio.sid)
    camera_thread = Thread(target=gen, args=(Camera(),))
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
    global fps
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
        #log.debug("Frame size " + str(sys.getsizeof(frame)))
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



#=======================================================
# main loop
hb_time = 0
def main_loop(arg):
    global hb_time
    global sio
    global camera_thread
    log.debug("entering main loop")
    while 1:
        while sio.connected == False:
            try:
                print("connecting... ")
                sio.connect(URL, namespaces=['/heartbeat', '/video', '/serverupdatelocation'])
            except:
                print("ERROR: connection refused: check your URL, server running, port forwarding, internet connection, etc")
            time.sleep(3) # wait a few seconds for the connection to establish

        # see if we need to start the camera thread
        if (isinstance(camera_thread, Thread)):
            if (camera_thread.is_alive() == False):
                log.debug('kicking off camera thread')
                camera_thread.start()

        if (sio.connected == True):
            print("ML: sending hb_from_client")
            hb_time = time.time()
            sio.emit("hb_from_client", {'foo' : 'bar'}, namespace='/heartbeat', callback=hb_response)
            time.sleep(10)
# end of main_loop


#=====================================================
def cleanup():
    print("cleaning up")
    #picar.destroy()

if __name__ == '__main__':
    atexit.register(cleanup)

    # kick off main loop as a thread - because we're a flask app
    ml = Thread(target=main_loop, args=(False,))
    ml.start()

    # need to use self-signed certs because we don't have a domain
    fsio.run(app, certfile='cert.pem', keyfile='key.pem', debug=True, host='0.0.0.0')
