'''
Created on Dec 9, 2021

@author: blew
'''
import os,sys

__version__ = 0.1
__date__ = '2022-01-10'
__updated__ = '2021-01-10'

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

def get_parser():
    
    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    # try:
    #     program_shortdesc = __import__('__main__').__doc__.split("\n")[1] if len(__import__('__main__').__doc__.split("\n"))>=2 else ''
    # except:
    program_shortdesc="Script to generate ANTAB files for its use with AIPS."
    program_epilog ='''
    
Script to generate ANTAB files for its use with AIPS.


    
Examples:

antabTr.py ea065btr.log

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
        parser = ArgumentParser(description=program_license, epilog=program_epilog, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]", default=0)
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        # parser.add_argument('--train_dir', type=str, default='../../data/train/',help='train dir')
        parser.add_argument(dest="paths", help="logfile.log [default: %(default)s]", metavar="path", nargs='*')
        parser.add_argument('-f','--rxgfiles', type=str, default='',help='''
            rxgfile_list, a list of RXG files comma separated. 
            
            All RXG files are supposed to be under the location specified in the antabfs.ini config file. 
            If the -f option is not given, the script
            will search there for a valid RXG file. Valid files are those which define a frequency range that contains 
            the observed setup in the log file AND match the station code in the log file name. To do so it must be
            named with the station code as Sc, e.g.:
            calYsQ.rxg            
            ''')
        parser.add_argument('--rxgDir', type=str,
                            help='Path to rxg files directory. If specified, this option takes precedence over the value stored in the .antabfs.ini config file [default: %(default)s]', 
                            default='')
        parser.add_argument('--antabfs', type=str,
                            help='extract wisdom option. Path to antabfs file. [default: %(default)s]', 
                            default='')
        parser.add_argument('--plot_wisdom', type=str,
                            help='Plot widom file. [default: %(default)s]', 
                            default='')
        parser.add_argument('--print_wisdom', type=str,
                            help='Print content of widom file. [default: %(default)s]', 
                            default='')
        parser.add_argument('--force_wisdom_save', action='store_true',
                            help='Save wisdom even if something fishy is detected. [default: %(default)s]', 
                            default=False)
        # parser.add_argument('--split_seed', type=int,
        #                     help='random seed for torch.Generator.manual_seed() [default: %(default)s]',default=1)
        # parser.add_argument('--lr', type=float, 
        #                     help='optimizer learning rate[default: %(default)s]', 
        #                     default=0.001)
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
