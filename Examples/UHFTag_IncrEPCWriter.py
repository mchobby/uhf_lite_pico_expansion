# UHFTag_IncEPCWrite.py - update the EPC of a presented tag and change the
# EPC last 4 bytes with an auto-incremented Number.
# Very Useful to create series of tags.
#
# See:
# * EPC_INITIAL_COUNTER can be updated to suite the needs.
# * calculate_new_upc() can be updated to change the numbering scheme
#
# Run me with the following command to get all the REPL message on the screen:
#  mpremote run UHFTag_IncrEPCWriter.py
#
# How it work:
#   1) Read a single_tag (get EPC with CRC & PC)
#   2) Write a new EPC in the Tag
#   3) Reread the tag & Check EPC change
#   4) if change Succeed:
#   4.1)   Increment Number
#   4.2)   Display Success! + Wait 5 seconds
#   4.3)   Restart at 1
#
# So, if it reads 300833b2ddd9014000000000 it will renumber 300833b2ddd90140 + 00000001
# then next one will be 300833b2ddd90140 + 00000002
# then next one will be 300833b2ddd90140 + 00000003
# and so on ...
from machine import UART, Pin,SPI,I2C
import time
from uhf import UHF, EPC_BANK, WriteTagError

EPC_INITIAL_COUNTER = 7 # Nex value used. See also calculate_new_epc() to customise number

enable_pin = machine.Pin(4, machine.Pin.OUT)
enable_pin.value(0)
uhf = UHF(baudrate=115200)
uhf.setRegion_EU()
#uhf.setRegion_US()

def calculate_new_epc( current_epc, epc_counter ):
	# Return the new UPC based on epc_counter FOR A GIVEN current_epc TAG.

	# Update the lower 4 bytes (so 8 Hex digits)
	# 300833b2ddd90140 + 00000002
	return '%s%08x' % (epc[:16],epc_counter)


def read_single_tag():
	global uhf

	_r = None # Result tuple ( pc, epc, crc )
	retry = 1
	while _r == None:
		print( "Single read attempt #%i" % retry)
		retry += 1

		rev = uhf.single_read()
		if rev is not None:
			#print('PC = ',rev[6],rev[7])
			#print('EPC = ',rev[8:20])
			#print('RSSI(dBm) = ',rev[5])
			#print('CRC = ',rev[20],rev[21] )
			_r = ( '%s%s' %(rev[6],rev[7]), "".join(rev[8:20]), '%s%s' %(rev[20],rev[21]) )
			break

		time.sleep(1)

	# Just wait before stopping
	time.sleep(1)
	uhf.stop_read()
	return _r


epc_counter = EPC_INITIAL_COUNTER # first value for new EPC value
while True:
	try:
		print( "" )
		print( "" )
		print( "" )
		print( "--- Capture tag ---------------------------------------------------")
		print( "Next epc_counter = %i" % epc_counter )
		pc, epc, crc = read_single_tag()
		print( 'current tag EPC:', epc )

		#Select the Tag for write operation
		r = uhf.Set_select_pera(epc) # change with the EPC of the tag, which you want to write
		if not( r ):
			print( '[ERROR] Tag selection failed! Restarting...' )
			print( '' )
			time.sleep(5)
			continue
		else:
			print( "Tag selection done!" )

		# Compute new EPC
		new_epc = calculate_new_epc( epc, epc_counter )
		print( "New EPC: ", epc,'-->',new_epc )

		print( "Updating Tag ..." )
		r = uhf.Write_tag_data( '%s%s%s'%(crc,pc,new_epc), EPC_BANK ) # Memory Bank = 1, maximum length is 32 words
		if r:
			print( "Write Successful")
		else:
			print( "[ERROR] Write denied!")
			time.sleep(5)
			continue

		print( "Checking the updated tag...")
		pc, epc, crc = read_single_tag()
		print( "Read EPC: ", epc )

		if epc == new_epc:
			print( "<SUCCESS> %i" % epc_counter )
			print( "<SUCCESS> %i" % epc_counter )
			print( "<SUCCESS> Tag EPC %i successfuly updated! :-)" % epc_counter )
			print( "<SUCCESS> %i" % epc_counter )
			print( "<SUCCESS> %i" % epc_counter )
			epc_counter += 1
			print( "Next epc_counter = %i" % epc_counter )
		else:
			print( "[FAILED]" )
			print( "[FAILED]" )
			print( "[FAILED] Tag EPC update failure!!! (currently %s)" % epc )
			print( "[FAILED]" )
			print( "[FAILED]" )
	except WriteTagError as err:
		print(  "[ERROR]", err ) # Just capture it!

	print( "Pausing...")
	print( "" )
	print( "" )
	time.sleep(5)
	#²print( response )
