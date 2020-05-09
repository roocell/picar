import time
from SunFounder_PCA9685 import PCA9685

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

    def __init__(self, name):
        self.name = name
        self.pwm = PCA9685.PWM() # I2C address 0x40
        self.pwm.frequency = 100

    # tested with LEDs first
    def testloop(self):
        print(self.name)
        while True:
            # ramp up and down
            # can also be tested with LED
            for i in range(0, 4095, 10):
                    self.pwm.write(self.motorChannel, 0, i)
                    self.pwm.write(self.steeringChannel, 0, i)
                    time.sleep(0.001)
            for i in range(4095, -1, -10):
                    self.pwm.write(self.motorChannel, 0, i)
                    self.pwm.write(self.steeringChannel, 0, i)
                    time.sleep(0.001)
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
