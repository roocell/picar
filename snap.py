import os
import datetime

def go():
  #cmd = "fswebcam -r 1280x720 --no-banner image3.jpg"
  suffix = datetime.datetime.now()
  filename = ""+ suffix.strftime("%m-%d-%Y_%H:%M:%S") + ".jpg"
  cmd = "wget http://localhost:8085/?action=snapshot -O static/images/" + filename
  os.system(cmd)

def browser():
    from os import listdir
    from os.path import isfile, join
    mypath = "static/images"
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    browser = ""
    for file in onlyfiles:
        url = mypath + "/" + file
        browser += "<a href=\""+url+"\"> <img src=\""+url+"\" width=30 height=30>"+file+"</img></a><BR>"
    return browser
