# sudo apt-get install python3-pygame
# be sure to turn off the video coming out of the audio jack
# sudo vi /boot/config.txt
# hdmi_force_hotplug=1

import pygame
import time

pygame.mixer.pre_init()
pygame.mixer.init()
pygame.init()
sound = pygame.mixer.Sound("sounds/ooga.wav")
sound.set_volume(0.1)
sound.play()

# duh! need the script to run in order for the sound to come out!
time.sleep(5)
