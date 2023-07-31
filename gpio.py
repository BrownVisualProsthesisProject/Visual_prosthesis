import Jetson.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)
channel = 15
cont = 0
GPIO.setup(channel, GPIO.OUT)

while cont<80:
   GPIO.output(channel, GPIO.HIGH)
   
   time.sleep(1)
   GPIO.output(channel, GPIO.LOW)

   time.sleep(3)
   cont+=1
   print(cont)

GPIO.cleanup()
