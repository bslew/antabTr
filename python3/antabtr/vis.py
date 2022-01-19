'''
Created on Jan 14, 2022

@author: blew
'''

import matplotlib.pyplot as plt

def plot_wisdom(args,wd):
    
    fig=plt.figure(figsize=(10,5))
    plt.plot(wd.get_inputs(), '-o', color='k', label='input')
    plt.plot(wd.get_targets(), '-o', color='r', ms=3,label='target')
    plt.title('{}, {}'.format(wd.get_title(),wd.get_logfile()))
    plt.legend()
    plt.show()
    
    
    