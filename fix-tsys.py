#!/usr/bin/env python
#
#  was a rudimentary Phase Display
#  plots OOF raw maps from ascii files.
# 
# V1.0 UB, May 2019 

import sys
import os

# Usage
if len(sys.argv)<2:
  print("Usage fix-tsys.py log-file")

# Try to open and read in log-file
try:
  f = open(sys.argv[1], "r" )
  all = f.readlines()
  f.close()
except:
  print("File not found")
  sys.exit()

# List of possible BBCs 
BBCS=["1l","1u","2l","2u","3l","3u","4l","4u","5l","5u","6l","6u","7l","7u","8l","8u","9l","9u","al","au","bl","bu","cl","cu","dl","du","el","eu","fl","fu","gl","gu"]
# List of possivle IFs
IFS=["ia","ib","ic","id"]

# Go through log and find and correct swapped cont_cal entries in TPCONT lines
for line in all:
  if line[20:34]=="#tpicd#tpcont/":
    newtpil=[]
    #print(line[:-1])
    tmpline = line[:-1].split("/")
    newline = tmpline[1].split(",")
    for i in range(len(newline)):
      if newline[i] in BBCS and newline[i+1]!="$$$$$$$" and newline[i+2]!="$$$$$$$":
        if int(newline[i+1]) > int(newline[i+2]):
          #print("%s,%s,%s" % (newline[i],newline[i+1],newline[i+2]))
          newtpi=("%s,%s,%s," % (newline[i],newline[i+1],newline[i+2]))
        else:
          newtpi=("%s,%s,%s," % (newline[i],newline[i+2],newline[i+1]))
        newtpil.append(newtpi)
      elif newline[i] in IFS and newline[i+1]!="$$$$$$$":
        newtpi=("%s,%s " % (newline[i],newline[i+1]))
        newtpil.append(newtpi)
    tmpline2=''.join(str(item) for item in newtpil)
    print(("%s/%s" % (tmpline[0],tmpline2[:-1])))
  else:
    print((line[:-1]))
