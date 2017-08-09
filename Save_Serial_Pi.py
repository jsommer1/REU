
# coding: utf-8

# In[ ]:
# This code is to be run from a Raspberry Pi 3. It'll hopefully read in serial data through the UART and save the raw 
# data in 4 separate text files. 


import serial 
import time
import struct
import datetime
import numpy as np


# Initializes serial connection 
ser = serial.Serial() 
ser.bytesize = 8      
ser.baudrate = 115200  
ser.port = '/dev/ttyAMA0'  
ser.stopbits = 1
TIMEOUT = 3
dummy = 1
while dummy == 1:    # Stops reading data after TIMEOUT seconds. User inputs value for TIMEOUT
    try:
        TIMEOUT = float(input("Enter runtime in seconds: "))   
        dummy = 0
    except ValueError:
        print('Please enter a valid runtime.')
ser.open() 


# Creates 4 text files to save data from different leads: ECG1, ECG2, Resp, and PPG
rightnow = datetime.datetime.now()

ecg1 = open('ECG1DATA' + str(rightnow.isoformat()) + '.txt', 'a')  
ecg2 = open('ECG2DATA' + str(rightnow.isoformat()) + '.txt', 'a')
resp = open('RESPDATA' + str(rightnow.isoformat()) + '.txt', 'a')
ppg = open('PPGDATA' + str(rightnow.isoformat()) + '.txt', 'a')

# Compares checksum to sum of rest of data 
checksum = open('CHECKSUM' + str(rightnow.isoformat()) + '.txt', 'a')

#
packnums = open('PACKNUMS' + str(rightnow.isoformat()) + '.txt', 'a')

        
# Initializes empty bytearray to store 12 bytes per packet in 
#packet = bytearray()
# packet = np.zeros(12)
#print ('INITIAL EMPTY PACKET')
#print (packet)
#print ('EVERYTHING ELSE SHOULD HAVE STUFF IN IT')
    

# Starts stopwatch for timeout purposes, this is here because IDK how to properly use PySerial's timeout functions
start_time = time.process_time()


# Syncs w/ beginning of a packet by clearing serial input and waiting for silent period between packets
while True:                    
    ser.reset_input_buffer()   # Clears serial input
    time.sleep(0.001)          # Waits 1ms before checking for silence 
    if (ser.in_waiting <= 0):  # Moves on w/ rest of program if silent period is reached
        break

    
# Reads serial data 1 packet at a time & stores data in the corresponding text files, stops after timeout has passed
while True:
    if (ser.in_waiting >= 12): 
        
        
        #packet = bytearray() 
        packet = b''
        #print ('initial packet: ')
        #print (packet) 
        for i in range(12): 
            print ('current input: ')
            CURRENTINPUT = ser.read()
            print (CURRENTINPUT)
            packet = packet + CURRENTINPUT 
            #packet.extend(ser.read()) 
            print ('packet ' + str(i))
            print (packet) 
            print ('------') 
            #packet.append(ser.read()
          
        
        
        #ecg1_entry = struct.unpack('<H', packet[2:4])
        ecg1_entry = int.from_bytes(packet[2:4], byteorder='little', signed=True)
        ecg1_unsigned = int.from_bytes(packet[2:4], byteorder='little', signed=False)
        ecg1.write(str(ecg1_entry) + '\n')
        
        #ecg1.write(packet[2:4])
        
        #ecg2_entry = struct.unpack('<H', packet[4:6])
        ecg2_entry = int.from_bytes(packet[4:6], byteorder='little', signed=True)
        ecg2_unsigned = int.from_bytes(packet[4:6], byteorder='little', signed=False)
        ecg2.write(str(ecg2_entry) + '\n')
        #ecg2.write(packet[4:6])

        
        #resp_entry = struct.unpack('<H', packet[6:8])
        resp_entry = int.from_bytes(packet[6:8], byteorder='little', signed=True)
        resp_unsigned = int.from_bytes(packet[6:8], byteorder='little', signed=False)
        resp.write(str(resp_entry) + '\n')
        #resp.write(packet[6:8])
        
        #ppg_entry = struct.unpack('<H', packet[8:10])
        ppg_entry = int.from_bytes(packet[8:10], byteorder='little', signed=True)
        ppg_unsigned = int.from_bytes(packet[8:10], byteorder='little', signed=False)
        ppg.write(str(ppg_entry) + '\n') 
        #ppg.write(packet[8:10])
        
        
        # Gets packet numbers 
        packnum_entry = int.from_bytes(packet[0:2], byteorder='little', signed=False)
        # 
        packnums.write(str(packnum_entry) + '\n')
        #packnums.write(packet[0:2])
        
        # This part records the pack number & compares the checksum value to the sum of the data
        checksum_entry = int.from_bytes(packet[10:12], byteorder='little', signed=False)
        #data_sum = ecg1_unsigned + ecg2_unsigned + resp_unsigned + ppg_unsigned 
        data_sum = ecg1_entry + ecg2_entry + ppg_entry + resp_entry
        checksum.write('checksum: ' + str(checksum_entry) + '  data sum: ' + str(data_sum) + '\n')
        #checksum.write('pack number: ' + str(packnum_entry) + ' checksum: ' + str(checksum_entry) + ', data sum: ' + str(data_sum) + '\n')
        #if checksum_entry != data_sum:
         #   checksum.write('DATA DOESN\'T ADD TO CHECKSUM, SOMETHING BAD HAPPENED UP HERE^^^ \n')
          #  break 
        
    current_time = time.process_time()
    if current_time - start_time >= TIMEOUT: 
        break    # Stops reading serial data if the timeout has passed 


# Closes everything     
ecg1.close()  
ecg2.close()  
resp.close()  
ppg.close()  
checksum.close()
#
packnums.close()
if ser.is_open: 
    ser.close()
