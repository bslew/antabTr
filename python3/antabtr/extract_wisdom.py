'''
Created on Jan 18, 2022

This program runs antabTr.py in parallel for all .log files in the current directory

@author: blew
'''

from multiprocessing import Pool,Process
import subprocess
import os,sys
import re
from antabtr import common

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

__version__ = 0.1
__date__ = '2022-01-10'
__updated__ = '2021-01-10'

def get_parser():
    
    program_shortdesc="Script to extract wisdom in parallel"
    program_epilog ='''
    
The program runs over log and antabfs files and extracts wisdom in parallel


    
Examples:

extract_wisdom.py -n 4 --logdir directory_with_logs_and_antab_files

'''
    program_license = '''%s

  Created by Bartosz Lew on %s.
  Copyright 2021 Bartosz Lew. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))
    
    try:
        # Setup argument parser
        # parser = ArgumentParser()
        parser = ArgumentParser(description=program_license, epilog=program_epilog, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]", default=0)
        parser.add_argument("-f",'--filter',dest='filter',
                            nargs="*", metavar="VALUE",
                            help='''filter to match files by file ending. E.g. -f log to select all log files, or -f tr.log to select only logs from Toruń station
                            [default: %(default)s]''', 
                            default=['log'])
        parser.add_argument('--logdir', type=str,
                            help='path the log and antabfs directory. [default: %(default)s]', 
                            default='')
        parser.add_argument('-n','--nthread', type=int, 
                            help=' number of threads in parallel [default: %(default)s]', 
                            default=1)

        # Process arguments
        args = parser.parse_args()

    except KeyboardInterrupt:
        ## handle keyboard interrupt ###
        raise
#     except Exception as e:
#         if DEBUG or TESTRUN:
#             raise(e)
#         indent = len(program_name) * " "
#         sys.stderr.write(program_name + ": " + repr(e) + "\n")
#         sys.stderr.write(indent + "  for help use --help")
#         return 2
        
    return args

def logantabBatch(bs,args):
    b=[]
    for i,d in enumerate(logantabFiles(args)):
        if i<bs:
            b.append(d)
        yield b
        
def logantabFiles(args):
    '''
    log and antab files pair generator
    '''
    rx = re.compile(r'('+'|'.join(args.filter)+')')
    src=args.logdir
    for path, dnames, fnames in os.walk(src,followlinks=True):
        F=[os.path.join(path, x) for x in fnames if rx.search(x)]
        for log in F:
            d,f,e=common.get_basename_ext(log)
            yield log,os.path.join(d,f+".antabfs")
    
def process_antab(logantab):
    log,antab=logantab
    cmd='antabTr.py --extract_wisdom --antabfs {} {}'.format(antab,log)
    
    print("executing: ",cmd)
    # p=Process(target=)
    subprocess.run(cmd.split())

def main():
    args=get_parser()
    with Pool(args.nthread) as p:
        it=logantabFiles(args)
        # for b in logantabFiles(args):
        #     log, antab=b
        p.map(process_antab,it)
            # print(b)
# antabTr.py --extract_wisdom --antabfs clean/vlbeer$antdst clean/vlbeer$dst


    
if __name__ == '__main__':
    main()
