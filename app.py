from flask import Flask, jsonify, render_template, request, send_from_directory
import os
import mjpg_streamer
import snap
import picar
import atexit

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
@app.route('/static/images')
def no_images():
    return "Nothing"
@app.route('/static/images/<filename>')
def download_file(filename):
    mypath = os.path.join(app.static_folder, 'images')
    return send_from_directory(mypath, filename, as_attachment=True)


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
    picar.destroy()

if __name__ == '__main__':
    mjpg_streamer.start("320x240", "10")
    atexit.register(cleanup)
    picar.setup()
    app.run(debug=True, host='0.0.0.0')
