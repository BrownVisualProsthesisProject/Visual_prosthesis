import Jetson.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)
CHANNEL = 15
cont = 0
GPIO.setup(CHANNEL, GPIO.OUT)
while cont<80:
   GPIO.output(CHANNEL, GPIO.HIGH)
   time.sleep(15)
   GPIO.output(CHANNEL, GPIO.LOW)

   cont+=1
   print(cont)

GPIO.cleanup()
