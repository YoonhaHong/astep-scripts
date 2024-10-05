"""
02/2023 Jihee Kim added making plots from csv file of beam measurements
"""
import argparse
import csv
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np
import glob
import os

def main(args):
   
    # Path to beamdata location
    path = args.datadir
    print(f"{args.datadir}, {args.inputfile}")

#    # Collect a list of multiple beamdata files
#    filename_list = [f"{path}/run{runnum}_*.csv" for runnum in args.runnolist]
#    # Read multiple beamdata csv files
#    all_files = []
#    for fname in filename_list:
#        nfile = glob.glob(fname)
#        all_files += nfile
     

    # List for hit pixels
    pair = []
    # How many events are used in plot
    n_evt_used = 0 
    tot_n_readouts = 0 
    # Loop over file
#    for f in all_files:
        # Read csv file
    f = args.datadir + args.inputfile
    df = pd.read_csv(f,sep='\t')
    print(f"Reading in {f}")
    # Skip rows with NAN
    df = df.apply(pd.to_numeric, errors='coerce')
    df = df.dropna()
    # Changed float to int for readout col
    df['readout'] = df['readout'].astype('Int64')

    #add
    print(df.head())
    print(df.columns)
    # 'readout' 열 존재 여부 확인 및 길이 확인
    if 'readout' in df.columns:
        if len(df['readout']) > 0:
            max_n_readouts = df['readout'].iloc[-1]
            print(f"Max readout value: {max_n_readouts}")
        else:
            print("The 'readout' column is empty.")
    else:
        print("The 'readout' column does not exist.")


    # Get total number of readouts/events per run
    max_n_readouts = df['readout'].iloc[-1]
    tot_n_readouts += max_n_readouts
    print(f"{max_n_readouts} events were found...")
    # Loop over readouts/events
    for ievt in range(0, max_n_readouts+1, 1):
        # Collect one event
        #if args.exclusively:
        #    dff = df. loc[(df['readout'] == ievt)] 
        #else:
        #    dff = df.loc[(df['readout'] == ievt) & (df['payl'] == 4)]
        dff = df.loc[(df['readout'] == ievt) & (df['payload'] == 4) & (df['ChipID'] == 0)]
        # Check how many bad decoding lines within one event 
        n_no_good_decoding = 0
        for payload in dff['payload']:
            if payload != 4:
                n_no_good_decoding += 1 
    
        if n_no_good_decoding != 0:
            pass
        else:
            n_evt_used += 1
            # List column info of pixel within one event
            dffcol = dff.loc[dff['isCol'] == True]
            # List row info of pixel within one event
            dffrow = dff.loc[dff['isCol'] == False]
            # time difference in time over threshold (tot) in us to define a pixel
            tot_time_limit = args.totdiff # before more exclusive cut on 0.3
            timestamp_diff = args.timestampdiff# before more exclusive cut on exact same
            # Loop over col and row info to find a pair to define a pixel
            for indc in dffcol.index:
                for indr in dffrow.index:
                    # Before more exclusive cut on timestamp like exact same
                    #print(f"dffcol['tot_us'][indc]={dffcol['tot_us'][indc]},dffrow['tot_us'][indr]={dffrow['tot_us'][indr]}")
                    if dffcol['tot_us'][indc] == 0 or dffrow['tot_us'][indr] ==0:
                        continue
                    if (abs(dffcol['timestamp'][indc] - dffrow['timestamp'][indr]) < timestamp_diff) & (abs(dffcol['tot_us'][indc] - dffrow['tot_us'][indr])/dffcol['tot_us'][indc]*100 < tot_time_limit):
                        if (dffcol['location'][indc] > 34 or dffrow['location'][indr] > 34):
                            print(f"[Matching but Continue] col.location, row.location = {dffcol['location'][indc]},{dffrow['location'][indr]}")
                            continue
                        # Record hit pixels per event
                        pair.append([dffcol['location'][indc], dffrow['location'][indr], dffcol['timestamp'][indc], dffrow['timestamp'][indr], dffcol['tot_us'][indc], dffrow['tot_us'][indr]])

    # Calculate how many events are used
    nevents = '%.2f' % ((n_evt_used/(tot_n_readouts + 1)) * 100.)
    # Hit pixel information for all events
    dffpair = pd.DataFrame(pair, columns=['col', 'row', 'timestamp_col', 'timestamp_row', 'tot_us_col', 'tot_us_row'])
    # For heatmap plot, it needs col, row, and hits 
    dfpair = dffpair[['col','row']].copy()
    dfpairc = dfpair[['col','row']].value_counts().reset_index(name='hits')
    print(dfpairc.to_string())
    # How many hits are collected and shown in a plot
    nhits = dfpairc['hits'].sum()

    print("draw plot")
    # Print run number(s)
    #runnum = '-'.join(args.runnolist)
    # Generate Plot - Pixel hits
    #fig, (ax1, ax2, ax3) = plt.subplots(ncols=3, figsize=(25, 6))
    fig, ax1 = plt.subplots( figsize=(8, 6))
    #p1 = ax1.hist2d(x=dfpairc['col'],y=dfpairc['row'],bins=35,range=[[-0.5,34.5],[-0.5,34.5]], weights=dfpairc['hits'], cmap='YlOrRd',cmin=1.0, norm=matplotlib.colors.LogNorm())
    p1 = ax1.hist2d(x=dfpairc['col'],y=dfpairc['row'],bins=35,range=[[0,35],[0,35]], weights=dfpairc['hits'], cmap='YlOrRd',cmin=1.0, norm=matplotlib.colors.LogNorm())
    plt.grid()
    fig.colorbar(p1[3], ax=ax1).set_label(label='Hit Counts', size=15)
    ax1.set_xlabel('Col', fontsize=15)
    ax1.set_ylabel('Row', fontsize=15)
    ax1.set_title(f"{args.beaminfo} {args.name} \n Used events/Total events =({n_evt_used}/{tot_n_readouts+1}): {nhits} hit counts shown", fontsize=12)
#    if args.exclusively:
#        ax1.set_title(f"{args.beaminfo} {args.name} \n Used events/Total events =({n_evt_used}/{tot_n_readouts+1}): {nhits} hit counts shown exclusively", fontsize=12)
#    else:
#        ax1.set_title(f"{args.beaminfo} {args.name} \n Used events/Total events =({n_evt_used}/{tot_n_readouts+1}): {nhits} hit counts shown", fontsize=12)
#    # Draw Plot
    print("plt.savefig()")
    plt.savefig(f"HitMap_{args.inputfile}_{args.beaminfo}_{args.name}__display.png")
#    print("plt.show()")
#    plt.show()
    #plt.savefig(f"accumulatedHitCounts_{args.beaminfo}_{args.name}__display.png")
    #print(f"plt.savefig(f{args.outdir}/accumulatedHitCounts_{args.beaminfo}_{args.name}__display.png)")
#    plt.close(fig)


#    # Path to noise scan data location
#    path = args.noisedir
#    # Find noise scan data and Read
#    filename = args.noisedir + '/noise_scan_summary_' + args.name +'*.csv'
#    file = glob.glob(filename)

#    for f in file:
#        dfnoise = pd.read_csv(f)
#    dfnoise['Masking'] = 0
#    dfnoise['Masking'] = np.where(dfnoise['Count'] > args.noisethreshold, 1, dfnoise['Masking']) 
#    # Calculate how many pixels are good
#    npixels = '%.2f' % ((dfnoise['Masking'].value_counts()[0]/1225.) * 100.)

#    # Generate Plot - Masking Map on specific chip
#    p2 = ax2.hist2d(x=dfnoise['Col'],y=dfnoise['Row'],bins=35,range=[[-0.5,34.5],[-0.5,34.5]], weights=dfnoise['Masking'], cmap='Greys')
#    fig.colorbar(p2[3], ax=ax2).set_label(label='Masking', size=15)
#    ax2.set_xlabel('Col', fontsize=15)
#    ax2.set_ylabel('Row', fontsize=15)
#    if args.exclusively:
#        ax2.set_title(f"{args.beaminfo} {args.name} masking map \n with noise threshold {args.noisethreshold} ({npixels}%)", fontsize=15)
#    else:
#        ax2.set_title(f"{args.beaminfo} {args.name} masking map \n with noise threshold {args.noisethreshold} ({npixels}%)", fontsize=15)
#    # Generate Plot - Masking over Pixel Hits
#    p3 = plt.hist2d(x=dfpairc['col'],y=dfpairc['row'],bins=35,range=[[-0.5,34.5],[-0.5,34.5]], weights=dfpairc['hits'], cmap='YlOrRd',cmin=1.0, norm=matplotlib.colors.LogNorm())
#    #p3 = plt.hist2d(x=dfpairc['col'],y=dfpairc['row'],bins=35,range=[[-0.5,34.5],[-0.5,34.5]], weights=dfpairc['hits'], cmap='YlOrRd',cmin=1.0)
#    plt.hist2d(x=dfnoise['Col'],y=dfnoise['Row'],bins=35,range=[[-0.5,34.5],[-0.5,34.5]], weights=dfnoise['Masking'], cmap='binary', alpha=0.3)
#    fig.colorbar(p3[3], ax=ax3).set_label(label='Hits', size=15)
#    ax3.set_xlabel('Col', fontsize=15)
#    ax3.set_ylabel('Row', fontsize=15)
#    if args.exclusively:
#        ax3.set_title(f"{args.beaminfo} {args.name} Run with masking exclusively", fontsize=15)
#    else:
#        ax3.set_title(f"{args.beaminfo} {args.name} Run with masking", fontsize=15)
#    # Save figure
#    if args.exclusively:
#        plt.savefig(f"{args.outdir}/{args.beaminfo}_{args.name}_run__exclusively.png")
#        print(f"{args.outdir}/{args.beaminfo}_{args.name}_run__exclusively.png was created...")
#    else:
#        plt.savefig(f"{args.outdir}/{args.beaminfo}_{args.name}_run_.png")
#        print(f"{args.outdir}/{args.beaminfo}_{args.name}_run_.png was created...")
#    # Draw Plot
#    plt.show()
#    plt.savefig(f"{args.outdir}/accumulatedHitCounts_{args.beaminfo}_{args.name}__display.png")

    # END OF PROGRAM
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Astropix Driver Code')
    parser.add_argument('-n', '--name', default=None, required=True,
                    help='chip ID that can be used in name of output file ex) chip230103 or APCv2-230202')

    parser.add_argument('-o', '--outdir', default=None, required=False,
                    help='output directory for all png files')

    parser.add_argument('-d', '--datadir', required=True, default =None,
                    help = 'input directory for beam data file')
    parser.add_argument('-if', '--inputfile', required=True, default =None,
                    help = 'input file')
    
    parser.add_argument('-s', '--noisedir', required=False, default = None,
                    help = 'input directory for noise scan summary file to mask pixels')

#    parser.add_argument('-l','--runnolist', nargs='+', required=True,
#                    help = 'List run number(s) you would like to see')

    parser.add_argument('-t','--noisethreshold', type=int, required=False, default=5,
                    help = 'noise threshold to determine which pixel to be masked')
    
    parser.add_argument('-td','--timestampdiff', type=float, required=False, default=2,
                    help = 'difference in timestamp in pixel matching')
   
    parser.add_argument('-tot','--totdiff', type=float, required=False, default=10,
                    help = 'difference in time over threshold [us] in pixel matching')
    
    parser.add_argument('-b', '--beaminfo', default='proton120GeV', required=False,
                    help='beam information ex) proton120GeV')
    
    parser.add_argument('--exclusively', default=False, action='store_true', 
                    help='Throw entire data event if some within event has bad decoding')

    parser.add_argument
    args = parser.parse_args()

    main(args)
