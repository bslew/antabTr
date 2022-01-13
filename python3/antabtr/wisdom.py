'''
Created on Jan 13, 2022

@author: blew
'''
import os,sys
import pickle
import numpy as np
from datetime import datetime
from antabtr import common

class UserWisdom():
    def __init__(self,cfg,logFileName='',idx=0):
        '''
        '''
        self.wis=None
        self.cfg=cfg
        self.odir=cfg['wisdom']['wisDir']
        self.idx=idx
        d,f,e=common.get_basename_ext(logFileName)
        self.logFileName=logFileName
        self.logFileNameNoExt=os.path.join(d,f)
        self.user=os.environ['USER']
        self.dt=datetime.strftime(datetime.utcnow(),'%Y-%m')

    def wisdom_info(self):
        print("")
        print("WISDOM NOTICE")
        print("=============")
        print("If you're done preparing antab files and they are ready for VLBeer, please consider sharing wisdom by executing 'share_wisdom.py' command in this directory")
        print("")
        print("")

    def have_wisdom(self):
        return os.path.isfile(self.get_wisdom_fname())

    def get_wisdom_fname(self):
        # return os.path.join(self.odir,self.logFileName+'.wispkl_%02i' % self.idx)
        
        return os.path.join(self.odir,self.dt+'.'+self.logFileNameNoExt+'.'+self.user+'.%02i.awpkl' % self.idx)

    def get_wisdom_vals(self):
        '''
        load wisdom and return y values
        '''
        self.load()
        return self.wis['y']

    def load(self):
        f= open(self.get_wisdom_fname(), 'rb')
        self.wis=pickle.load(f)
        return self.wis

    def store(self,wis):
        '''
        wis - dict('x' : array, 'y' : array, 'x0':array, 'y0': array, 'ridx': list)
        '''
        self.wis=wis
        # fname=os.path.join(
        #     os.environ['VIRTUAL_ENV'].split(os.path.sep)[:-1],
        #     cfg['wisdom']['wisDir'],
        #     self.get_wisdom_fname())
        # self.save(fname)
        return self

    def checkodir(self,fname):
        odir=os.path.dirname(fname)
        if not os.path.isdir(odir):
            common.mkdir_p(odir)

    def save(self,fname=None):
        if fname==None:
            fname=self.get_wisdom_fname()
        # else:
        #     fname=os.path.join(self.odir,fname)
        self.checkodir(fname)
        fileObj = open(fname, 'wb')
        pickle.dump(self.wis,fileObj)
        fileObj.close()    

    def savetxt(self,fname):
        fname=os.path.join(self.odir,fname)
        self.checkodir()

        np.savetxt(fname+'.X',np.column_stack((self.wis['x0'],self.wis['y0'])))
        np.savetxt(fname+'.Y',np.column_stack((self.wis['x'],self.wis['y'])))
        np.savetxt(fname+'.ridx',np.asarray(self.wis['ridx'],dtype=int),fmt='%i')
        
        