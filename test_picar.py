#!/usr/bin/env python3
#############################################################################
# Filename    : Motor.py
# Description : Control Motor with L293D
# Author      : www.freenove.com
# modification: 2019/12/27
########################################################################
import RPi.GPIO as GPIO
import time

# define the pins connected to L293D 
motoRPin1 = 13
motoRPin2 = 11
enablePin = 15

drivePin1 = 16 # gpio23
drivePin2 = 18 # gpio24
enableDrivePin = 22 #gpio25

def setup():
    global p
    global p2

    GPIO.setmode(GPIO.BOARD)   
    GPIO.setup(motoRPin1,GPIO.OUT)   # set pins to OUTPUT mode
    GPIO.setup(motoRPin2,GPIO.OUT)
    GPIO.setup(enablePin,GPIO.OUT)
        
    GPIO.setup(drivePin1,GPIO.OUT)   # set pins to OUTPUT mode
    GPIO.setup(drivePin2,GPIO.OUT)   # set pins to OUTPUT mode
    GPIO.setup(enableDrivePin,GPIO.OUT)   # set pins to OUTPUT mode

    p = GPIO.PWM(enablePin,1000) # creat PWM and set Frequence to 1KHz
    p.start(0)

    p2 = GPIO.PWM(enableDrivePin,1000) # creat PWM and set Frequence to 1KHz
    p2.start(0)

# mapNUM function: map the value from a range of mapping to another range.
def mapNUM(value,fromLow,fromHigh,toLow,toHigh):
    return (toHigh-toLow)*(value-fromLow) / (fromHigh-fromLow) + toLow
	
# motor function: determine the direction and speed of the motor according to the input ADC value input
def motor(value):
    if (value > 0):  # make motor turn forward
        GPIO.output(motoRPin1,GPIO.HIGH)  # motoRPin1 output HIHG level
        GPIO.output(motoRPin2,GPIO.LOW)   # motoRPin2 output LOW level
        print ('Turn Forward...')
    elif (value < 0): # make motor turn backward
        GPIO.output(motoRPin1,GPIO.LOW)
        GPIO.output(motoRPin2,GPIO.HIGH)
        print ('Turn Backward...')
    else :
        GPIO.output(motoRPin1,GPIO.LOW)
        GPIO.output(motoRPin2,GPIO.LOW)
        print ('Motor Stop...')
    p.start(mapNUM(abs(value),0,128,0,100))
    print ('The PWM duty cycle is %d%%\n'%(abs(value)*100/127))   # print PMW duty cycle.


def drive(value):
    if (value > 0):  # make motor turn forward
        GPIO.output(drivePin1,GPIO.HIGH)  # motoRPin1 output HIHG level
        GPIO.output(drivePin2,GPIO.LOW)   # motoRPin2 output LOW level
        print ('Turn Forward...')
    elif (value < 0): # make motor turn backward
        GPIO.output(drivePin1,GPIO.LOW)
        GPIO.output(drivePin2,GPIO.HIGH)
        print ('Turn Backward...')
    else :
        GPIO.output(drivePin1,GPIO.LOW)
        GPIO.output(drivePin2,GPIO.LOW)
        print ('Motor Stop...')
    p2.start(mapNUM(abs(value),0,128,0,100))
    print ('The PWM duty cycle is %d%%\n'%(abs(value)*100/127))   # print PMW duty cycle.


def loop():
    while True:
        #motor(value)
        #time.sleep(0.01)
        motor(128)
        drive(128)
        time.sleep(2)
        motor(-128)
        drive(-128)
        time.sleep(2)

def destroy():
    GPIO.cleanup()
    
if __name__ == '__main__':  # Program entrance
    print ('Program is starting ... ')
    setup()
    try:
        loop()
    except KeyboardInterrupt: # Press ctrl-c to end the program.
        destroy()

