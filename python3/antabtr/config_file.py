'''
Created on Jan 23, 2019

@author: blew
'''
import configparser
import os,sys
import json
# import csv
# from io import StringIO
import re
# from argparse import ArgumentParser
# from argparse import RawDescriptionHelpFormatter

class antabParser(configparser.ConfigParser):
    def __init__(self):
        super().__init__()
#         list_keys=['db_keys']
    
    
    def __getitem__(self, key):
        if key=='rxgDir':
            if not configparser.ConfigParser.has_option('CALIB', key):
                raise Exception('Cound not find rxgDir configuration in CALIB section in config file. Please edit your config file')
            
        return configparser.ConfigParser.__getitem__(self, key)
        
    def getlist(self, section_name,option_name):
#         for lk in list_keys:
#             for s in config.sections():
#                 if lk in config[s].keys():
#                     print(config[s][lk])
#                     print(type(config[s][lk]))
#                     config[s][lk]=csv.reader(config[s][lk], delimiter=',')
        val=self.get(section_name,option_name)
        if not val.startswith('['):
            raise "List should start with ["
        if not val.endswith(']'):
            raise "List should end with ]"
#         print(val[1:-1])
#         f=StringIO(val[1:-1])
#         reader = csv.reader([val[1:-1]], delimiter=',')
#         for r in reader:
#             print('----')
#             print(r)
#         print('----')
#         print('----')
        chars_to_remove=['"']
        rx = '[' + re.escape(''.join(chars_to_remove)) + ']'
        l=[ re.sub(rx,'',x.strip()) for x in val[1:-1].split(',')]
#         for it in l:
#             print(it)
        return l



def readConfigFile(inifile='antabfs.ini'):
#     config = configparser.ConfigParser()
    homeLoc=os.environ['HOME']+os.sep+'.'
    homeLoc2=os.environ['HOME']+os.sep+'.config/antabfs/'
    searchLocations=['./','etc/',homeLoc,homeLoc2,'/etc/antabfs/']
    
    config = antabParser()
    
    for loc in searchLocations:
        configFile=loc+inifile
        if os.path.isfile(configFile):
            print('Found configuration file: {}'.format(configFile))
            config.read(configFile)
            return config
        else:
            print('Cound not find config file: {}'.format(loc))            

    raise Exception("Config file is required but not found. Please consult the docs.")

