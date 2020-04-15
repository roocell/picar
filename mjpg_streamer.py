import os

def start(resolution, fps):
  os.system("killall mjpg_streamer")
  cmd = "/usr/local/bin/mjpg_streamer -i \"/usr/local/lib/mjpg-streamer/input_uvc.so -n -f " + fps +" -r " + \
       resolution + "\"  -o \"/usr/local/lib/mjpg-streamer/output_http.so -p 8085 -w /usr/local/share/mjpg-streamer/www\"&"
  os.system(cmd)

#start("800x600")
