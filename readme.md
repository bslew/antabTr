# GENERAL

This package ports the antabfs program 
(see [VLBI-utilities](https://github.com/evn-vlbi/VLBI-utilities) repository) 
to python3 and implements gathering users' inputs to facilitate machine learning 
approach to generating antab files automatically. It also unifies tabs/spaces convention, 
introduces experimental processing pipeline and provides support for configuration files.

This version of the program is extended at Toruń VLBI station, but the core functionality
related to processing logs and generating antabs is largely unchanged.

The name of the program "antabTr" is a variation of the original name and indicates
that the program collects and stores users input as training data useful
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
Go to your logs directory and use the antabTr.py program instead of antabfs.py:

```
antabTr.py ea065btr.log
```

# Wisdom

antabTr.py program should be used in the same way as the original antabfs.py program but
this version will automatically store information about how the user reduces the data in wisdom files.
Wisdom files are meant to simplify I/O operations in supervised ML approach to automatically generate
antabs.
Any pre-processing steps that are possibly performed prior to using antabfs.py should also be
performed when using antabTr.py. The Makefile scripts makes some of that steps easier, but using 
the Makefile pipeline is currently in experimental stage.

## Storing wisdom files
If you cancel execution of the antabTr.py program
before saving your final .antab file and then restart processing the same log file,
the program will continue from the point your left off using the wisdom data stored in the local
directory. The wisdom files are stored by default in the 'wisdom' sub-directory.
The wisdom files contain Tsys data from both the log file and from the generated antab file.
This information can be used in supervised machine learning.
To facilitate ML this information can also be extracted for past EVN sessions from analysis 
of both .log and .antab files.

## Correcting/re-generating antab files

If you wish to reprocess your log file all over again without loading the wisdom from the previous run, simply
go to the wisdom directory and remove the file[s] corresponding to that log file.

## Sharing
It will be useful if you decide to share the wisdom gathered by this program after your antab files
are prepared and ready to export to VLBeer. After all, this is one of the reasons for writing
this variation of the original program. In order to share the wisdom execute:

```
share_wisdom.py
```

script in the directory where you started antabTr.py program.
The wisdom files will be sent to a remote server in order to improve machine learning training process
that will eventually remove the need for manual preparation of antab files.

The server will ask you for a password, which is the same as the one used for uploading antab files
to VLBeer. Alternatively, if you do not want to enter the password every time you run this script,
please send your public ssh-key to the author.

In time, the wisdom will be made publicly available via [antab-wisdom](https://github.com/bslew/antab-wisdom)
repository.

### What is shared?

Only wisdom files are being shared. Wisdom files are pickled dictionaries containing the name of log file,
the input Tsys data, cleaned Tsys data and indexes of points that were removed by the user for each bbc.
The naming of the wisdom files follows convention:

`yyyy-mm.logfile_prefix.user_name.bbc.awpkl`

where:
- yyyy-mm are year and month at saving time
- logfile_prefix is the log file name without extension (VLBI experiment with station code)
- user_name is the value of the $USER environment variable
- bbc - an integer
- awpkl - wisdom files extension

Hence, sharing wisdom is equivalent with sharing fraction of the information stored in
.antab files and .log files that are sent to VLBeer.

## Multiple uploads
If you shared the wisdom once and then decided to correct and regenerate the antab files you can
share_wisdom.py again. The files will be uploaded again and their previous version will be overwritten if
the updated version of the antab files is generated the same month as the previous one which results from
the naming convention of the wisdom files.

# AUTHOR
Bartosz Lew [<bartosz.lew@umk.pl>](bartosz.lew@umk.pl)

