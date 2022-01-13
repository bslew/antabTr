# GENERAL

This package ports the antabfs program 
(see [VLBI-utilities](https://github.com/evn-vlbi/VLBI-utilities) repository) 
to python3 and implements gathering users' inputs to facilitate machine learning 
approach to generating antab files automatically. It also introduces several minor
configuration and pre-processing modifications and support for config files.

This program is developed at Toruń VLBI station.

The name of the program "antabTr" is a variation of the original name that indicates
that the program collects and stores users input and stores it as training data useful
in machine learning.

The user has a choice to decide when or if the collected data should be shared and 
made visible to other contributors.


# DOWNLOAD

```
git clone https://github.com/bslew/antabTr.git
```

# INSTALL

Download the package from git repository

## Installation steps

Change directory to newly downloaded antabTr repository, create and activate virtual environment,
update it and install required packages.

```
cd antabTr
python3 -m venv venv
. venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

```

Make sure the venv is located in antabTr subdirectory.
Copy the configuration file to one of the default locations.
The configuration file is sought at:

- ./antabfs.ini
- etc/antabfs.ini
- ~/.antabfs.ini
- ~/.config/antabfs/antabfs.ini (preferred)
- /etc/antabfs.ini

Perform eg:

```
cp antabfs.ini ~/.config/antabfs/antabfs.ini
cd python3 && python setup.py install
cd ..

```

or execute

```
make install
```

Now edit ~/.config/antabfs/antabfs.ini config file to match your preferences.
The config file currently defines the location of the .rxg files required to generate .antab files.


# Use

Use antabTr.py from virtual environment, i.e activate the environment unless you already have done so:

```
cd antabTr
. venv/bin/activate
```

"(venv)" prompt will appear to indicate you are in the virtual environment.
Go to your logs directory and use the modified antabTr.py program instead of antabfs.py:

```
antabTr.py ea065btr.log
```

# Wisdom

antabTr.py program should be used in the same way as the original antabfs.py program. 
This version however stores information about how to reduce your data. If you cancel execution
before you save your final .antab file and then restart processing the same log file,
the program will continue from the point your left off using the wisdom data stored in the local
directory. 

If you wish to redo your log file again without loading wisdom from the previous run, simply
go to the wisdom directory and remove the file[s] corresponding to that log file.

It will be useful if you decide to share the wisdom gathered by this program after your antab files
are prepared and ready to export to VLBeer. After all, this is one of the reasons for writing
this modification to the original program. To share the wisdom execute:

```
share_wisdom.py
```

script in the directory where you started antabTr.py program.
The wisdom files will be sent to remote server in order to improve machine learning process
that will eventually remove the need for manual preparation of antab files.

The server will ask you for password, which is the same as the one used for uploading antab files
to VLBeer. Alternatively, if you do not want to enter password every time you run this script,
please send your public ssh-key to the author.

In time, the wisdom will be made publicly available.


# AUTHOR
Bartosz Lew [<bartosz.lew@umk.pl>](bartosz.lew@umk.pl)

