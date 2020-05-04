#!/usr/local/bin python3

# Flask server  with FLask-socketio
# this app will display picar web controls, etc
# it will also maintain a socket connection to picar
# so that it can send commands and/or get notified of other events


from flask import Flask, jsonify, request, render_template, send_from_directory
import json
import os, time
import apikeys
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def index():
    return "<html> </html>"
# incoming
@socketio.on("hb_from_client", namespace='/heartbeat')
def hb_from_client(message):
    print("======================================")
    print("rx client HEARBEAT")
    socketio.emit('server_response', {'data': 'OK'})

def m_hb_cb(data):
    print("m_hb_cb: " + data)

@socketio.on('connect', namespace='/heartbeat')
def m_heartbeat():
    print("======================================")
    print("client connected")
    #print("tx server HEARBEAT")
    socketio.emit('hb_from_server', {'data': 'OK'}, callback=m_hb_cb)

@socketio.on('disconnect', namespace='/heartbeat')
def test_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    print("starting socketio")
    #socketio.run(app, certfile='cert.pem', keyfile='key.pem', debug=True, host='0.0.0.0')
    socketio.run(app, debug=True, host='0.0.0.0')
