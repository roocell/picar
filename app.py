from flask import Flask, jsonify, render_template, request, send_from_directory
import os
import mjpg_streamer
import snap

app = Flask(__name__)

@app.route('/')
def index():
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

@app.route('/takeSnapshot')
def takeSnapshot():
    print('taking picture...')
    snap.go()
    return "Nothing"

# allows static file subdirectories to be download / displayed
@app.route('/static/images/<filename>')
def download_file(filename):
    mypath = os.path.join(app.static_folder, 'images')
    return send_from_directory(mypath, filename, as_attachment=True)


@app.route('/moveForward')
def moveForward():
    print('moving forward')
    return "Nothing"

@app.route('/moveBackward')
def moveBackward():
    print('moving backward')
    return "Nothing"

@app.route('/moveLeft')
def moveLeft():
    print('moving left')
    return "Nothing"

@app.route('/moveRight')
def moveRight():
    print('moving right')
    return "Nothing"

@app.route('/neutral')
def neutral():
    print('in neutral')
    return "Nothing"

@app.route('/steeringOff')
def steeringOff():
    print('no steering - go straight')
    return "Nothing"


if __name__ == '__main__':
    mjpg_streamer.start("320x240", "10")
    app.run(debug=True, host='0.0.0.0')
