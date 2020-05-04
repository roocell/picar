import os
import datetime
import glob

def go():
  #cmd = "fswebcam -r 1280x720 --no-banner image3.jpg"
  suffix = datetime.datetime.now()
  filename = ""+ suffix.strftime("%m-%d-%Y_%H:%M:%S") + ".jpg"
  cmd = "wget http://localhost:8085/?action=snapshot -O static/images/" + filename
  os.system(cmd)

# TODO: this should really return json
# and then the JS can make the innerHTML
def innerHTML():
    from os import listdir
    from os.path import isfile, join
    mypath = "static/images/"
    files = glob.glob(mypath+"*.jpg")
    files.sort(key=os.path.getmtime, reverse=True)
    innerHTML = ""
    for file in files:
        filename = os.path.basename(file)
        innerHTML += "<a href=\""+file+"\"> <img src=\""+file+"\" width=30 height=30>"+filename+"</img></a><BR>"
    return innerHTML
