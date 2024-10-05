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
layer, chip = 0,0
pixel = [layer, chip, 0, 11] #layer, chip, row, column
async def main(args):
        
    #Allow only -f or -d to be evoked - not both
    if args.fileInput and args.dirInput:
        logger.error("Input a single file with -f OR a single directory with -d... not both! Try running again")
        exit()

    print(f"{args.fileInput}")

    #Define boolean for args.fileInput
    f_in = True if args.fileInput is not None else False

    #Create objet
    #astro = astropix3(offline=True)
    print("creating object")
    astro = astepRun(inject=pixel)

    #Define output file path
    if args.outDir is not None:
        outpath = args.outDir
    elif f_in:
        try: #Mac path
            dirInd = args.fileInput.rindex('/')
        except ValueError: #Windows path
            dirInd = args.fileInput.rindex('\\')
        outpath = args.fileInput[:dirInd+1] #add 1 to keep final delimiter in path
    elif args.dirInput is not None:
        outpath = args.dirInput
    
    #Symmetrize structure
    inputFiles = [args.fileInput] if f_in else glob.glob(f'{args.dirInput}*.log')

    #Run over all input files
    for infile in inputFiles:
        print(f"infile={infile}")
        #Define output file name
        csvname = re.split(r'\\|/',infile)[-1][:-4] #split Mac or OS path; identify file name and eliminate '.log'
        csvpath = outpath + csvname + '_offline.csv'

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
        f=np.loadtxt(infile, skiprows=1, dtype=str)
        #f=np.loadtxt(infile, dtype=str)

        #isolate only bitstream without b'...' structure 
        #strings = [a[2:-1] for a in f[:,1]]
        strings = [a[2:-1] for a in f]
        #print(strings)#works!

        i = 0
        errors=0

        #astro.decode_readout(hit, inc) 

        for s in strings:
            #convert hex to binary and decode
            #rawdata = list(binascii.unhexlify(s)) #orig.
            #print(rawdata)
            try:
                hits = astro.decode_readout_offline(s, i, printer = args.printDecode) #2024.june.2 updated
                #hits = astro.decode_readout(rawdata, i, printer = args.printDecode) #orig.
                #print(hits)
                #hits.hittime = time.time()
                #hits.h_hit = time.time()
            except IndexError:
                errors += 1
                logger.warning(f"Decoding failed. Failure {errors} on readout {i}")
                hits = decode_fail_frame
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
        logger.info(f"Saving to {csvpath}")
        csvframe.to_csv(csvpath,sep='\t')




if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Post-run decoding')
    parser.add_argument('-f', '--fileInput', default=None, required=False,
                    help='Input data file to decode')

    parser.add_argument('-d', '--dirInput', default=None, required=False,
                    help='Input directory of data files to decode')

    #parser.add_argument('-o', '--outDir', default='/home/astropixadmin/astropix/AstroPixBenchData/chip-APS3-W2-S03_noise_scan/', required=False,
    parser.add_argument('-o', '--outDir', default=None, required=False,
                    help='Output Directory for all decoded datafiles. Defaults to directory raw data is saved in')

    parser.add_argument('-L', '--loglevel', type=str, choices = ['D', 'I', 'E', 'W', 'C'], action="store", default='I',
                    help='Set loglevel used. Options: D - debug, I - info, E - error, W - warning, C - critical. DEFAULT: D')

    parser.add_argument('-p', '--printDecode', action='store_true', default=True, required=False,
                    help='Print decoded info into terminal. Default: False')

    #python3.9 decode_postRun.py -f "../BeamTest0223/BeamData/Chip_230103/run17_protons120_20230224-090711.log" -o "../BeamTest0223/BeamData/Chip_230103/" -L D -p

    parser.add_argument
    args = parser.parse_args()

    # Sets the loglevel
    ll = args.loglevel
    if ll == 'D':
        loglevel = logging.DEBUG
    elif ll == 'I':
        loglevel = logging.INFO
    elif ll == 'E':
        loglevel = logging.ERROR
    elif ll == 'W':
        loglevel = logging.WARNING
    elif ll == 'C':
        loglevel = logging.CRITICAL
    
    # Logging - print to terminal only
    formatter = logging.Formatter('%(asctime)s:%(msecs)d.%(name)s.%(levelname)s:%(message)s')
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)

    logging.getLogger().addHandler(sh) 
    logging.getLogger().setLevel(loglevel)

    logger = logging.getLogger(__name__)

    
    #main(args)
    start_time = time.time()
    asyncio.run(main(args))
    end_time = time.time()
    print(f"{end_time-start_time} : time for this run")
