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
                            help='''filter to match files by extension. E.g. -f log LOG
                            [default: %(default)s]''', 
                            default=['log'])
        # parser.add_argument('-V', '--version', action='version', version=program_version_message)
        # # parser.add_argument('--train_dir', type=str, default='../../data/train/',help='train dir')
        # parser.add_argument(dest="paths", help="logfile.log [default: %(default)s]", metavar="path", nargs='*')
        # parser.add_argument('-f','--rxgfiles', type=str, default='',help='''
        #     rxgfile_list, a list of RXG files comma separated. 
        #
        #     All RXG files are supposed to be under the location specified in the antabfs.ini config file. 
        #     If the -f option is not given, the script
        #     will search there for a valid RXG file. Valid files are those which define a frequency range that contains 
        #     the observed setup in the log file AND match the station code in the log file name. To do so it must be
        #     named with the station code as Sc, e.g.:
        #     calYsQ.rxg            
        #     ''')
        parser.add_argument('--logdir', type=str,
                            help='path the log and antabfs directory. [default: %(default)s]', 
                            default='')
        # parser.add_argument('--plot_wisdom', type=str,
        #                     help='Plot widom file. [default: %(default)s]', 
        #                     default='')
        # parser.add_argument('--split_seed', type=int,
        #                     help='random seed for torch.Generator.manual_seed() [default: %(default)s]',default=1)
        parser.add_argument('-n','--nthread', type=int, 
                            help=' number of threads in parallel [default: %(default)s]', 
                            default=1)
        # parser.add_argument('--momentum', type=float, 
        #                     help='optimizer momentum [default: %(default)s]', 
        #                     default=0.9)
        # parser.add_argument('--device', type=str, 
        #                     help='select device to use [default: %(default)s]', 
        #                     choices=['auto','cpu','cuda:0'], 
        #                     default='auto')

        # parser.add_argument('--file_ext', type=str,
        #                     help='input file extension [default: %(default)s]', 
        #                     default=['awpkl'],
        #                     nargs='*',
        #                     )
        # parser.add_argument('--model_dir', type=str, 
        #                     help='directory containing trained model and all partial files [default: %(default)s]', 
        #                     required=False,
        #                     default='../../models/lstm')
        #
        # parser.add_argument('--chkpt_save', type=int, 
        #                     help='save ckp file every this epoch [default: %(default)s]', 
        #                     required=False,
        #                     default=100)
        #
        # parser.add_argument('--model', type=str, 
        #                     help='model name [default: %(default)s]', 
        #                     required=False,
        #                     default='class',
        #                     choices=['class','autoenc','lstm','dense','conv1d'])
        # parser.add_argument('--denseConf',type=int,
        #                     help='dense model linear hidden layers sizes configuration',
        #                     default=[],
        #                     nargs='*')
        # parser.add_argument('--loss', type=str, 
        #                     help='loss function name [default: %(default)s]', 
        #                     required=False,
        #                     default='smoothL1',
        #                     choices=['smoothL1','L1','MSE'])
        #
        # parser.add_argument('--epochs', type=int, help='Number of epochs during training [default: %(default)s]', default=100)
        # parser.add_argument('--bs', type=int, help='batch size [default: %(default)s]', default=10000)
        # parser.add_argument('--load_workers', type=int, help='batch load workers number [default: %(default)s]', default=1)

        # parser.add_argument('--dsize',type=int,default=1000,help='''Data size. Incompatible data
        # will be padded with zeros on the input and output or truncated
        # ''')
        parser.add_argument('--extract_wisdom', action='store_true',
                            help='extract wisdom from provided log file and antabfs file [default: %(default)s]', 
                            default=False)

        # parser.add_argument('--MLflow_tracking_uri',type=str,default='',
        #                     help='''MLflow tracking server e.g. "http://host.name:4040.
        #                     Use empty string to skip MLflow logging''')
        # parser.add_argument('--MLflow_exp_name',type=str,default='',help='MLflow experiment name. If empty will generate name using datetime')
        # parser.add_argument('--MLflow_run_name',type=str,default='',help='MLflow run name.')

        # parser.add_argument('--test_file', type=str, 
        #                     help='path to awpkl file [default: %(default)s]. Eg. "../../data/train/blew-May-Jun21-ec077dtr.01.awpkl"', 
        #                     required=False,
        #                     default='')
        


        # parser.add_argument('--title',type=str,default='', help='''
        # Plot title
        # ''')

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
    rx = re.compile(r'\.('+'|'.join(args.filter)+')')
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
