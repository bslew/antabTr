'''
Created on Jan 13, 2022

@author: blew
'''
from antabTr import config_file
import subprocess

cfg=config_file.readConfigFile()
# cmd='share_wisdom.sh {}'.format(cfg['wisdom']['wisDir'])
subprocess.call(['share_wisdom.sh',cfg['wisdom']['wisDir']])
