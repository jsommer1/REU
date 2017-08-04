
# coding: utf-8

# In[ ]:


# TO DO: 
# - connect the Pi to wifi so that it can download this program
# - get this code onto Github & get it on the Pi 
# - check if I need to do the online training for CNI 
# - test the code: connect to the machine, try to save like 30s of data, compare to the raw data

# Check here: http://cni.stanford.edu/wiki/MR_Hardware#Scan_Triggers



# This code is to be run from a Raspberry Pi 3. It'll hopefully read in serial data through the UART and save the raw 
# data in 4 separate text files. 


import serial 
import time
import struct


# Initializes serial connection 
ser = serial.Serial() 
ser.bytesize = 8      
ser.baudrate = 115200  
ser.port = '/dev/ttyAMA0'  # Please work
# Can set ser.timeout = T to stop reading after T seconds, might be useful for testing 
ser.open() 


# Creates 4 text files to save data from different leads: ECG1, ECG2, Resp, and PPG
ecg1 = open('ECG1DATA.txt', 'w+')  
ecg2 = open('ECG2DATA.txt', 'w+')
resp = open('RESPDATA.txt', 'w+')
ppg = open('PPGDATA.txt', 'w+')


# Syncs w/ beginning of a packet by clearing serial input and waiting for silent period between packets
while True:                    
    ser.reset_input_buffer()   # Clears serial input
    time.sleep(0.001)          # Waits 1ms before checking for silence 
    if (ser.in_waiting <= 0):  # Moves on w/ rest of program if silent period is reached
        break

        
# Initializes empty bytearray to store 12 bytes per packet in 
packet = bytearray(12)
        
    
# Reads serial data 1 packet at a time & stores data in the corresponding text files
while True:
    if (ser.in_waiting >= 12): 
        for i in range(0,12):
            packet[i] = ser.read()
        ecg1_entry = struct.unpack('H', packet[2:4])
        ecg1.write(ecg1_entry)
        ecg2_entry = struct.unpack('H', packet[4:6])
        ecg2.write(ecg2_entry)
        resp_entry = struct.unpack('H', packet[6:8])
        resp.write(resp_entry)
        ppg_entry = struct.unpack('H', packet[8:10])
        ppg.write(ppg_entry) 
        
        
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
ser.close()

