"""
02/2023 Jihee Kim added number of events from csv file of beam measurements
06/2024 Bobae Kim updated
"""
import argparse
import csv
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np
import glob
import os
from matplotlib.colors import Normalize
import matplotlib as mpl
import asyncio
from astep import astepRun

plt.style.use('classic')

#async def main(args):
def main(args):
   
    ##### Find and Combine all data files #####################################
    # Path to beam data location
    path = args.datadir
    # Collect a list of multiple beamdata files
    #filename_list = [f"{path}/run{runnum}_*.csv" for runnum in args.runnolist]
    print(f"{args.datadir}, {args.inputfile}")
#    filename_list = [f"{path}/{runnum}" for runnum in args.inputfile]
#    # List multiple beamdata csv files
#    all_files = []
#    for fname in filename_list:
#        nfile = glob.glob(fname)
#        all_files += nfile
    ###########################################################################

    ##### Loop over data files and Find hit pixels #######################################################
    # List for hit pixels
#    pair = [] 
    # How many events are remained in one dataset
    tot_n_nans = 0
    tot_n_evts = 0
    n_evt_excluded = 0
    n_evt_used = 0
    # Loop over file
    #for f in all_files:
     # Read csv file
    f = args.datadir + args.inputfile
    print(f"Reading in {f}")
    df = pd.read_csv(f,sep='\t',on_bad_lines='skip')
    print(df.head())
    print(f"Reading is done")

    # Count per run
    # Total number of rows
    n_all_rows = df.shape[0]
    print(f"n_all_rows={n_all_rows}")
    # Non-NaN rows
    n_non_nan_rows = df['readout'].count() 
    # NaN events
    n_nan_evts = n_all_rows - n_non_nan_rows
    # Skip rows with NAN
    df = df.apply(pd.to_numeric, errors='coerce')
    df = df.dropna()
    # Change float to int for readout col
    df['readout'] = df['readout'].astype('Int64')
    # Get last number of readouts/events per run
    max_readout_n = df['readout'].iloc[-1]
    
    # Count for summary if multiple runs are read in
    ni = 0
    for ievt in range(0, max_readout_n+1, 1):
        dff = df.loc[(df['readout'] == ievt)] 
        if dff.empty:
            continue
        else:
            ni += 1
    n_evts = ni + n_nan_evts
    tot_n_evts += n_evts
    tot_n_nans += n_nan_evts

#    row = 1
#    col = 3
#    fig, ax = plt.subplots(row,col, figsize=(25, 7))

# for 1 event each ? #
    # Create dataframe for normalized time-over-threshold per pixel
    i = 0
    pixel = []
#    while i < 35:
   # Loop over readouts/events
    for ievt in range(0, max_readout_n+1, 1):
        pair = [] 
    #for ievt in range(0, 200, 1):
        # Collect one event
#        if args.exclusively:
#            dff = df. loc[(df['readout'] == ievt)] 
#        else:
#            dff = df.loc[(df['readout'] == ievt) & (df['payl'] == 4)]
        dff = df.loc[(df['readout'] == ievt) & (df['payload'] == 4) & (df['ChipID']==0) ]
        # Check if it's empty
        if dff.empty:
            continue

        # Check how many bad decoding lines within one event 
        n_no_good_decoding = 0
        for payload in dff['payload']:
            if payload != 4:
                n_no_good_decoding += 1 
        if n_no_good_decoding != 0:
            n_evt_excluded += 1
            pass
        # Match col and row to find hit pixel
        else:
            n_evt_used += 1
            # List column info of pixel within one event
            dffcol = dff.loc[dff['isCol'] == True]
            # List row info of pixel within one event
            dffrow = dff.loc[dff['isCol'] == False]
            # Matching conditions: timestamp and time-over-threshold (ToT)
            timestamp_diff = args.timestampdiff
            tot_time_limit = args.totdiff
            # Loop over col and row info to find a pair to define a pixel
            for indc in dffcol.index:
                for indr in dffrow.index:
                    if dffcol['tot_us'][indc] == 0 or dffrow['tot_us'][indr] ==0:
                        continue
                    if ((abs(dffcol['timestamp'][indc] - dffrow['timestamp'][indr]) < timestamp_diff) & 
                    (abs(dffcol['tot_us'][indc] - dffrow['tot_us'][indr])/dffcol['tot_us'][indc] < tot_time_limit)):
                        if (dffcol['location'][indc] > 34 or dffrow['location'][indr] > 34):
                            print(f"[Matching but Continue] col, row = {dffcol['location'][indc]},{dffrow['location'][indr]}")
                            continue
                        # Record hit pixels per event
                        pair.append([dffcol['location'][indc], dffrow['location'][indr], 
                                     dffcol['timestamp'][indc], dffrow['timestamp'][indr], 
                                     dffcol['tot_us'][indc], dffrow['tot_us'][indr],
                                    (dffcol['tot_us'][indc] + dffrow['tot_us'][indr])/2])
                        print(f"{ievt} evt: [Matching] col, row = {dffcol['location'][indc]},{dffrow['location'][indr]}, {dffcol['tot_us'][indc]}+{dffrow['tot_us'][indr]}")
        #print(f"{ievt} event: pair = {len(pair)}, {pair[0]},{pair[1]}")#, pair={pair}")
        if len(pair) == 0:
            continue

        x=[] 
        y=[] 
        totavg=[] 
        for i in range (0,len(pair),1):
            print(f"{i}th hits: {pair[i]}")
        x = [row[0] for row in pair]
        y = [row[1] for row in pair]
        totavg = [row[6] for row in pair]

        if len(pair) < args.hitspevt:
            continue

#    #works 1 plot
        fig=plt.figure()
        plt.hist2d(x,y,bins=35,range=[[0,35],[0,35]],weights=totavg,norm=Normalize(vmin=0,vmax=20),cmap='YlOrRd')
        hist, xedges, yedges, _ = plt.hist2d(x, y, bins=35, range=[[0, 35], [0, 35]], weights=totavg, norm=Normalize(vmin=0, vmax=20), cmap='Reds')
        for i in range(len(xedges)-1):
            for j in range(len(yedges)-1):
                if hist[i, j] == 0:
                    rect = plt.Rectangle((xedges[i], yedges[j]), xedges[i+1]-xedges[i], yedges[j+1]-yedges[j], fill=True, color='white')
                    plt.gca().add_patch(rect)
        plt.grid()
        plt.colorbar()
        #fig.colorbar(plt.set_label(label='ToT[ns]',weight='bold',size=18)
        #fig.colorbar(p1[3], ax=ax[0, 0]).set_label(label='Hits', weight='bold', size=18)
        #fig.suptitle(f"Evt{ievt}: totavg={totavg} display", fontweight = 'bold', fontsize=18)
        fig.suptitle(f"Evt{ievt}: {len(pair)} hits display", fontweight = 'bold', fontsize=18)
        #print(f'Evt{:0.0f}:totavg={:0.2f}display'.format(ievt,totavg))
        #fig.suptitle(titlestring, fontweight = 'bold', fontsize=18)
        plt.xlabel('col', fontsize=16)
        plt.ylabel('row', fontsize=16)
        plt.gca().set_facecolor('white')
        print(f"plt.savefig(f{args.outdir}/{args.inputfile}_Evt{ievt}_{len(pair)}hits_{args.beaminfo}_{args.name}__evtdisplay.png)")
        plt.savefig(f"{args.outdir}/{args.inputfile}_Evt{ievt}_{len(pair)}hits_{args.beaminfo}_{args.name}__evtdisplay.png")
        plt.close()



    # END OF PROGRAM
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Astropix Driver Code')
    parser.add_argument('-n', '--name', default='test', required=True,
                    help='chip ID that can be used in name of output file')

#    parser.add_argument('-l','--runnolist', nargs='+', required=True,
#                    help = 'List run number(s) you would like to see')

    parser.add_argument('-o', '--outdir', default='.', required=False,
                    help='output directory for all png files')

    parser.add_argument('-d', '--datadir', required=True, default =None,
                    help = 'input directory for beam data file')

    parser.add_argument('-if', '--inputfile', required=True, default =None,
                    help = 'input file')
    
    parser.add_argument('-td','--timestampdiff', type=float, required=False, default=2,
                    help = 'difference in timestamp in pixel matching <2')
   
    parser.add_argument('-tot','--totdiff', type=float, required=False, default=10.0,
                    help = 'error(abs(col.tot-row.tot)/col.tot)<10% in time over threshold [us] in pixel matching')
    
    parser.add_argument('-b', '--beaminfo', default='proton120GeV', required=False,
                    help='beam information ex) proton120GeV')

    parser.add_argument('-hit', '--hitspevt', type=int, default=100, required=False,
                    help='How many hits per events > 100 ')

#    parser.add_argument('--exclusively', default=False, action='store_true', 
#                    help='Throw entire data event if some within event has bad decoding')

    parser.add_argument
    args = parser.parse_args()

    #asyncio.run(main(args))
    main(args)
