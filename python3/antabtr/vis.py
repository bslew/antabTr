'''
Created on Jan 14, 2022

@author: blew
'''

import matplotlib.pyplot as plt
import numpy as np

def plot_wisdom(args,wd):
    
    fig=plt.figure(figsize=(10,5))
    plt.plot(wd.get_inputs(), '-o', color='k', label='input')
    plt.plot(wd.get_targets(), '-o', color='r', ms=3,label='target')
    plt.title('{}, {}'.format(wd.get_title(),wd.get_logfile()))
    plt.legend()
    plt.show()
    
    
def plot_wisdom_diffrel(args,wd):
    fig=plt.figure(figsize=(10,8))
    ax1=plt.subplot(311)
    plt.plot(wd.get_inputs(), '-o', color='k', label='input')
    plt.plot(wd.get_targets(), '-o', color='r', ms=3,label='target')

    
    ax2=plt.subplot(312,sharex=ax1)
    X=wd.get_inputs()
    Y=wd.get_targets()
    
    Y=np.abs((Y-X)/(X+np.spacing(1)))
    plt.plot(Y, '-o', color='k', label='rel')
    
    ax3=plt.subplot(313,sharex=ax1)
    plt.plot(np.array(Y>0.3,dtype=int), '-o', color='k', label='rel')
    plt.title('{}, {}'.format(wd.get_title(),wd.get_logfile()))
    plt.legend()
    plt.show()
    
    
    