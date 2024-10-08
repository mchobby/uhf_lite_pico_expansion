import machine
import time
import binascii
import array

EPC_BANK  = '1'
USER_BANK = '3'

STARTBYTE     ='BB00'
ENDBYTE       ='7E'

'''2.1 Get the reader module information'''
HARD_VERSION  ='0300010004'

''' 2.3 Several times polling command '''
MULTIPLE_READ ='27000322271083'

''' 2.2 Single polling command '''
SINGLE_READ   ='22000022'

STOP_READ     ='28000028'

''' section: 2.12 Set Working Place'''
SET_REGION_EU = '070001030B' #for Setting EU Region
SET_REGION_US = '070001020A' #for Setting US Region

''' Section: 2.16 Get transmitting power '''
GET_TRANSMIT_PWR = 'B70000B7'

class InvalidResponseFrame( RuntimeError ):
	def __init__( self, msg_or_obj ):
		self.cargo = msg_or_obj

	def __str__( self ):
		return '%s: %r' % (self.__class__.__name__, self.cargo )

class WriteTagError( RuntimeError ):
	def __init__( self, msg, memory_bank ):
		self.msg = msg
		self.memory_bank = memory_bank

	def __str__( self ):
		return '%s for memory_bank=%s' % ( self.msg, self.memory_bank )


class UHF():
    def __init__(self,baudrate, timeout=1000 ):
        self.serial = machine.UART(0, baudrate=baudrate, bits=8, parity=None, stop=1, tx=machine.Pin(0), rx=machine.Pin(1), timeout=timeout)
        self.serial.init(baudrate=baudrate, bits=8, parity=None, stop=1)
        time.sleep(0.2)

    def read_mul(self):
        # Pop tag after multiple_read() call
        rec_data = self.serial.read(24)
        if rec_data is not None and len(rec_data)>22:
            if rec_data[0] != 0xbb or rec_data[23] != 0x7e or rec_data[1] != 0x02:
                return None
            return ['{:02x}'.format(x) for x in rec_data]
        return None

    #####################################################
    def calculate_checksum(self,data):
        checksum = 0
        for byte in data:
            checksum += byte
        checksum_1 = (checksum) % 256
        return checksum

    def calculation(self,Data):
        bin_data1 = binascii.unhexlify(Data)
        chk_1 = (hex(self.calculate_checksum(bin_data1)))
        #print("checksum",chk_1)
        if len(chk_1) == 5:
            return str(chk_1[3:])
        elif len(chk_1) == 4:
            return str(chk_1[2:])
        else:
            return '0'+ str(chk_1[3:])
    ######################################################

    def send_command(self, data):
        # data: list of string (or single string) of hexilified data. ex: '0C001300000000206000'
        Data = ''.join(data)
        bin_data = binascii.unhexlify(Data)
        self.serial.write(bin_data)

    ######################################################

    def Set_select_pera(self,epc):
        # Returns True if select is successfull (otherwise False for Invalid)
        #
        #fig = '0C00130'+Memory_bank+'000000206000'+ epc
        fig = '0C001300000000206000'+ epc
        dat = self.calculation(fig)
        dat1 = STARTBYTE+fig+dat+ENDBYTE
        #print('card select = ',dat1)
        data = self.send_command(dat1)
        time.sleep(0.2)
        rec_data = self.serial.read(16)
        if rec_data is None:
            raise InvalidResponseFrame('missing response')
        a = ['{:02x}'.format(x) for x in rec_data]
        #print('select response = ',a)
        return ("".join(a) == 'bb010c0001000e7e')


    def Read_tag_data(self,memory_bank):
        fig = '390009000000000'+memory_bank+'00000008'
        dat = self.calculation(fig)
        dat1 = STARTBYTE+fig+dat+ENDBYTE
        #print("dat1 = ",dat1)

        data = self.send_command(dat1)
        time.sleep(0.2)
        rec_data = self.serial.read(40)
        if rec_data is not None:
                a = ['{:02x}'.format(x) for x in rec_data]
                print(a)
                if "".join(a) == 'bb01ff0001090a7e':
                     return 'No card is there'

                elif "".join(a) != 'bb01ff0001090a7e':
                    if memory_bank == '2':
                        return "".join(a)[40:72]

                    elif memory_bank == '3':
                        return "".join(a)[40:70]

                    elif memory_bank == '1':
                        return "".join(a)[48:72]



    def Write_tag_data(self,data_w,memory_bank):
        # write a data memory to memory bank (ex: '1' for EPC)
        # data_w is a 16 bytes data (hex encoded string so 32 chars).
        #
        fig = '490019000000000'+memory_bank+'00000008'+ data_w
        dat = self.calculation(fig)
        dat1 = STARTBYTE+fig+dat+ENDBYTE
        # print('write1111 = ',dat1)
        data = self.send_command(dat1)
        time.sleep(0.2)
        rec_data = self.serial.read(23)
        if rec_data is not None:
            a = ['{:02x}'.format(x) for x in rec_data]
            print('write data = ',a)
            if "".join(a) == 'bb01ff000110117e':
                raise WriteTagError('Write card failed, No tag response', memory_bank)
            elif "".join(a) == 'bb01ff000117187e':
                raise WriteTagError('Command error', memory_bank) #' Data length should be should be integer multiple words'
            else:
                return True # 'Card successful write'
        return False
    ################################################################################


    def hardware_version(self):
        self.send_command([STARTBYTE,HARD_VERSION,ENDBYTE])
        time.sleep(0.5)
        d = self.serial.read(19)
        if d is not  None:
            def split_bytes_data(data, packet_size):
                # Split the bytes object into packets of the specified size
                packets = [data[i:i+packet_size] for i in range(0, len(data), packet_size)]
                return packets
            ds = split_bytes_data(d,6)
            s = []
            for i in range(1,len(ds)):
                s.append(str(ds[i],'latin-1'))
            return "".join(s)


    def multiple_read(self):
        # Start multiple read mode. Use read_mul() to pop tags from reader.
        # Use stop_read() to halt reading.
        # Return: True if succeed. False when no tag or CRC error
        data = self.send_command([STARTBYTE, MULTIPLE_READ, ENDBYTE])
        time.sleep(0.2)
        # Do not try to read the confirmation because lots of Notice_Frame may
        # comes before receiving the command confirmation !!!

        '''# Pump up all data from UART (which may also contains some Notice_Frame
        # before the multiple_read conformation)
        while True:
            rec_data = self.serial.read(1) # Timeout of 1 sec
            time.sleep_ms(1)
            if rec_data==None:
                raise InvalidResponseFrame("Empty buffer before multi_read confirmation")

            if rec_data[0]!=0xbb: # not( Start_of_Frame )
                continue
            # Yo! Try to read the content of the confirmation frame
            rec_data = self.serial.read(7) # read the remaining 7 chars
            #print( 'multiple_read rec_data', rec_data)
            if rec_data[0] == 0x01 and rec_data[1] == 0xff and rec_data[6] == 0x7e: # Several_time_polling confirmation
                print( 'Several Time Confirm Confirm', binascii.hexlify(rec_data))
                # Do not purge more data (which may contains other Notice_Frame)
                return # We can exit without error '''


    def stop_read(self):
        self.send_command([STARTBYTE, STOP_READ, ENDBYTE])
        time.sleep_ms(200)
        # Pump up all data from UART (which may also contain some Notice_Frame)
        while True:
            rec_data = self.serial.read(1) # Timeout of 1 sec
            time.sleep_ms(1)
            if rec_data==None:
                raise InvalidResponseFrame("Empty buffer before stop read confirmation")

            if rec_data[0]!=0xbb: # not( Start_of_Frame )
                continue
            # Yo! Try to read the content of the confirmation frame
            rec_data = self.serial.read(7) # read the remaining 7 chars
            if rec_data[0] == 0x01 and rec_data[1] == 0x28: # stop_read confirmation
                # print( 'Stop Frame Confirm', binascii.hexlify(rec_data))
                # Quick purge the remaining of UART
                rec_data = self.serial.read(1)
                while rec_data != None:
                    rec_data = self.serial.read(1)
                return # We can exit without error

    def setRegion_EU(self):
        data = self.send_command([STARTBYTE, SET_REGION_EU, ENDBYTE])
        time.sleep(0.5)
        rec_data = self.serial.read(24)
        #print(rec_data)


    def setRegion_US(self):
        data = self.send_command([STARTBYTE, write_tag, ENDBYTE])
        time.sleep(0.5)
        rec_data = self.serial.read(24)
        #print(rec_data)

    def getTransmit_Power(self):
        data = self.send_command([STARTBYTE, GET_TRANSMIT_PWR, ENDBYTE])
        time.sleep(0.5)
        rec_data = self.serial.read(24)
        return rec_data

    def single_read(self):
        data = self.send_command([STARTBYTE, SINGLE_READ, ENDBYTE])
        time.sleep(0.5)
        rec_data = self.serial.read(24)
        if rec_data is not None and len(rec_data)>22:
            if rec_data[0] != 0xbb or rec_data[23] != 0x7e or rec_data[1] != 0x02:
                return None
            return ['{:02x}'.format(x) for x in rec_data]
