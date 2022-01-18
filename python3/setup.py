#!/usr/bin/env python

# from distutils.core import setup, Extension
from setuptools import setup
import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()
os.environ["CC"] = "c++" 
os.environ["CXX"] = "c++"


reqired_packages=[
    'numpy',
    'matplotlib',
    'statsmodels',
    ]

setup(name='antabTr',
      version='1.0',
      description='Extended version of antabfs program ported to python3',
      long_description=read('../readme.md'),
      long_description_content_type='text/markdown',
      author='Bartosz Lew',
      author_email='bartosz.lew@umk.pl',
      url='https://github.com/bslew/antabTr',
      install_requires=reqired_packages,
      package_dir = {'': '.'},
      packages = ['antabtr',
                  ],
      scripts=['antabtr/antabTr.py',
               'antabtr/fix-tsys.py',
               'antabtr/share_wisdom.py',
               'antabtr/extract_wisdom.py',
               ],
      classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License"
        ],
     )
      #       ext_modules=[cpedsRotation]

#       py_modules = ['pyCPEDScommonFunctions.libcpedsRotation.so'],
#       py_modules=['RadiometerData.RPG_tau','RadiometerData.RPG_Tatm'],


