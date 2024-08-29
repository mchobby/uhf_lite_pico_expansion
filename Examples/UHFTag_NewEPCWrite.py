# UHFTag_NewEPCWrite.py : demonstrate how to write the EPC in the memory of UHF Tags.
#
# See also the UHFTag_IncrEPCWriter.py resulting from this experiment.
#
# Remarks:
#  Only EPC and USER memory are writeable
#  EPC Memory: (Read/Write) allow to change default EPC value of Tag
#  USER Memory: (Read/Write) to store required data

from machine import Pin
import time
from uhf import UHF, EPC_BANK

#UHF enable pin connected at GP4
enable_pin = machine.Pin(4, machine.Pin.OUT) # set pin as OUTPUT
enable_pin.value(0) # LOW value enables UHF module, HIGH to disable module

uhf = UHF(baudrate=115200) # create instance for class UHF

# Select the Tag for write operation
response = uhf.Set_select_pera('80464500e280101010121100') # change with the EPC of the tag, which you want to write
print(response)

'''Make sure to maintain correct data length cannot exceed 32 words (64 bytes) for write operation, as shown below
e.g.
91418800000000000000000000000000  => Any Data, 32 word length
10c9340080464500e280101010121100  => with EPC value, again 32 word length

- Build write data for USER : simply contains byte value of your choice

- Build EPC write data : this include,
Checksum (of Previous EPC) + PC(of Previous EPC) + EPC (change with NEW) =>
10c9 + 3400 + 80464500e280101010121100

To get checksum and PC of Tag run below script first,
https://github.com/sbcshop/UHF_Lite_Pico_Expansion_Software/blob/main/Examples/multiple_read.py
'''

#Change Data which you want to Write, in case of EPC write build correct data format as shown above
# Read single_read.py returned
# * CRC= c4 1e , PC= 34 00 ,
# * EPC = ['30', '08', '33', 'b2', 'dd', 'd9', '01', '40', '00', '00', '00', '00']
# Change EPC to
# * ['30', '08', '33', 'b2', 'dd', 'd9', '01', '40', '00', '00', '00', '02'] change the last byte
# data_w will be:
#   Checksum (of Previous EPC) + PC(of Previous EPC) + EPC (change with NEW)
#   c4 1e + 34 00 + 300833b2ddd9014000000002
response = uhf.Write_tag_data('c41e3400300833b2ddd9014000000002', EPC_BANK ) # Memory Bank = 1, maximum length is 32 words
print( response )
