
# coding: utf-8

# In[ ]:
# This code is to be run from a Raspberry Pi 3 with reconfigured UART. It reads in serial data in packets of 12 bytes (6 shorts) every 
# 5ms and writes the data into 6 text files: 4 for each lead's waveform and 2 for package labels and checksum values. 
# Currently, the checksum comparison to detect data corruption has not been completed yet, but as the packet labels increment correctly, 
# this program is believed to work properly. 
# Joe Sommer 2017 

import serial 
import time
import struct
import datetime

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


# Creates 4 text files to save data from different leads (ECG1, ECG2, Resp, and PPG) and 2 more to save checksum values & packet numbers
rightnow = datetime.datetime.now()

ecg1 = open('ECG1DATA' + str(rightnow.isoformat()) + '.txt', 'a')  
ecg2 = open('ECG2DATA' + str(rightnow.isoformat()) + '.txt', 'a')
resp = open('RESPDATA' + str(rightnow.isoformat()) + '.txt', 'a')
ppg = open('PPGDATA' + str(rightnow.isoformat()) + '.txt', 'a') 
checksum = open('CHECKSUM' + str(rightnow.isoformat()) + '.txt', 'a')
packnums = open('PACKNUMS' + str(rightnow.isoformat()) + '.txt', 'a')


# Starts stopwatch for timeout purposes, this is here because IDK how to properly use PySerial's timeout functions
start_time = time.process_time()


# Syncs w/ beginning of a packet by clearing serial input and waiting for silent period between packets
while True:                    
    ser.reset_input_buffer()   # Clears serial input
    time.sleep(0.001)          # Waits 1ms before checking for silence 
    if (ser.in_waiting <= 0):  # Moves on w/ rest of program if silent period is reached
        break
    
        
# This function converts a 16-bit unsigned int into two 8-bit unsigned ints and returns their sum
def unsignedSum(unsigned_sixteen): 
    mask1 = int('0b0000000011111111',2)
    mask2 = int('0b1111111100000000',2)
    signed_eight_1 = unsigned_sixteen & mask1 
    signed_eight_2 = (unsigned_sixteen & mask2) >> 8
    return signed_eight_1 + signed_eight_2   


# Reads serial data 1 packet at a time & stores data in the corresponding text files, stops after timeout has passed
while True:
    if (ser.in_waiting >= 12): 
        packet = b''
        for i in range(12): 
            CURRENTINPUT = ser.read()
            packet = packet + CURRENTINPUT         
        
        # Writes in data from each lead into the corresponding file 
        ecg1_entry = int.from_bytes(packet[2:4], byteorder='little', signed=True)
        ecg1_unsigned = int.from_bytes(packet[2:4], byteorder='little', signed=False)
        ecg1.write(str(ecg1_entry) + '\n')
                
        ecg2_entry = int.from_bytes(packet[4:6], byteorder='little', signed=True)
        ecg2_unsigned = int.from_bytes(packet[4:6], byteorder='little', signed=False)
        ecg2.write(str(ecg2_entry) + '\n')
        
        resp_entry = int.from_bytes(packet[6:8], byteorder='little', signed=True)
        resp_unsigned = int.from_bytes(packet[6:8], byteorder='little', signed=False)
        resp.write(str(resp_entry) + '\n')
        
        ppg_entry = int.from_bytes(packet[8:10], byteorder='little', signed=True)
        ppg_unsigned = int.from_bytes(packet[8:10], byteorder='little', signed=False)
        ppg.write(str(ppg_entry) + '\n') 
        
        # Gets packet numbers 
        packnum_entry = int.from_bytes(packet[0:2], byteorder='little', signed=False)
        packnums.write(str(packnum_entry) + '\n')
       
        # This big chunk (lines 85 to 101) is to try and figure out how to compare the data to the checksum in order to check for corrupt data
        
        # This is the value to compare the other stuff to 
        checksum_entry = int.from_bytes(packet[10:12], byteorder='little', signed=False)
        
        data_sum = unsignedSum(packnum_entry) + unsignedSum(ecg1_unsigned) + unsignedSum(ecg2_unsigned) + unsignedSum(resp_unsigned) + unsignedSum(ppg_unsigned) 
        
        checksum.write('---\n')
        checksum.write('Checksum: ' + str(checksum_entry) + ' Data sum: ' + str(data_sum) + '\n')
        checksum.write('Comparison: ' + str(checksum_entry - data_sum) + '\n')
        
        if checksum_entry != data_sum:
            checksum.write('DATA DOESN\'T ADD TO CHECKSUM, SOMETHING BAD HAPPENED UP HERE^^^ \n')
            break 
        
    current_time = time.process_time()
    if current_time - start_time >= TIMEOUT: 
        break    # Stops reading serial data if the timeout has passed 



# Closes everything     
ecg1.close()  
ecg2.close()  
resp.close()  
ppg.close()  
checksum.close()
packnums.close()
if ser.is_open: 
    ser.close()
