import time
from SunFounder_PCA9685 import PCA9685
import logging

# traxxas
# steering and motor are both controlled via PWM
# 100 Hz, 10ms cycle
# Vpp = 3.44V  (so use 3V3)

# idle is 14-15% duty cycle
# forward/left is 20% duty cycle
# reverse/right is 10% duty cycle


class Drive:
    motorChannel = 11
    steeringChannel = 4
    pwmMax = 4096 # PCA9682 is 12 bits resolution

    maxForwardDutyCycle = 20
    maxForwardPwm = pwmMax * maxForwardDutyCycle / 100
    maxReverseDutyCycle = 10
    maxReversePwm = pwmMax * maxReverseDutyCycle / 100
    idleMotorDutyCycle = 15
    idleMotorPwm = pwmMax * idleMotorDutyCycle / 100

    maxLeftDutyCycle = 20
    maxLeftPwm = pwmMax * maxLeftDutyCycle / 100
    maxRightDutyCycle = 10
    maxRightPwm = pwmMax * maxRightDutyCycle / 100
    straightDutyCycle = 15
    straightPwm = pwmMax * straightDutyCycle / 100


    # create logger
    log = logging.getLogger('drive.py')
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)


    def __init__(self, name):
        self.name = name
        self.pwm = PCA9685.PWM() # I2C address 0x40
        self.pwm.setup()

        """
        The internal reference clock is 25mhz (25000000.0) but may vary slightly
        with environmental conditions and
        manufacturing variances. Providing a more precise ``refclock`` can improve the
        accuracy of the frequency and duty_cycle computations.
        Have to imperically figure out the refclock tuning with an oscilloscope
        """
        self.pwm.refclock = 26000000.0
        self.pwm.frequency = 100 # Hz

    def forward(self, percentage): # 0 .. 100
        pwmval = self.idleMotorPwm + (self.maxForwardPwm - self.idleMotorPwm) * percentage / 100
        self.log.debug("forward %d -> %d (idlepwm = %d)", percentage, pwmval, self.idleMotorPwm);
        self.pwm.write(self.motorChannel, 0, int(pwmval))
    def reverse(self, percentage): # 0 .. -100
        if (percentage > 0):
            self.log.error("reverse percentage must be negative" + str(percentage))
            return "error"
        pwmval = self.idleMotorPwm + (self.idleMotorPwm - self.maxReversePwm) * percentage / 100
        self.log.debug("reverse %d -> %d (idlepwm = %d)", percentage, pwmval, self.idleMotorPwm);
        self.pwm.write(self.motorChannel, 0, int(pwmval))
    def neutral(self):
        self.log.debug("neutral")
        self.pwm.write(self.motorChannel, 0, int(self.idleMotorPwm))

    def left(self, percentage): # 0 .. 100
        pwmval = self.straightPwm + (self.maxLeftPwm - self.straightPwm) * percentage / 100
        self.log.debug("left %d -> %d (straightPwm = %d)", percentage, pwmval, self.straightPwm);
        self.pwm.write(self.steeringChannel, 0, int(pwmval))
    def right(self, percentage): # 0 .. -100
        if (percentage > 0):
            self.log.error("right percentage must be negative", str(percentage))
            return "error"
        pwmval = self.straightPwm + (self.straightPwm - self.maxRightPwm) * percentage / 100
        self.log.debug("right %d -> %d (straightPwm = %d)", percentage, pwmval, self.straightPwm);
        self.pwm.write(self.steeringChannel, 0, int(pwmval))
    def straight(self):
        self.log.debug("straight")
        self.pwm.write(self.steeringChannel, 0, int(self.straightPwm))

    def allstop(self):
        self.neutral()
        self.straight()

    # tested with LEDs first
    def testloop(self):
        delay = 0.01
        step = 1
        print(self.name)
        while True:
            # ramp up forward to max
            for i in range(0, 100, step):
                self.forward(i)
                time.sleep(delay)
            self.log.debug("holding max forward")
            time.sleep(5)

            # ramp up reverse to max
            for i in range(0, -100, -1*step):
                self.reverse(i)
                time.sleep(delay)
            self.log.debug("holding max reverse")
            time.sleep(5)

            self.stop()
            self.log.debug("holding idle")
            time.sleep(5)

            for i in range(0, 100, step):
                self.left(i)
                time.sleep(delay)
            self.log.debug("holding max left")
            time.sleep(5)

            for i in range(0, -100, -1*step):
                self.right(i)
                time.sleep(delay)
            self.log.debug("holding max right")
            time.sleep(5)

            self.straight()
            self.log.debug("holding straight")
            time.sleep(5)

    def cleanup(self):
        self.pwm.write(self.motorChannel, 0, 0)
        self.pwm.write(self.steeringChannel, 0, 0)

def destroy():
    drive.cleanup()

if __name__ == '__main__':     # Program entrance
    drive = Drive("traxxas")
    try:
        drive.testloop()
    except KeyboardInterrupt:  # Press ctrl-c to end the program.
        destroy()
