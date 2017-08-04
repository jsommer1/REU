
# coding: utf-8

# In[ ]:


# This code is to be run from a Raspberry Pi 3. It'll hopefully read in serial data through the UART and save the raw 
# data in 4 separate text files. 


import serial 
import time
import struct
import datetime


# Initializes serial connection 
ser = serial.Serial() 
ser.bytesize = 8      
ser.baudrate = 115200  
ser.port = '/dev/ttyAMA0'  #Please work...  
#ser.timeout = 3  # Probably delete this line later 
TIMEOUT = 3 # Set a 3-second timeout, stops reading data after 3 seconds. Set manual user input later 
ser.open() 


# Creates 4 text files to save data from different leads: ECG1, ECG2, Resp, and PPG
rightnow = datetime.datetime.now()

ecg1 = open('ECG1DATA' + str(rightnow.isoformat()) + '.txt', 'w+')  
ecg2 = open('ECG2DATA' + str(rightnow.isoformat()) + '.txt', 'w+')
resp = open('RESPDATA' + str(rightnow.isoformat()) + '.txt', 'w+')
ppg = open('PPGDATA' + str(rightnow.isoformat()) + '.txt', 'w+')


# Syncs w/ beginning of a packet by clearing serial input and waiting for silent period between packets
while True:                    
    ser.reset_input_buffer()   # Clears serial input
    time.sleep(0.001)          # Waits 1ms before checking for silence 
    if (ser.in_waiting <= 0):  # Moves on w/ rest of program if silent period is reached
        break

        
# Initializes empty bytearray to store 12 bytes per packet in 
packet = bytearray(12)
        

# Starts stopwatch for timeout purposes, this is here because IDK how to properly use PySerial's timeout functions
start_time = time.process_time()
    
    
# Reads serial data 1 packet at a time & stores data in the corresponding text files, stops after timeout has passed
while True:
    if (ser.in_waiting >= 12): 
        #for i in range(0,12):
         #   packet[i] = ser.read()
        for byte in packet: 
            byte = ser.read()
        ecg1_entry = struct.unpack('H', packet[2:4])
        ecg1.write(str(ecg1_entry))
        ecg2_entry = struct.unpack('H', packet[4:6])
        ecg2.write(str(ecg2_entry))
        resp_entry = struct.unpack('H', packet[6:8])
        resp.write(str(resp_entry))
        ppg_entry = struct.unpack('H', packet[8:10])
        ppg.write(str(ppg_entry)) 
    current_time = time.process_time()
    if current_time - start_time >= TIMEOUT: 
        break    # Stops reading serial data if the timeout has passed 
        
## THIS PART IS PROBABLY OBSOLETE ##         
# Reads serial data and stores it in the text file 
#while True:              # Should be a continuous loop while serial data is coming in
#    x = ser.readline()   # I'm about 95% sure it's readline() here; if not, replace w/ read()
#    f.write(x)           # This should add the current line of data to the file SAVEDATA.txt 


# Closes everything     
ecg1.close()  
ecg2.close()  
resp.close()  
ppg.close()  
if ser.is_open: 
    ser.close()
    
