'''
Created on Jan 13, 2022

@author: blew
'''
import os,sys
import pickle
import numpy as np
from datetime import datetime
from antabtr import common
import matplotlib.pyplot as plt

class UserWisdom():
    def __init__(self,cfg,logFileName='',idx=0):
        '''
        '''
        self.wis={}
        self.cfg=cfg
        self.odir=cfg['wisdom']['wisDir']
        self.idx=idx
        d,f,e=common.get_basename_ext(logFileName)
        self.logFileName=logFileName
        # self.logFileNameNoExt=os.path.join(d,f)
        self.logFileNameNoExt=f
        self.user=os.environ['USER']
        self.dt=datetime.strftime(datetime.utcnow(),'%Y-%m')

    def __str__(self):
        return repr(self.wis)

    def __repr__(self):
        return repr(self.wis)

    def wisdom_info(self):
        print("")
        print("WISDOM NOTICE")
        print("=============")
        print("If you're done preparing antab files and they are ready for VLBeer, please consider sharing wisdom by executing 'share_wisdom.py' command in {} directory".format(os.getcwd()))
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

    def get_title(self):
        try:
            return self.wis['title']
        except KeyError:
            pass
        return ''

    def get_logfile(self):
        try:
            return self.wis['log']
        except:
            pass
        return ''

    def get_inputs(self):
        if 'X' in self.wis:
            return self.wis['X']
        return self.wis['y0']

    def get_removed_mask(self):
        '''
        return 1-d bool array that can be used for selecting removed data points
        '''
        res=np.ones(len(self.get_inputs()))
        res[self.wis['ridx']]=0
        return np.array(res,dtype=bool)
        
    
    def get_targets(self):
        if 'Y' in self.wis:
            return self.wis['Y']
        return self.wis['y']

    def load(self,fname=None):
        if fname==None:
            fname=self.get_wisdom_fname()
            
        try:
            # self.wis=pickle.load(f, encoding="latin1")
            f= open(fname, 'rb')
            self.wis=pickle.load(f)
        except UnicodeDecodeError:
            print('could not decode wisdom, tryinig latin1 enc')
            try:
                f= open(fname, 'rb')
                self.wis=pickle.load(f, encoding="latin1")
            except:
                raise
            

        return self

    def store(self,wis):
        '''
        wis - dict('x' : array, 'y' : array, 'x0':array, 'y0': array, 'ridx': list) -- depreciated
        wis - dict('X' : array, 'Y' : array)
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
        
        # print("saving to ",fname)
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
        
  
    
class WisdomExtractor():
    '''
    Class to extract wisdom data from .log and .antabfs files even without 
    proper tcal .rxg files. If no calibration is given (case for 
    most of the stations because rxg files are not uploaded to vlbeer)
    tcal is assumed 1.0. In such cases calibration is inferred from antab file
    based on most frequently occuring value. This assumes that at least some 
    parts of the data are not noisy. If they are, the extractor will ignore such
    log/antab combination.
    '''
    
    def __init__(self,args,cfg):
        self.args=args
        self.cfg=cfg
        maxlim=cfg.getfloat('Tsys','maxlim')

        self.logFileName=args.paths[0]
        self.logF = common.logFile(self.logFileName,cfg=cfg, 
                                   verbosity=args.verbose,
                                   enforceTcalIfNoCal=1.)
        logData = self.logF.getLogData()
        tsysline = logData[3] 
        block = logData[4] 
        
        # print(tsysline)
        # print(block)

        tsysline_aux=tsysline
        block_aux=block
        tptsys=np.matrix.transpose(np.array(tsysline_aux))
        self.X=common.prefilter(tptsys,block_aux,maxlim)
        # print(X)
        # self.x0=np.arange(len(self.X.T))
        
        self.Y=common.AntabFile().load(args.antabfs).Tsys().T
        
        self.wisdom_min_length=cfg.getint('wisdom','min_length')
        self.wisdom_lmargin=cfg.getfloat('wisdom','lmargin')/100
        self.wisdom_rmargin=cfg.getfloat('wisdom','rmargin')/100
        self.wisdom_maxTsys=cfg.getfloat('wisdom','maxTsys')
        self.input_target_resolution=cfg.getfloat('wisdom','input_target_resolution')
        self.selection_thres=cfg.getfloat('wisdom','selection_thres')
        self.most_frequent_calib_factor_max=10.
        
    def get_data(self,x,y, channel=0):
        '''
        returns x,y,status
        '''

        if len(x)<self.wisdom_min_length:
            print("Ignoring due to {}<{} length of tptsys (channel: {})".format(len(x),self.wisdom_min_length,channel))
            return x,y,False

        
        # make equal length
        imax=np.min([len(x),len(y)])
        x=x[:imax]
        y=y[:imax]


        # apply margin
        ist=int(len(x)*self.wisdom_lmargin)
        ien=int(len(x)-len(x)*self.wisdom_rmargin)
        x=x[ist:ien]
        y=y[ist:ien]
        # print(ist,ien)

        if len(x)<self.wisdom_min_length:
            print("Ignoring due to {}<{} length of tptsys (channel: {})".format(len(x),self.wisdom_min_length,channel))
            return x,y,False


        # normalize due to missing calibration information
        f=list(np.array(y/x*self.input_target_resolution,dtype=int))
        s=set(f)
        tsys_norm_stats=np.array([ np.array([float(val)/self.input_target_resolution,f.count(val)]) for val in s])
        tsys_norm_stats=tsys_norm_stats[tsys_norm_stats[:,1].argsort()]
        tsys_norm_stats[:,1]/=len(f)
        if self.args.verbose>4:
            print(tsys_norm_stats)
        most_frequent_calib_factor=tsys_norm_stats[-1][0]

        # plt.plot(x)
        # plt.plot(y)
        # plt.show()
        x=x*most_frequent_calib_factor

        if most_frequent_calib_factor>np.max([self.most_frequent_calib_factor_max,1./self.most_frequent_calib_factor_max]):
            print('ignoring due to too too suspecious calibration factor value ({}, channel: {})'.format(most_frequent_calib_factor,channel))
            return x,y,False

        # check log file consistency (was the correct antab/log file transferred?)
        # sigma_diff=(y-x).std()
        # print('st.dev of difference',sigma_diff)
        # if sigma_diff>1.:
            # print('ignoring due to too large st.dev of difference (possible log-antab mismatch, or extreemely noisy')
            # return x,y,False

        '''
        screen by empirical calibration factor occurance threshold.
        I.e. at least 10% of data should be unaffected by noise and have calibration
        factor value within 0.1% of the original value from the log file
        '''
        freq_thres=self.selection_thres
        if tsys_norm_stats[-1][1]<freq_thres:
            print('ignoring due to too possible log-antab mismatch, or extremely noisy (channel: {}, val: {}, thres: {})'.format(channel, tsys_norm_stats[-1][1],freq_thres))
            return x,y,False
            
        if np.median(y)>self.wisdom_maxTsys:
            return x,y,False

        if np.any(y>self.cfg.getfloat('wisdom','maxTsys')):
            print('ignoring due to possibly not cleaned data (channel: {}, max Tsys val thres: {})'.format(channel, self.cfg.getfloat('wisdom','maxTsys')))
            return x,y,False

        if np.any(y<self.cfg.getfloat('wisdom','minTsys')):
            print('ignoring due to possibly not cleaned data (channel: {}, min Tsys val thres: {})'.format(channel, self.cfg.getfloat('wisdom','minTsys')))
            return x,y,False
        if np.any(x<0.):
            print('ignoring due to possibly wrong data (channel: {}, min input Tsys val thres: {})'.format(channel, 0.))
            return x,y,False

        return x,y,True
        
    def extract_wisdom(self):
        '''
        '''
        
        if len(self.X.T)==0:
            print("Ignoring due to {} length of tptsys".format(len(self.X)))
            
        
        
        for i,x in enumerate(self.X):
            if self.args.verbose>2:
                print('testing bbc {}'.format(i))
            x,y,status=self.get_data(x, self.Y[i],channel=i)
            
            if status or self.args.force_wisdom_save:
            
                wis=UserWisdom(self.cfg,self.logFileName,i)
    
                idx=np.arange(len(x))
                wis.store({
                        'X' : x,
                        'Y' : y,
                        'bbc' : i,
                        # 'x' : idx,
                        # 'y': self.Y[i][:imax],
                        # 'x0' : idx, 
                        # 'y0' : x[:imax],
                        # 'ridx' : [],
                        'title' : i,
                        'log' : self.logFileName,
                          })
                wis.save()
            else:
                if self.args.verbose>2:
                    print('channel ignored')
