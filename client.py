#!/usr/bin python3

# change threads to eventlet
#import eventlet
#eventlet.monkey_patch(socket=False)
#from eventlet.green import threading
import threading
from threading import Thread


# a python socketio client
# https://blog.miguelgrinberg.com/post/flask-video-streaming-revisited
import socketio
import time, os, io, datetime, sys
from importlib import import_module
import logging
import atexit

# we want to run a flask app here as well to serve up the location page
# this app will get the location from a cellphone and then emit that info
# to the server
from flask import Flask, jsonify, render_template, request, send_from_directory
import json
import apikeys
import flask_socketio

# things needed to control raspi I/O
import atexit
import drive

drive = drive.Drive("traxxas")

# to suppress InsecureRequestWarning when using https
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

os.environ['CAMERA'] = "opencv"
os.environ['OPENCV_CAMERA_SOURCE'] = "0"
os.environ['FPS'] = "60"
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
#=============================================================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
fsio = flask_socketio.SocketIO(app)

#=============================================================
# location routes w/ socketio
LOC_FILE = "loc.file"
@app.route('/location')
def location():
    return render_template('location.html', key = apikeys.google_map_api)
@fsio.on('update_location', namespace='/updatelocation')
def updatelocation(message):
    log.debug("======================================")
    log.debug("location received")
    # TODO: json.loads doesnt' get all the decimal places.
    data = json.loads(message['data'])
    log.debug(data)
    loc = {"latitude":data['latitude'], "longitude":data['longitude']}
    # emit back to web client so it can update location on it's page
    fsio.emit('location_updated', loc, namespace="/updatelocation")

    # relay location to server (I'm such a hack)
    f = open(LOC_FILE, "w")
    f.write(json.dumps(message))
    f.close()
    #sio.emit('location_updated', message, namespace="/serverupdatelocation")
    return "OK"

@fsio.on('connect', namespace='/updatelocation')
def connect():
    log.debug("flask client connected")
    return "OK"

#=================================================
# MOTOR
@sio.event
def movement(data):
    log.debug("======MOVEMENT======")
    log.debug(data)
    # +x = right
    # -x = left
    # +y = forward
    # -y = reverse
    # y==0 -> neutral
    # x==0 -> straight
    x = int(data['x']);
    y = int(data['y']);
    if (y > 0):
        drive.forward(y)
    elif (y < 0):
        drive.reverse(y)
    else:
        drive.neutral()
    if (x > 0):
        drive.right(x*(-1)) # drive API is right (-)
    elif (x < 0):
        drive.left(x*(-1))
    else:
        drive.straight()
    # call python to adjust PWM
    return "OK"
@sio.event
def neutral(data):
    log.debug("======NEUTRAL======")
    log.debug(data)
    # all stop!
    drive.neutral()
    drive.straight()
    return "OK"

#====================================================
# CAMERA
last_tx = 0
last_sec_log = 0
def processCamera(camera):
    global last_tx
    global last_sec_log
    sec = int(round((time.time()-last_sec_log)))
    # log.debug a log every second
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
            pass
        except:
            log.debug("server is busy...trying again")
        last_tx = time.time()

# ============================================
# SERVER CONNECTION / HEARTBEAT
main_thread = None
@sio.event
def connect():
    global main_thread
    log.debug('connection established')
    log.debug('my sid is' + sio.sid)

    # check if camera exists
    if "video0" in os.listdir("/dev"):
        camera = Camera()
        main_thread = Thread(target=main_loop, args=(camera,))
    else:
        log.debug("creating main thread without camera")
        main_thread = Thread(target=main_loop, args=(None,))


@sio.event
def connect_error():
    log.debug("The connection failed!")
@sio.event
def disconnect():
    log.debug('disconnected from server')

def hb_response(data):
    global hb_time
    milliseconds = int(round((time.time()-hb_time) * 1000))
    #log.debug(time.time())
    log_every_10secs = int(time.time()) % 10
    if (log_every_10secs == 0):
        log.debug("HB " + str(data) + " (rt=" + str(milliseconds) +"ms)")

#==========================================================
# MAIN LOOP
hb_time = 0
def main_loop(camera):
    global hb_time
    global fps
    last_hb = 0
    last_loc_mod_time = 0
    log.debug("entering main loop")
    while sio.connected:
        if camera is not None:
            processCamera(camera)

        # sending of the frame is interrupting any other messages
        # the only way i could figure out how to overcome this is
        # to send everything else to the server from the thread.
        # so any ayncronous things from flask routes (for example)
        # will have to set a global, then sent here
        # no idea how this is going to handle multiple cameras.... :(
        hb = int(round((time.time()-last_hb)))
        if (sio.connected == True and hb >= 1):
            hb_time = time.time()
            #log.debug("ML: sending hb_from_client " + str(hb_time))
            sio.emit("hb_from_client", {'hb_time' : str(hb_time)}, namespace='/heartbeat', callback=hb_response)
            last_hb = time.time()

        # if we've missed 2 heartbeats in a row - go neutral
        if (sio.connected == True and hb >= 2):
            log.debug("NO HB! ALL STOP")
            drive.allstop()

        if (os.path.exists(LOC_FILE)):
            modtime = os.path.getmtime(LOC_FILE)
        else:
            modtime = 0
        if (modtime > last_loc_mod_time):
            f = open(LOC_FILE, "r")
            message = f.read()
            log.debug("forwarding loc to server")
            sio.emit('location_updated', message, namespace="/serverupdatelocation")
            last_loc_mod_time = modtime



    if (sio.connected == False):
        log.debug("disconnected! allstop!")
        drive.allstop()

# end of main_loop

#=======================================================
# START LOOP
def start_loop(arg):
    global sio
    global main_thread
    log.debug("entering start loop")
    while 1:
        while sio.connected == False:
            try:
                log.debug("connecting... ")
                sio.connect(URL, namespaces=['/heartbeat', '/video', '/serverupdatelocation'])
            except:
                log.debug("ERROR: connection refused: check your URL, server running, port forwarding, internet connection, etc")
            time.sleep(3) # wait a few seconds for the connection to establish

        # see if we need to start the main thread
        if (isinstance(main_thread, Thread)):
            if (main_thread.is_alive() == False):
                log.debug('kicking off main thread')
                main_thread.start()

        time.sleep(1)
# end of start_loop




#=====================================================
def cleanup():
    log.debug("cleaning up")
    #picar.destroy()

if __name__ == '__main__':
    atexit.register(cleanup)

    # kick off main loop as a thread - because we're a flask app
    log.debug("creating start loop")
    sl = Thread(target=start_loop, args=(False,))
    sl.start()

    # need to use self-signed certs because we don't have a domain
    # use_reloader=False # to prevent __main__ from being called twice and having client
    # connect to the server twice (was generating double socketio events)
    fsio.run(app, certfile='cert.pem', keyfile='key.pem', debug=True, host='0.0.0.0', use_reloader=False)

    # bah! becomeCA.txt doesn't work either.
    #fsio.run(app, certfile='picar.crt', keyfile='picar.key', debug=True, host='0.0.0.0')
