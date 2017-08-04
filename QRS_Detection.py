
# coding: utf-8

# In[4]:


###### 
# This code detects the QRS complex from an ECG signal in real time. 
# The method is based off of that described by Jinkwon Kim and Hangsik Shin in their article
#  'Simple and Robust Realtime QRS Detection Algorithm Based on Spatiotemporal Characteristic of the QRS Complex'. 
# 
# The source article can be found here: 
#  http://journals.plos.org/plosone/article?id=10.1371/journal.pone.0150144
# 
# This code has been adapted from the original algorithm source code, found here:
#  https://github.com/HangsikShin/QRS-Detection/blob/master/Simple-and-Robust-Realtime-QRS-Detection-Algorithm-based-on-Spatiotemporal-Characteristic-of-the-QRS-Complex/QRSdetection.m
#
# Joe Sommer 2017 
######

# Currently set up to test algorithm on 30,000 samples from sample #100 from the MIT-BIH database 

import numpy as np
from scipy import signal, io 
import matplotlib.pyplot as plt

import time


# The function QRSdetection is adapted from QRSdetection.m and does the actual detection of the QRS complex.
#
# Inputs: wdata (ECG waveform data), Fs (sampling frequency)
#   
# 
# The original source code also takes in a variable 'ftype', which modifies coefficients used in the bandpass filter depending 
#  on which database (MIT-BIH / AHA) is being tested by the algorithm. In order to use this algorithm on any signal,
#  this code omits 'ftype' and instead implements a general-purpose 64-tap bandpass filter with a passband from 5 to 25 Hz. 
# The original code also takes in 'wtime', an array of time indices. This variable is contained in the matlab file of the waveform,
#  so since this code's input waveform file doesn't contain this variable, it is calculated separately. 
# This function returns an array [loc, time], respectively indicating the indices and times of QRS locations. 

def QRSdetection(wdata, Fs):   
#wtime was originally an input here too
        
        ### Parameters ###
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
    
        ### Window Configuration ###
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
        loc = np.asarray([])
        isStart=0
        
        maxV_Buf = None 
        
        ### Preprocessing ###
        
        cutoffs = np.array([(5/(Fs/2)),(25/(Fs/2))]) 
        
        b = signal.firwin(64,cutoffs,pass_zero=False) 
        fSig = signal.filtfilt(b, 1, wdata, axis=0)   # Signal after bandpass filter
        sSig = np.sqrt(fSig**2)               # Signal after squaring
        dSig = Fs*np.append([0], np.diff(sSig,axis=0),axis=0) 
        
        #print ('Check 1.5 - Filtering done')

        
        sigLen = len(sSig)
    
        ### Memory Allocation ###
        # column vectors, turn into row vectors if you get rid of ',1' 
        ELQRS = np.zeros((sigLen,1))
        EVQRS = np.zeros((sigLen,1))
        thEL = np.ones((sigLen,1)) * thEL0    # Threshold for EL (Adaptive threshold)
        thEV = np.zeros((sigLen-1,1))         # Threshold for EV (Hard threshold)
        thN = np.zeros((sigLen,1))
        maxVArray = np.zeros((ArrayL,1))
        maxDifBuf = np.zeros((ArrayL,1))
        minDifBuf = np.zeros((ArrayL,1))
        BUF1 = np.zeros((winsizeEL,1))
        BUF2 = np.zeros((winsizeEV,1))
    
        LargeWin = winsizeEV
    
        maxV = 1
        QRScount = 0
    
        for kk in np.arange(LargeWin, sigLen):
            ### Moving average with weight ###            
                if kk == LargeWin: 
                        for i in np.arange(len(BUF1), kk-1): 
                                BUF1 = np.append(BUF1, [[0]],axis=0)
            
                BUF1 = np.append(BUF1, [[(np.sum( sSig[kk-winsizeEL:kk],axis=0 )/winsizeEL)]],axis=0) 
            
                BUF2 = np.append(BUF2, [[(np.sum( dSig[kk-winsizeEV:kk],axis=0 )/winsizeEV)]],axis=0)
    

                
                ELQRS[kk-1] = np.sum( np.copy(BUF1[kk-winsizeEL:kk]),axis=0 )/winsizeEL 
                EVQRS[kk-1] = np.sum( np.copy(BUF2[kk-winsizeEV:kk]),axis=0 )/winsizeEV 
        
            ### Step 1: Energy Level Detection ###
                if isStart == 0 and ELQRS[kk-1] >= thEL[kk-1]:
                        thEL[kk-1] = np.copy(ELQRS[kk-1])  
                        maxV = np.copy(ELQRS[kk-1])       
                        maxP = kk - 1 
                        isStart = 1
                
                if ELQRS[kk-1] < thN[kk-1]:
                        thN[kk-1] = np.copy(ELQRS[kk-1]) 
                
                if isStart == 1: 
                        if ELQRS[kk-1] >= maxV:
                                thEL[kk-1] = np.copy(ELQRS[kk-1]) 
                                maxV = np.copy(ELQRS[kk-1])  
                                maxP = kk - 1 
                                Timer = refractoryP
                        else: 
                                Timer = Timer - 1
                                thEL[kk-1] = maxV
                                
                                if Timer == 0:
                                            isStart = 0
                                            checker2 = 1
                                            TimerOfPeak = winsizeEV-(refractoryP-winsizeEL)
                                            maxP_Buf = maxP
                                            maxV_Buf = maxV
            
            ### Step 2: Energy Variation Detection ###
                if checker2 == 1:
                        TimerOfPeak = TimerOfPeak-1
                        if TimerOfPeak == 0:
                                checker2 = 0
                                
                                if maxP_Buf-winsizeEL < 1: 
                                        BufStartP2 = 1
                                else: 
                                        BufStartP2 = maxP_Buf - winsizeEL
                                
                                if maxP_Buf + 2 * diffWinsize > sigLen:                  
                                        BufEndP2 = wdata.size                
                                else: 
                                        BufEndP2 = maxP_Buf + 2*diffWinsize*2
                    
                                DiffSumCheck1 = np.amax(np.copy(EVQRS[(BufStartP2-1):(maxP_Buf+diffWinsize)]),axis=0)  
                                DiffSumCheck2 = np.amin(np.copy(EVQRS[(maxP_Buf+diffWinsize-1):BufEndP2]),axis=0)   
                    
                                if loc.size == 0 or (DiffSumCheck1-DiffSumCheck2>thEVlimit and DiffSumCheck1*DiffSumCheck2<0 and DiffSumCheck1>thEVub and DiffSumCheck2<thEVlb and DiffSumCheck1<thEVub2 and DiffSumCheck2>thEVlb2):  
                                        
                                        QRScount = QRScount + 1
                                        loc = np.append(loc, np.copy([maxP_Buf-winsizeEL+2]),axis=0)  
            
                        ### Step 3: Weight Adjustment ### 
                                        maxVArray[(QRScount % ArrayL)] = maxV_Buf
                                        maxDifBuf[(QRScount % ArrayL)] = np.amax(np.copy(EVQRS[(BufStartP2-1):BufEndP2]),axis=0) 
                                        minDifBuf[(QRScount % ArrayL)] = np.amin(np.copy(EVQRS[(BufStartP2-1):BufEndP2]),axis=0) 
                                        
                                        if stabLevel > np.mean(maxVArray,axis=0): 
                                                AdujR1 = np.amin([r_a*(stabLevel - np.median(np.copy(maxVArray),axis=0)),r_b*stabLevel],axis=0)  
                                        else: 
                                                AdujR1 = np.amin([r_a*(stabLevel - np.median(np.copy(maxVArray),axis=0)),-1*r_b*stabLevel],axis=0) 
                                        
                                        Weight = Weight + AdujR1
                thN[kk] = np.copy(thN[kk-1]) + r_s*np.copy(ELQRS[kk-1]) 
                
            
                if maxV_Buf is not None: 
                        thEL[kk] = np.copy(thEL[kk-1]) * ( decayF * (1-r_d*(np.copy(thN[kk-1])/maxV_Buf))) + r_n*np.copy(thN[kk-1])  
                else: 
                        thEL[kk] = np.copy(thEL[kk-1]) * decayF  
                
                if thEL[kk] < r_nr * thN[kk-1]:
                        thEL[kk] = r_nr * np.copy(thN[kk-1]) 

        return loc 
        

        
        
        
### MAIN PART OF THE PROGRAM, LOADS FILE, RUNS ALGORITHM, PLOTS ORIGINAL DATA + QRS PEAKS ###        
        
# Change data file here 
#wave_file = 'ECG3Data_mfast_0713201711_06_46_987'

#data_array = np.asarray([])

#with open(wave_file) as f:
#        for line in f: 
#                data_str = line
#                data_array = np.append(data_array, [float(data_str)], axis=0) #

#print ('Check 1 - read in data')     
                
#Fs = 200  # Based on packet coming in every 5ms, try 1000Hz (1ms) for ECG or 100Hz (10ms) for PG 

#loc = QRSdetection(data_array, Fs)

#print ('Check 2 - finish detection')

#time = np.arange(len(data_array)) / Fs

#QRS_time = time[np.ix_(loc.astype(int))]

#QRS_locations = data_array[np.ix_(loc.astype(int))] # amplitudes of detected peaks

#plt.plot(time, data_array, 'b-', QRS_time, QRS_locations, 'ro')
#plt.show()    




#########
# testing w/ ECG No. 100 from MIT-BIH database
testFs = 360  
testwave = np.asarray([])
testcounter = 0
testlength = 30000
with open('ecg100.txt') as f2: 
        for line in f2: 
                   # if testcounter % 5000 == 0:        
                    #        print(testcounter)
                    if testcounter == testlength:
                            break # only reads in first 10,000 points 
                    testcounter = testcounter + 1
                    value = line
                    testwave = np.append(testwave, float(value))
#print ('Check 1 - Data loaded')  
testwave_short = testwave[0:testlength]
time_start = time.process_time()
testloc = QRSdetection(testwave_short, testFs)
time_end = time.process_time()
#print('Check 2 - found QRS points')
time = np.arange(len(testwave_short)) / testFs
QRS_time = time[np.ix_(testloc.astype(int))]
QRS_locations = testwave_short[np.ix_(testloc.astype(int))]
plt.plot(time, testwave_short, 'b-', QRS_time, QRS_locations, 'ro')
plt.title('MIT-BIH DB #100 (Python)')
plt.show()
print('Elapsed time: ' + str(time_end - time_start) + ' seconds')
    
    

