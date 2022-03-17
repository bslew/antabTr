'''
Created on Jan 13, 2022

@author: blew
'''
import os
import errno
import numpy as np
import datetime
import itertools
import re
from scipy.interpolate import interp1d
import statsmodels.api as sm
import statsmodels.tsa as smtsa
import pandas as pd
from antabtr import vis
import matplotlib.pyplot as plt

debug=False

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise  

def moving_avg_1d(X,w):
    '''
    X - -1d array-like
    w - integer defining 
    '''
    return np.convolve(X, np.ones(w), 'valid') / w    

def get_basename_ext(fname):
    '''
    return triple dirname,basename and file extension
    '''
    fname_base=os.path.basename(fname)
    l=fname_base.split('.')
    fnamenoext='.'.join(l[:-1])
    ext=l[-1]
    
    return os.path.dirname(fname),fnamenoext,ext



def get_band_Tsys_min_max(freq_GHz,cfg):
    '''
    return tuple(minTsys,maxTsys) for a given frequency and config settings
    '''
    if not cfg.has_option('REC','freq'):
        return cfg.getfloat('Tsys','minTsys'),cfg.getfloat('Tsys','maxTsys')

    # print(freq_GHz)    
    f=np.array([ float(x) for x in cfg['REC']['freq'].split(',')])
    # print(f)
    v=np.array([ float(x) for x in cfg['REC']['minTsys'].split(',')])
    v1=interp1d(f,v,kind='nearest-up',fill_value='extrapolate')
    v=np.array([ float(x) for x in cfg['REC']['maxTsys'].split(',')])
    v2=interp1d(f,v,kind='nearest-up',fill_value='extrapolate')
    
    return v1(freq_GHz),v2(freq_GHz)
#-----------------------------------------------------------------------------------------------------
def prefilter(tsysline,block,maxlim,minlim=0):
    '''
    handle negative Tsys and values larger than maxlim
    '''
    tsysline=np.array(tsysline);block=np.array(block)
    for i in range(0,len(tsysline)):
        #badcond=(tsysline[i]<0)+(tsysline[i]>maxlim)
        badcond=[(tsyselement<=minlim or tsyselement>maxlim) for tsyselement in tsysline[i]]
        for j in range(0,len(badcond)):
            if badcond[j]==True:
                goodblock=(block==block[j])*(tsysline[i]>minlim)*(tsysline[i]<maxlim)
                oklist=np.extract(goodblock,tsysline[i])
                jcount=j
                while len(oklist)==0:        #i don't know what to do in this case should i copy values from another scan with the same source? this will not work in the last serie of data 
                    goodblock=(block==block[jcount])*(tsysline[i]>minlim)*(tsysline[i]<maxlim)
                    oklist=np.extract(goodblock,tsysline[i])
                    jcount=jcount+1
                    if (jcount-j)>20 or (jcount>=len(block)):
                        #oklist=[50]
                        okcond=(tsysline[i]>minlim)*(tsysline[i]<maxlim)
                        oklist=np.extract(okcond,tsysline[i])#if nothing good, compute mean of all data, another alternative is delete the whole line but is more difficult to implement and you lose data in all bbc
                        break        
                gm=1
                for k in oklist:
                    gm=gm*(k)**(1/float(len(oklist)))
                tsysline[i][j]=gm

    return tsysline


###______________________________________________________________###
class logFile:
    '''
    Utility class to manage the log file
    '''

    #-----------------------------------------------------------------------------------------------------
    def __init__(self, fileName, cfg=None, rxgfiles=None, verbosity=0, **kwagrs):
        '''Constructor.
        It opens the LOG file, reads its content and closes it. The content is stored in a private variable: self.fileContent
        Other variables are also stored like:
                self.logname, self.stationName, self.expName, self.freqLOMHzArray, self.polArray

        @param fileName. Name of the LOG file including the PATH
        '''

        self.verbosity=verbosity
        self.cfg=cfg
        self.__rxgDirectory=cfg['CALIB']['rxgDir']
        self.rxgfiles=rxgfiles

        self.logname = fileName.split('/')[-1]
        exp_station = self.logname.split('.')[0]
        self.stationName = exp_station[-2:].upper()
        self.expName = exp_station[0:-2].lower()
        try:
            logfIn = open(fileName, 'r')
            self.fileContent = logfIn.readlines()
            logfIn.close()
        except Exception as ex:
            raise 

        self.freqLOMHzArray = dict()
        self.ifdSetup = dict()
        self.polArray = dict()
        self.bandArray = dict()
        self.dbbcModeName = None
        #self.calModeName = None
        self.calModeName = dict() 
        self.lastCalMode = None
        self.logData = []

        self.__bbcinfo = dict()
        self.__vsiCh = dict()
        #self.__lower = True
        self.__formType = None
        self.__chId = None
        self.__chIdIndex = None
        self.__scanNum = 0
        self.__scanName = None
        self.__dataValid = False
        self.__dtStartInt = None
        self.__intComplete = False
        self.__tempDict = [dict(), dict(), dict(), dict()] # tpiprime, tpical, tpidiff and tcal (The latest should always be tcal)-> SINGLE CALIBRATION MODE (Changed if use CONT)
        self.__headerComp = False
        self.__bbccodelist = dict()
        self.__bw = dict()
        self.__bbcfq = dict()
        self.__whichif = dict()
        self.__intTime = datetime.timedelta(0,1) # Integration time. Set to 1 seconds.
        self.__pfbFreq = [1040,1008,976,944,912,880,848,816,784,752,720,688,656,624,592,560]
        self.__tsyslogDict = dict()

        self.__scanline = []
        self.__indexline = []
        self.__header = []
        self.__tsyslog = []
        self.__setupTime = [] 
        self.__setupTcal = dict()
        self.__caltempRead = dict()
        #self.__BB = []
        self.__currentSetup = None
        self.__lastSetup = None
        self.__newSetup = False
        self.__fila10gMode = dict()
        self.__recMode = dict()

        self.__formChannels = {'geo': ['1u','2u','3u','4u','5u','6u','7u','8u','1l','8l','9u','au','bu','cu','du','eu'],
                       'astro': ['1u','2u','3u','4u','5u','6u','7u','8u','1l','2l','3l','4l','5l','6l','7l','8l'],
                       'astro2': ['1u','2u','3u','4u','9u','au','bu','cu','1l','2l','3l','4l','9l','al','bl','cl'],
                       'astro3': ['1u','3u','5u','7u','9u','bu','du','fu','1l','3l','5l','7l','9l','bl','dl','fl'],
                       'lba': ['1u','2u','5u','6u','3u','4u','7u','8u','1l','2l','5l','6l','3l','4l','7l','8l'],
                       'wastro': ['1u','2u','3u','4u','5u','6u','7u','8u','1l','2l','3l','4l','5l','6l','7l','8l','9u','au','bu','cu','du','eu','fu','gu','9l','al','bl','cl','dl','el','fl','gl']}

        self.__epoch = datetime.datetime.utcfromtimestamp(0)
        
        if verbosity>2:
            print("Reading log data")
        self.__readLog(**kwagrs)
        if verbosity>2:
            print("Reading log data done")
    #------------------------------------------------------------------------------------
    def __readLog(self, **kwargs):
        '''
        Reads the LOG file to find variables. Reading can be divided in two parts: header reading and data reading.

            - In header reading, variables that only appear at the beginning of the LOG file are read. 
              These variables usually indicate the individual DBBC channels configuration.

            - In data reading, temperature variables are read. These variables are stored depending on their type
              and the DBBC channel that they refer.

            - There are variables that can appear anywhere inside the LOG file, that are named general
              variables. These variables should be read in both reading parts.

        As a result, the class variable self.logData will store the DBBC and LO configuration detected, every scan number
        with the source observed and all tsys calculated with their time tag.           
        
        keywords
        --------
            enforceTsysTsys - enforces this value of Tsys to be used
            
        '''

        time = []    # List of Tsys time tag
        block = []    # List of Tsys scan tag
        tsysline = []    # List of calculated Tsys
        
        enforceTsys=False
        if 'enforceTsys' in kwargs:
            enforceTsys=kwargs['enforceTsys']

        for nLine in range(0, len(self.fileContent)):

            line = self.fileContent[nLine]    # Each iteration reads one LOG file line

            if line.strip() == "":
                #print "Line number %d is empty." % nLine
                continue

            #---------------Reading Header Variables------------------
            # Read the LOG line, check if it is a header line and process it if it is so.
            # headerComp will tell me if we have already finished reading header variables because 
            # we have already started reading data
            if not self.__headerComp:
                if self.__readHeader(line):
                    continue

            #---------------Reading General Variables-----------------
            # Check if the LOG line has information about general variables.
            # General variables can appear anywhere inside the LOG file.
            if self.__getGenVar(line):
                continue

            #----------------Checking Data Validation-----------------
            # Check if the LOG line is "data_valid=on/off". 
            if self.__checkDataValid(line, **kwargs):
                continue

            #----------------Reading Temp Variables-------------------
            # If data is valid, check if the LOG line has temperature information.
            if self.__dataValid:
                if nLine+1 >= len(self.fileContent):
                    self.__readTempVar(line, "", **kwargs)
                else:
                    self.__readTempVar(line, self.fileContent[nLine+1].strip(), **kwargs)

            #--------Integration Complete. Tsys calculation-----------
            # If a "data_valid=off" is read or the integration time has been exceeded (20 seconds),
            # we suppose that the integration is complete. Using temperature variables stored, Tsys
            # is calculated and stored with its time and scan tags.
            if self.__intComplete:

                if not self.__currentSetup in self.__bbccodelist:
                    continue

                dt = self.__getDatetime(line)

                # if 'enforceTsys' in kwargs:
                #     tsysline_aux=float(kwargs['enforceTsys'])
                # else:
                tsysline_aux = self.__getTsys(self.__bbccodelist[self.__currentSetup], dt, **kwargs)
                    
                

                """    
                if not tsysline_aux:    # If is empty means that some temperature variable was empty during Tsys calculation.
                    #print self.__tempDict
                    #sleep(3)
                            # In this case, the last Tsys read from the LOG file is stored.

                    tsysline_aux = []

                    sortedKeys = sorted(self.__tsyslogDict)

                    if not sortedKeys:
                        print dt
                        for j in self.__bbccodelist[self.__currentSetup]:
                            tsysline_aux.append(-1)
                    else:
                    
                        auxDict = self.__tsyslogDict[sortedKeys[-1]]
                        for j in self.__bbccodelist[self.__currentSetup]:
                            try:
                                tsyslog_aux = auxDict[j]
                                tsyslogMean = sum(tsyslog_aux)/len(tsyslog_aux)
                            except:
                                tsyslogMean = -1
    
                            tsysline_aux.append(tsyslogMean)
                """

                if tsysline_aux and (not all(-1 == tsys for tsys in tsysline_aux)):
                    # Tsys time tag
                    dt = self.__getDatetime(line)
                    total_seconds = (dt - self.__epoch).total_seconds()
                    time.append(total_seconds)
                    #days = (dt - datetime.datetime(dt.year,1,1,dt.hour,dt.minute,dt.second,dt.microsecond)).days + 1
                    #time.append(days + (dt.hour/24.) + (dt.minute/(60.*24.)) + (dt.second/(3600.*24.)) + (dt.microsecond/(3600.*24.*1e6)))

                    # Tsys scan tag
                    block.append(self.__scanNum)

                    # Tsys calculated
                        
                    tsysline.append(tsysline_aux)
                """

                # Tsys time tag
                dt = self.__getDatetime(line)
                days = (dt - datetime.datetime(dt.year,1,1,dt.hour,dt.minute,dt.second,dt.microsecond)).days + 1
                time.append(days + (dt.hour/24.) + (dt.minute/(60.*24.)) + (dt.second/(3600.*24.)) + (dt.microsecond/(3600.*24.*1e6)))

                # Tsys scan tag
                block.append(self.__scanNum)

                # Tsys calculated
                tsysline.append(tsysline_aux)
                """

                self.__intComplete = False

        # When the LOG file has been read, we fill the header using the variables read.
        self.__fillHeader()

        # All variables read and calculated are stored in self.logData class variable.
        self.logData = [self.__header,self.__indexline,self.__scanline,tsysline,block,time, self.__tsyslog, self.__setupTime]

    #------------------------------------------------------------------------------------
    def __fillHeader(self):
        '''
        ANTAB file header is made using the information about the individual DBBC channels configuration and the LOs configuration.
        As a result, ANTAB file header should be like this:

            self.__indexline:     ["INDEX= 'R1','R2','L1','L2'\\n"]
            self.__header:        ["!Column 1 = R1: ifA, bbc01, 43130.49 MHz , LSB, BW= 16.00 MHz, Tcal=250.00 K\\n
                          !Column 2 = R2: ifA, bbc01, 43146.49 MHz , USB, BW= 16.00 MHz, Tcal=250.00 K\\n
                          !Column 3 = L1: ifC, bbc09, 43130.49 MHz , LSB, BW= 16.00 MHz, Tcal=250.00 K\\n
                          !Column 4 = L2: ifC, bbc09, 43146.49 MHz , USB, BW= 16.00 MHz, Tcal=250.00 K\\n"]

            self.__indexline and self.__header are list where are stored the header of each band used in the LOG file.

        The Tsys read from the LOG file is calculated here too.
        '''    

        
        #----------------ANTAB file header-------------------

        # When the individual DBBC channels change their configuration, the time tag is stored
        # in self.__bandTime.
    
        ind_off = 0
    
        # Make an ANTAB header for each band in the LOG file.
        for bP in range(len(self.__setupTime)):
            setup = self.__setupTime[bP][1]
            colnum = 1
            polNum = {'L':1, 'R':1}
            headerStr = "!\n! Setup %s\n! Calibration mode: %s\n!\n" % (setup,self.calModeName[setup])
            indexStr = "INDEX= "
            if setup not in self.__bbccodelist:
                self.__header.append(headerStr[:-1])
                self.__indexline.append(indexStr + '\n')
                continue
            for i in self.__bbccodelist[setup]:
                lofq = self.freqLOMHzArray[setup][self.__whichif[setup][i]][-1] # Get LO frequency, polarization and bandwidth for every DBBC channel
                pol = self.polArray[setup][self.__whichif[setup][i]][-1]
                band = self.bandArray[setup][self.__whichif[setup][i]][-1]
                bw_aux = self.__bw[setup][i]
                if self.dbbcModeName == "DDC":             # If DBBC mode is DDC, LSB and USB should be differenciate.
                    if i[-1] == 'l':                # USB (Upper SideBand) -> Freq + BW/2
                        bw_aux = -bw_aux             # LSB (Lower SideBand) -> Freq - BW/2 
                    if "lsb" in band:
                        bbcFreq = -self.__bbcfq[setup][i]
                    else:
                        bbcFreq = self.__bbcfq[setup][i]
                    fchan=lofq+bbcFreq+bw_aux/2.
                    auxStr = '0%s' % i[0]
                    # Manage special case of channel 16 with hex code 'g'
                    if auxStr == '0g':
                        bbcnum = 16
                    else:
                        bbcnum = int(auxStr,16)            # DBBC channel number (from 1 to 16)

                    sbLetter = i[-1].upper()         # Sideband Letter (L or U)

                elif self.dbbcModeName == "PFB":            # When DBBC uses PFB mode only use LSB.
                    if "lsb" in band:
                        bbcFreq = -self.__bbcfq[setup][i]
                    else:
                        bbcFreq = self.__bbcfq[setup][i]
                    fchan=lofq+bbcFreq-bw_aux/2.    # LSB (Lower SideBand) -> Freq - BW/2
                    bbcnum = int(i[1:])            # DBBC channel number (from 1 to 16)
                    sbLetter = 'L'                # Sideband Letter: Always 'L'

                #if self.calModeName[setup] == "SINGLE":        # When DBBC uses SINGLE calibration, Tcal is got from the LOG file is used
                #    tcal = self.__setupTcal[setup][i][0]
                #else:                        # When DBBC uses CONTINUOUS calibration, Tcal is got from RXG file is used
                #    tcal = self.__setupTcal[setup][i]
                tcal = self.__setupTcal[setup][i][0]

                # Header string format
                headerStr += '!Column %d = %s%d: if%s, bbc%02d, %.2f MHz , %sSB, BW= %04.2f MHz, Tcal=%.2f K\n'%(colnum,pol[0].upper(),polNum[pol[0].upper()],self.__whichif[setup][i].upper(),bbcnum,fchan,sbLetter,self.__bw[setup][i],tcal) 
                # Index string format
                indexStr += "'%s%d'," % (pol[0].upper(), polNum[pol[0].upper()])
                colnum += 1
                polNum[pol[0].upper()] += 1

            indexStr = indexStr.strip(',')         # Removes the last comma
            self.__header.append(headerStr[:-1])    # Take all header string except the last line feed character
            self.__indexline.append(indexStr + '\n')


        #----------------Tsys from the LOG file-------------------

        #print self.__tsyslogDict
        sortedKeys = sorted(self.__tsyslogDict)        # Sort the Tsys read from the LOG file by their time tag

        for i in sortedKeys:
            tsyslog = [i]             # Store Tsys time tag (index 0)
            auxDict = self.__tsyslogDict[i]
            for j in self.__bbccodelist[self.__currentSetup]:
                try:
                    tsyslog_aux = auxDict[j]
                    tsyslogMean = sum(tsyslog_aux)/len(tsyslog_aux) # Calculate Tsys for each DBBC channel
                except:
                    tsyslogMean = -1

                tsyslog.append(tsyslogMean) # Store Tsys dict (index 1)

            self.__tsyslog.append(tsyslog) # Store Tsys dict with its time tag
            


    #------------------------------------------------------------------------------------
    def __setParams(self, **kwargs):
        '''
        When header reading finish, the information read should be sorted. 
        This method fill variables about DBBC channel identification, frequency and bandwidth 
        and initialize the dictionaries used to get temperature information.
        '''

        if not self.__currentSetup in self.__bbccodelist:

            self.__bbccodelist[self.__currentSetup] = []
            self.__bbcfq[self.__currentSetup] = dict()
            self.__whichif[self.__currentSetup] = dict()
            self.__bw[self.__currentSetup] = dict()

            if not self.__currentSetup in self.calModeName:
                print("Calibration mode not found for setup %s.\nSINGLE calibration mode will be assumed as used by setup %s." % (self.__currentSetup,self.__currentSetup))
                self.calModeName[self.__currentSetup] = "SINGLE"
                self.lastCalMode = self.calModeName[self.__currentSetup]
                if not self.__currentSetup in self.__setupTcal:
                    self.__setupTcal[self.__currentSetup] = dict()
                    self.__caltempRead[self.__currentSetup] = False
                if len(self.__tempDict) < 5:
                    self.__tempDict = [dict()] + self.__tempDict

            if self.dbbcModeName == "PFB":                                # If the DBBC uses PFB mode:
                self.__bbccodelist[self.__currentSetup] = self.__vsiCh[self.__currentSetup][0] + self.__vsiCh[self.__currentSetup][1]    #     self.__bbccodelist should be fill with self.__vsiCh content
                self.__bbccodelist[self.__currentSetup].sort()
                for ch in self.__bbccodelist[self.__currentSetup]:
                    self.__bw[self.__currentSetup][ch] = 32                    #     DBBC channel bandwidth is always 32 MHz
                    self.__whichif[self.__currentSetup][ch] = ch[0]
                    self.__bbcfq[self.__currentSetup][ch] = self.__pfbFreq[int(ch[1:])]    #     DBBC channel frequency is got from self.__pfbFreq private variable


            elif self.dbbcModeName == "DDC":                        # If the DBBC uses DDC mode:
                if not self.__currentSetup in self.__bbcinfo:
                    self.__bbcinfo[self.__currentSetup] = []    
                self.__bbcinfo[self.__currentSetup].sort()
                self.__bbcinfo[self.__currentSetup] = list(k for k,_ in itertools.groupby(self.__bbcinfo[self.__currentSetup]))
                bbcinfo_aux = self.__bbcinfo[self.__currentSetup]
                for i in range(0,len(self.__bbcinfo[self.__currentSetup])):
                    aux = int(bbcinfo_aux[i][0][-2:])
                    if (self.__currentSetup in self.__fila10gMode) and (self.__formType in self.__formChannels):
                        bbcNumIndex = [a for a in range(len(self.__formChannels[self.__formType])) if (('%x' % aux) in self.__formChannels[self.__formType][a]) or ((aux == 16) and ('g' in self.__formChannels[self.__formType][a]))]
                        for index in bbcNumIndex:
                            aux_code = 2**(index*2) + 2**(index*2+1)
                            if aux_code & self.__fila10gMode[self.__currentSetup]:
                                bbclcode=self.__formChannels[self.__formType][index]
                                self.__bbcfq[self.__currentSetup][bbclcode] = float(bbcinfo_aux[i][1]) 
                                self.__whichif[self.__currentSetup][bbclcode] = bbcinfo_aux[i][2]
                                self.__bw[self.__currentSetup][bbclcode] = float(bbcinfo_aux[i][3])
                                self.__bbccodelist[self.__currentSetup].append(bbclcode)
                    elif (self.__currentSetup in self.__recMode) and (self.__formType in self.__formChannels):
                        bbcNumIndex = [a for a in range(len(self.__formChannels[self.__formType])) if ('%x' % aux) in self.__formChannels[self.__formType][a]]
                        for index in bbcNumIndex:
                            aux_code = 2**(index*2) + 2**(index*2+1)
                            if aux_code & self.__recMode[self.__currentSetup]:
                                bbclcode=self.__formChannels[self.__formType][index]
                                self.__bbcfq[self.__currentSetup][bbclcode] = float(bbcinfo_aux[i][1]) 
                                self.__whichif[self.__currentSetup][bbclcode] = bbcinfo_aux[i][2]
                                self.__bw[self.__currentSetup][bbclcode] = float(bbcinfo_aux[i][3])
                                self.__bbccodelist[self.__currentSetup].append(bbclcode)
                    else:
                        if (self.__formType != "geo2"):                    #If format type is "geo2", only uses USB (Upper SideBand), else uses both sidebands.
                            if (self.__formType != "geo") or (aux in [1,8]):    #If format type is "geo", uses these BBCs: 1u,2u,3u,4u,5u,6u,7u,8u,1l,8l,9u,au,bu,cu,du,eu
                                bbclcode='%sl'%str(hex(aux)[-1])        #The other formats use always USB and LSB of each BBC.
                                self.__bbcfq[self.__currentSetup][bbclcode] = float(bbcinfo_aux[i][1])    #All DBBC channel information is got from self.__bbcinfo private variable
                                self.__whichif[self.__currentSetup][bbclcode] = bbcinfo_aux[i][2]
                                self.__bw[self.__currentSetup][bbclcode] = float(bbcinfo_aux[i][3])
                                self.__bbccodelist[self.__currentSetup].append(bbclcode)
                        bbcucode='%su'%str(hex(aux)[-1])
                        self.__bbcfq[self.__currentSetup][bbcucode] = float(bbcinfo_aux[i][1])
                        self.__whichif[self.__currentSetup][bbcucode] = bbcinfo_aux[i][2] 
                        self.__bw[self.__currentSetup][bbcucode] = float(bbcinfo_aux[i][3])
                        self.__bbccodelist[self.__currentSetup].append(bbcucode)                    

            self.__bbccodelist[self.__currentSetup].sort()
            #if self.calModeName[self.__currentSetup] == 'CONT':                # If the DBBC uses CONTINUOUS calibration mode:

            for i in self.__bbccodelist[self.__currentSetup]:            #    Tcal of every DBBC channel should be got from RXG files
                lofq = self.freqLOMHzArray[self.__currentSetup][self.__whichif[self.__currentSetup][i]][-1] 
                pol = self.polArray[self.__currentSetup][self.__whichif[self.__currentSetup][i]][-1]
                band = self.bandArray[self.__currentSetup][self.__whichif[self.__currentSetup][i]][-1]
                bw_aux = self.__bw[self.__currentSetup][i]
                if (self.dbbcModeName == "DDC") and (i[-1] == 'u'):
                    bw_aux = -1*bw_aux
                if "lsb" in band:
                    bbcFreq = -self.__bbcfq[self.__currentSetup][i]
                else:
                    bbcFreq = self.__bbcfq[self.__currentSetup][i]

                fchan=lofq+bbcFreq-bw_aux/2.
                tcal=get_tcal(lofq,pol,fchan, self.station().lower(),cfg=self.cfg,rxgfiles=self.rxgfiles, verbosity=self.verbosity, **kwargs)



                if not self.__caltempRead[self.__currentSetup]:
                    self.__tempDict[-1][i] = [tcal]                
                    self.__setupTcal[self.__currentSetup][i] = [tcal]

        else:
            #if self.calModeName[self.__currentSetup] == 'CONT':
            for i in self.__bbccodelist[self.__currentSetup]:
                self.__tempDict[-1][i] = self.__setupTcal[self.__currentSetup][i]
    
    #------------------------------------------------------------------------------------
    def __readTempVar(self, line, nextLine, **kwargs):
        """
        Read 'tpicd' temperature variable from the LOG file.
        At the beginning, this method check two strings to detect if DBBC uses 
        CONT or SINGLE calibration mode. When calibration mode has been identified,
        just use the string corresponding to the detected mode.
        
        To determine if the integration time has been exceeded, this method compare the
        dates of the checked line and the next line. 

        @param line Line to check
        @param nextLine The next line of the line to check
        """

        if self.calModeName[self.__currentSetup] == "CONT":                    # If the DBBC uses CONTINUOUS calibration mode, check the line with "#tpicd#tpcont/"
            tempReference = ['#tpicd#tpcont/']
        elif self.calModeName[self.__currentSetup] == "SINGLE":                # If the DBBC uses SINGLE calibration mode, check the line with "#tpicd#tpi/"
            tempReference = ['#tpicd#tpi/']

        tempInd = self.__idLine(line,tempReference)

        if not self.__headerComp and not self.__currentSetup in self.calModeName:        # If the calibration mode has been identified:
            self.__setParams(**kwargs)                                #    Call self.__setParams() method to prepare the variables used to store temperature information
            self.__headerComp = True                            #     Set self.__headerComp to True, indicating that header reading has finished
        
        dt = self.__getDatetime(line)
        if nextLine == "":
            dt_nextLine = dt + datetime.timedelta(0,0,0,200)
        else:
            dt_nextLine = self.__getDatetime(nextLine)

        if (dt-self.__dtStartInt)>= self.__intTime and (dt_nextLine-dt)>datetime.timedelta(0,0,0,100): # Compare the checked line date and the next line date. If the integration time
            self.__intComplete = True                  # has been exceeded, set self.__intComplete to True and store the date when the integration
            self.__dtStartInt = dt                      # finished.

        if tempInd == 0:                          # Only store temperature information if tempInd == 0, because it means that a reference string 
            pass                              # was found in the checked line.
        else:
            self.__getTempLine(line, tempInd)

    #------------------------------------------------------------------------------------
    def __checkDataValid(self, line, **kwargs):
        """
        Read a LOG file line to check if the following lines have valid data or not.
        When a 'data_valid=off' is read, it indicates that integration has finished 
        and Tsys is calculated.

        @param line Line to check
        """

        idIndex = self.__idLine(line,['data_valid=on', 'data_valid=off'])

        if idIndex == 0:
            pass
        elif idIndex == 1:
            if not self.__currentSetup == None:     
                self.__dataValid = True
                self.__dtStartInt = self.__getDatetime(line)
                if self.__newSetup:
                    self.__setParams(**kwargs)
                self.__newSetup = False

            return True
        elif idIndex == 2:
            if not self.__currentSetup == None:
                if self.__dataValid:
                    self.__intComplete = True
                self.__dataValid = False

            return True

        return False

    #------------------------------------------------------------------------------------
    def __getGenVar(self, line):
        """
        Read a LOG file line to check if there are general variables.
        General variables are variables that can appear anywhere inside the LOG file.
        These variables are:
            - Scan name/number
            - Source to observe
            - LO configuration
            - Tsys printed inside the LOG file
            - In SINGLE calibration mode: tpiprime, tpical and caltemp can appear anywhere inside the LOG file, even if data is not valid. 

        @param line Line to check
        """

        # If DBBC configuration mode was found, look for the DBBC channels used in the observation
        if self.dbbcModeName == "PFB":        
            vsiNum = self.__idLine(line, ['/vsi1=', '/vsi2='])         
            if vsiNum != 0:                          # When DBBC uses PFB mode: 
                auxStr = line.split('=')              # "&setup01/vsi1=a05,a06,a07,a08,a09,a10,a11,a12,b05,b06,b07,b08,b09,b10,b11,b12"
                if not self.__currentSetup in self.__vsiCh:
                    self.__vsiCh[self.__currentSetup] = [[],[]]
                self.__vsiCh[self.__currentSetup][vsiNum-1] = auxStr[1].split('\n')[0].split(',')    
                return True

        elif self.dbbcModeName == "DDC":                  
            if self.__idLine(line,['&dbbc']) and not self.__idLine(line,['/if=bbc']):              # When DBBC uses DDC mode:
                #print line
                auxStr=line.split('/')[1].split('=')          # "&dbbc01d/bbc01=638.49,a,16.00"
                bbcstr=auxStr[0]
                bbcsplt=auxStr[1].split(',')
                if not self.__currentSetup in self.__bbcinfo:
                    self.__bbcinfo[self.__currentSetup] = []
                self.__bbcinfo[self.__currentSetup].append([bbcstr,bbcsplt[0],bbcsplt[1],bbcsplt[2]]) # self.__bbcinfo: [['bbc01', '638.49', 'a', '16.00'],[...]]
                return True                                          #               chID     Freq     chIF  bandwidth

        if self.__idLine(line,[':scan_name=']):
            self.__scanName = scan_aux=line.split('=')[1].split(',')[0]    # The scan name usually corresponds with the scan number, but not always.
            self.__scanNum += 1                        # For this reason, the scan name and the scan number are separated in different variables.

            return True

        if self.__idLine(line,[':source=']):                    # When source string reference is found, a new scan line is made to write scan information inside ANTAB file.
            dt = self.__getDatetime(line)                    # This line is usually the next line to a scan name line.
            days = (dt - datetime.datetime(dt.year,1,1,dt.hour,dt.minute,dt.second,dt.microsecond)).days + 1
            sourceName = line.split('=')[1].split(',')[0]
            strLine=('\n! %03d %02d:%05.2f: scanNum=%04d scanName=%s source=%s'%(days,dt.hour,dt.minute + (dt.second/60.) + (dt.microsecond/(60.*float(1e6))),self.__scanNum, self.__scanName,sourceName))
            self.__scanline.append(strLine)
            return True

        #-----------------------Current Setup-------------------------

        if self.__idLine(line, [':setup',';setup','/setup']):
            self.__currentSetup = line.split('p')[-1].strip()

            if not self.__currentSetup in self.__setupTcal:
                self.__setupTcal[self.__currentSetup] = dict()
                self.__caltempRead[self.__currentSetup] = False

            if self.__currentSetup != self.__lastSetup:
                dt = self.__getDatetime(line)
                time_aux =  (dt - self.__epoch).total_seconds()
                #days = (dt - datetime.datetime(dt.year,1,1,dt.hour,dt.minute,dt.second,dt.microsecond)).days + 1
                #time_aux = days + (dt.hour/24.) + (dt.minute/(60.*24.)) + (dt.second/(3600.*24.)) + (dt.microsecond/(3600.*24.*1e6))
                self.__setupTime.append([time_aux,self.__currentSetup])
                self.__lastSetup = self.__currentSetup
                self.__newSetup = True

                if self.__currentSetup in self.calModeName:
                    if self.calModeName[self.__currentSetup] == 'SINGLE':
                        self.__tempDict = [dict(),dict(),dict(),dict()]
                    elif self.calModeName[self.__currentSetup] == 'CONT':
                        self.__tempDict = [dict(),dict(),dict()] 

                return True

        if self.__idLine(line, ['&setup']):

            auxStr = line.split('&')[1].split('/')
            curSetup = auxStr[0].split('setup')[1]
            if "ifd" in auxStr[1]:
                if not curSetup in self.ifdSetup:
                    self.ifdSetup[curSetup] = auxStr[1].strip()
            
        #------------------------Fila10G Mode-------------------------
        if self.__idLine(line, ['/fila10g_mode=']):
            tmpLine = line.split('=')[1]
            mask1 = tmpLine.split(',')[0].strip('0x')
            mask2 = tmpLine.split(',')[1].strip('0x')
            mask = ''.join(['0x',mask2,mask1])
            #self.__fila10gMode[self.__currentSetup] = int(line.split(',')[1],16)
            self.__fila10gMode[self.__currentSetup] = int(mask,16)
        elif self.__idLine(line, ['_mode=']):
            self.__recMode[self.__currentSetup] = int(line.split(',')[1],16)

        #----------------------Calibration Mode-----------------------

        if self.__idLine(line, ['/cont_cal=']) and self.__idLine(line, ['&setup']):

            auxStr = line.split('=')[1].split(',')                    # 2017.067.01:06:11.50&setup03/cont_cal=off
            if auxStr[0].strip() == 'off':
                self.calModeName[self.__currentSetup] = 'SINGLE'
            elif auxStr[0].strip() == 'on':
                self.calModeName[self.__currentSetup] = 'CONT'

            if self.calModeName[self.__currentSetup] != self.lastCalMode:
                self.lastCalMode = self.calModeName[self.__currentSetup]    
                if self.calModeName[self.__currentSetup] == 'SINGLE':
                    self.__tempDict = [dict(),dict(),dict(),dict(), dict()]
                elif self.calModeName[self.__currentSetup] == 'CONT':
                    self.__tempDict = [dict(),dict(),dict(), dict()]

            return True

        #---------------------LO Configuration------------------------
        # Get LOs frequency and polarization.
        loReference = ["/lo=loa", "/lo=lob", "/lo=loc", "/lo=lod"]

        if self.__idLine(line, loReference):                        # Line to check:
            ifID = line.split('&')[1].split("/")[0]

            if ifID != self.ifdSetup[self.__currentSetup]:
                return True 

            auxStr = line.split(',')                        #    "lo=loa,42500.00,usb,rcp,1.000"
            ifsel = auxStr[0][-1]                            #     ifsel = 'a'

            if (self.__currentSetup in self.freqLOMHzArray):
                freqLOMHzArray_aux = self.freqLOMHzArray[self.__currentSetup]
                polArray_aux = self.polArray[self.__currentSetup]
                bandArray_aux = self.bandArray[self.__currentSetup]

                if (ifsel in freqLOMHzArray_aux) and (ifsel in polArray_aux) and (ifsel in bandArray_aux):
                    freqAux = freqLOMHzArray_aux[ifsel]
                    polAux = polArray_aux[ifsel]
                    bandAux = bandArray_aux[ifsel]
                else:
                    freqAux = []
                    polAux = []
                    bandAux = []
            else:
                self.freqLOMHzArray[self.__currentSetup] = dict()
                self.polArray[self.__currentSetup] = dict()
                self.bandArray[self.__currentSetup] = dict()
                freqAux = []
                polAux = []
                bandAux = []

            fill = True
            try:
                newFreq = float(auxStr[1])                        #    newFreq = 42500.0
            except:
                print("Couldn't convert '%s' to float. Ignoring current line: '%s'" % (auxStr[1],line))
                return True
            newPol = auxStr[3]                            #    newPol = 'rcp'
            newBand = auxStr[2]                            #    newBand = 'usb'
            for i in range(len(freqAux)):
                if (freqAux[i] == newFreq) and (polAux[i] == newPol) and (bandAux[i] == newBand):        # If the new pair of frequency and polarization has been stored before for this IF, 
                    fill = False                                        # this new pair is not stored.
                    break

            if fill:                                # The program stored the pair of frequency and polarization.
                freqAux.append(newFreq) 
                polAux.append(newPol)
                bandAux.append(newBand)
                self.freqLOMHzArray[self.__currentSetup][ifsel] = freqAux
                self.polArray[self.__currentSetup][ifsel] = polAux
                self.bandArray[self.__currentSetup][ifsel] = bandAux

            return True

        if self.__currentSetup in self.calModeName: 

            if self.calModeName[self.__currentSetup] == "SINGLE":        # If the DBBC uses SINGLE calibration mode, 
                auxReference = ['/tpi/', '/tpical', '/tpdiff/', '/caltemp/']    # check the LOG file line to look for tpiprime, tpical and caltemp temperature variables.
                tempInd = self.__idLine(line,auxReference)       

                if tempInd != 0:                    # If any temperature variable was found, store it in its dictionary.
                    tempInd += 1                    # If SINGLE calibration mode was identified, increase temperature index in one.  
                    self.__getTempLine(line, tempInd)        # At the beginning     -> tempDict: [tpiprime, tpical, caltemp]
                    return True                    # SINGLE cal detected  -> tempDict: [tpicd, tpiprime, tpical, caltemp]

                elif self.__idLine(line, ['/tsys/']):            # If no temperature variable was found, check the LOG file line to look for Tsys printed inside the LOG file.
                                            #     "/tsys/1l,130.8,1u,130.8,3l,130.8,3u,131.0,ia,145.5"
                    dt = self.__getDatetime(line)            #       time_aux: Time tag of the checked line
                    time_aux =  (dt - self.__epoch).total_seconds()
                    
                    #days = (dt - datetime.datetime(dt.year,1,1,dt.hour,dt.minute,dt.second,dt.microsecond)).days + 1
                    #time_aux = days + (dt.hour/24.) + (dt.minute/(60.*24.)) + (dt.second/(3600.*24.)) + (dt.microsecond/(3600.*24.*1e6))
                    auxStr = line.split('/')[-1].split(',')

                    if not time_aux in self.__tsyslogDict:
                        self.__tsyslogDict[time_aux] = dict()    

                    auxDict = self.__tsyslogDict[time_aux]
    
                    for i in range(0,len(auxStr),2):
                        dictExist = False
                        if (auxStr[i] in auxDict):
                            dictExist = True        
                        for element in self.__chId:
                            if element==auxStr[i][self.__chIdIndex]:
                                if dictExist:
                                    try:
                                        auxDict[auxStr[i]].append(float(auxStr[i+1]))
                                    except:
                                        auxDict[auxStr[i]].append(-1)
                                else:
                                    try:
                                        auxDict[auxStr[i]] = [float(auxStr[i+1])]
                                    except:
                                        auxDict[auxStr[i]] = [-1]        
    
                    self.__tsyslogDict[time_aux] = auxDict    # self.__tsyslogDict = [ time_aux : [ '1l' : [130.8], '1u' : [130.8], '3l' : [130.8], '3u' : [131.0] ], ... ]
                    return True
    
            else:
                if self.__idLine(line, ['/caltemp/']):
                    self.__getTempLine(line,len(self.__tempDict))
                    return True
                                            # If the DBBC uses CONTINUOUS calibration mode, check the LOG file line to look for Tsys printed inside the LOG file.
                elif self.__idLine(line, ['#tpicd#tsys/']):        #     "#tpicd#tsys/1l,46.3,1u,49.5"
                    dt = self.__getDatetime(line)            #    time_aux: Time tag of the checked line  
                    time_aux =  (dt - self.__epoch).total_seconds()
                    #days = (dt - datetime.datetime(dt.year,1,1,dt.hour,dt.minute,dt.second,dt.microsecond)).days + 1
                    #time_aux = days + (dt.hour/24.) + (dt.minute/(60.*24.)) + (dt.second/(3600.*24.)) + (dt.microsecond/(3600.*24.*1e6))
                    auxStr = line.split('/')[-1].split(',')
                    
                    if not time_aux in self.__tsyslogDict:
                        self.__tsyslogDict[time_aux] = dict()
    
                    auxDict = self.__tsyslogDict[time_aux]
    
                    for i in range(0,len(auxStr),2):
                        dictExist = False
                        if (auxStr[i] in auxDict):
                            dictExist = True
                        for element in self.__chId:
                            if element==auxStr[i][self.__chIdIndex]:
                                if dictExist:
                                    try:
                                        auxDict[auxStr[i]].append(float(auxStr[i+1]))
                                    except:
                                        auxDict[auxStr[i]].append(-1)
                                else:   
                                    try:
                                        auxDict[auxStr[i]] = [float(auxStr[i+1])]
                                    except:
                                        auxDict[auxStr[i]] = [-1]
    
                    self.__tsyslogDict[time_aux] = auxDict        # self.__tsyslogDict = [ time_aux : [ '1l' : [46.3], '1u' : [49.5] ], ... ]
                    return True
        else:
            auxReference = ['/tpi/', '/tpical', '/caltemp/']    
            tempInd = self.__idLine(line,auxReference)          
                    
            if tempInd != 0:                    
                self.__getTempLine(line, tempInd)        
                return True


        return False
            
    #------------------------------------------------------------------------------------
    def __getTsys(self, bbccodelist, dt,**kwargs):
        '''
        Calculate Tsys for each individual DBBC channel used in the LOG file.
        
        @param bbccodelist List that contains all individual DBBC channel used in the LOG file
        @param dt Date when integration was completed. 
        '''

        if not self.__headerComp and not (self.__currentSetup in self.calModeName):        # If header reading was not finished yet means that no tpicd line was found in the LOG file.
            self.calModeName[self.__currentSetup] = "SINGLE"                # In that case, set SINGLE as the calibration mode used by the DBBC.
            self.__setParams(**kwargs)    
            self.__headerComp = True

        temp=[]
        dt_newOrder = datetime.datetime(2015,9,17)
        tpzero = 0
        for i in bbccodelist:
            if not i in self.__tempDict[-1]:            
                temp.append(-1)                 
                continue

            tcal = self.__tempDict[-1][i][0]            # Get Tcal from temperature dictionary. This dictionary was filled with Tcal from RXG files or LOG file.
            if tcal == 0:                        
                temp.append(-1)                    # If Tcal is 0, Tsys cannot be calculated.
                continue

            if self.calModeName[self.__currentSetup] == "CONT":        # If the DBBC uses CONTINUOUS calibration mode, tpicd1 and tpicd2 will be used to calculate Tsys.

                try:
                    if dt < dt_newOrder:                # Until 17th september 2015, tpicd2 was Vsys ON and tpicd1 was Vsys OFF
                        vsysONlist = self.__tempDict[1][i]
                        vsysOFFlist = self.__tempDict[0][i]
                    else:                        # After 17th september 2015, tpicd1 is Vsys ON and tpicd2 is Vsys OFF 
                        vsysONlist = self.__tempDict[0][i]
                        vsysOFFlist = self.__tempDict[1][i]
                except:
                    temp.append(-1)                    # Tsys cannot be calculated if there is any exception getting temperature variables
                    continue                    # from temperature dictionaries for a certain DBBC channel.


                if len(vsysONlist) == 0 or len(vsysOFFlist) == 0:    # If any Vsys list is empty, Tsys cannot be calculated.
                       continue

                vsysON = sum(vsysONlist)/len(vsysONlist)        # Get the mean value of Vsys ON and Vsys OFF
                vsysOFF = sum(vsysOFFlist)/len(vsysOFFlist)

                if vsysON <= vsysOFF:                    # If Vsys OFF is greater than Vsys ON, Tsys cannot be calculated.
                    tsys=-1
                else:
                    tsys=0.5*tcal*(vsysON+vsysOFF)/(vsysON-vsysOFF) 

            elif self.calModeName[self.__currentSetup] == "SINGLE":        # If the DBBC uses CONTINUOUS calibration mode, tpicd, tpiprime and tpical will be used to calculate Tsys.

                tpiprimeList = []
                tpicalList = []
                vsysList = []
                tpidiffList = []

                try:
                    if self.__tempDict[1]:
                        tpiprimeList = self.__tempDict[1][i]
                    if self.__tempDict[2]:
                        tpicalList = self.__tempDict[2][i]
                    if self.__tempDict[0]:
                        vsysList = self.__tempDict[0][i]
                    if self.__tempDict[3]:
                        tpidiffList = self.__tempDict[3][i]
                        
                except Exception as e:                            # Tsys cannot be calculated if there is any exception getting temperature variables
                    temp.append(-1)                    # from temperature dictionaries for a certain DBBC channel.
                    continue                
                if len(tpidiffList) != 0:
                    if len(vsysList) == 0:
                        temp.append(-1)
                        continue
                        #vsys = sum(tpiprimeList)/len(tpiprimeList)
                    else:
                        vsys = sum(vsysList)/len(vsysList)
                    tpidiff = sum(tpidiffList)/len(tpidiffList)
                    if tpidiff <= 0:
                        tsys=-1
                    else:
                        tsys=tcal*(vsys-tpzero)/tpidiff

                else:
                    if len(tpiprimeList) == 0 or len(tpicalList) == 0:    # If any temperature list is empty, Tsys cannot be calculated.
                        temp.append(-1)
                        continue                    

                    
                    tpiprime = sum(tpiprimeList)/len(tpiprimeList)        # Get the mean value of each temperature variable.
                    tpical = sum(tpicalList)/len(tpicalList)
                    if len(vsysList) == 0:
                        temp.append(-1)
                        continue
                        #vsys = sum(tpiprimeList)/len(tpiprimeList)
                    else:
                        vsys = sum(vsysList)/len(vsysList)
                    if tpical<=tpiprime:                    # If tpiprime is greater than tpical, Tsys cannot be calculated.
                        tsys=-1
                        #print "tpiprime: %f; tpical: %f" % (tpiprime,tpical) 
                    else:
                        tsys=tcal*(vsys-tpzero)/(tpical-tpiprime)

            temp.append(tsys)

        self.__tempDict[0] = dict()                        # Clear temperature dictionaries:
        if self.calModeName[self.__currentSetup] == "CONT":            #    CONTINUOUS calibration case: tpicd1 and tpicd2 (indexes 0 and 1)
            self.__tempDict[1] = dict()                    #    SINGLE calibration case: tpicd (index 0)

        return temp

    #------------------------------------------------------------------------------------
    def __getTempLine(self, line, tempInd):
        '''
        Store temperature variables in the proper temperature dictionary.
        
        @param line Checked line (It should be checked before using self.__idLine method)
        @param tempInd Index returned by self.__idLine method that indicates what is the temperature dictionary
                   where the temperature variable found should be stored.
        '''

        auxDict = self.__tempDict[tempInd - 1]
        auxStr = line.split('/')[-1].split(',')

        if self.__currentSetup in self.calModeName:
            tpcontDet = (tempInd == 1) and (self.calModeName[self.__currentSetup] == "CONT")    # If the DBBC uses CONTINUOS calibration mode and the temperature variable is tpicd,
        else:                                                # tpcontDet variable will be set to True, otherwise will be set to False.
            tpcontDet = False        

        if tpcontDet:                                        # tpicd line using CONTINUOUS calibration mode: 
            auxRange = list(range(0,len(auxStr),3))                        #     '#tpicd#tpcont/9l,17453,16984,9u,17553,17100,ic,1464.25'
        else:                                            #    - Each individual DBBC channel has two temperature values
            auxRange = list(range(0,len(auxStr),2))                        # tpicd line using SINGLE calibration mode:
                                                    #    '#tpicd#tpi/a05,23980,a06,45220,a07,58900,a08,62240,a09,67080,a10,78810,a11,96400'
        for i in auxRange:                                    #    - Each individual DBBC channel has one temperature value
            dictExist = False
            if (auxStr[i] in auxDict):
                dictExist = True
                #if tempInd == len(self.__tempDict):        # If tempInd is equal than self.__tempDict length means that tcal will be stored
                if tempInd != 1 or not self.__currentSetup in self.calModeName:    # If tempInd is equal than self.__tempDict length means that tcal will be stored
                    dictExist = False            # In this case, the program only stores the last tcal value read.
            for element in self.__chId:
                if element==auxStr[i][self.__chIdIndex]:
                    if dictExist:                # If dictExist is True, the values read will be appended.
                        try:
                            auxDict[auxStr[i]].append(float(auxStr[i+1]))
                            if tpcontDet:
                                self.__tempDict[1][auxStr[i]].append(float(auxStr[i+2]))
                        except:
                            auxDict[auxStr[i]].append(-1)
                            if tpcontDet:
                                self.__tempDict[1][auxStr[i]].append(-1)
                    else:                    # If dictExist is False, a new list with the values read will be created.
                        try:
                            auxDict[auxStr[i]] = [float(auxStr[i+1])]
                            if tpcontDet:
                                self.__tempDict[1][auxStr[i]] = [float(auxStr[i+2])]
                        except:
                            auxDict[auxStr[i]] = [-1]
                            if tpcontDet:
                                self.__tempDict[1][auxStr[i]] = [-1]

            
    
        self.__tempDict[tempInd - 1] = auxDict

        if (tempInd == len(self.__tempDict)):                # If temperature variable read was tcal, update self.__setupTcal with the new tcal value.
            self.__setupTcal[self.__currentSetup] = self.__tempDict[-1]    
            self.__caltempRead[self.__currentSetup] = True    

    #------------------------------------------------------------------------------------
    def __readHeader(self, line):
        '''Reads one LOG file line to find header variables.
        Header variables are those coming from the procedures the first time they are executed, 
        because later they no longer appear in the log. Usually associated to different modes
        or settings of the individual DBBC channels

        Results are in private variables of the class:
        self.dbbcModeName Name of the mode being used: None, DDC or PFB

        @param line LOG file line read.
        '''

        #-------------------DBBC Configuration------------------------
        
        # If DBBC configuration mode was not found, look for it.
        if self.dbbcModeName == None:                      # Look for DBBC configuration mode
            indAux = self.__idLine(line,["Rack=DBBC", 'equip,dbbc_']) # Check if one of these strings is in the LOG file line
            if indAux == 0:                          # If indAux == 0, neither of them has been found
                pass
            else:
                if indAux == 1:                      # If indAux == 1, "Rack=DBBC" found.
                    aux1 = line.split(' ')[1]          
                    aux2 = aux1.split('_')              
                    if len(aux2)==2:              # " Rack=DBBC_PFB  ..." -> PFB
                        self.dbbcModeName = aux2[1]      # " Rack=DBBC_DDC  ..." -> DDC
                    else:                      # " Rack=DBBC      ..." -> DDC
                           self.dbbcModeName = "DDC"
                elif indAux == 2:                  # If indAux == 2, "equip,dbbc_" found.
                    aux1 = line.split('_')[1]          # "equip,dbbc_pfb/..." -> PFB
                    aux2 = aux1.split(',')[0]          # "equip,dbbc_ddc/..." -> DDC
                    aux3 = aux2.split('/')[0]          # "equip,dbbc_ddc/..." -> DDC
                    self.dbbcModeName = aux3.upper()

                if self.dbbcModeName == "PFB":              # If the DBBC uses PFB mode, each DBBC channel has as preffix "a", "b", "c" or "d" in temperature lines
                    self.__chId = ['a','b','c','d']          # DBBC channel identification
                    self.__chIdIndex = 0              # '0' indicates identification as preffix

                elif self.dbbcModeName == "DDC":          # If the DBBC uses DDC mode, each DBBC channel has as suffix "u" or "l" in temperature lines
                    self.__chId = ['u','l']              # DBBC channel identification
                    self.__chIdIndex = -1              # '-1' indicates identification as suffix
                else:
                    self.dbbcModeName = None

                return True


        #---------------Lower Sideband Identification-----------------
        if self.__idLine(line,['/form=']):                  #Get format type
            self.__formType = line.split('=')[1][:-1]
            #self.__lower = False
            return True
        

        return False
            
    #------------------------------------------------------------------------------------
    def __idLine(self, line, reference):
        '''
        Check a LOG file line using a list of reference strings.
        Return the index of the reference string found in the checked line.
        If neither reference string is found, return 0.
        '''
        for i in range(0,len(reference)):
            if reference[i] in line:
                return (i+1)
        return 0

    #------------------------------------------------------------------------------------
    def __getDatetime(self, line):
        """
        Return the date of the LOG file line as python datetime.datetime
        """
        auxDate = line.split('.')
        auxTime = auxDate[2].split(':')
        usec = int(int(auxDate[3][:2]) * 1e4)

        year=int(auxDate[0])
        day=int(auxDate[1])
        hour=int(auxTime[0])
        minu=int(auxTime[1])
        sec=int(auxTime[2])

        dt = datetime.datetime(year,1,1,hour,minu,sec,usec) + datetime.timedelta(day-1)
        return dt

    #------------------------------------------------------------------------------------
    def getLogData(self):
        
        return self.logData 

    #------------------------------------------------------------------------------------
    def loArray(self):
        '''Creates a set from the array removing repeated elements. It is a Python builtin module.
        Returns an array with unique elements (no one is repeated)
        '''

        fLOArray_aux, pArray = self.loPArray()
        #fLOArray = sorted(set(fLOArray_aux), key=lambda x: fLOArray_aux.index(x))
        fLOArray = dict()
        for setup in reversed(list(fLOArray_aux.keys())):
            fLOArray[setup] = sorted(set(fLOArray_aux[setup]), key=lambda x: fLOArray_aux[setup].index(x))

        return fLOArray

    #------------------------------------------------------------------------------------
    def loPArray(self):
        '''
        '''

        fLOArray = dict() 
        pArray = dict()

        for setup in reversed(list(self.polArray.keys())):
            fLOArray[setup] = []
            pArray[setup] = []
            tup = []
            for key in self.polArray[setup]:
                for ind in range(len(self.polArray[setup][key])):
                    appendData = True
                    if len(tup) == 0:
                        pass
                    else:
                        for i in range(0, len(tup)):
                            if (tup[i][0] == self.freqLOMHzArray[setup][key][ind]) and (tup[i][1] == self.polArray[setup][key][ind]): 
                                appendData = False
                    if appendData:
                        tup.append((self.freqLOMHzArray[setup][key][ind], self.polArray[setup][key][ind]))
        
            for el in tup:
                fLOArray[setup].append(el[0])
                pArray[setup].append(el[1])

        return fLOArray, pArray    

    #------------------------------------------------------------------------------------
    def station(self):
        '''Returns the name of the station in uppercase. The string is extracted in the constructor
        '''
        return self.stationName    

    #------------------------------------------------------------------------------------
    def experiment(self):
        '''Returns the name of the experiment in lowercase. The string is extracted in the constructor
        '''
        return self.expName    
    #------------------------------------------------------------------------------------
    def dbbcMode(self):
        '''Returns DBBC mode (PFB or DDC)
        '''

        return self.dbbcModeName
    #------------------------------------------------------------------------------------
    def calMode(self):
        '''Returns calibration mode (SINGLE or CONT)
        '''

        return self.calModeName
    #------------------------------------------------------------------------------------
    def rxgFiles(self):
        '''Returns the names of the RXG files required by the LOs
        '''

        fLOArray = self.loArray()
        rxgFileArray = dict()

        for setup in reversed(list(fLOArray.keys())):
            rxgFileArray[setup] = []            
            for fLO in fLOArray[setup]:
                rxgName = self.getRXGFileName(fLO)
                rxgFileArray[setup].append( rxgName )

        return rxgFileArray

    #------------------------------------------------------------------------------------
    #def getBandwidth(self, freqLOMHz):
        '''
        We need something to know if there is more than one mode with different BWs
        '''

        # Clean repeated entries
    #    for i in self.__BB:
    #        return i


    #------------------------------------------------------------------------------------
    def getRXGFileName(self, freqLOMHz):
        '''Gets the name of the RXG file which matches the LO frequency
        The procedure looks in directory /usr2/control/rxg_files
        @param LO freq in MHz
        @return RXG file name
        '''

        # global rxgfiles
        rxgfiles=self.rxgfiles
        foundFile = False
        fileRXG = " "

        if rxgfiles:
            ficherosRXG = rxgfiles    
        else:
            ficherosRXG = os.listdir(self.__rxgDirectory)

        for fileN in ficherosRXG:
            if fileN.endswith(".rxg") and not foundFile:
                #stName = fileN[5:7].lower()
                #if stName != self.stationName.lower():
                #    continue
                
                # If the rxgfile are provided no need to check the name
                stcode = self.stationName[0].upper()+self.stationName[1].lower()
                if stcode not in fileN and not rxgfiles:
                    continue
                fileName = "%s/%s" % (self.__rxgDirectory, fileN)
                rxgF = rxgFile(fileName)
                try:
                    fLOList = rxgF.lo()
                    if len(fLOList) == 1:
                        freqLOf = float(fLOList[0])
                        if freqLOMHz == freqLOf:
                            fileRXG = fileName
                            foundFile = True
                            break
                    else:
                        freqStart = float(fLOList[0])
                        freqEnd = float(fLOList[1])
                        if freqLOMHz >= freqStart and freqLOMHz <= freqEnd:
                            fileRXG = fileName
                            foundFile = True
                            break
                        else:
                            pass
                except Exception as ex:
                    print("Error getting LO freq")
                    raise ex
                del rxgF
        return fileRXG

def get_tcal(lofq,pol,freq,station,cfg=None, rxgfiles=None, verbosity=0, **kwargs):
    print('----- Tcal -----')
    caldir=cfg['CALIB']['rxgDir']

    # caldir='/home/blew/programy/antab/data/rxg_files/'
    #caldir='/usr2/oper/antabfs_pruebas/rxg_files/'
    # If rxgfiles are provided check them, otherwhise look into cal dir
    # global rxgfiles

    smooth_rxg='raw'
    if 'smooth_rxg' in kwargs.keys():
        smooth_rxg=kwargs['smooth_rxg']

    allow_Tcal_extrapolate=False
    if 'allow_Tcal_extrapolate' in kwargs.keys():
        allow_Tcal_extrapolate=kwargs['allow_Tcal_extrapolate']

    if allow_Tcal_extrapolate=='false':
        allow_Tcal_extrapolate=False
    elif allow_Tcal_extrapolate=='true':
        allow_Tcal_extrapolate=True



    if rxgfiles:
        rxglist = [os.path.join(caldir,f) for f in rxgfiles]
        # rxglist = rxgfiles
    else:
        rxglist=[]
        lall=[]
        if os.path.isdir(caldir):
            lall=os.listdir(caldir)
        else:
            if verbosity>0:
                print("Warning: caldir ({}) not found".format(caldir))
        for f in lall:
            # print(f)
            if f.endswith('.rxg'):
                '''
                select appropriate rxg for this log file
                '''
                rxg=rxgFile(os.path.join(caldir,f))
                fmin,fmax=rxg.freqMinMax()
                margin=500.
                fmin-=margin
                fmax+=margin
                if fmin<=freq and freq<=fmax:
                    rxglist.append(os.path.join(caldir,f))
                    print('Will use {} file'.format(f))

    

    
    # if verbosity>1:
    #     print(rxglist)
    if verbosity>0:
        print('smooth_rxg: ',smooth_rxg)
        print('requested frequecy: ',freq)
    fileok=False
    tcal=0
    for filename in rxglist:
        if verbosity>0:
            print("Using %s RXG file" % filename)
        rxgfilename = filename.split('/')[-1]
        #stationfilename = rxgfilename[3:5].lower()
        # Station code checkout is not necessary if user provides RXG files
        stcode = station[0].upper()+station[1]
        if stcode in filename or rxgfiles:
        #if station == stationfilename or forzado:

            if smooth_rxg=='raw':
                f=open(filename).read().splitlines()
                for f in range(0,len(f)):
                    if f[f][0:5]=='range':
                        rmin=float(f[f].split()[1]);rmax=float(f[f].split()[2])
                        if rmin<=lofq<=rmax:
                            fileok=True
                        else:
                            break
                    elif f[f][0:5]=='fixed':
                        rmin=float(f[f].split()[1])-10;rmax=float(f[f].split()[1])+10
                        if rmin<=lofq<=rmax:
                            fileok=True
                            if debug:
                                print("Using %s RXG file" % filename)
                        else:
                            break
                    if fileok and f < len(f)-1:
                        if f[f][0:3]==pol and f[f+1][0:3]==pol:
                            f1=float(f[f].split()[1]);f2=float(f[f+1].split()[1])
                            if f1<=freq<=f2:
                                t1=float(f[f].split()[2]);t2=float(f[f+1].split()[2])
                                tcal=t1+(freq-f1)*(t2-t1)/(f2-f1)
                                break
            else:
                rxg=rxgFile(filename)
                fmin,fmax=rxg.freqMinMax()
                if (fmin<=freq and freq<=fmax) or allow_Tcal_extrapolate:
                    xy=np.array(rxg.calvsFreq(pol),dtype=float)
                    dl=[xy]
                    labels=['measurement']
#                    xyfit=rxg.get_fitTcal(pol,rxg_fit_method='ols', regressors=smooth_rxg)
                    xyfit2=rxg.get_fitTcal(pol,rxg_fit_method='rlm', regressors='poly4')
                    labels.append('%s fit (rlm)' % 'poly4')
                    dl.append(xyfit2)
                    
                    if 'poly' in smooth_rxg:
                        xyfit3=rxg.get_fitTcal(pol,rxg_fit_method='rlm', regressors=smooth_rxg)
                        labels.append('%s fit' % smooth_rxg)
                    elif smooth_rxg=='rolling_avg':
                        xyfit3=rxg.get_fitTcal(pol,rxg_fit_method='rolling_avg')
                        labels.append('rolling average')
                    elif smooth_rxg=='arima':
                        xyfit3=rxg.get_fitTcal(pol,rxg_fit_method='arima')
                        labels.append('arima model')
                    else:
                        xyfit3=xy
                        
                    dl.append(xyfit3)
                    
                    
                    if (fmin<=freq and freq<=fmax) or allow_Tcal_extrapolate:
                        if (fmin<=freq and freq<=fmax):
                            fint=interp1d(xyfit2[:,0],xyfit2[:,1])
                            tcal=fint(freq)
                        else:
                            fint=interp1d(xyfit2[:,0],xyfit2[:,1], bounds_error=False,
                                          fill_value=(xy[0,1],xy[-1,1]))
                            tcal=fint(freq)
                            print("WARNING: REQUESTED FREQUENCY ({}) IS NOT COVERED BY RXG FILE ({},{})".format(freq,fmin,fmax))
                            print("WARNING: USING EXTRAPOLATED T_CAL VALUE ({}) DUE TO allow_Tcal_extrapolate FLAG.".format(tcal))

                    if verbosity>1:
                        print('Interpolated tcal={}'.format(tcal))
                        vis.plot_Tcal(dl,labels,pol,freq)
                else:
                    if verbosity>2:
                        print('Ignoring rxg file {} due to wrong frequency range'.format(filename))
            
            if tcal!=0:
                break
    if fileok==False:
        if verbosity>1:
            print("tcal = %g" % tcal)
        #sys.exit('A suitable rxg_file was not found')
            print('A suitable rxg_file was not found. Maybe tcal is inside LOG file ("caltemp" tag)')

    if verbosity>0:
        print('tcal',tcal)
    if 'enforceTcalIfNoCal' in kwargs.keys():
        if tcal==0:
            tcal=kwargs['enforceTcalIfNoCal']
            if verbosity>2:
                print('enforceTcalIfNoCal: ',tcal)
    
    return tcal


class rxgFile:
    '''
    Information about the content of the RXG file.
    Class to extract and manage the infromation from the RXG file.
    '''
    #-----------------------------------------------------------------------------------------------------
    # first line: LO values and ranges, Format: range 4000 4300 or fixed
    # 2nd line: creation date. Format: yyyy mm dd (0 is valid for all for intial set-up)
    # 3rd line: FWHM beamwidthm format. Format: frequency value or constant value
    # 4th line polarizations available: Format lcp rcp
    # 5th line: DPFU (degrees/Jansky) for polarizations in previous line in order. Format: value value
    # 6th line: gain curve (only one) for ALL polarizations in 4th line. Format: ELEV POLY 0.957988140846 0.00234976142727 -3.28545927679e-05
    # 7th and following lines: tcal versus frequency. Format: POL FREQ TCAL
    # 8th line: Trec: receiver temperature. Format: Value value
    # 9th and following lines: Spillover versus frequency Format: Elevation Tspill
    # Ends with: end_spillover_table
    #-----------------------------------------------------------------------------------------------------
    def __init__(self, fileName):
        '''Constructor.
        It opens the file, reads its content and closes it. The content is stored in a private variable
        @param fileName. Name of the RXG file
        '''

        self.rxgname = fileName.split('/')[-1]
        try:
            rxgfIn = open(fileName, 'r')
            self.fileContent = rxgfIn.readlines()
            rxgfIn.close()
        except Exception as ex:
            raise 

    # --------------------------------------------------------------------------------------------
    def getLineFromParamName(self, param, star):
        '''
        Get the parameter we want from the RXG file. It is based in the name of the parameter
        and not in the number of line as the FS usually works. 
        Lines starting with * are considered comments
        @param param Parameter we are looking for
        @star If the param value is in that same line or in another one. 
            True means the parameter is in a line without star that comes later
            False means the parameter is in that same line. 

        Usage example: self.getLineFromParamName('DPFU', True)
        '''

        foundLine = False
        for line in self.fileContent:
            if param in line:
                if not star and param[0] == line[0]:
                    foundLine = True
                    lineWithParam = line
                    break
                if star:
                    foundLine = True
                # if the information is in the next line without a * look for it.
            else:
                if foundLine:
                    if star:
                        if line[0] != '*':
                            lineWithParam = line
                            break
                        else:
                            pass
                    # If the information is in that same line, return. This never should happen
                    else:
                        lineWithParam = line
                        break
                else:
                    pass

        return lineWithParam

    # --------------------------------------------------------------------------------------------
    def getLineFromParam(self, parameter):
        '''
        Get the parameter we want from the RXG file. We know which line to read from the RXG file 
        assuming there is correspondence between the line number and the parameter
        Lines starting with * are skipped during the count since they are considered comments
        TCAL and SPILL are special cases because they have ain unknown number of lines in their section.
        Eevery time we read line from TCAL we have to play with the counter. See the code below.

        @param param Parameter we are looking for.

        Usage example: self.getLineFromParam('DPFU')
        '''

        param = parameter.upper()
        lineParamArray = []

        if param == 'LO':
            lineNumber = 1
        elif param == 'DATE':
            lineNumber = 2
        elif param == 'FWHM':
            lineNumber = 3
        elif param == 'POLS':
            lineNumber = 4
        elif param == 'DPFU':
            lineNumber = 5
        elif param == 'GAIN':
            lineNumber = 6
        elif param == 'TCAL':
            lineNumber = 7
        elif param == 'TREC':
            lineNumber = 8
        elif param == 'SPILL':
            lineNumber = 9
        else:
            # print("Unknown param")
            raise Exception("Unknown param")
            # raise ex


        i = 1
        line7 = False
        line9 = False
        for line in self.fileContent:
            if line[0] == '*':
                # If we find a * after having reached the 7th line that means we have already read
                # all lines in that section => Turn it off and break (get out of the loop)
                if line7:
                    line7 = False
                    break
                if line9:
                    line9 = False
                    break
            else:
                if i == lineNumber:
                    if lineNumber == 7:
                        line7 = True
                        lineParamArray.append( line )
                        i = i - 1
                    elif lineNumber == 9:
                        line9 = True
                        lineParamArray.append( line )
                        i = i - 1
                    else:
                        lineParamArray.append( line )
                        break
                i = i + 1

        return lineParamArray

    # --------------------------------------------------------------------------------------------
    def name(self):
        '''Returns the name of the RXG file without the PATH
        '''
        return self.rxgname

    # --------------------------------------------------------------------------------------------
    def date(self):
        '''Returns the date of creation or last modification of the RXG file
        '''

        dateLine = self.getLineFromParam('Date')[0]
        dateLine = dateLine.strip('\n')

        return dateLine
    # --------------------------------------------------------------------------------------------
    def pols(self):
        '''Returns a list with the available polarizations. For example: ['lcp', 'rcp'] or ['rcp']
        '''

        polsLine = self.getLineFromParam('POLS')[0]
        polsList = polsLine.split()

        return polsList
    # --------------------------------------------------------------------------------------------
    def dpfu(self):
        '''Returns a list with the DPFU. The values are sorted according to the polarization. For example
        [valuercp, valuelcp]. Beware that values are returned as strings not floats !!!
        '''

        dpfuLine = self.getLineFromParam('DPFU')[0]
        dpfuList = dpfuLine.split()

        return dpfuList
    # --------------------------------------------------------------------------------------------
    def gain(self):
        '''Returns a list with the GAIN. 
        '''

        gainLine = self.getLineFromParam('GAIN')[0]
        gainList = gainLine.split()

        return gainList

    # --------------------------------------------------------------------------------------------
    def lo(self):
        '''Returns a list with the local oscillators. 
        The file can have this line:
                range 4000 4300
        or this one:
                fixed 4158
        '''

        loList = []

        loLine = self.getLineFromParam('LO')[0]
        auxList = loLine.split()

        if auxList[0] == 'range':
            loType = 'range'
        elif auxList[0] == 'fixed':
            loType = 'fixed'

        for element in auxList[1:]:
            loList.append(element)

        # We do not use loType. If fixed the array will only contain 1 element if range it will contain 2 elements.

        return loList

    # --------------------------------------------------------------------------------------------
    def trec(self):
        '''Returns the line with the Receiver temperature. It may contain one or two values
        Line looks like: 
            8.0 8.0
        '''

        trecLine = self.getLineFromParam('TREC')[0]
        trecList = trecLine.split()

        return trecList

    # --------------------------------------------------------------------------------------------
    def tcal(self):
        '''Returns an array with the tcal lines 
        Lines look like this:
            lcp 4650.0 1.5
            lcp 4700.0 1.0
            rcp 4650.0 1.5
            rcp 4700.0 1.0
        '''

        tcalArray = []
        tcalArrayLine = self.getLineFromParam('TCAL')

        # The last element contains a string with "end_tcal_table" and we have to drop it out.
        for element in tcalArrayLine:
            if 'end_tcal_table' in element:
                continue
            else:
                tcalArray.append( element.strip('\n') )

        return tcalArray

    # --------------------------------------------------------------------------------------------
    def freqCal(self):
        '''Returns 4 arrays with floats, some of which can be empty or not. The arrays are:
        RCP frequency
        TCAL for RCP
        LCP frequency
        TCAL for LCP
        '''

        freqRCPArray = []
        freqLCPArray = []
        tcalRCPArray = []
        tcalLCPArray = []

        tcArray = self.tcal()

        for element in tcArray:
            listtc = element.split()
            if len(listtc) == 0:
                continue
            elif listtc[0] == 'rcp':
                freqRCPArray.append( float(listtc[1]) )
                tcalRCPArray.append( float(listtc[2]) )
            elif listtc[0] == 'lcp':
                freqLCPArray.append( float(listtc[1]) )
                tcalLCPArray.append( float(listtc[2]) )

        return freqRCPArray, tcalRCPArray, freqLCPArray, tcalLCPArray

    # --------------------------------------------------------------------------------------------
    def freqMinMax(self):
        '''Returns the maximum and minimum frequency covered by TCal array in the RXG file. Units: the same 
        as in the RXG file
        '''

        frA, trA, flA, tlA = self.freqCal()
        freqMax = []
        freqMin = []
        if len(frA) > 0:
            freqMax.append(max(frA))
            freqMin.append(min(frA))
        if len(flA) > 0:
            freqMax.append(max(flA))
            freqMin.append(min(flA))

        # return min(freqMin), max(freqMax)
        return max(freqMin), min(freqMax)

    # --------------------------------------------------------------------------------------------
    def calvsFreq(self, pol):
        ''' Creates and returns an array of pairs of frequency and cal temperature.
        @param pol  Polarization: RCP or LCP
        '''

        frA, trA, flA, tlA = self.freqCal()
        fcArray = []
        if pol.lower() == 'rcp':
            if len(frA) > 0:
                i = 0
                while i < len(frA):
                    fcArray.append([frA[i], trA[i]])
                    i = i + 1
        elif pol.lower() == 'lcp':
            if len(flA) > 0:
                i = 0
                while i < len(flA):
                    fcArray.append([flA[i], tlA[i]])
                    i = i + 1

        return fcArray



    def get_fitTcal(self,pol,**kwargs):
        regressors='poly2'
        if 'regressors' in kwargs.keys():
            regressors=kwargs['regressors']
            
        method='ols'
        if 'rxg_fit_method' in kwargs.keys():
            method=kwargs['rxg_fit_method']
        xy=np.array(self.calvsFreq(pol),dtype=float)
        xoffset=np.mean(xy[:,0])
        x=xy[:,0]-xoffset
        y=xy[:,1]
        if regressors=='poly2':
            X=np.column_stack((x**0,x,x**2))
        elif regressors=='poly4':
            X=np.column_stack((x**0,x,x**2,x**3,x**4))
        elif regressors=='poly8':
            X=np.column_stack((x**0,x,x**2,x**3,x**4,x**5,x**6,x**7,x**8))
        # elif regressors=='arima0_1_2':
        
        if method=='ols':
            model = sm.OLS(y, X)
            res = model.fit().predict()
        elif method=='rlm':
            model = sm.RLM(y, X)
            res = model.fit().predict()
        elif method=='arima':
            model=smtsa.arima.model.ARIMA(y, order=(1, 1, 1))
            res = model.fit().predict()
        elif method=='rolling_avg':
            df=pd.DataFrame(np.vstack((x,y)).T,columns=['x','y'])
            ravg=df.rolling(8,min_periods=1,center=True).mean().to_numpy()
            # ravg=np.vstack(([[x[0],y[0]]],ravg,[[x[-1],y[-1]]]))
            ravg[:,0]+=xoffset
            return ravg
        else:
            res=y
        return np.vstack((x+xoffset,res)).T

class AntabFile():
    def __init__(self):
        '''
        '''
        
    def load(self, fname):
        with open(fname,"r") as F:
            a=F.readlines()
            
        tsys=[]
        r=r"\d"
        for l in a:
            if re.match(r,l[0]):
                # print(l)
                tsys.append(np.array(l.split()[2:],dtype=float))
                
        self.tsys=np.array(tsys)
        # print(tsys)
        return self
    
    def Tsys(self):
        '''
        returns 2d array NxC
        where N is data length, C - number of channels (bbcs)
        '''
        return self.tsys
    
