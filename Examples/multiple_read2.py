# multiple_read2.py - Start reading for specific number of seconds (10 sec)
#  and collect all the distinct EPC detected
#
from machine import UART, Pin,SPI,I2C
import time
from uhf import UHF
enable_pin = machine.Pin(4, machine.Pin.OUT)
enable_pin.value(0) # (0)Enable the Module,(1)Disable the Module

SCAN_MS = 10000 # 10 seconds

uhf = UHF(baudrate = 115200)

'''
Uncomment corresponding section to increase reading range,
you will have to set the region as per requirment
'''
uhf.setRegion_EU()
#uhf.setRegion_US()

try:
	while True:
		uhf.multiple_read()
		try:
			print( '--------------------------------------------' )
			print( 'Acquiring for %i ms' % SCAN_MS )
			hashdic = {} # Use dictionnary to collect unique EPC
			start_time = time.ticks_ms()
			while time.ticks_diff( time.ticks_ms(), start_time ) < SCAN_MS:
				rev = uhf.read_mul()
				if rev is not None:
					epc = "".join(rev[8:20])
					hashdic[epc] = None # Append or update the entry
				time.sleep_ms( 1 ) # time.sleep(0.0009)
			print( list(hashdic.keys()) )
		finally:
			uhf.stop_read()
			time.sleep(1)
except KeyboardInterrupt:
    print("User abort!")
except Exception as err:
	print( err )
