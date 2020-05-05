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
from flask_socketio import SocketIO, emit

from camera_relay import Camera
relayCam = Camera()

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


def getFrame():
    global frame
    return frame

def setFrame(f):
    global frame
    frame = f

@socketio.on("video_source", namespace='/video')
def video_source(message):
    print("=======================")
    print("rx video frame")
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
    socketio.run(app, debug=True, host='0.0.0.0')
