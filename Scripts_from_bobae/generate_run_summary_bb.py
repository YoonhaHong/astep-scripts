"""
02/2023 Jihee Kim added number of events from csv file of beam measurements
06/2024 Bobae Kim updated
python3.12 scripts/generate_event_display_bb_update.py -d June2_TBpreparation/ -if June2_ftbf_may28FWSW_masked3col_t200_10m___20240602_144719_offline.csv -n test
> create June2_ftbf_may28FWSW_masked3col_t200_10m___20240602_144719_offline.csv_proton120GeV_test_diffTS2_diffToT10.png

#python3.12 scripts/generate_event_display_bb_update.py -n test -d /Users/gimbobae/Desktop/astropix_test/APS3w06s01/May31_ftbt/May28_updatedFWSW/ -if June2_ftbf_may28FWSW_masked3col_t200_1m___20240602_143319_offline.csv
#> create June2_ftbf_may28FWSW_masked3col_t200_1m___20240602_143319_offline.csv_proton120GeV_test_diffTS2_diffToT10.png
"""
import argparse
import csv
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np
import glob
import sys
import os
from matplotlib.colors import Normalize
import matplotlib as mpl
import asyncio
from astep import astepRun
plt.style.use('classic')

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
    pair = [] 
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
    df = pd.read_csv(f,sep=',')
    #print(df.head())
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

    # Loop over readouts/events
    for ievt in range(0, max_readout_n+1, 1):
        # Collect one event
#        if args.exclusively:
#            dff = df. loc[(df['readout'] == ievt)] 
#        else:
#            dff = df.loc[(df['readout'] == ievt) & (df['payl'] == 4)]
        dff = df.loc[(df['readout'] == ievt) & (df['payload'] == 4) & (df['ChipID'] == 0)]
        # Check if it's empty
        if dff.empty:
            continue

#        # Check how many bad decoding lines within one event 
#        n_no_good_decoding = 0
#        for payload in dff['payl']:
#            if payload != 4:
#                n_no_good_decoding += 1 
#        if n_no_good_decoding != 0:
#            n_evt_excluded += 1
#            pass
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
				#col0-3 skip
                    if ( dffcol['location'][indc] < 3 ):
                            continue
                    if (abs(dffcol['timestamp'][indc] - dffrow['timestamp'][indr]) < timestamp_diff) & (abs(dffcol['tot_us'][indc] - dffrow['tot_us'][indr])/dffcol['tot_us'][indc]*100 < tot_time_limit):
                        if (dffcol['location'][indc] > 34 or dffrow['location'][indr] > 34):
                            print(f"[Matching but Continue] col.location, row.location = {dffcol['location'][indc]},{dffrow['location'][indr]}")
                            continue
                        # Record hit pixels per event
                        average_tot = ((dffcol['tot_us'][indc] + dffrow['tot_us'][indr])/2)
                        pair.append([dffcol['readout'][indc], dffcol['location'][indc], dffrow['location'][indr], dffcol['timestamp'][indc], dffrow['timestamp'][indr], dffcol['tot_us'][indc], dffrow['tot_us'][indr], ((dffcol['tot_us'][indc] + dffrow['tot_us'][indr])/2)])
                        dffrow = dffrow.drop(indr)
                        break
                        #pair.append([dffcol['location'][indc], dffrow['location'][indr], dffcol['timestamp'][indc], dffrow['timestamp'][indr], dffcol['tot_us'][indc], dffrow['tot_us'][indr]])
#                    if ((abs(dffcol['TS'][indc] - dffrow['TS'][indr]) < timestamp_diff) & 
#                    (abs(dffcol['tot_us'][indc] - dffrow['tot_us'][indr]) < tot_time_limit)):
#                        # Record hit pixels per event
#                        pair.append([dffcol['loc'][indc], dffrow['loc'][indr], 
#                                     dffcol['TS'][indc], dffrow['TS'][indr], 
#                                     dffcol['tot_us'][indc], dffrow['tot_us'][indr],
#                                    (dffcol['tot_us'][indc] + dffrow['tot_us'][indr])/2])
    print("... Matching is done!")
    ######################################################################################################

    ##### Summary of how many events being used ###################################################
    nevents = '%.2f' % ((n_evt_used/(tot_n_evts)) * 100.)
    nnanevents = '%.2f' % ((tot_n_nans/(tot_n_evts)) * 100.)
    n_empty = tot_n_evts - n_evt_used - tot_n_nans
    nemptyevents = '%.2f' % ((n_empty/(tot_n_evts)) * 100.)
    print("Summary:")
    print(f"{tot_n_nans} of {tot_n_evts} events were found as NaN...")
    print(f"{n_empty} of {tot_n_evts} events were found as empty...")
    print(f"{n_evt_used} of {tot_n_evts} events were processed...")
    print(f"Matching hit: {len(pair)} ")
#        print(f"{n_evt_excluded} of {tot_n_evts} events were excluded because of bad payload...")
#        print(f"{nevents}[%] are used in exclusively mode...")
#        print(f"{nnanevents}[%] are trashed...")
#        print(f"{nemptyevents}[%] are emptied...")
#        print(f"{nevents}[%] are used...")
#        print(f"{nnanevents}[%] are trashed...")
#        print(f"{nemptyevents}[%] are emptied...")

    ###############################################################################################
    # Masking pixels
    # Read noise scan summary file
#    disablepix=[]
#    if args.noisescaninfo is not None:
#        print("masking pixels")
#        noise_input_file = open(args.noisescaninfo, 'r')
#        lines = noise_input_file.readlines()
#    # Get counts
#        count_vals=0
#        for line in lines:
#            noise_val = int(line.split('\t')[2])
#            col_val = int(line.split('\t')[0])
#            row_val = int(line.split('\t')[1])
#            if noise_val > 100:
#                disablepix.append([col_val, row_val,1])
#    pixs=pd.DataFrame(disablepix, columns=['col','row','disable'])
#    print(pixs)
#    npixel = '%.2f' % ( (1-(len(pixs)/1225)) * 100.)
#    print(f"{len(pixs)}, {npixel}% active")
    disablepix=[]
    for r in range(0,35,1):
        for c in range(0,3,1): # 0-4 col
                disablepix.append([c, r, 1])
    #disablepix.append([14, 31, 1])
    pixs=pd.DataFrame(disablepix, columns=['col','row','disable'])
    print(pixs)
    npixel = '%.2f' % ( (1-(len(pixs)/1225)) * 100.)
    print(f"{len(pixs)}, {npixel}% active")
     
    ##### Create hit pixel dataframes #######################################################
    # Hit pixel information for all events
    #dffpair = pd.DataFrame(pair, columns=['readout', 'col', 'row','timestamp_col', 'timestamp_row', 'tot_us_col', 'tot_us_row', 'avg_tot_us'])
    dffpair = pd.DataFrame(pair, columns=['readout','col','row','timestamp_col', 'timestamp_row', 'tot_us_col', 'tot_us_row', 'avg_tot_us'])
    dffpair.to_csv(f"MatchingHitinfo_{args.inputfile}", sep='\t', index=False)
    # Create dataframe for number of hits 
    dfpair = dffpair[['col','row']].copy()
    dfpairc = dfpair[['col','row']].value_counts().reset_index(name='hits')
    # How many hits are collected and shown in a plot
    nhits = dfpairc['hits'].sum()
    # mean of avg_tot_us, each col, row
    grouped_avg = dffpair.groupby(['col', 'row'])['avg_tot_us'].mean().reset_index(name='avg')
    print(f"average_tot = {grouped_avg}")

    if grouped_avg.empty:
        print("no maching hit at all. exit code")
        sys.exit()
    
    # Generate Plot - Pixel hits
    #fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(20, 8))
    row = 2
    col = 3
    fig, ax = plt.subplots(row, col, figsize=(20, 10))
    for irow in range(0, row):
        for icol in range(0, col):
            for axis in ['top','bottom','left','right']:
                ax[irow, icol].spines[axis].set_linewidth(1.5)

    #p1 = ax[0, 0].hist2d(x=dfpairc['col'], y=dfpairc['row'], bins=35, range=[[0,35],[0,35]], weights=dfpairc['hits'], cmap='YlOrRd', cmin=1.0, norm=matplotlib.colors.LogNorm())
    p1 = ax[0, 0].hist2d(x=dfpairc['col'], y=dfpairc['row'], bins=35, range=[[0,35],[0,35]], weights=dfpairc['hits'], cmap='YlOrRd', cmin=1.0)
    fig.colorbar(p1[3], ax=ax[0, 0]).set_label(label='Hit Counts', weight='bold', size=14)
    ax[0,0].grid()
    ax[0, 0].set_xlabel('Col', fontweight = 'bold', fontsize=14)
    ax[0, 0].set_ylabel('Row', fontweight = 'bold', fontsize=14)
    ax[0, 0].xaxis.set_tick_params(labelsize = 14)
    ax[0, 0].yaxis.set_tick_params(labelsize = 14)

    p2 = ax[0, 1].hist2d(x=pixs['col'], y=pixs['row'], bins=35, range=[[0.,35],[0,35]], weights=pixs['disable'], norm=Normalize(vmin=0,vmax=1),cmap='Greys')
    fig.colorbar(p2[3], ax=ax[0, 1]).set_label(label='Masked', weight='bold', size=14)
    ax[0,1].grid()
    ax[0, 1].set_xlabel('Col', fontweight = 'bold', fontsize=14)
    ax[0, 1].set_ylabel('Row', fontweight = 'bold', fontsize=14)
    ax[0, 1].xaxis.set_tick_params(labelsize = 14)
    ax[0, 1].yaxis.set_tick_params(labelsize = 14)

#p1+p2 overlay plot
    p3 = ax[0,2].hist2d(x=pixs['col'], y=pixs['row'], bins=35, range=[[0.,35],[0,35]], weights=pixs['disable'], norm=Normalize(vmin=0,vmax=1),cmap='Greys')
    #p3 = ax[0,2].hist2d(x=dfpairc['col'], y=dfpairc['row'], bins=35, range=[[0,35],[0,35]], weights=dfpairc['hits'], cmap='YlOrRd', cmin=1.0, norm=matplotlib.colors.LogNorm())
    p3 = ax[0,2].hist2d(x=dfpairc['col'], y=dfpairc['row'], bins=35, range=[[0,35],[0,35]], weights=dfpairc['hits'], cmap='YlOrRd', cmin=1.0)
#    masked_weights = np.ma.masked_where(pixs['disable'] != 1, pixs['disable'])
#    p4 = ax[0, 2].hist2d(x=pixs['col'], y=pixs['row'], bins=35, range=[[0., 35], [0, 35]], 
#                     weights=masked_weights, norm=Normalize(vmin=0, vmax=1), cmap='Greys', alpha=1.)
    #col_disable_1 = pixs['col'][pixs['disable'] == 1]
    #row_disable_1 = pixs['row'][pixs['disable'] == 1]
    #ax[0, 2].scatter(col_disable_1, row_disable_1, color='black', s=10, label='Disabled (1)')

#    h2, xedges, yedges = np.histogram2d(pixs['col'], pixs['row'], bins=35, range=[[0., 35], [0, 35]], 
#                                    weights=np.where(pixs['disable'] == 1, 1, 0))
#    masked_weights = np.ma.masked_where(h2 == 0, h2)
#    masked_weights = np.ma.masked_where(np.isnan(h2), h2)
#    X, Y = np.meshgrid(xedges, yedges)
#    ax[0, 2].pcolormesh(X, Y, masked_weights.T, cmap='gray', edgecolors='face', vmin=0, vmax=1)


#    h2, xedges, yedges = np.histogram2d(pixs['col'], pixs['row'], bins=35, range=[[0., 35], [0, 35]], 
#                                        weights=np.where(pixs['disable'] == 1, 1, 0))
#    h2 = np.ma.masked_where(h2 == 0, h2)  # 0인 값을 마스킹
#    
#    # 두 번째 히스토그램을 imshow로 그리기
#    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
#    ax[0, 2].imshow(h2.T, cmap='gray', extent=extent, origin='lower', interpolation='none', alpha=1.0)
    # 두 번째 데이터 히스토그램
#    h2, xedges, yedges = np.histogram2d(pixs['col'], pixs['row'], bins=35, range=[[0., 35], [0, 35]], 
#                                        weights=np.where(pixs['disable'] == 1, 1, 0))
#    
#    # col 값이 0부터 3 사이에 있는 경우 모든 빈을 1로 설정
#    h2[:, :4] = 1
#    # 0인 값을 마스킹
#    h2 = np.ma.masked_where(h2 == 0, h2)
#    
#    # 두 번째 히스토그램을 imshow로 그리기
#    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
#    ax[0, 2].imshow(h2.T, cmap='gray', extent=extent, origin='lower', interpolation='none', alpha=1.0)



#    p3 = ax[0,2].hist2d(x=pixs['col'], y=pixs['row'], bins=35, range=[[0.,35],[0,35]], weights=pixs['disable'], norm=Normalize(vmin=0,vmax=1),cmap='Greys')
#    p3 = ax[1, 0].hist2d(x=dfpixel['col'], y=dfpixel['row'], bins=35, range=[[-0.5,34.5],[-0,35]], weights=dfpixel['norm_sum_avg_tot_us'], cmap='Blues',cmin=1.0, norm=matplotlib.colors.LogNorm())
    fig.colorbar(p3[3], ax=ax[0, 2]).set_label(label='Hit Counts', weight='bold', size=14)
    ax[0,2].grid()
    ax[0,2].set_xlabel('Col', fontweight = 'bold', fontsize=14)
    ax[0,2].set_ylabel('Row', fontweight = 'bold', fontsize=14)
    ax[0,2].xaxis.set_tick_params(labelsize = 14)
    ax[0,2].yaxis.set_tick_params(labelsize = 14)

    p4 = ax[1, 0].hist2d(x=grouped_avg['col'], y=grouped_avg['row'], bins=35, range=[[0,35],[0,35]], weights=grouped_avg['avg'], cmap='Blues',vmin=0.0)
    fig.colorbar(p4[3], ax=ax[1, 0]).set_label(label='Avg.ToT [us]', weight='bold', size=14)
    ax[1, 0].grid()
    ax[1, 0].set_xlabel('Col', fontweight = 'bold', fontsize=14)
    ax[1, 0].set_ylabel('Row', fontweight = 'bold', fontsize=14)
    ax[1, 0].xaxis.set_tick_params(labelsize = 14)
    ax[1, 0].yaxis.set_tick_params(labelsize = 14)

    p5 = ax[1, 1].hist(x=dffpair['avg_tot_us'], bins=22, range=(0, 22), color='blue', edgecolor='black')
#    fig.colorbar(p5[3], ax=ax[1, 2]).set_label(label='Average Normalized Time-over-Threshold[us]', weight='bold', size=18)
    ax[1, 1].grid()
    ax[1, 1].set_xlabel('ToT [us]', fontweight = 'bold', fontsize=14)
    ax[1, 1].set_ylabel('Counts', fontweight = 'bold', fontsize=14)
    ax[1, 1].xaxis.set_tick_params(labelsize = 14)
    ax[1, 1].yaxis.set_tick_params(labelsize = 14)

    # Text
    ax[1, 2].set_axis_off()
    ax[1, 2].text(0.1, 0.85, f"Beam: {args.beaminfo}", fontsize=15, fontweight = 'bold');
    ax[1, 2].text(0.1, 0.80, f"ChipID: {args.name}", fontsize=15, fontweight = 'bold');
    ax[1, 2].text(0.1, 0.40, f"Available Pixels: {npixel}%", fontsize=15);
#    ax[0, 2].text(0.1, 0.75, f"Runs: {runnum}", fontsize=15, fontweight = 'bold');
    ax[1, 2].text(0.1, 0.70, f"Events: {tot_n_evts}", fontsize=15);#, fontweight = '');
    ax[1, 2].text(0.1, 0.60, "Processed below", fontsize=15, fontweight = 'bold');
    ax[1, 2].text(0.1, 0.55, f"conditions: <{args.timestampdiff} timestamp and <{args.totdiff}% in ToT", fontsize=15);#, fontweight = '');
    ax[1, 2].text(0.1, 0.50, f"nevents: {nevents}%", fontsize=15);#, fontweight = '');
    ax[1, 2].text(0.1, 0.45, f"nhits: {nhits}", fontsize=15);#, fontweight = '');

    ax[0, 0].set_title(f"Hit Map", fontweight = 'bold', fontsize=14)
    ax[0, 1].set_title(f"Masked pixel (v3QuadChip_layer0_chip0)", fontweight = 'bold', fontsize=14)
    ax[0, 2].set_title(f"Hit Map with Masked pixels", fontweight = 'bold', fontsize=14)
    ax[1, 0].set_title(f"Avg.ToT per pixel", fontweight = 'bold', fontsize=14)
    ax[1, 1].set_title(f"Avg.ToT for all pixels", fontweight = 'bold', fontsize=14)
    #plt.savefig(f"{args.outdir}/{args.beaminfo}_{args.name}_run_{runnum}_evtdisplay.png")
    #print(f"{args.outdir}/{args.beaminfo}_{args.name}_run_{runnum}_evtdisplay.png was created...")

    plt.savefig(f"{args.outdir}/{args.inputfile}_{args.beaminfo}_{args.name}_diffTS{args.timestampdiff}_diffToT{args.totdiff}.png")
    print(f"{args.inputfile}_{args.beaminfo}_{args.name}_diffTS{args.timestampdiff}_diffToT{args.totdiff}.png was created...")
    # Draw Plot
    plt.show()

    # END OF PROGRAM
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Astropix Driver Code')
    parser.add_argument('-n', '--name', default='v3QuadChip_layer0_chip0', required=False,
                    help='chip ID that can be used in name of output file (default=APSw06s01_TB0624)')

#    parser.add_argument('-l','--runnolist', nargs='+', required=True,
#                    help = 'List run number(s) you would like to see')

    parser.add_argument('-o', '--outdir', default='.', required=False,
                    help='output directory for all png files')

    parser.add_argument('-d', '--datadir', required=True, default =None,
                    help = 'input directory for beam data file')

    parser.add_argument('-if', '--inputfile', required=True, default =None,
                    help = 'input file')
    
    parser.add_argument('-td','--timestampdiff', type=float, required=False, default=2,
                    help = 'difference in timestamp in pixel matching (default:col.ts-row.ts<2)')
   
    parser.add_argument('-tot','--totdiff', type=float, required=False, default=10,
                    help = 'error in ToT[us] in pixel matching (default:(col.tot-row.tot)/col.tot<10%)')
    
    parser.add_argument('-b', '--beaminfo', default='NoSource', required=False,
                    help='beam information ex) proton120GeV')

    parser.add_argument('-ns', '--noisescaninfo', action='store', required=False, type=str, default ='.',
                    help = 'filepath noise scan summary file containing chip noise infomation.')

    parser.add_argument
    args = parser.parse_args()

    main(args)
