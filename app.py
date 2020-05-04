#!/usr/bin/env python3

# the idea here is to have a phone connected to the picar webserver
# a special location page so the webserver can ask the phone for the geolocation
# and send the location back to the server. so it can then display it on a
# map (to other devices - like the controller)
# the phone will be on the car as well - so it will essentially track the car's
# location

from flask import Flask, jsonify, render_template, request, send_from_directory
import json
import os
import mjpg_streamer
import snap
import picar
import atexit
import time
import apikeys
from config import Config
import models
from models import db, Picar
from flask_socketio import SocketIO, emit

webcam_w = 320
webcam_h = 240
fps = 10

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# create db if it doesn't exists
with app.app_context():
    db.create_all()
    exists = db.session.query(db.exists().where(Picar.id == 1)).scalar()

    #exists = Picar.query.filter_by(id=0).first().scalar()
    if (exists == 0):
        print("creating defaults for picar in db")
        picarDb = Picar(name = "picarv1")
        db.session.add(picarDb)
        db.session.commit()

    # query to make sure it's in there
    #ppp = db.session.query(db.exists().where(Picar.id == 0))
    ppp = Picar.query.filter_by(id=1).first()
    #ppp = Picar.query.get(0)
    print("got picar from db name:" + ppp.name)



#=============================================================
# location routes w/ scoketio
@app.route('/location')
def location():
    return render_template('location.html', key = apikeys.google_map_api)

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# incoming
@socketio.on('new location', namespace='/updatelocation')
def updatelocationIO(message):
    print("======================================")
    print("client updated location via SOCKET")
    emit('my response', {'data': 'OK'})
    # TODO: json.loads doesnt' get all the decimal places.
    data = json.loads(message['data'])
    print(data)
    picarDb = Picar.query.filter_by(id=1).first()
    picarDb.latitude = data['latitude']
    picarDb.longitude = data['longitude']
    db.session.commit()
    loc = {"latitude":picarDb.latitude, "longitude":picarDb.longitude}
    emit('location updated', loc, broadcast=True)

# outgoing
@socketio.on('connect', namespace='/updatelocation')
def test_connect():
    print("client connected")
    picarDb = Picar.query.filter_by(id=1).first()
    loc = {"latitude":picarDb.latitude, "longitude":picarDb.longitude}
    print("DB " + str(loc))
    emit('location updated', loc)





#==============================================
# index route
@app.route('/')
def index():
    picar.setup()  # needs to be in index() otherwise weird output

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
           render_template('joy.html', key = apikeys.google_map_api,
                              # need a little more to get rid of the scrollbars
                               webcam_w=str(webcam_w+20)+"px", webcam_h=str(webcam_h+20)+"px") + \
           render_template('snap.html', innerHTML=snap.innerHTML()) + \
           bottom





#=============================================================
# snapshot routes
@app.route('/takeSnapshot')
def takeSnapshot():
    print('taking picture...')
    snap.go()
    return snap.innerHTML()

# allows static file subdirectories to be download / displayed
@app.route('/static/images')
def no_images():
    return "Nothing"
@app.route('/static/images/<filename>')
def download_file(filename):
    mypath = os.path.join(app.static_folder, 'images')
    return send_from_directory(mypath, filename, as_attachment=True)




#=============================================================
# movement routes
@app.route('/moveForward')
def moveForward():
    print('moving forward')
    picar.forward()
    return "Nothing"

@app.route('/moveBackward')
def moveBackward():
    print('moving backward')
    picar.backward()
    return "Nothing"

@app.route('/moveLeft')
def moveLeft():
    print('moving left')
    picar.left()
    return "Nothing"

@app.route('/moveRight')
def moveRight():
    picar.right()
    print('moving right')
    return "Nothing"

@app.route('/neutral')
def neutral():
    print('in neutral')
    picar.stop()
    return "Nothing"

@app.route('/steeringOff')
def steeringOff():
    print('no steering - go straight')
    picar.straight()
    return "Nothing"


#=====================================================
def cleanup():
    print("cleaning up")
    #picar.destroy()

if __name__ == '__main__':
    mjpg_streamer.start(webcam_w, webcam_h, fps)
    atexit.register(cleanup)


    # https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https
    #app.run(ssl_context=('cert.pem', 'key.pem'), debug=True, host='0.0.0.0')
    #app.run(ssl_context='adhoc', debug=True, host='0.0.0.0')
    #app.run(debug=True, host='0.0.0.0')

    print("running socketio")
    # can't use adgoc. evenlet only work in production server so need to use the SSL files
    socketio.run(app, certfile='cert.pem', keyfile='key.pem', debug=True, host='0.0.0.0')
    print("done run socketio")
