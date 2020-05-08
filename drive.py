import time
from SunFounder_PCA9685 import Servo
from SunFounder_PCA9685 import PCA9685
import RPi.GPIO as GPIO

steering = Servo.Servo(0)
steering.setup()

motor = PCA9685.PWM() # I2C address 0x40
motor.frequency = 60
motorchannel = 15 # channel 16 (last one)

# setup up GPIO to L293D for motor driver
motorPin1 = 13 # GPIO27
motorPin2 = 11 # GPIO17

def setupMotor():
    global motorPin1
    global motorPin2
    GPIO.setmode(GPIO.BOARD)      # use PHYSICAL GPIO Numbering
    GPIO.setup(motorPin1,GPIO.OUT)   # set pins to OUTPUT mode
    GPIO.setup(motorPin2,GPIO.OUT)

def direction(value):
    global motorPin1
    global motorPin2
    # this is because we're using L293D
    # on the real picar all we will control is the PWM
    # does that mean we can't go backwards?
    if (value > 0):
        # forward
        GPIO.output(motorPin1,GPIO.HIGH)
        GPIO.output(motorPin2,GPIO.LOW)
    elif (value < 0):
        # backward
        GPIO.output(motorPin1,GPIO.LOW)
        GPIO.output(motorPin2,GPIO.HIGH)
    else:
        # stop
        GPIO.output(motorPin1,GPIO.LOW)
        GPIO.output(motorPin2,GPIO.LOW)


def loop():
    while True:
            # rotate servo 180 degrees and back
            # in 5 degree steps
            for i in range(0, 180, 5):
                    steering.write(i)
                    time.sleep(0.1)
            for i in range(180, 0, -5):
                    steering.write(i)
                    time.sleep(0.1)

            steering.write(0)

            # ramp motor up and down
            # can also be tested with LED
            direction(1)
            for i in range(0, 4095, 10):
                    motor.write(motorchannel, 0, i)
                    time.sleep(0.0001)
            direction(-1)
            for i in range(4095, -1, -10):
                    motor.write(motorchannel, 0, i)
                    time.sleep(0.0001)
            direction(0)

def destroy():
    global steering
    GPIO.cleanup()                    # Release GPIO resource
    steering.write(0)


if __name__ == '__main__':     # Program entrance
    setupMotor()
    try:
        loop()
    except KeyboardInterrupt:  # Press ctrl-c to end the program.
        destroy()
