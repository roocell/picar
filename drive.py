import time
from SunFounder_PCA9685 import PCA9685
import logging
from threading import Thread

# traxxas
# steering and motor are both controlled via PWM
# 100 Hz, 10ms cycle
# Vpp = 3.44V  (so use 3V3)

# idle is 14-15% duty cycle
# forward/left is 20% duty cycle
# reverse/right is 10% duty cycle

# need to keep track of previous settings so we can do
# a more smooth control of the motor/servo.
# this will also help control the braking/reverse
# control. if we were moving forward we have to brake (10%)
# then goto 15% for a period before we can actually reverse.


class Drive:
    motorChannel = 11
    steeringChannel = 4
    pwmMax = 4096 # PCA9682 is 12 bits resolution

    maxForwardDutyCycle = 20
    maxForwardPwm = int(pwmMax * maxForwardDutyCycle / 100)
    maxReverseDutyCycle = 10
    maxReversePwm = int(pwmMax * maxReverseDutyCycle / 100)
    idleMotorDutyCycle = 15.1
    idleMotorPwm = int(pwmMax * idleMotorDutyCycle / 100)

    maxLeftDutyCycle = 20
    maxLeftPwm = int(pwmMax * maxLeftDutyCycle / 100)
    maxRightDutyCycle = 10
    maxRightPwm = int(pwmMax * maxRightDutyCycle / 100)
    straightDutyCycle = 15
    straightPwm = int(pwmMax * straightDutyCycle / 100)

    lastMotorPWM = idleMotorPwm
    lastSteeringPWM = straightPwm
    smoothTrigger = int(0.05 * maxForwardPwm) # 5% to trigger smoothing
    smoothStep = int(0.01 * maxForwardPwm) # 1% smoothly steps
    smoothDelay = 0.01

    # init - just so our check to kill it works
    smoothMotorThread = Thread(target=None, args=(idleMotorPwm))
    smoothSteeringThread = Thread(target=None, args=(straightPwm))

    # create logger
    log = logging.getLogger(__file__)
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

        # initialize PWM to idle values
        self.allstop()


    def smoothMotor(self, newPwm, stop):
        self.log.debug("smoothMotor: %d -> %d (trigger %d)", self.lastMotorPWM, newPwm, self.smoothTrigger)
        if (abs(self.lastMotorPWM - newPwm) >= self.smoothTrigger):
            # ramp to newPwm in steps
            pwmval = self.lastMotorPWM
            if (newPwm > pwmval):
                dir = 1
            else:
                dir = -1
            while pwmval != newPwm:
                if (stop()):
                    break
                pwmval += self.smoothStep * dir
                if ((pwmval > newPwm and dir == 1) or (pwmval < newPwm and dir == -1)):
                    pwmval = newPwm
                self.log.debug("smoothMotor: " + str(pwmval))
                self.pwm.write(self.motorChannel, 0, int(pwmval))
                self.lastMotorPWM = pwmval;
                if (self.smoothDelay):
                    time.sleep(self.smoothDelay)
        else:
            # go right to new value
            self.pwm.write(self.motorChannel, 0, int(newPwm))
            self.lastMotorPWM = newPwm;

    def smoothSteering(self, newPwm, stop):
        self.log.debug("smoothSteering: %d -> %d (trigger %d)", self.lastSteeringPWM, newPwm, self.smoothTrigger)
        if (abs(self.lastSteeringPWM - newPwm) >= self.smoothTrigger):
            # ramp to newPwm in steps
            pwmval = self.lastSteeringPWM
            if (newPwm > pwmval):
                dir = 1
            else:
                dir = -1
            while pwmval != newPwm:
                if (stop()):
                    break
                pwmval += self.smoothStep * dir
                if ((pwmval > newPwm and dir == 1) or (pwmval < newPwm and dir == -1)):
                    pwmval = newPwm
                self.log.debug("smoothSteering: " + str(pwmval))
                self.pwm.write(self.steeringChannel, 0, int(pwmval))
                self.lastSteeringPWM = pwmval;
                if (self.smoothDelay):
                    time.sleep(self.smoothDelay)
        else:
            # go right to new value
            self.pwm.write(self.steeringChannel, 0, int(newPwm))
            self.lastSteeringPWM = newPwm;


    def forward(self, percentage): # 0 .. 100
        pwmval = self.idleMotorPwm + (self.maxForwardPwm - self.idleMotorPwm) * percentage / 100
        pwmval = int(pwmval)
        #self.log.debug("forward %d -> %d (idlepwm = %d)", percentage, pwmval, self.idleMotorPwm);
        if (self.smoothMotorThread.is_alive()):
            self.log.debug("killing previous smoothMotorThread")
            self.stopMotorThread = True
            self.smoothMotorThread.join()
        self.stopMotorThread = False
        self.smoothMotorThread = Thread(target=self.smoothMotor, args=(pwmval, lambda : self.stopMotorThread,))
        self.smoothMotorThread.start()

    # in order for reverse to work, user has to go reverse one time
    # and then neutral and then reverse again (just like the controller)
    # the important part is to start this script before turning on the ESC
    # if the ESC is flashing then it won't work properly
    def reverse(self, percentage): # 0 .. -100
        if (percentage > 0):
            self.log.error("reverse percentage must be negative" + str(percentage))
            return "error"
        pwmval = self.idleMotorPwm + (self.idleMotorPwm - self.maxReversePwm) * percentage / 100
        pwmval = int(pwmval)
        #self.log.debug("reverse %d -> %d (idlepwm = %d)", percentage, pwmval, self.idleMotorPwm);

        if (self.smoothMotorThread.is_alive()):
            self.log.debug("killing previous smoothMotorThread")
            self.stopMotorThread = True
            self.smoothMotorThread.join()

        # stop is full reverse PWM
        # TODO: not sure if we need to introduce this scary thing
        if (self.lastMotorPWM > self.idleMotorPwm):
            self.log.debug("hitting the brakes")
            #self.pwm.write(self.motorChannel, 0, self.maxReversePwm)
            return

        self.stopMotorThread = False
        self.smoothMotorThread = Thread(target=self.smoothMotor, args=(pwmval, lambda : self.stopMotorThread,))
        self.smoothMotorThread.start()
    def neutral(self):
        # no smoothing here
        self.log.debug("neutral")
        self.pwm.write(self.motorChannel, 0, int(self.idleMotorPwm))
        self.lastMotorPWM = self.idleMotorPwm;

    def left(self, percentage): # 0 .. 100
        pwmval = self.straightPwm + (self.maxLeftPwm - self.straightPwm) * percentage / 100
        pwmval = int(pwmval)
        #self.log.debug("left %d -> %d (straightPwm = %d)", percentage, pwmval, self.straightPwm);
        if (self.smoothSteeringThread.is_alive()):
            self.log.debug("killing previous smoothSteeringThread")
            self.stopSteeringThread = True
            self.smoothSteeringThread.join()
        self.stopSteeringThread = False
        self.smoothSteeringThread = Thread(target=self.smoothSteering, args=(pwmval, lambda : self.stopSteeringThread,))
        self.smoothSteeringThread.start()
    def right(self, percentage): # 0 .. -100
        if (percentage > 0):
            self.log.error("right percentage must be negative", str(percentage))
            return "error"
        pwmval = self.straightPwm + (self.straightPwm - self.maxRightPwm) * percentage / 100
        pwmval = int(pwmval)
        #self.log.debug("right %d -> %d (straightPwm = %d)", percentage, pwmval, self.straightPwm);
        if (self.smoothSteeringThread.is_alive()):
            self.log.debug("killing previous smoothSteeringThread")
            self.stopSteeringThread = True
            self.smoothSteeringThread.join()
        self.stopSteeringThread = False
        self.smoothSteeringThread = Thread(target=self.smoothSteering, args=(pwmval, lambda : self.stopSteeringThread,))
        self.smoothSteeringThread.start()
    def straight(self):
        # no smoothing here
        if (self.smoothSteeringThread.is_alive()):
            self.log.debug("killing previous smoothSteeringThread")
            self.stopSteeringThread = True
            self.smoothSteeringThread.join()

        self.log.debug("straight")
        self.pwm.write(self.steeringChannel, 0, int(self.straightPwm))
        self.lastSteeringPWM = self.straightPwm;

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
