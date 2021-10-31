import RPi.GPIO as GPIO 
from time import sleep 
GPIO.setmode(GPIO.BCM) 
GPIO.setwarnings(False) # Ignore warning for now


SEND_NANO_PIN = 20
RECEIVE_NANO_PIN=16

GPIO.setup(SEND_NANO_PIN, GPIO.OUT) 
GPIO.setup(RECEIVE_NANO_PIN, GPIO.IN, pull_up_down = GPIO.PUD_UP)

# default no signal is HIGH, send low to trigger shutdown sequence
GPIO.output(SEND_NANO_PIN, GPIO.HIGH)
def button_callback(channel):
    print('Power off system')
GPIO.add_event_detect(RECEIVE_NANO_PIN, GPIO.FALLING, callback = button_callback)




while True: 
    # print(GPIO.input(RECEIVE_NANO_PIN))
    pass