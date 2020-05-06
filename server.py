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
from flask_socketio import SocketIO, emit

# to overcome error
# ValueError: Too many packets in payload
# (can probably implement a fps limiter as well)
from engineio.payload import Payload
Payload.max_decode_packets = 100


from camera_relay import Camera
relayCam = Camera()


# create logger
log = logging.getLogger('server.py')
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.threading = True
socketio = SocketIO(app)

@app.route('/')
def index():
    return """<html>
              <head>
                <title>picar streaming video</title>
              </head>
              <body>
                <img src="http://www.roocell.com:5000/video_feed">
              </body>
            </html>"""

@socketio.on('connect', namespace='/heartbeat')
def m_heartbeat():
    print("======================================")
    print("client connected")
    #print("tx server HEARBEAT")
    socketio.emit('hb_from_server', {'data': 'OK'}, callback=m_hb_cb)

# incoming
@socketio.on("hb_from_client", namespace='/heartbeat')
def hb_from_client(message):
    print("======================================")
    print("rx client HEARBEAT")
    print(message)
    return "OK"

def m_hb_cb(data):
    print("m_hb_cb: " + data)

@socketio.on("video_source", namespace='/video')
def video_source(message):
    #print("=======================")
    log.debug("rx video frame")
    #print(message)
    # push this frame to the video destination client
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


@socketio.on('disconnect', namespace='/heartbeat')
def test_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    print("starting socketio")
    #socketio.run(app, certfile='cert.pem', keyfile='key.pem', debug=True, host='0.0.0.0')
    #socketio.run(app, log_output=False, debug=True, host='0.0.0.0')
    socketio.run(app, debug=False, host='0.0.0.0')
