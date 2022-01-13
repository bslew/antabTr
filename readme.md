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
git clone git@github.com:bslew/antabTr.git
```

# INSTALL

Download the package from git repository

## Installation steps

Change directory to newly donwloaded antabTr repository, create and activate virtual environment,
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
- ~/.config/antabfs/antabfs.ini (prefered)
- /etc/antabfs.ini

Perform eg:

```
cp antabfs.ini ~/.config/antabfs/antabfs.ini
cd python3 && python setup.py install

```

or execute

```
make install
```

Now edit ~/.config/antabfs/antabfs.ini config file to match your preferences.
The config file currently defines the location of the .rxg files required to generate .antab files.


# Use

Use antabTr.py from vitrual environment, i.e:

```
cd antabTr
. venv/bin/activate
python antabTr.py ea065btr.test.log
```

Use antabTr.py in the same way as the original antabfs.py program. 
If you want to share the wisdom gathered by this program after your antab files
are ready to export to VLBeer you can execute 

```
share_wisdom.sh
```

script in the directory where you started antabTr.py program.
The wisdom files will be stored by default in ~/.config/antabTr/wisdom subdirectory.


# AUTHOR
Bartosz Lew [<bartosz.lew@umk.pl>](bartosz.lew@umk.pl)

