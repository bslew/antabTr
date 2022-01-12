# GENERAL

This package implements python3 version of the antabfs program and extends it 
in order to enable gathering users input data to facilitate machine learning 
approach to generating antab files automatically.

This program was developed and tested on Toruń VLBI station

The name of the program antabTr is a variation of the original name that indicates
that the program collects and stores training data input by the user, but also 
the Tr suffix concides with the Toruń VLBI station abbreviation.

The user has a choice to decide when or if the collected data should be shared and 
made public by executing export_wisdom.sh script.



# DOWNLOAD

`git clone git@github.com:bslew/antabTr.git`

# INSTALL

Download the package from git repository

## Installation steps

`cd antabTr
python3 -m venv venv
. venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
`



# Use

Use antabfs_tassili.py from vitrual environment, i.e:

`cd antabTr`
`. venv/bin/activate`
`python antab_tassili.py`

Use antabfs_tassili.py in the same way as the original antabfs.py program. 
If you want to share the data gathered by this program execute 

`export_wistom.sh`

script. The wisdom files are stored by default in ~/.config/antabTr/ subdirectory.


#AUTHOR
Bartosz Lew [<bartosz.lew@umk.pl>](bartosz.lew@umk.pl)

