#!/usr/bin/env python3
import RPi.GPIO as GPIO
import os, time

wifiSwitch = 7  # pin 7  GPIO4

wlanfile = "/etc/wpa_supplicant/wpa_supplicant-wlan1.conf"
tether = "sudo cp -f /etc/wpa_supplicant/tether.conf.bak /etc/wpa_supplicant/wpa_supplicant-wlan1.conf"
wifi = "sudo cp -f /etc/wpa_supplicant/roocell.conf.bak /etc/wpa_supplicant/wpa_supplicant-wlan1.conf"
restart = "sudo wpa_cli -i wlan1 reconfigure"

tetherssid = "ssid=\"iPhone"
wifissid = "ssid=\"roocell"

def setup():
    GPIO.setmode(GPIO.BOARD)      # use PHYSICAL GPIO Numbering
    GPIO.setup(wifiSwitch, GPIO.IN, pull_up_down=GPIO.PUD_UP)    # set wifiSwitch to PULL UP INPUT mode

def loop():
    while True:
        f = open(wlanfile,"r")
        fstr = f.read()

        if (GPIO.input(wifiSwitch) == GPIO.HIGH and tetherssid in fstr):
            # connect to roocell (default)
            print("switching to wifi")
            os.system(wifi)
            os.system(restart)
        elif (GPIO.input(wifiSwitch) == GPIO.LOW and wifissid in fstr):
            print("switching to tether")
            os.system(tether)
            os.system(restart)
        time.sleep(1)

def destroy():
    GPIO.cleanup()                    # Release GPIO resource

if __name__ == '__main__':     # Program entrance
    setup()
    try:
        loop()
    except KeyboardInterrupt:  # Press ctrl-c to end the program.
        destroy()
