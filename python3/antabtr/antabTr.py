#!/usr/bin/env python
#-*- coding: utf-8 -*-

#----------------------------------------------------------------------------------------------------------------------------------------------------------
# Alberto Moreno, Pablo de Vicente (Obs. de Yebes) 2015 - 2016
# Francisco Javier Beltran (Obs. de Yebes) 2016 - 2019
# Bartosz Lew (Institute of Astronomy, Nicolaus Copernicus University) modifications of the original code 2021-2022
#
# who      when       what
# --------     ----------     -----------------------------------------------------------------------------------------------------------------------------
# beltran      24/04/2017     - Cal. Temp. is read from RXG files by default. 
#                If "/caltemp/" lines appear in LOG file, the program reads them and overwrites the last Cal. Temp values.
#
# beltran      02/05/2017     - Minimum and maximum frequencies for each setup are calculated as [min(bbcFreq) - bbcBw] and [max(bbcFreq) + bbcBw] respectively.
#                  - Station name is got from LOG file name and is written inside ANTAB file.
#
# beltran      04/05/2017     - DPFU and POLY lines are written in the same line inside ANTAB file.
#                  - DPFU values are separated by commas ("DPFU=0.20.2" -> "DPFU=0.2,0.2")
#                  - Integration time set to 1 second. It means that Tsys is calculated if the time difference between data line
#                read and the following data line is greater than 1 second.
#                If the time difference between two data lines is smaller than 100 ms, the program will assume that these
#                lines are in the same integration period.
#                  - If "/cont_cal=" tag does not found in LOG file, the program will assume that SINGLE calibration mode is used.
#
# beltran      08/06/2017     - Now ANTAB file is saved in the same directory of this script.
#                  - Minor fixes.
#
# beltran      28/06/2017     - Repeated BBCs are removed from self.__bbcinfo.
#                Example: Before -> [['bbc01', '637.49', 'a', '16.00\n'], ['bbc01', '637.49', 'a', '16.00\n'], ['bbc03', '669.49', 'a', '16.00\n'], ['bbc03', '669.49', 'a', '16.00\n'] 
#                     After  -> [['bbc01', '637.49', 'a', '16.00\n'], ['bbc03', '669.49', 'a', '16.00\n']]
#
# beltran      16/10/2017     - X axis shows date and time in the following format: "%d %02d:%05.2f" % (day,hour,minute) -> Example: "100 09:01.03", "200 18:30.10"
#                  - Minor fixes.
#
# beltran      24/10/2017     - The program will use the correct sidebands (LSB and USB) corresponding to each format (line: "/form=...")
#
# beltran      30/10/2017     - The program will read "/fila10g_mode=" and "_mode=" lines and will write Tsys only for the specified BBCs.
#
# beltran      03/01/2018     - The program will ignore empty lines.
#
# beltran      10/12/2018     - The program will read the side band used for each LO from lines "lo=loa,42500.00,lsb/usb,rcp,1.000"
#                If it uses LSB, each BBC frequency will be calculated as: LO_freq - BBC_freq +- BBC_BW
#                If it uses USB, each BBC frequency will be calculated as: LO_freq + BBC_freq +- BBC_BW
#                Now the program works when the setups have a different number of channels.
#                  - Minor fixes
#
# beltran      04/03/2019     - Now, the colunms are sorted by frequency in each polarization.
#
# beltran      23/04/2019     - Now the program checks the "ifdXX" of each setup in order to know what is the proper IF configuration for each setup.
#                  - Minor fixes.
#
# beltran &    09/06/2020     - Now the program checks the station name from the LOG file and reads only the RXG file corresponding to that station.
# gonzalez            - Added flags ";setup" and "/setup" to get the current setup.
#                  - Minor fixes.
# gonzalez     11/08/2020     - Changed datetime.fromtimestamp() to datetime.utcfromtimestamp() to keep UTC independently of user's timezone.
# marcote      14/09/2020     - Removes a trailing comma in poly avoiding the case of e.g. POLY=1.0, /
# gonzalez     23/11/2020     - Added "form=wastro" support. Thanks to Jun Yang (Onsala) for reporting.
#----------------------------------------------------------------------------------------------------------------------------------------------------------

import collections

try:
    collectionsAbc=collections.abc
except AttributeError:
    collections.abc = collections

import sys
import os
from copy import copy
import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import statsmodels.api as smapi
from statsmodels.sandbox.regression.predstd import wls_prediction_std
import itertools
from time import sleep
import argparse
import math
import struct
import pydoc
import pickle
from antabtr import config_file, wisdom, antabTr_parser,common,vis
from scipy.special import erfinv

station = ""
# rxgfiles = ""

version=20201123
# print('tassili_version={}'.format(version))

debug = False

###______________________________________________________________###

###______________________________________________________________###
class antabHeader:

    '''Class to create the header of an antab file
    '''
    """
    def __init__(self, logFileName):
        '''Constructor which uses the log file name and creates some private variables:
        self.logF, self.expName, self.stationName, self.rxgDirectory
        '''

        self.logF = logFile(logFileName)
        self.expName = self.logF.experiment()
        self.stationName = self.logF.station()
        self.rxgDirectory = "/usr2/control/rxg_files"

    # --------------------------------------------------------------------------------------------
    """
    def __init__(self, logFileObject, cfg=None): # FJB
        '''Constructor which uses the log file object to create some private variables:
        self.logF, self.expName, self.stationName, self.rxgDirectory
        '''

        self.logF = logFileObject
        self.expName = self.logF.experiment()
        self.stationName = self.logF.station()
        self.cfg=cfg
        self.rxgDirectory=cfg['CALIB']['rxgDir']

        # self.rxgDirectory = "/home/blew/programy/antab/data/rxg_files"
        #self.rxgDirectory = "/usr2/oper/antabfs_pruebas/rxg_files"

    def rxgLines(self):
        '''Creates a line with information from the RXG file. This line will be included in the antab header
        '''

        linerxg = []
        fLOArray, polArray = self.logF.loPArray()
        
        for setup in reversed(list(fLOArray.keys())):
            i = 0
            for fLO in fLOArray[setup]:
                rxgFileName = self.logF.getRXGFileName(fLO)
                print(rxgFileName)
                rxgF = common.rxgFile(rxgFileName)

                linerxg.append(    "%.2f MHz %s: %s %s" % (fLO, polArray[setup][i], rxgF.name(), rxgF.date()) )
                i += 1

        return linerxg

    # --------------------------------------------------------------------------------------------
    def dpfuLines(self):
        '''Return the fixed LO frequency. It looks for the accurrence of DPFU in the RXG file.
        If we decide to use the othe policy, base din the number of line DPFU is
        Beware that the maximum frequency is LOMax + BW self.__bw[i]
        @param RXG file name
        @return  a line of the type: POLY=A,B,C,D (where A, B,C,D are coefficients of a polynomium)
        '''
    
        dpfuLineArray = dict()
        rxgFilesArray = self.logF.rxgFiles()
        logData = self.logF.getLogData()
        header = logData[0]
        #index = 0

        for setup in reversed(list(rxgFilesArray.keys())):    
            dpfuLineArray[setup] = []
            for rxgFileName in sorted(set(rxgFilesArray[setup])):
                strLine = ""
                if rxgFileName == " ":
                    continue
                rFile = common.rxgFile(rxgFileName)    
                dpfuList = rFile.dpfu()
                freqMin, freqMax = rFile.freqMinMax()
                #bw = self.logF.bandwidth()
    
                strLine = 'GAIN %s ELEV DPFU=' % (self.stationName)
    
                i = 0
                for element in dpfuList:
                    if i == 0:
                        strLine = "%s%s" % (strLine,element)
                    else:
                        strLine = "%s,%s" % (strLine,element)
                    i = i + 1

                for line in header:
                    hLines_aux = line.split('\n')
                    if setup in hLines_aux[1]:
                        break

                hLines = hLines_aux[4:]
                #hLines = header[index].split('\n')[4:]
                ifFreq = []
                ifBw = []
                for line in hLines:
                    auxStr = line.split()
                    freqAux = float(auxStr[6])
                    #if int(freqAux) >= freqMin and int(freqAux) <= freqMax:
                    if freqAux >= (freqMin-float(auxStr[11])) and freqAux <= (freqMax+float(auxStr[11])):
                        ifFreq.append(freqAux)    
                        ifBw.append(float(auxStr[11]))
        
                if len(ifFreq) == 0:
                    ifFreq = [freqMin,freqMax]
                    ifBw = [0,0]
    
                strLine = "%s FREQ=%.2f,%.2f" % (strLine, min(ifFreq) - ifBw[ifFreq.index(min(ifFreq))], max(ifFreq) + ifBw[ifFreq.index(max(ifFreq))])
                #strLine = "%s      FREQ=%d,%d" % (strLine, int( float(freqMin)), int(float(freqMax)+bw) )
                #strLine = "%s      FREQ=%d,%d" % (strLine, int( float(freqMin)), int(float(freqMax)) )

                dpfuLineArray[setup].append(strLine)
    
            #index += 1

        return dpfuLineArray

    # --------------------------------------------------------------------------------------------
    def polyelevLine(self):
        '''Return the fixed LO frequency
        @param RXG file name
        @return  a line of the type: POLY=A,B,C,D (where A, B,C,D are coefficients of a polinomium)
        '''

        polyLineArray = dict()
        rxgFilesArray = self.logF.rxgFiles()

        for setup in reversed(list(rxgFilesArray.keys())):
            polyLineArray[setup] = []
            for rxgFileName in sorted(set(rxgFilesArray[setup])):
                strLine = ""
                if rxgFileName == " ":
                    continue
                rFile = common.rxgFile(rxgFileName)
                gainList = rFile.gain()
    
                strLine = 'POLY='
                i = 0
                for element in gainList[2:]:
                    if i == 0:
                        strLine = "%s%s" % (strLine,element)
                    else:
                        strLine = "%s,%s" % (strLine,element)
                    i = i + 1
                if strLine.strip()[-1] == ',':
                    strLine = strLine.strip()[:-1]
                strLine += ' /\n'
                polyLineArray[setup].append(strLine)
    
        #strLine = "/"
        #polyLineArray.append(strLine)
    
        return polyLineArray

    # --------------------------------------------------------------------------------------------
    def loLines(self):
        '''Returns a line with LO information. It is similar to method rxgLines()
        '''
        loLines = []

        fLOMHzArray, polArray = self.logF.loPArray()

        setups = list(fLOMHzArray.keys())
        setups.sort()

        for setup in setups:
            i = 0
            lstr = '!   Setup %s' % setup
            loLines.append(lstr)
            loLinesList = []
            freqList = []
            for lof in fLOMHzArray[setup]:
                rxgFileName = self.logF.getRXGFileName(lof)
                if rxgFileName == " ":
                    lstr = '!     LO=%.2f MHz %s' % (lof, polArray[setup][i])
                    loLinesList.append(lstr)    
                    freqList.append(lof)
                else:
                    rFile = common.rxgFile(rxgFileName)
                    lstr = '!     LO=%.2f MHz %s %s %s' % (lof, polArray[setup][i], rFile.name(), rFile.date())
                    loLinesList.append(lstr)
                    freqList.append(lof)
                i = i + 1

            newLoLines = [x for _,x in sorted(zip(freqList,loLinesList))]
            loLines += newLoLines
        #line.append('!     LO= %.2f MHz rcp: calYsM.rxg 2012 11 06\n' % (freqLOMHz, rxgFileName, date))
        #line.append('!     LO= %.2f MHz lcp: calYsM.rxg 2012 11 06\n' % (freqLOMHz, rxgFileName, date))
        
        return loLines    

    # --------------------------------------------------------------------------------------------
    def firstLines(self):
        '''Write the first lines in the antab file with comments
        '''

        todayDate = datetime.datetime.now().strftime("%Y-%m-%d")

        waveBandArray = self.waveBands()
        waveBand = ""
        for wv in waveBandArray:
            waveBand = "%s %scm" % (waveBand, wv)
        waveBand = "%s." % waveBand 

        #fLOMHzArray = self.logF.loArray()

        dbbcMode = self.logF.dbbcMode()
        #calMode = self.logF.calMode()
    
        line = []
        line.append('! Amplitude calibration data for %s in %s.' % (self.stationName, self.expName))
        line.append('! For use with AIPS task ANTAB.')
        line.append('! Waveband(s) = %s' % (waveBand))
        line.append('! RXG files used for each LO:')
        for l in self.loLines():
            line.append(l)

        line.append('! DBBC used in mode %s' % dbbcMode)
        #line.append('! Calibration mode: %s' % calMode)

        version = "2019-10-11"

        line.append('! Produced on %s using antabfs.py version: %s' % (todayDate, version))

        return line

    #---------------------------------------------------------------------------------------------
    def writeAntabPreamble(self, antabFile):
        '''Write the complete antab file header
        '''

        fOut = open(antabFile,'w')

        lines = self.firstLines()
        for l in lines:
            fOut.write(l+'\n')

        fOut.close()
        return [self.dpfuLines(), self.polyelevLine()]

    #---------------------------------------------------------------------------------------------
    def waveBands(self):
        '''Return an array with the name of the band using the LO values
        '''

        fLOMHzArray = self.logF.loArray()
        wavebandArray = []

        for setup in reversed(list(fLOMHzArray.keys())):
            for freqLO in fLOMHzArray[setup]:
                """
                if freqLO > 1500 and freqLO < 2400:
                    wavebandArray.append('13.6cm')
                elif freqLO > 4000 and freqLO < 4900:
                    wavebandArray.append('6cm')
                elif freqLO > 5000 and freqLO < 6600:
                    wavebandArray.append('5cm')
                elif freqLO > 7500 and freqLO < 9000:
                    wavebandArray.append('3.6cm')
                elif freqLO > 20000 and freqLO < 27000:
                    wavebandArray.append('1.3cm')
                elif freqLO > 40000 and freqLO < 50000:
                    wavebandArray.append('0.7cm')
                """
                wavebandArray.append('%.1f' % (3e8/(freqLO*1e4)))

        wavebandArray = sorted(set(wavebandArray), key=float, reverse=True)

        return wavebandArray
    
#--------- Alberto Moreno section --------------------------------------------------------------------
class Selection(object):    #clase para la selecci??n manual de los datos

    def __init__(self,x,y,block,title,**kwargs):
        sec_loc = mdates.SecondLocator()
        self.x=np.array(x);self.y=np.array(y);self.block=block;self.title=title
        self.xrectangle=[];self.yrectangle=[]
        self.delIndX=[]
        # self.wisdom={}
        self.wisdom={'x0' : x, 'y0': y, 'x': [], 'y':[], 'ridx' : [], 'X' : y, 'Y' : y}
        # self.BLwisdom_x0=x
        # self.BLwisdom_y0=y
        # self.BLwisdom_x=[]
        # self.BLwisdom_y=[]
        # self.BLwisdom_removed_idx=[]
        self.press = False
        #self.tolerance=0.05
        self.tolerance=0.1
        
        self.experimentName=''
        if 'experimentName' in kwargs.keys():
            self.experimentName=kwargs['experimentName']
        if 'alpha' in kwargs.keys():
            self.tolerance=kwargs['alpha']
            
        
        self.clean_type='ols'
        if 'clean_type' in kwargs.keys():
            self.clean_type=kwargs['clean_type']
        
        
        self.verbose=0
        if 'verbose' in kwargs.keys():
            self.verbose=kwargs['verbose']
        
        if self.clean_type=='ols':
            self.fig = plt.figure(figsize=(13,8))
            self.ax = self.fig.add_subplot(111)
            self.ax.set_title('Tsys %s'%self.title)
            self.ax.set_xlabel('Time')
            self.ax.set_ylabel('Tsys [K]')
            self.ax.grid()
         # plt.margins(0.2)
            
            self.timeInit = self.x[0]
            new_x = []
            new_y = []
            new_block = []
            for i in range(0,len(self.x)):
                auxVal = (self.x[i] - self.timeInit) * (24.*60.)
                if auxVal >= 0:
                    new_x.append(auxVal)
                    new_y.append(self.y[i])
                    new_block.append(self.block[i])
                else:
                    self.delIndX.append(i)
    
            self.x = np.array(new_x)
            self.y = np.array(new_y)
            self.block = np.array(new_block)
    
            self.fit,self.low,self.up,self.inx,self.iny,self.outx,self.outy,ridx=outliers(self.block,self.x,self.y,self.tolerance)
        
            self.ax.plot(self.x,self.fit,'b-',label='fit')
            self.ax.plot(self.x,self.low,'k--',label='lower/upper')
            self.ax.plot(self.x,self.up,'k--')
            self.ax.plot(self.outx,self.outy,'ro',label='outliers')
            self.ax.plot(self.inx,self.iny,'g*',label='data')
            self.ax.legend(loc='best')
            #defining the limits of the plot
            #self.xmin,self.xmax=plt.xlim()        
            self.xmin = min(self.x)
            self.xmax = max(self.x)        
            self.ymin,self.ymax=plt.ylim()
            xdiff = self.xmax - self.xmin
            self.xmin=self.xmin-(xdiff*0.05)
            self.xmax=self.xmax+(xdiff*0.05)
            self.ymin=self.ymin-(self.ymax-self.ymin)*0.01
            self.ymax=self.ymax+(self.ymax-self.ymin)*0.01
            plt.xlim((self.xmin,self.xmax))
            plt.ylim((self.ymin,self.ymax))
            self.ax.figure.canvas.mpl_connect('button_press_event', self.on_press)
            self.ax.figure.canvas.mpl_connect('button_release_event', self.on_release)
            self.ax.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)
            self.fig.canvas.draw()
            self.labels = []
            for item in self.ax.get_xticklabels():
                text = item.get_text()
                if text != '':
                    text = text.replace('\u2212','')
                    value = (int(float(text))/(24.*60.)) + self.timeInit
                    day = int(value)
                    hour = int((value - day)*24)
                    minute = (value - day - (hour/24.))*24*60
                    text = '%d %02d:%05.2f' % (day,hour,minute)
                self.labels.append(text)
            self.ax.set_xticklabels(self.labels)
            plt.show()

        else:
            # binN=[1,20,30,40,50,100,200]
            # binEq=[False,True2,4,10,20,40,100]
            binN=[1]
            bf_idx=0
            chisq=[]
            res_all=[]
            for i,b in enumerate(binN):
                make_equal=True
                # if i==0:
                make_equal=False
                
                if self.verbose>2:
                    print('bin {}, make_equal: {}'.format(b,make_equal))
                segments=bin_segments(self.block, binN=b, make_equal=make_equal)
                counts=np.array([ len(segments[segments==x]) for x in set(segments) ])
                segment_sigma=np.array([ np.std(self.y[segments==x]) for x in set(segments) ])
                # print('segment_sigma',segment_sigma)
                segment_sigma=np.median(segment_sigma)
                if 'all_scans_noise_estimate' in kwargs.keys():
                    if kwargs['all_scans_noise_estimate']=='median':
                        segment_sigma=np.median(segment_sigma)
                    elif kwargs['all_scans_noise_estimate']=='mean':
                        segment_sigma=np.mean(segment_sigma)
                    else:
                        print('ERROR: incorrect all_scans_noise_estimate parameter value')
                        print("Will use value: ",segment_sigma)
                        
                res=outliers(segments,self.x,self.y,self.tolerance,method=self.clean_type, verbose=self.verbose,sigma=segment_sigma)
                # res=outliers(segments,self.x,self.y,self.tolerance,method=self.clean_type, verbose=self.verbose,sigma=np.mean(segment_sigma))
                self.fit,self.low,self.up,self.inx,self.iny,self.outx,self.outy,ridx=res
                res_all.append(res)
                median_segment_size=np.median(counts)
                x2=np.mean((self.fit-self.y)**2)/median_segment_size
                if self.verbose>0:
                    print('x2: {}, median_segment_size: {}'.format(x2,median_segment_size))
                    print('np.median(segment_sigma): ',np.median(segment_sigma))
                    print('np.mean(segment_sigma): ',np.mean(segment_sigma))
                chisq.append(x2)

                if self.verbose>2:
                    fig=plt.figure(figsize=(14,10))
                    plt.plot(self.inx,self.iny,'k.')
                    plt.plot(self.x,self.fit,'b-',marker='.')
                    plt.plot(self.outx,self.outy,'r.')
                    plt.plot(self.x,self.low,'k--')
                    plt.plot(self.x,self.up,'k--')
                    plt.title('method: {}, x2: {}, median_segment_size: {}'.format(
                        self.clean_type, x2, median_segment_size))
                # plt.plot(self.x,self.low,'k-')
                # plt.plot(self.x,self.up,'k-')
                    plt.show()
            bf_idx=np.argmin(np.array(chisq))
            self.fit,self.low,self.up,self.inx,self.iny,self.outx,self.outy,ridx=res_all[bf_idx]

            if self.verbose>0:
                fig=plt.figure(figsize=(14,10))
                plt.plot(self.inx,self.iny,'g.')
                plt.plot(self.x,self.fit,'b-',marker='.')
                plt.plot(self.outx,self.outy,'r.')
                plt.plot(self.x,self.low,'b--')
                plt.plot(self.x,self.up,'b--')
                plt.title('{}, {} (best idx.{:d})'.format(self.experimentName,self.title,bf_idx))
                plt.show()

            # self.x=self.inx
            # self.y=self.iny
            
            # print(ridx)
            y=self.y
            ridx=np.array(ridx,dtype=int)
            # print(y[ridx])
            y[ridx]=np.array(self.fit)[ridx]
            self.wisdom['ridx'].extend(ridx)
            self.wisdom['x']=self.x
            self.wisdom['y']=y
            self.wisdom['Y']=y
            

    def getDeletedX(self):
        return self.delIndX

    def on_press(self, event):
        if event.inaxes != None:
            self.rect = Rectangle((0,0), 0, 0, linestyle='dashed', facecolor="#dddddd")
            self.ax.add_patch(self.rect)
            self.x0 = event.xdata
            self.y0 = event.ydata
            self.press=True
        else:
            self.press=False
        
    def on_motion(self, event):
        #if event.inaxes != self.rect.axes: return
        if self.press and event.inaxes != None:
            self.dx=event.xdata
            self.dy=event.ydata
            self.rect.set_width(self.dx - self.x0)
            self.rect.set_height(self.dy - self.y0)
            self.rect.set_xy((self.x0, self.y0))
            self.rect.figure.canvas.draw()
    
    def on_release(self, event):
        if self.press:
            if event.inaxes == None:
                self.xf = self.dx
                self.yf = self.dy
            else:
                self.xf = event.xdata
                self.yf = event.ydata
            self.xmin=min(self.x0,self.xf)
            self.xmax=max(self.x0,self.xf)
            self.ymin=min(self.y0,self.yf)
            self.ymax=max(self.y0,self.yf)
            self.xrectangle.append([self.xmin,self.xmax])
            self.yrectangle.append([self.ymin,self.ymax])
            
            #elimina puntos en el rectangulo y recalcula el ajuste
            '''
            self.cond=(self.x<self.xmin)+(self.x>self.xmax)+(self.y<self.ymin)+(self.y>self.ymax)
            self.x=np.extract(self.cond,self.x)
            self.y=np.extract(self.cond,self.y)
            self.block=np.extract(self.cond,self.block)
            '''
            self.y,rem_idcs=modifydata(self.x,self.y,self.block,self.xmax,self.xmin,self.ymax,self.ymin)
            self.wisdom['ridx'].extend(rem_idcs)
            self.wisdom['x']=self.x
            self.wisdom['y']=self.y
            self.wisdom['Y']=self.y
            removed_idx=self.y==1
            self.fit,self.low,self.up,self.inx,self.iny,self.outx,self.outy,ridx=outliers(self.block,self.x,self.y,self.tolerance)
            
            #sustituir puntos malos por media geometrica o moda
            
            self.ax.cla()
            self.ax.set_title('Tsys %s'%self.title)
            self.ax.set_xlabel('Time')
            self.ax.set_ylabel('Tsys [K]')
            self.ax.autoscale(True,'both',False)
            self.ax.grid()
            self.ax.plot(self.x,self.fit,'b-',label='fit')
            self.ax.plot(self.x,self.low,'k--',label='lower/upper')
            self.ax.plot(self.x,self.up,'k--')
            self.ax.plot(self.outx,self.outy,'ro',label='outliers')
            self.ax.plot(self.inx,self.iny,'g*',label='data')
            self.ax.legend(loc='best')
            
            #self.xmin,self.xmax=plt.xlim()
            self.xmin = min(self.x)
            self.xmax = max(self.x)
            self.ymin,self.ymax=plt.ylim()
            xdiff = self.xmax-self.xmin
            self.xmin=self.xmin-(xdiff*0.05)
            self.xmax=self.xmax+(xdiff*0.05)
            self.ymin=self.ymin-(self.ymax-self.ymin)*0.01
            self.ymax=self.ymax+(self.ymax-self.ymin)*0.01
            plt.xlim((self.xmin,self.xmax))
            plt.ylim((self.ymin,self.ymax))

            self.ax.set_xticklabels(self.labels)

            plt.show()
            self.press=False
#-----------------------------------------------------------------------------------------------------
def modifydata(x,y,block,xmax,xmin,ymax,ymin):
    cond=(x<xmin)+(x>xmax)+(y<ymin)+(y>ymax)+(y<0)
    removed_idcs=np.arange(len(y))[np.logical_not(cond)]
#     print(idcs,len(idcs))
    for i in range(0,len(cond)):
        if cond[i]==False:
            bcond=(np.array(block)==block[i])*cond
            templist=np.extract(bcond,y)
            icount=i
            while len(templist)==0:
                bcond=(np.array(block)==block[icount])*cond
                templist=np.extract(bcond,y)
                icount=icount+1
                if (icount-i)>20:
                    #templist=[50]
                    templist=np.extract(cond,y)    #if nothing good, compute mean of all data, another alternative is delete the whole line but is more difficult to implement and you lose data in all bbc
                    break
            temp=1
            for j in templist:
                temp=temp*j**(1/float(len(templist)))
            y[i]=temp
    return y,removed_idcs
#-----------------------------------------------------------------------------------------------------
def linregfit(x,y,method='gls', alpha=0.05, verbose=0,sigma=None):
    '''
    '''
    nsample = len(x)
    pred=np.array([])
    low=np.array([])
    high=np.array([])

    if nsample==1:
        return y,y,y
    
    if nsample>1:
        # X = np.column_stack((x, x**2,np.ones(nsample)))
        X = np.column_stack((x, np.ones(nsample)))

        if method=='gls':
            res = smapi.OLS(y, X).fit()
            pred_ols = res.get_prediction()
            iv_l = pred_ols.summary_frame(alpha=alpha)["obs_ci_lower"]
            iv_u = pred_ols.summary_frame(alpha=alpha)["obs_ci_upper"]
        elif method=='rlm':
            res = smapi.RLM(y, X).fit()
            if sigma:
                sigma_loc=sigma
            else:
                sigma_loc=np.sqrt(np.mean((res.fittedvalues-y)**2))
            # sigma=res.bse[-1]
            nsigma=erfinv(1.-alpha)*math.sqrt(2)
            iv_l=res.fittedvalues-sigma_loc*nsigma
            iv_u=res.fittedvalues+sigma_loc*nsigma
        
        if verbose>3:
            print("alpha: ",alpha)
            print("Parameters: ", res.params)
            print("Standard errors: ", res.bse)
            print("Predicted values: ", res.predict())
        
        
        pred=res.fittedvalues
        low=iv_l
        high=iv_u
    
    return pred,low,high
        


def smfit(x,y):        #fit data, lower and upper limits
    if len(x)>1:                        #it would be convenient to rewrite this without statsmodels, using pyplot and a exp func
        x=np.array(x)
        y=np.array(y)
        # plt.plot(x,y)
        # plt.title('%i'%len(x))
        # plt.show()
        X=np.column_stack((x,np.ones(len(x))))
        res = smapi.OLS(y,X).fit()
        prstd, low, up = wls_prediction_std(res)
        fit=res.fittedvalues
        return  res.fittedvalues,low,up
    elif len(x)==1:
        nodata=np.array([y,y-0.1*y,y+0.1*y])
        return nodata
    else:
        nodata=np.array([[],[],[]])
        return nodata
#-----------------------------------------------------------------------------------------------------
def finalplot(x,y,bbclist,partNum, experimentName=''):    #plot all procesed data
    style=['bo','go','ro','co','mo','yo','ko','wo','b*','g*','r*','c*','m*','y*','k*','w*','b^','g^','r^','c^','m^','y^','k^','w^','bs','gs','rs','cs','ms','ys','ks','ws']
    fig = plt.figure(figsize=(16,11))
    ax = fig.add_subplot(111)
    ax.set_facecolor('grey')
    plt.title(experimentName)
    plt.suptitle('All BBCs, Part %d' % (partNum+1))
    plt.xlabel('Time')
    plt.ylabel('Tsys [K]')
    plt.grid()
    for i in range(0,len(y)):
        plt.plot(x,y[i],style[i],label='%s'%bbclist[i],ms=2)
    plt.legend(loc='best')
    xmin = min(x)
    xmax = max(x)
    xdiff = xmax - xmin
    xmin -= xdiff*0.01
    xmax += xdiff*0.01
    plt.xlim((xmin,xmax))
    fig.canvas.draw()
    labels = []
    for item in ax.get_xticklabels():
        text = item.get_text()
        if text != '':
            value = float(text)
            day = int(value)
            hour = int((value - day)*24)
            minute = (value - day - (hour/24.))*24*60
            text = '%d %02d:%05.2f' % (day,hour,minute)
        labels.append(text)
    ax.set_xticklabels(labels)
    plt.show()
#-----------------------------------------------------------------------------------------------------
def outliers(block,x,y,tolerance,method='ols', **kwargs):
    fit=[];low=[];up=[]
    idx=np.arange(len(x))
    # plt.plot(block)
    # plt.show()

    verbose=0
    if 'verbose' in kwargs.keys():
        verbose=kwargs['verbose']

    sigma=None
    if 'sigma' in kwargs.keys():
        sigma=kwargs['sigma']

    if method=='ols':
    
        for j in range(min(block),max(block)+1):                #fit data in diferent parts
            #no hay que quitar los outliers sino darles el valor del fit o de la moda
            # print(block.shape)
            # print(len(set(block)))
            cond=np.array(block)==j
            xblock=np.extract(cond,x)
            yblock=np.extract(cond,y)
            fitblock,lowblock,upblock=smfit(xblock,yblock)    #statsmodels to compute the fit and limits
            fit=fit+fitblock.tolist()
            low=low+lowblock.tolist()
            up=up+upblock.tolist()
        low=np.array(fit)-np.array(fit)*tolerance        #sometimes statsmodels doesn't return the correct lower and upper limits
        up=np.array(fit)+np.array(fit)*tolerance
    else:
        for j in range(min(block),max(block)+1):                #fit data in diferent parts
            cond=np.array(block)==j
            xblock=np.extract(cond,x)
            yblock=np.extract(cond,y)
            fitblock,lowblock,upblock=linregfit(xblock, yblock, method=method, alpha=tolerance, verbose=verbose, sigma=sigma)
            fit=fit+fitblock.tolist()
            low=low+lowblock.tolist()
            up=up+upblock.tolist()
    
    incond=(np.array(y)<=np.array(up))*(np.array(y)>=np.array(low))
    inx=np.extract(incond,x)
    iny=np.extract(incond,y)
    outcond=(np.array(y)>np.array(up))+(np.array(y)<np.array(low))
    outx=np.extract(outcond,x)
    outy=np.extract(outcond,y)
    ridx=np.extract(outcond,idx)
    return fit,low,up,inx,iny,outx,outy,ridx

def bin_segments(block, binN=1, make_equal=False):
    '''
    block - 1-d array of entire data length, containing increasing integers that map
    source observations history e.g.
    
                                .
                                .
                                .
                   2-----------
         1----------
    0----
    
    The length of each segment can be different and proportional to time spend on given source.
    This map can be used to select sub-set of data for eg. OLS outliers detection
    
    This function can combine segments in order to increase their length:
    Eg.
    
                                .    
                                .    
                                .    
                   1------------
    0---------------
    
    
    binN - defines how many neighbouring blocks will be combined
    '''

    if make_equal:
        block=np.arange(len(block))

    new_map=np.array(np.round(np.array(block,dtype=float)/binN),dtype=int)

    return new_map
#-----------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------
def write_antab(fileOut,header,indexline,scanline,tsysline,block,time, tsyslog, setupTime, dpfuLines, polyelevLine, stationName):
    '''Write the content of the antab file except the header
    '''

    f = open(fileOut,'a')
    """
    for i in range(len(dpfuLines[0])):
        f.write(dpfuLines[0][i] + ' ' + polyelevLine[0][i])
    f.write('/\n')
    #f.write(polyelevLine[0] + '\n/\n')
    f.write('TSYS %s FT = 1.0 TIMEOFF=0\n' % stationName)
    #f.write(indexline[0:-1]+'\n')
    f.write(indexline[0][0:-1]+'\n')
    f.write('/\n')
    for line in header[0]:
        f.write(line)

    dpfuLines_aux = []
    for setupList in setupTime:
        if setupList[1] in dpfuLines_aux:
            pass
        else:
            dpfuLines_aux.append(setupList[1]) 
    """

    tsyslogNLine = 0
    setupTime_ind = 0
    time_tsyslog = tsyslog[0][0]
    for i in range(0,len(block)):
        if setupTime_ind < len(setupTime):
            setup = setupTime[setupTime_ind][1]
            if setupTime[setupTime_ind][0] <= time[i]:
                for ind in range(len(dpfuLines[setup])):
                    if setupTime_ind > 0:
                        f.write('\n/\n')
                    #f.write(dpfuLines[dpfuLines_aux.index(setup)][ind] + ' ' + polyelevLine[dpfuLines_aux.index(setup)][ind])
                    f.write(dpfuLines[setup][ind] + ' ' + polyelevLine[setup][ind])
                f.write('/\n')
                f.write('TSYS %s FT = 1.0 TIMEOFF=0\n' % stationName)
                f.write(indexline[setupTime_ind][0:-1]+'\n')
                f.write('/\n')
            
                for line in header[setupTime_ind]:
                    f.write(line)
                setupTime_ind += 1
        if i == 0:
            for j in scanline:
                strAux = j.split('=')[1].split(' ')[0]
                if int(strAux) == block[i]:
                    dayAux = j.split(": scanNum")[0].split(" ")
                    scanTime = int(dayAux[1]) + (int(dayAux[2].split(":")[0])/24.) + (float(dayAux[2].split(":")[1])/(24.*60.))
                    if tsyslogNLine < len(tsyslog):
                        dt = datetime.datetime.utcfromtimestamp(time_tsyslog)
                        d=dt.timetuple().tm_yday
                        h=dt.hour
                        m=dt.minute + (dt.second/60.0) + dt.microsecond/(1e6*60.0)
                        dtTsysLog = d+h/24.+m/(24.*60.)
                        while dtTsysLog <= scanTime:
                            strLine = '\n! %03d %02d:%05.2f'%(d,h,m)
                            for j_tsys in range(1,len(tsyslog[tsyslogNLine])):
                                try:
                                    int(tsysline[i][j_tsys-1])
                                except:
                                    continue
                                strLine=strLine+' %.1f' % tsyslog[tsyslogNLine][j_tsys]
                            tsyslogNLine += 1
                            if tsyslogNLine < len(tsyslog):
                                time_tsyslog = tsyslog[tsyslogNLine][0]
                                dt = datetime.datetime.utcfromtimestamp(time_tsyslog)
                                d=dt.timetuple().tm_yday
                                h=dt.hour
                                m=dt.minute + (dt.second/60.0) + dt.microsecond/(1e6*60.0)
                                dtTsysLog = d+h/24.+m/(24.*60.)
                            else:
                                break
                            f.write(strLine)
                                
                    f.write(j)
                    break
        else:
            if block[i]!=block[i-1]:
                for j in scanline:
                    strAux = j.split('=')[1].split(' ')[0]
                    if int(strAux) == block[i]:
                        dayAux = j.split(": scanNum")[0].split(" ")
                        scanTime = int(dayAux[1]) + (int(dayAux[2].split(":")[0])/24.) + (float(dayAux[2].split(":")[1])/(24.*60.))
                        if tsyslogNLine < len(tsyslog):
                            dt = datetime.datetime.utcfromtimestamp(time_tsyslog)
                            d=dt.timetuple().tm_yday
                            h=dt.hour
                            m=dt.minute + (dt.second/60.0) + dt.microsecond/(1e6*60.0)
                            dtTsysLog = d+h/24.+m/(24.*60.)
                            while dtTsysLog <= scanTime:
                                strLine = '\n! %03d %02d:%05.2f'%(d,h,m)
                                for j_tsys in range(1,len(tsyslog[tsyslogNLine])):
                                    try:
                                        int(tsysline[i][j_tsys-1])
                                    except:
                                        continue
                                    strLine=strLine+' %.1f' % tsyslog[tsyslogNLine][j_tsys]
                                tsyslogNLine += 1
                                if tsyslogNLine < len(tsyslog):
                                    time_tsyslog = tsyslog[tsyslogNLine][0]
                                    dt = datetime.datetime.utcfromtimestamp(time_tsyslog)
                                    d=dt.timetuple().tm_yday
                                    h=dt.hour
                                    m=dt.minute + (dt.second/60.0) + dt.microsecond/(1e6*60.0)
                                    dtTsysLog = d+h/24.+m/(24.*60.)
                                else:
                                    break
                                f.write(strLine)
                                    
                        f.write(j)
                        break

        if tsyslogNLine < len(tsyslog):
            while time_tsyslog <= time[i]:
                dt = datetime.datetime.utcfromtimestamp(time_tsyslog)
                d=dt.timetuple().tm_yday
                h=dt.hour
                m=dt.minute + dt.second/60.0 + dt.microsecond/(1e6*60.0)
                strLine = '\n! %03d %02d:%05.2f'%(d,h,m)
                for j in range(1,len(tsyslog[tsyslogNLine])):
                    try:
                        int(tsysline[i][j-1])
                    except:
                        continue
                    strLine=strLine+' %.1f' % tsyslog[tsyslogNLine][j]
                tsyslogNLine += 1
                if tsyslogNLine < len(tsyslog):
                    time_tsyslog = tsyslog[tsyslogNLine][0]
                else:
                    break
                f.write(strLine)

        dt = datetime.datetime.utcfromtimestamp(time[i])
        d=dt.timetuple().tm_yday
        h=dt.hour
        m=dt.minute + (dt.second/60.0) + dt.microsecond/(1e6*60.0)
        #h_float, d= math.modf(time[i])
        #h_float *= 24.0
        #m, h = math.modf(h_float)
        #m *= 60.
        #m=int((time[i]-(d + (h/24.)))*(60*24))
        #s=int((time[i]-(d + (h/24.) + (m/(60.*24.))))*(3600*24))
        #us=int((time[i]-(d + (h/24.) + (m/(60.*24.)) + (s/(3600.*24.)))) * (3600*24*1e2))
    
        strline='\n%03.0f %02.0f:%05.2f'%(d,h,m)
        for j in tsysline[i]:
            try:
                int(j)
            except:
                continue
            strline=strline+' %.1f'%j
        f.write(strline)

    while tsyslogNLine < len(tsyslog):
        dt = datetime.datetime.utcfromtimestamp(time_tsyslog)
        d=dt.timetuple().tm_yday
        h=dt.hour
        m=dt.minute + dt.second/60.0 + dt.microsecond/(1e6*60.0)
        strLine = '\n! %03d %02d:%05.2f'%(d,h,m)
        for j in range(1,len(tsyslog[tsyslogNLine])):
            strLine=strLine+' %.1f' % tsyslog[tsyslogNLine][j]
        tsyslogNLine += 1
        if tsyslogNLine < len(tsyslog):
            time_tsyslog = tsyslog[tsyslogNLine][0]
        else:
            break
        f.write(strLine)

    f.write('\n/\n')
    f.close()



#-----------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------
def main(argv=None):
    '''Command line options.'''
    #read data

    # helpStr = ""

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    args = antabTr_parser.get_parser()
    rxgfiles=""
    if args.rxgfiles!="":
        rxgfiles=args.rxgfiles.split(',')


    cfg=config_file.readConfigFile(verbosity=args.verbose)
    if args.rxgDir!='':
        cfg.set('CALIB','rxgDir',args.rxgDir)
        print('Overriding config file rxgDir value. Will use: {}'.format(cfg['CALIB']['rxgDir']))
        
    if args.plot_wisdom!='':
        wd=wisdom.UserWisdom(cfg).load(args.plot_wisdom)
        if args.verbose>0:
            vis.plot_wisdom_diffrel(args,wd)
        else:
            vis.plot_wisdom(args,wd)
        exit(0);
    if args.print_wisdom!='':
        wd=wisdom.UserWisdom(cfg).load(args.print_wisdom)
        print(wd)
        exit(0);

    if args.extract_wisdom:
        wext=wisdom.WisdomExtractor(args,cfg)
        wext.extract_wisdom()
        exit(0);

    
    smooth_rxg=cfg['CALIB']['smooth_rxg']
    allow_Tcal_extrapolate=cfg['CALIB']['extrapolate']
    all_scans_noise_estimate=cfg['clean']['all_scans_noise_estimate']
    
    if len(args.paths)==0:
        print("No log files provided")
        sys.exit(0)
    logFileName = str(args.paths[0])
    if '/' in str(args.paths[0]):
        pass
    else:
        logFileName = str(args.paths[0])
        # print(logFileName)
        global station
        station = logFileName[-6:-4]
    logFileName =args.paths[0]
    
    if not logFileName.endswith('.log'):
        print("The provided file has unusual extension. Are you sure you provided log file ? Better stop now.")
        sys.exit(1)

#    antabFile = os.path.dirname(os.path.abspath(__file__)) + ('/%s.antabfs' % (logFileName.split('/')[-1].split('.')[0]))
    antabFile = os.path.join(os.path.dirname(logFileName),'%s.antabfs' % (logFileName.split('/')[-1].split('.')[0]))

    if os.path.isfile(antabFile):
        print("{} file already exists, skipping".format(antabFile))
        exit(0)
    


    logF = common.logFile(logFileName,cfg=cfg,rxgfiles=rxgfiles, verbosity=args.verbose,
                          smooth_rxg=smooth_rxg,
                          rolling_avg_samples=cfg.getint('CALIB','rolling_avg_samples'),
                          allow_Tcal_extrapolate=allow_Tcal_extrapolate,
                          )
    #antabH = antabHeader(logFileName)
    antabH = antabHeader(logF,cfg=cfg)  #FJB

    bbclist=[]
    tsyswrite=[]
    tsyswrite_aux = []
    timewrite_aux = []
    blockwrite_aux = []
    # maxlim=10000
    maxlim=cfg.getfloat('Tsys','maxlim')
    maxTsys=cfg.getfloat('Tsys','maxTsys')
    minTsys=cfg.getfloat('Tsys','minTsys')


    logData = logF.getLogData() # this should better return a dict or class
    header = logData[0] 
    indexline = logData[1]
    scanline = logData[2] 
    tsysline = logData[3] 
    block = logData[4] 
    time = logData[5] 
    tsyslog = logData[6] 
    setupTime = logData[7]

    # print('time.len ',len(time))
    # print('setupTime.len ',len(setupTime))
    # print('block')
    # print(np.array(block))
    # print(np.array(block).shape)
    # np.savetxt(logFileName+'.block.dump.txt',np.array(block))
    # print('scanline')
    # print(np.array(scanline))
    # print(np.array(scanline).shape)
    # np.savetxt(logFileName+'.scanline.dump.txt',np.array(scanline))
    # print('tsysline')
    # print(np.array(tsysline))
    # print(np.array(tsysline).shape)
    # np.savetxt(logFileName+'.tsysline.dump.txt',np.array(tsysline))
    # print('tsyslog')
    # print(np.array(tsyslog))
    # print(np.array(tsyslog).shape)
    # np.savetxt(logFileName+'.tsyslog.dump.txt',np.array(tsyslog))
        
        
    # print(setupTime)
    #bands = logF.loArray()
    #header,indexline,scanline,tsysline,block,time=readlog(logFileName)

    startInd = 0
    widx=0
    for bP in range(len(setupTime)):

        hLines = header[bP].split('\n')[4:]
        bbclist = []
        frequencies_GHz=[]
        for i in hLines:
            auxStr = i.split()
            bbclist.append(auxStr[4].strip(',') + ' ' + auxStr[5].strip(',')+' '+auxStr[9].strip(',')+', Freq '+auxStr[6]+' MHz, '+auxStr[3][0]+'CP' )
            frequencies_GHz.append(float(auxStr[6])/1000)

        minTsys,maxTsys=common.get_band_Tsys_min_max(frequencies_GHz[0],cfg)
        if args.minTsys!='':
            minTsys=float(args.minTsys)
        if args.maxTsys!='':
            maxTsys=float(args.maxTsys)


        if bP == (len(setupTime)-1):
            endInd = len(time)    
        else:
            for ind in range(len(time)):
                if time[ind] >= setupTime[bP+1][0]:
                    endInd = ind
                    break

        tsysline_aux = tsysline[startInd:endInd]
        block_aux = block[startInd:endInd]
        time_aux = time[startInd:endInd]
        x = []
        for time_ind in range(len(time_aux)):
            x_val = time_aux[time_ind]
            dt = datetime.datetime.utcfromtimestamp(x_val)
            days = (dt - datetime.datetime(dt.year,1,1,dt.hour,dt.minute,dt.second,dt.microsecond)).days + 1
            t = days + (dt.hour/24.) + (dt.minute/(60.*24.)) + (dt.second/(3600.*24.)) + (dt.microsecond/(3600.*24.*1e6))
            x.append(t)


        tptsys=np.matrix.transpose(np.array(tsysline_aux))
        # tptsys=common.prefilter(tptsys,block_aux,maxlim)    #filter negative values
        print('tptsys before prefiltering')
        print(np.array(tptsys).shape)
        tptsys=common.prefilter(tptsys,block_aux,maxTsys,minTsys)    #filter negative values
        print('using Tsys prefiltering min/max values: ', minTsys,maxTsys)
        print('tptsys after prefiltering')
        # print(np.array(tptsys))
        print(np.array(tptsys).shape)
        # np.savetxt(logFileName+'.tptsys.dump.txt',np.array(tptsys.T))

        #loop analizing all bbcs
        print('Draw a rectangle over the points that you want to delete. Then, close the window.')
        alltsys_aux = []
        removed_idx=[]
        for i in range(0,len(tptsys)):
            print('processing experiment: ',logFileName)
            
            blw=wisdom.UserWisdom(cfg=cfg,logFileName=logFileName,idx=widx)
            widx+=1
            fully=tptsys[i][:]
            #if len(fully) != len(time_aux):
            #    continue
            print('frequency [GHz]', frequencies_GHz[i])
            print('using Tsys prefiltering min/max values: ', minTsys,maxTsys)
            if args.verbose>0:
                print('bbclist[i]', bbclist[i])
            if not debug:
                if blw.have_wisdom():
                    alltsys_aux.append(blw.load().get_targets())
                    print('Using wisdom from file: {}'.format(blw.get_wisdom_fname()))
                else:
                    results=Selection(x,fully,block_aux,bbclist[i],
                                      clean_type=args.clean,
                                      alpha=cfg.getfloat('clean','alpha'),
                                      all_scans_noise_estimate=all_scans_noise_estimate,
                                      allow_Tcal_extrapolate=allow_Tcal_extrapolate,
                                      verbose=args.verbose,
                                      experimentName=logFileName[:-4])
                    delIndX = results.getDeletedX()
                    delIndX.reverse()
                    if delIndX != []:
                        for ind in delIndX:
                            time_aux.pop(ind)
                            block_aux.pop(ind)
                    removed_idx.append(delIndX)
                    alltsys_aux.append(results.y); 

                    get_clean_type=lambda x: 'manual' if x=='ols' else x
                    blw.store({
                        'x' : x,
                        'X' : results.wisdom['X'],
                        'Y': results.wisdom['Y'],
                        'ridx' : np.array(results.wisdom['ridx'],dtype=int),
                        'title' : bbclist[i],
                        'log' : logFileName,
                        'method' : get_clean_type(args.clean),
                        'sections' : np.array(block_aux,dtype=int),
                              })
                    # blw.store({
                    #     'x' : results.wisdom['x'], 
                    #     'y': results.wisdom['y'],
                    #     'x0' : results.wisdom['x0'], 
                    #     'y0' : results.wisdom['y'],
                    #     'ridx' : results.wisdom['ridx'],
                    #     'title' : bbclist[i],
                    #     'log' : logFileName,
                    #           })
                    blw.save()
                    # blw.savetxt(logFileName+'.wistxt_%02i' % i)
                    print('Saved wisdom to: {}'.format(blw.get_wisdom_fname()))
#
            else:
                alltsys_aux.append(fully)

        if not debug:
            if time_aux and alltsys_aux:
                x = []
                for time_ind in range(len(time_aux)):
                    x_val = time_aux[time_ind]
                    dt = datetime.datetime.utcfromtimestamp(x_val)
                    days = (dt - datetime.datetime(dt.year,1,1,dt.hour,dt.minute,dt.second,dt.microsecond)).days + 1
                    t = days + (dt.hour/24.) + (dt.minute/(60.*24.)) + (dt.second/(3600.*24.)) + (dt.microsecond/(3600.*24.*1e6))
                    x.append(t)

                # print(len(x))
                # for y in alltsys_aux:
                #     print(len(y))
                finalplot(x,alltsys_aux,bbclist, bP, experimentName=logFileName[:-4])

        tsyswrite_aux.append(np.matrix.transpose(np.array(alltsys_aux)))
        timewrite_aux.append(time_aux)
        blockwrite_aux.append(block_aux)
        
        startInd = endInd

    #print 'Close the plot and choose an option:'
    save=input('Would you like to save the results? y/n: ')
    if save == 'y':
        dpfuLines, polyelevLine = antabH.writeAntabPreamble(antabFile)        
        tsyswrite = None
        timewrite = None
        blockwrite = None
        for ind in range(len(setupTime)):
            if tsyswrite_aux[ind].size != 0:
                if tsyswrite is None:
                    tsyswrite = tsyswrite_aux[ind]
                else:
                    if tsyswrite_aux[ind].shape[1] != tsyswrite.shape[1]:
                        ncol = max(tsyswrite_aux[ind].shape[1],tsyswrite.shape[1])
                        if ncol != tsyswrite_aux[ind].shape[1]:
                            coldiff = ncol - tsyswrite_aux[ind].shape[1]
                            nrow = tsyswrite_aux[ind].shape[0]
                            nan_matrix = np.zeros((nrow,coldiff))
                            nan_matrix.fill(np.nan)
                            tsyswrite_aux[ind] = np.concatenate((tsyswrite_aux[ind],nan_matrix),axis=1)
                        elif ncol != tsyswrite.shape[1]:
                            coldiff = ncol - tsyswrite.shape[1]
                            nrow = tsyswrite.shape[0]
                            nan_matrix = np.zeros((nrow,coldiff))
                            nan_matrix.fill(np.nan)
                            tsyswrite = np.concatenate((tsyswrite,nan_matrix),axis=1)
                        
                    tsyswrite = np.concatenate((tsyswrite, tsyswrite_aux[ind]), axis=0)
            if len(timewrite_aux) != 0:
                if timewrite is None:
                    timewrite = copy(timewrite_aux[ind])
                    blockwrite = copy(blockwrite_aux[ind])
                else:
                    timewrite += timewrite_aux[ind]
                    blockwrite += blockwrite_aux[ind]
        if tsyswrite is None:
            tsyswrite = np.array([])

        #write_antab(antabFile, header, indexline, scanline, tsyswrite, block, time, tsyslog, setupTime, dpfuLines, polyelevLine, logF.stationName)
        write_antab(antabFile, header, indexline, scanline, tsyswrite, blockwrite, timewrite, tsyslog, setupTime, dpfuLines, polyelevLine, logF.stationName)
        print('Results in file %s' % antabFile)
        wisdom.UserWisdom(cfg).wisdom_info()

    else:
        print('Results not saved')
#-----------------------------------------------------------------------------------------------------
# def usage():
#     pydoc.pager(
# """
# Usage: {progname} [-f rxgfile_list] logfile
#
# Script to generate ANTAB files for its use with AIPS.
# Version: {date_version}
#
# Options:
#     -f : Allows the user to specify rxgfile_list, a list of RXG files comma separated.
#
#
# All RXG files are supposed to be under /usr2/control/rxg_files/. If the -f option is not given, the script
# will search there for a valid RXG file. Valid files are those which define a frequency range that contains 
# the observed setup in the log file AND match the station code in the log file name. To do so it must be
# named with the station code as Sc, e.g.:
# calYsQ.rxg
# """.format(progname=sys.argv[0],date_version=version))

#-----------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------
if __name__=='__main__':
    # main(sys.argv)
    main()
    # if len(sys.argv)==1 or '-h' in sys.argv:
    #     usage()
    #     sys.exit( 0 )
    # elif len(sys.argv) == 2:
    #     main(sys.argv)
    # elif len(sys.argv) == 4 and '-f' in sys.argv:
    #     rxg = sys.argv[2]
    #     rxgfiles = rxg.split(',')
    #     print(rxgfiles)
    #     main(sys.argv)
