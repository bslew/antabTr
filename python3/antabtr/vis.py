'''
Created on Jan 14, 2022

@author: blew
'''

import matplotlib.pyplot as plt

def plot_wisdom(args,wd):
    
    
    plt.plot(wd.get_inputs(), '-o', color='k', label='input')
    plt.plot(wd.get_targets(), '-o', color='r', label='target')
    plt.legend()
    plt.show()
    
    
    