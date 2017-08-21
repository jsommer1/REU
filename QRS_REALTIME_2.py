
# coding: utf-8

# In[ ]:

# This code is a modified version of QRS_Detection.py that performs QRS detection in real-time on incoming serial data.
# It is based around a custom class called "Algorithm" that implements the particular detection algorithm, so if 
# someboy would like to change algorithms, modification to this class should be almost all that is required. There is 
# also a small if statement that occurs later on (I have pointed it out in the code) that also would require fixing,
# but other than that, the class should be the only thing that needs to be changed in order to swap algorithms. 
# Joe Sommer 2017 

import matplotlib
matplotlib.use('Agg')

import numpy as np
from scipy import signal, io 
import matplotlib.pyplot as plt
import serial
import struct
import time
import datetime

# Sets up the serial port
ser = serial.Serial() 
ser.bytesize = 8      
ser.baudrate = 115200  
ser.port = '/dev/ttyAMA0'
ser.stopbits = 1
ser.open()
Fs = 200  # Serial data comes in at rate of every 5ms = 200Hz

# Initializes 4 waveform arrays 
ecg1 = np.asarray([])
ecg2 = np.asarray([])
resp = np.asarray([])
ppg = np.asarray([])

# Initializes 10 textfiles: 4 to store raw data, 4 to store QRS points, 2 to store packet labels and checksum values
rightnow = datetime.datetime.now()
ECG1_RAW = open('ECG1_RAW' + str(rightnow.isoformat()) + '.txt', 'a')
ECG1_QRS = open('ECG1_QRS' + str(rightnow.isoformat()) + '.txt', 'a')
ECG2_RAW = open('ECG2_RAW' + str(rightnow.isoformat()) + '.txt', 'a')
ECG2_QRS = open('ECG2_QRS' + str(rightnow.isoformat()) + '.txt', 'a')
RESP_RAW = open('RESP_RAW' + str(rightnow.isoformat()) + '.txt', 'a')
RESP_QRS = open('RESP_QRS' + str(rightnow.isoformat()) + '.txt', 'a')  # Does the resp even have QRS points?
PPG_RAW = open('PPG_RAW' + str(rightnow.isoformat()) + '.txt', 'a')
PPG_QRS = open('PPG_QRS' + str(rightnow.isoformat()) + '.txt', 'a')
PACK_LABELS = open('PACK_LABELS' + str(rightnow.isoformat()) + '.txt', 'a')
CHECKSUMS = open('CHECKSUMS' + str(rightnow.isoformat()) + '.txt', 'a')



# This function converts a 16-bit unsigned int into two 8-bit unsigned ints and returns their sum.
def unsignedSum(unsigned_sixteen): 
    mask1 = int('0b0000000011111111',2)
    mask2 = int('0b1111111100000000',2)
    signed_eight_1 = unsigned_sixteen & mask1 
    signed_eight_2 = (unsigned_sixteen & mask2) >> 8
    return signed_eight_1 + signed_eight_2



# This function reads in data from the serial at a rate of 1 packet (12 bytes/6 shorts) every 5ms (200Hz). 
# It stores the data in the appropriate text files. It also checks for data corruption and throws an error message
# if it detects corruption. 
def readAndSaveRaw(ser, ecg1, ecg2, resp, ppg, ECG1_RAW, ECG2_RAW, RESP_RAW, PPG_RAW, PACK_LABELS, CHECKSUMS):
    packet = b''
    #if (ser.in_waiting >= 12):
    if 1 == 1: 
        for i in range(12): 
            CURRENTINPUT = ser.read()
            packet = packet + CURRENTINPUT 
        
        # Writes in raw data from each lead into the corresponding file & array
        ecg1_entry = int.from_bytes(packet[2:4], byteorder='little', signed=True)
        ecg1_unsigned = int.from_bytes(packet[2:4], byteorder='little', signed=False)
        ecg1_entry = ecg1_entry / 1000  # Scales values down
        ECG1_RAW.write(str(ecg1_entry) + '\n')
         
        if ecg1.size == 0:
            ecg1 = np.append(ecg1, [ecg1_entry])
        else:
            ecg1 = np.concatenate((ecg1, [ecg1_entry]))
            
        #print('----')
        #print(ecg1)
                
        ecg2_entry = int.from_bytes(packet[4:6], byteorder='little', signed=True)
        ecg2_unsigned = int.from_bytes(packet[4:6], byteorder='little', signed=False)
        ecg2_entry = ecg2_entry / 1000  # Scales values down 
        ECG2_RAW.write(str(ecg2_entry) + '\n')
        if ecg2.size == 0:
            ecg2 = np.append(ecg2, [ecg2_entry])
        else:
            ecg2 = np.concatenate((ecg2, [ecg2_entry]))
        
        resp_entry = int.from_bytes(packet[6:8], byteorder='little', signed=True)
        resp_unsigned = int.from_bytes(packet[6:8], byteorder='little', signed=False)
        #resp_entry = resp_entry / 1000  # Scales values down 
        RESP_RAW.write(str(resp_entry) + '\n')
        if resp.size == 0:
            resp = np.append(resp, [resp_entry])
        else:
            resp = np.concatenate((resp, [resp_entry]))
        
        ppg_entry = int.from_bytes(packet[8:10], byteorder='little', signed=True)
        ppg_unsigned = int.from_bytes(packet[8:10], byteorder='little', signed=False)
        #ppg_entry = ppg_entry / 1000  # Scales values down 
        PPG_RAW.write(str(ppg_entry) + '\n') 
        if ppg.size == 0:
            ppg = np.append(ppg, [ppg_entry])
        else:
            ppg = np.concatenate((ppg, [ppg_entry]))
        
        packnum_entry = int.from_bytes(packet[0:2], byteorder='little', signed=False)
        PACK_LABELS.write(str(packnum_entry) + '\n')
        
        checksum_entry = int.from_bytes(packet[10:12], byteorder='little', signed=False)
        data_sum = unsignedSum(packnum_entry) + unsignedSum(ecg1_unsigned) + unsignedSum(ecg2_unsigned) + unsignedSum(resp_unsigned) + unsignedSum(ppg_unsigned) 
        CHECKSUMS.write('---\n')
        CHECKSUMS.write('Checksum: ' + str(checksum_entry) + ' Data sum: ' + str(data_sum) + '\n')
        CHECKSUMS.write('Comparison: ' + str(checksum_entry - data_sum) + '\n')
        
        if checksum_entry != data_sum:
            CHECKSUMS.write('DATA DOESN\'T ADD TO CHECKSUM, SOMETHING BAD HAPPENED UP HERE^^^ \n')
            #break 
    return ecg1, ecg2, resp, ppg



#     Sets up the Algorithm Class, which implements the particular QRS complex detection method described in 
# QRS_Detection.py. It initializes parameters and a function that calls one iteration of the algorithm. 
# This algorithm will be used by reading in a single data packet, calling the iteration function, and repeating these
# two actions in a continous loop. 

class Algorithm: 
    
    # Initial parameters
    Fs = 200                 # Data packs come in every 5ms = 200Hz
    wsize1 = 0.15            # MAF size for Energy Level Detection, size of 1st MAF
    wsize2 = 0.2             # MAF size for Energy Variation Detection, size of 2nd MAF
    refractory_time = 0.15   # Refractory Period 
    thEL0 = 0.1              # Initial value for EL threshold
    stabLevel = 0.5          # Stabilization Reference Voltage
    r_a = 0.1                # application rate for weight adjustment
    r_b = 0.05               # application rate for weight adjustment
    r_nr = 1.75              # application rate of noise level (for signal threshold)
    r_s = 0.001              # application rate of signal level (for noise threshold)
    r_d = 0.05               # decay rate for adaptive threshold
    r_n = 0.03               # application rate of noise level (for signal threshold)
    Weight = 1               # weight for adjustment signal level 
    
    winsizeEL = round(wsize1*Fs)             # window size for Energy Level (EL)
    winsizeEV = round(wsize2*Fs)             # window size for Energy Variation (EV)
    diffWinsize = winsizeEV - winsizeEL      # difference in window sizes 
    refractoryP = round(refractory_time*Fs)  # refractory period 

    thEVlimit = 1*Fs/(0.2*Fs*20)            
    thEVub = 0.45*Fs/(0.2*Fs*20)            
    thEVlb = -0.45*Fs/(0.2*Fs*20)   
    thEVub2 = 20*Fs/(0.2*Fs*20)
    thEVlb2 = -20*Fs/(0.2*Fs*20)

    ArrayL = 5 
    decayF = 1-1/( (0.40-refractory_time)*Fs ) 
    checker2=0 
    isStart=0
    maxV_Buf = None 
    maxV = 1
    QRScount = 0
    
    cutoffs = np.array([(5/(Fs/2)),(25/(Fs/2))])
    
    
    maxVArray = np.zeros((ArrayL,1))
    maxDifBuf = np.zeros((ArrayL,1))
    minDifBuf = np.zeros((ArrayL,1))
    BUF1 = np.zeros((winsizeEL,1))
    BUF2 = np.zeros((winsizeEV,1))
    
    # Expand the following w/in the iterate array
    ELQRS = np.asarray([])
    EVQRS = np.asarray([])
    thEL = np.asarray([])  # Threshold for EL (Adaptive threshold)
    thEV = np.asarray([])  # Threshold for EV (Hard threshold)
    thN = np.asarray([])
    mem_allocation = 0     # Dummy counter to initialize these arrays
    
    kk = winsizeEV
    
    Timer = -1 
    TimerOfPeak = -1
    
    maxP = -1
    maxP_Buf = -1
    
    BufStartP2 = -1
    BufEndP2 = -1
    
    def __init__(self, lead): 
        self.lead = lead   # Labels the algorithm w/ the corresponding lead
        self.qrsLocs = np.asarray([])  # Stores locations of detected QRS complexes
        
        
    # This function runs 1 iteration of the algorithm & is to be called after reading in a single data point.
    # It also saves the QRS points in a text file. 
    def iterate(self, data, file):
        # (A) preprocessing
        b = signal.firwin(64,self.cutoffs,pass_zero=False)
        fSig = signal.filtfilt(b, [1], data, axis=0)   # Signal after bandpass filter
        sSig = np.sqrt(fSig**2)               # Signal after squaring
        dSig = self.Fs*np.append([0], np.diff(sSig,axis=0),axis=0) 
        sigLen = len(sSig)
            
        #Initializes the arrays, then expands them each iteration after that
        if self.mem_allocation == 0: 
            self.ELQRS = np.zeros((sigLen,1))
            self.EVQRS = np.zeros((sigLen,1))
            self.thEL = np.ones((sigLen,1)) * self.thEL0    
            self.thEV = np.zeros((sigLen-1,1))        
            self.thN = np.zeros((sigLen,1))
            self.mem_allocation = 1
        else:
            self.ELQRS = np.append(self.ELQRS, [0])
            self.EVQRS = np.append(self.EVQRS, [0])
            self.thEL = np.append(self.thEL, [self.thEL0])
            self.thEV = np.append(self.thEV, [0])
            self.thN = np.append(self.thN, [0])
    
        LargeWin = self.winsizeEV
        
        ### Moving average w/ weight ###
        if self.kk == LargeWin: 
            for i in np.arange(len(self.BUF1), self.kk-1): 
                self.BUF1 = np.append(self.BUF1, [[0]],axis=0)
        self.BUF1 = np.append(self.BUF1, [[(np.sum( sSig[self.kk-self.winsizeEL:self.kk],axis=0 )/self.winsizeEL)]],axis=0) 
        self.BUF2 = np.append(self.BUF2, [[(np.sum( dSig[self.kk-self.winsizeEV:self.kk],axis=0 )/self.winsizeEV)]],axis=0)
        self.ELQRS[self.kk-1] = np.sum( np.copy(self.BUF1[self.kk-self.winsizeEL:self.kk]),axis=0 )/self.winsizeEL 
        self.EVQRS[self.kk-1] = np.sum( np.copy(self.BUF2[self.kk-self.winsizeEV:self.kk]),axis=0 )/self.winsizeEV 
            
        ### Step 1: Energy Level Detection ###
        if self.isStart == 0 and self.ELQRS[self.kk-1] >= self.thEL[self.kk-1]:
            self.thEL[self.kk-1] = np.copy(self.ELQRS[self.kk-1])
            self.maxV = np.copy(self.ELQRS[self.kk-1])
            self.maxP = self.kk - 1 
            self.isStart = 1
            
            #print(self.ELQRS[self.kk-1])
            #print(self.maxV)
        
        #print(self.ELQRS[self.kk-1])
        #print(self.maxV)
        
        if self.ELQRS[self.kk-1] < self.thN[self.kk-1]:
            self.thN[self.kk-1] = np.copy(self.ELQRS[self.kk-1]) 
        #print(self.ELQRS[self.kk-1])
        #print(self.maxV)
        
        if self.isStart == 1: 
            
            #print(self.ELQRS[self.kk-1])
            #print(self.maxV)
            #print('----')
            
            if self.ELQRS[self.kk-1] >= self.maxV:
                self.thEL[self.kk-1] = np.copy(self.ELQRS[self.kk-1])
                self.maxV = np.copy(self.ELQRS[self.kk-1])  
                self.maxP = self.kk - 1 
                self.Timer = self.refractoryP
            else: 
                self.Timer = self.Timer - 1
                self.thEL[self.kk-1] = self.maxV
                if self.Timer == 0:
                    self.isStart = 0
                    self.checker2 = 1
                    self.TimerOfPeak = self.winsizeEV-(self.refractoryP-self.winsizeEL)
                    self.maxP_Buf = self.maxP
                    self.maxV_Buf = self.maxV
            print(self.Timer)
        ### Step 2: Energy Variation Detection ###
        if self.checker2 == 1:
            self.TimerOfPeak = self.TimerOfPeak-1
            if self.TimerOfPeak == 0:
                self.checker2 = 0
                if self.maxP_Buf-self.winsizeEL < 1: 
                    self.BufStartP2 = 1
                else:
                    self.BufStartP2 = self.maxP_Buf - self.winsizeEL
                if self.maxP_Buf + 2 * self.diffWinsize > sigLen:
                    self.BufEndP2 = data.size
                else:
                    self.BufEndP2 = self.maxP_Buf + 2*self.diffWinsize*2
                DiffSumCheck1 = np.amax(np.copy(self.EVQRS[(self.BufStartP2-1):(self.maxP_Buf+self.diffWinsize)]),axis=0)  
                DiffSumCheck2 = np.amin(np.copy(self.EVQRS[(self.maxP_Buf+self.diffWinsize-1):self.BufEndP2]),axis=0)  
                if self.qrsLocs.size == 0 or (DiffSumCheck1-DiffSumCheck2>self.thEVlimit and DiffSumCheck1*DiffSumCheck2<0 and DiffSumCheck1>self.thEVub and DiffSumCheck2<self.thEVlb and DiffSumCheck1<self.thEVub2 and DiffSumCheck2>self.thEVlb2):
                    self.QRScount = self.QRScount + 1
                    if self.qrsLocs.size == 0: 
                        self.qrsLocs = np.append(self.qrsLocs, np.copy([self.maxP_Buf-self.winsizeEL+2]),axis=0)
                    else:
                        print(self.qrsLocs.size)
                        print(np.copy([self.maxP_Buf-self.winsizeEL+2]).size)
                        self.qrsLocs = np.concatenate((self.qrsLocs,[np.copy([self.maxP_Buf-self.winsizeEL+2])]))
                    file.write(str(np.copy([self.maxP_Buf-self.winsizeEL+2])) + '\n')
                    
            ### Step 3: Weight Adjustment ### 
                    self.maxVArray[(self.QRScount % self.ArrayL)] = self.maxV_Buf
                    self.maxDifBuf[(self.QRScount % self.ArrayL)] = np.amax(np.copy(self.EVQRS[(self.BufStartP2-1):self.BufEndP2]),axis=0) 
                    self.minDifBuf[(self.QRScount % self.ArrayL)] = np.amin(np.copy(self.EVQRS[(self.BufStartP2-1):self.BufEndP2]),axis=0) 
                    if self.stabLevel > np.mean(self.maxVArray,axis=0): 
                        AdujR1 = np.amin([self.r_a*(self.stabLevel - np.median(np.copy(self.maxVArray),axis=0)),self.r_b*self.stabLevel],axis=0)  
                    else:
                        AdujR1 = np.amin([self.r_a*(self.stabLevel - np.median(np.copy(self.maxVArray),axis=0)),-1*self.r_b*self.stabLevel],axis=0)
                    self.Weight = self.Weight + AdujR1
        self.thN[self.kk] = np.copy(self.thN[self.kk-1]) + self.r_s*np.copy(self.ELQRS[self.kk-1]) 
        if self.maxV_Buf is not None:
            self.thEL[self.kk] = np.copy(self.thEL[self.kk-1]) * ( self.decayF * (1-self.r_d*(np.copy(self.thN[self.kk-1])/self.maxV_Buf))) + self.r_n*np.copy(self.thN[self.kk-1])  
        else: 
            self.thEL[self.kk] = np.copy(self.thEL[self.kk-1]) * self.decayF
        if self.thEL[self.kk] < self.r_nr * self.thN[self.kk-1]:
            self.thEL[self.kk] = self.r_nr * np.copy(self.thN[self.kk-1])
        
        self.kk = self.kk + 1
         


# Initializes algorithms to run on each of the 4 leads
ecg1_algorithm = Algorithm(ecg1)
ecg2_algorithm = Algorithm(ecg2)
resp_algorithm = Algorithm(resp)
ppg_algorithm = Algorithm(ppg)



## TEST CODE: sets up timer to end the program in order to plot results. 
TIMEOUT = 3
dummy = 1
while dummy == 1:    # Stops reading data after TIMEOUT seconds. User inputs value for TIMEOUT
    try:
        TIMEOUT = float(input("Enter runtime in seconds: "))   
        dummy = 0
    except ValueError:
        print('Please enter a valid runtime.')
start_time = time.process_time()        



# Syncs w/ beginning of a packet by clearing serial input and waiting for silent period between packets
while True:                    
    ser.reset_input_buffer()   # Clears serial input
    time.sleep(0.001)          # Waits 1ms before checking for silence 
    if (ser.in_waiting <= 0):  # Moves on w/ rest of program if silent period is reached
        break

        
iterationcounter = 1

while True: 
    if (ser.in_waiting >= 12):
    
    # Reads in & saves one packet of serial data
        ecg1, ecg2, resp, ppg = readAndSaveRaw(ser, ecg1, ecg2, resp, ppg, ECG1_RAW, ECG2_RAW, RESP_RAW, PPG_RAW, PACK_LABELS, CHECKSUMS)

    # Runs one iteration of the algorithm for each of the 4 leads. 
    # In order for this particular algorithm to start, the data must be at least a certain length, so the if statement
    # is added in order to meet this minimum length. This part may require modification in order to switch to another 
    # algorithm later on, but other than this small detail and the algorithm class itself, no other modification should
    # be required. 
        data_length = len(ecg1)   # doesn't necessarily have to be ecg1, all waveforms have same length
        
        #print(data_length)
       
        
        if data_length > 192:  # technicality for filtering purposes 
        #if data_length >= ecg1_algorithm.winsizeEV - 1:
            print('Iteration number ' + str(iterationcounter))
            iterationcounter = iterationcounter + 1
            ecg1_algorithm.iterate(ecg1, ECG1_QRS)
            #ecg2_algorithm.iterate(ecg2, ECG2_QRS)
            #resp_algorithm.iterate(resp, RESP_QRS)
            #ppg_algorithm.iterate(ppg, PPG_QRS)
    
    ## TEST CODE: cuts out the program in order to plot stuff
    current_time = time.process_time()
    if current_time - start_time >= TIMEOUT: 
        break    # Stops reading serial data if the timeout has passed 


# Closes everything 
if ser.is_open:
    ser.close()
CHECKSUMS.close()
PACK_LABELS.close()
ECG1_RAW.close()
ECG1_QRS.close()
ECG2_RAW.close()
ECG2_QRS.close()
RESP_RAW.close()
RESP_QRS.close()
PPG_RAW.close()
PPG_QRS.close()



## TEST CODE: this part is to graph the results at the end and see if everything recorded properly 
#testloc = ecg1_algorithm.qrsLocs
#time = np.arange(len(ecg1)) / 200
#QRS_time = time[np.ix_(testloc.astype(int))]
#QRS_locations = ecg1[np.ix_(testloc.astype(int))]
#plt.plot(time, testloc, 'b-', QRS_time, QRS_locations, 'ro')
#plt.show()
