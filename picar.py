import os
import RPi.GPIO as GPIO
import time

steeringPin1 = 11 # gpio27
steeringPin2 = 13 # gpio17
steeringEnablePin = 15 # gpio22

drivePin1 = 18 # gpio23
drivePin2 = 16 # gpio24
driveEnablePin = 22 #gpio25

picarIsSetup = 0

def mapNUM(value,fromLow,fromHigh,toLow,toHigh):
    return (toHigh-toLow)*(value-fromLow) / (fromHigh-fromLow) + toLow

def setup():
    global pDrive
    global pSteer
    global picarIsSetup

    # user could hit refresh - we don't want to setup the PI hardware again.
    if (picarIsSetup == 1):
        return

    picarIsSetup = 1

    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(steeringPin1,GPIO.OUT)   # set pins to OUTPUT mode
    GPIO.setup(steeringPin2,GPIO.OUT)
    GPIO.setup(steeringEnablePin,GPIO.OUT)

    GPIO.setup(drivePin1,GPIO.OUT)   # set pins to OUTPUT mode
    GPIO.setup(drivePin2,GPIO.OUT)   # set pins to OUTPUT mode
    GPIO.setup(driveEnablePin,GPIO.OUT)   # set pins to OUTPUT mode

    pDrive = GPIO.PWM(driveEnablePin,1000) # creat PWM and set Frequence to 1KHz
    pDrive.start(0)

    pSteer = GPIO.PWM(steeringEnablePin,1000) # creat PWM and set Frequence to 1KHz
    pSteer.start(0)


def forward(speed = 128):
    GPIO.output(drivePin1,GPIO.HIGH)
    GPIO.output(drivePin2,GPIO.LOW)
    pDrive.start(mapNUM(abs(speed),0,128,0,100))

def backward(speed = -128):
    GPIO.output(drivePin1,GPIO.LOW)
    GPIO.output(drivePin2,GPIO.HIGH)
    pDrive.start(mapNUM(abs(speed),0,128,0,100))

def stop():
    GPIO.output(drivePin1,GPIO.LOW)
    GPIO.output(drivePin2,GPIO.LOW)
    pDrive.start(mapNUM(abs(0),0,128,0,100))


def left(speed = 128):
    GPIO.output(steeringPin1,GPIO.HIGH)
    GPIO.output(steeringPin2,GPIO.LOW)
    pSteer.start(mapNUM(abs(speed),0,128,0,100))

def right(speed = -128):
    GPIO.output(steeringPin1,GPIO.LOW)
    GPIO.output(steeringPin2,GPIO.HIGH)
    pSteer.start(mapNUM(abs(speed),0,128,0,100))

def straight():
    GPIO.output(steeringPin1,GPIO.LOW)
    GPIO.output(steeringPin2,GPIO.LOW)
    pSteer.start(mapNUM(abs(0),0,128,0,100))

def destroy():
    GPIO.cleanup()
