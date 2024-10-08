"""
Decode raw data (bitstreams) after data-taking, save decoded information in CSV format identical to when running beam_test.py with option -c
Author: Amanda Steinhebel
amanda.l.steinhebel@nasa.gov
"""
import asyncio
from astep import astepRun
import time
import binascii
import logging
import glob
import pandas as pd
import numpy as np
import argparse
import re
import time


#Initialize
#pixel=[0,0]
layer, chip = 0,0
pixel = [layer, chip, 0, 11] #layer, chip, row, column
def decode_offline(logfile, toprint=False):



    astro = astepRun(inject=pixel)

    print(f"logfile={logfile}")
    #Define output file name
    csvfile = logfile.replace('.log', '.csv')

    #Setup CSV structure
    csvframe =pd.DataFrame(columns = [
            'readout',
            'ChipID',
            'payload',
            'location',
            'isCol',
            'timestamp',
            'tot_msb',
            'tot_lsb',
            'tot_total',
            'tot_us',
            'fpga_ts'
    ])

    #Import data file            
    #f=np.loadtxt(logfile, skiprows=6, dtype=str)
    f=np.loadtxt(logfile, dtype=str)

    #isolate only bitstream without b'...' structure 
    #strings = [a[2:-1] for a in f[:,1]]
    strings = [a[2:-1] for a in f]
    #print(strings)#works!

    i = 0
    errors=0

    #astro.decode_readout(hit, inc) 

    for s in strings:
        #convert hex to binary and decode
        #rawdata = list(binascii.unhexlify(s))
        #print(rawdata)
        try:
            hits = astro.decode_readout_offline(s, i, printer = toprint)
            #print(hits)
            #hits.hittime = time.time()
            #hits.h_hit = time.time()
        except IndexError:
            errors += 1
            #hits.rawdata = i
            #hits['hittime']=np.nan
    #hits['t_hit']=np.nan
        finally:
            i += 1
            #Overwrite hittime - computed during decoding
            #Populate csv
            csvframe = pd.concat([csvframe, hits])
            #csvframe.readout = csvframe.readout.astype(int)
    #Save csv
    csvframe.index.name = "order"
    csvframe.to_csv(csvfile,sep='\t')

    print("Decoding done!")

