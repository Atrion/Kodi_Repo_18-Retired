import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM) # Use GPIO numbers
 
RELAIS_1_GPIO = 18 # GPIO used
GPIO.setup(RELAIS_1_GPIO, GPIO.OUT) # Set GPIO mode
GPIO.output(RELAIS_1_GPIO, GPIO.HIGH) # Relay ON
