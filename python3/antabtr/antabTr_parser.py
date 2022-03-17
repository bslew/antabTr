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
        # parser.add_argument('-o', type=str,
        #                     help='Print content of widom file. [default: %(default)s]', 
        #                     default='')
        parser.add_argument('--force_wisdom_save', action='store_true',
                            help='Save wisdom even if something fishy is detected. [default: %(default)s]', 
                            default=False)

        parser.add_argument('--extract_wisdom', action='store_true',
                            help='extract wisdom from provided log file and antabfs file [default: %(default)s]', 
                            default=False)

        # parser.add_argument('--smooth_rxg', action='store_true',
        #                     help='Create a smoothed version of rxg files [default: %(default)s]', 
        #                     default=False)

        parser.add_argument('--clean', type=str,
                            help='clean logfile automatically using selected method [default: %(default)s]', 
                            choices=['ols','gls','rlm'],
                            default='ols')

        parser.add_argument('--maxTsys', type=str,
                            help='Maximal Tsys value for prefilter. This value, if given overrides the values from the config file [default: %(default)s]', 
                            default='')
        parser.add_argument('--minTsys', type=str,
                            help='Minimal Tsys value for prefilter. This value, if given overrides the values from the config file [default: %(default)s]', 
                            default='')

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
