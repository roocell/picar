#!/usr/local/bin python3

# Flask server  with FLask-socketio
# this app will display picar web controls, etc
# it will also maintain a socket connection to picar
# so that it can send commands and/or get notified of other events


from flask import Flask, jsonify, request, render_template, send_from_directory
from flask import Response
import json
import os, time
import apikeys
import logging
import snap
from flask_socketio import SocketIO, emit

# to overcome error
# ValueError: Too many packets in payload
# (can probably implement a fps limiter on client side as well)
from engineio.payload import Payload
Payload.max_decode_packets = 100

from camera_relay import Camera
relayCam = Camera()

webcam_w = 320
webcam_h = 240

# create logger
log = logging.getLogger(__file__)
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


#=============================================================
# movement routes
# these send % values to client.py via socketio
def movement_cb(data):
    #log.debug("movement_cb: " + data)
    pass
def neutral_cb(data):
    #log.debug("neautral_cb: " + data)
    pass
def clearreverse_cb(data):
    #log.debug("clearreverse_cb: " + data)
    pass
timestamp = 0;
@app.route('/movement/')
def movement():
    global timestamp
    t = int(request.args.get('t'))
    if (t < timestamp):
        # dont want the car jerking back and forth
        log.debug("OOO packet %d < %d", t, timestamp)
        return "NOK"
    timestamp = t
    x = request.args.get('x')
    y = request.args.get('y')
    log.debug("movement  x=%s y=%s t=%d", x, y, t)
    socketio.emit('movement', {'x': x, 'y':y}, callback=movement_cb)
    return "OK"
@app.route('/neutral')
def neutral():
    global timestamp
    t = int(request.args.get('t'))
    if (t < timestamp):
        # dont want the car jerking back and forth
        log.debug("OOO packet %d < %d", t, timestamp)
        return "NOK"
    timestamp = t
    log.debug('in neutral')
    socketio.emit('neutral', {'x': 0, 'y':0}, callback=neutral_cb)
    return "OK"

#=============================================================
# index routes
@app.route('/')
def index():
    top = """<!DOCTYPE HTML>
    <html>
        <head>
            <title>Pi Car</title>
            <meta charset="utf-8">
            <meta name="description" content="Raspberry Pi control RC car.">
            <meta name="author" content="Michael Russell">
            <meta name="viewport" content="initial-scale=1.0">
            <link rel="shortcut icon" type="image/png" href="static/raspi.png">
            </head><body> """
    bottom =  "</body></html>"
    return top + \
           render_template('index.html', key = apikeys.google_map_api,
                              # need a little more to get rid of the scrollbars
                               webcam_w=str(webcam_w+20)+"px", webcam_h=str(webcam_h+20)+"px") + \
           bottom
           #render_template('snap.html', innerHTML=snap.innerHTML()) + \
#=============================================================
# location
@socketio.on("location_updated", namespace='/serverupdatelocation')
def location_updated(message):
    log.debug("location_updated")
    mdict = eval(message)
    #log.debug(mdict)
    data = json.loads(mdict["data"])
    log.debug(data)
    loc = {"latitude":data['latitude'], "longitude":data['longitude']}

    # emit to web client
    # TODO: sending of video frames is causing issues on reception of anything
    socketio.emit('server_location_updated', loc, namespace='/serverupdatelocation', broadcast=True)
    return "OK"

# serve up location page
# phone can update car location directly (not relayed through client.py)
@app.route('/location')
def location():
    return render_template('location.html', key = apikeys.google_map_api)
@socketio.on('update_location', namespace='/updatelocation')
def updatelocation(message):
    log.debug("======================================")
    log.debug("location received")
    # TODO: json.loads doesnt' get all the decimal places.
    data = json.loads(message['data'])
    log.debug(data)
    loc = {"latitude":data['latitude'], "longitude":data['longitude']}

    # emit back to web client so it can update location on it's page
    socketio.emit('location_updated', loc, namespace="/updatelocation")

    # emit to web client
    socketio.emit('server_location_updated', loc, namespace='/serverupdatelocation', broadcast=True)
    return "OK"
@socketio.on('connect', namespace='/updatelocation')
def connect():
    log.debug("location flask client connected")
    return "OK"
@socketio.on('disconnect', namespace='/updatelocation')
def test_disconnect():
    print('location flask client disconnected')

#=============================================================
# Video
last_rx_frame_log = 0
@socketio.on("video_source", namespace='/video')
def video_source(message):
    global last_rx_frame_log
    sec = int(round((time.time()-last_rx_frame_log)))
    if (sec > 1):
        log.debug("rx video frame")
        last_rx_frame_log = time.time()
    socketio.sleep(0) # helps prevent webpage from freezing at start ?
    relayCam.set(message)
    return "OK"

def gen(camera):
    """Video streaming generator function."""

    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        # this religuishes the CPU so another route can be processed
        # but it's far from true concurrency
        # https://github.com/miguelgrinberg/Flask-SocketIO/issues/896
        socketio.sleep(0)

@app.route('/video_feed')
def video_feed():
    #"""Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(relayCam),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

#===========================================================
# heartbeat
@socketio.on("hb_from_client", namespace='/heartbeat')
def hb_from_client(message):
    #print("======================================")
    #print("rx client HEARBEAT")
    #print(message)
    return "OK"
def m_hb_cb(data):
    print("m_hb_cb: " + data)
@socketio.on('connect', namespace='/heartbeat')
def connet():
    print("======================================")
    print("hearbeat client connected")
    return "OK"
@socketio.on('disconnect', namespace='/heartbeat')
def test_disconnect():
    print('hearbeat client disconnected')


#=====================================================
# main
if __name__ == '__main__':
    print("starting socketio")

    socketio.run(app, certfile='/etc/letsencrypt/live/roocell.com/fullchain.pem',
                    keyfile='/etc/letsencrypt/live/roocell.com/privkey.pem',
                    debug=False, host='0.0.0.0', use_reloader=False)
