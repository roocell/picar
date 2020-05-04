#!/usr/local/bin python3

# a python socketio client
import socketio
import time

sio = socketio.Client()

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

#@sio.on('hb_from_server')
#def on_message(data):
#    print('I received hb_from_server!')

def background_task(my_argument):
    # do some background work here!
    # this is background work while the client is connecting
    print("my background task " + str(my_argument) + " while socketio does it's thing")
    sio.sleep(2)
    print("my background task says: yo!")
    pass


print("connecting...")
sio.start_background_task(background_task, 123)
sio.connect('http://localhost:5000', namespaces=['/heartbeat'])

#sio.wait()
time.sleep(3)

print("entering main loop")
while 1:
    time.sleep(3)
    print("ML: sending hb_from_client")
    sio.emit("hb_from_client", {'foo' : 'bar'}, namespace='/heartbeat')
