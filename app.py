#!/usr/bin/env python3

# the idea here is to have a phone connected to the picar webserver
# a special location page so the webserver can ask the phone for the geolocation
# and send the location back to the server. so it can then display it on a
# map (to other devices - like the controller)
# the phone will be on the car as well - so it will essentially track the car's
# location

from flask import Flask, jsonify, request, jsonify, render_template, request, send_from_directory
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
    		<link rel="shortcut icon" type="image/png" href="static/raspi.png">
            </head> """
    bottom =  "</html>"
    return top+render_template('joy.html')+render_template('snap.html', browser=snap.browser())+bottom

#=============================================================
@app.route('/takeSnapshot')
def takeSnapshot():
    print('taking picture...')
    snap.go()
    return "Nothing"

# allows static file subdirectories to be download / displayed
@app.route('/static/images')
def no_images():
    return "Nothing"
@app.route('/static/images/<filename>')
def download_file(filename):
    mypath = os.path.join(app.static_folder, 'images')
    return send_from_directory(mypath, filename, as_attachment=True)

#=============================================================
@app.route('/location')
def location():
    return render_template('location.html', key = apikeys.google_map_api)
@app.route('/updatelocation', methods=['GET', 'POST'])
def updatelocation():
    # this will update the blue dot location on the map(s)
    print("updating location")

    # POST request
    if request.method == 'POST':
        print('Incoming..')
        position = request.get_json() # (force=True to ignore mimetype)
        print(position)  # parse as JSON
        # store this in a serverside global for picar's location
        # this is only good in the current session
        picar.location = position

        # but we want this to be retrieve by another session
        # so we have to use a DB
        picarDb = Picar.query.filter_by(id=1).first()
        print("got picar from db name:" + picarDb.name)
        picarDb.latitude = position['latitude']
        picarDb.longitude = position['longitude']
        db.session.commit()
        return 'OK', 200
    # GET request
    else:
        message = {'greeting':'Hello from Flask!'}
        return jsonify(message)  # serialize and use JSON headers
    return "Nothing"
@app.route('/picar_location')
def picar_location():
    print("picar.location " + str(picar.location))
    picarDb = Picar.query.filter_by(id=1).first()
    loc = {"latitude":str(picarDb.latitude), "longitude":str(picarDb.longitude)}
    print("DB " +str(loc))
    return jsonify(loc)


#=============================================================

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



def cleanup():
    print("cleaning up")
    #picar.destroy()

if __name__ == '__main__':
    mjpg_streamer.start("320x240", "10")
    atexit.register(cleanup)

    #https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https
    #app.run(ssl_context=('cert.pem', 'key.pem'), debug=True, host='0.0.0.0')
    app.run(ssl_context='adhoc', debug=True, host='0.0.0.0')
    #app.run(debug=True, host='0.0.0.0')
