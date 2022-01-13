'''
Created on Jan 13, 2022

@author: blew
'''
import os
import errno

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise  


def get_basename_ext(fname):
    '''
    return triple dirname,basename and file extension
    '''
    fname_base=os.path.basename(fname)
    l=fname_base.split('.')
    fnamenoext='.'.join(l[:-1])
    ext=l[-1]
    
    return os.path.dirname(fname),fnamenoext,ext
