import asyncio
from astep import astepRun
import pandas as pd
import time
import binascii
import logging
import csv
import argparse #add

print("setup logger")
logname = "run.log"
formatter = logging.Formatter('%(asctime)s:%(msecs)d.%(name)s.%(levelname)s:%(message)s')
fh = logging.FileHandler(logname)
fh.setFormatter(formatter)
sh = logging.StreamHandler()
sh.setFormatter(formatter)
logging.getLogger().addHandler(sh) 
logging.getLogger().addHandler(fh)
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)

#pixel = [0,14]
#print("creating object")
#astro = astepRun(inject=pixel)

#noisepath = 'noise_scan_summary_' + time.strftime("%Y%m%d-%H%M%S") + '.csv'
#noisefile = open(noisepath,'w')
#noisewriter = csv.writer(noisefile)
#noisewriter.writerow(["Col\tRow\tCount"])

#pixel=[r,c]
#print("creating object")
#print(pixel)
#astro = astepRun(inject=pixel)

async def main(args,pixel):
    layer, chip = 0,0
    print("creating object")
    print(f"pixel[r,c]={pixel}")
    astro = astepRun(inject=pixel)

    print("opening fpga")
    #await astro.open_fpga()
    await astro.open_fpga(cmod=False, uart=False)

#    print("dump fpga") # add
#    await astro.dump_fpga() # add

    print("setup clocks")
    await astro.setup_clocks()

    print("setup spi")
    await astro.enable_spi()
    
    print("initializing asic")
    await astro.asic_init(yaml=args.yaml, analog_col=[layer, chip ,pixel[3]])
    #print(f"Header: {astro.get_log_header()}")

    print("initializing voltage")
    await astro.init_voltages(vthreshold=args.threshold) ## th in mV, same as previous fw

    #print("FUNCTIONALITY CHECK")
    #await astro.functionalityCheck(holdBool=True)

    print("update threshold")
    await astro.update_pixThreshold(layer, chip, vThresh=args.threshold)
    #await astro.update_pixThreshold(layer, chip,0)

    print("enable pixel")
    await astro.enable_pixel(layer, chip, pixel[2], pixel[3])
    
    #print("init injection")
    #await astro.init_injection(inj_voltage=300)

    print("final configs")
    print(f"Header: {astro.get_log_header(layer, chip)}")
    await astro.asic_configure(layer)
    
    print("setup readout")
    await astro.setup_readout(layer, autoread=0) #disable autoread


    i = 0
    fname = f"{args.name}_col{pixel[3]}_row{pixel[2]}_"
# add example_loop.py  
    # And here for the text files/logs
    bitpath = args.outdir + '/' + fname + time.strftime("%Y%m%d-%H%M%S") + '.log'
    #bitpath =  'noiselog'+strPix + time.strftime("_%Y%m%d_%H%M%S") + '.log'
    # textfiles are always saved so we open it up 
    bitfile = open(bitpath,'w')
    # Writes all the config information to the file
    #bitfile.write(astro.get_log_header())
    bitfile.write(str(args))
    bitfile.write("\n")

    if args.saveascsv: # Here for csv
        csvpath = args.outdir +'/' + fname + time.strftime("%Y%m%d-%H%M%S") + '.csv'
        csvframe =pd.DataFrame(columns = [
                'readout',
                'Chip ID',
                'payload',
                'location',
                'isCol',
                'timestamp',
                'tot_msb',
                'tot_lsb',
                'tot_total',
                'tot_us',
                'hittime'
        ])

    n_noise = 0
    event = 0
    if args.maxtime is not None: 
        end_time=time.time()+(args.maxtime) # second! not minute
    t0 = time.time()
    inc = -2
    dataf = b''
    start_intime = time.time()
    #while (time.time() < t0+5):
    while (time.time() < end_time): # Loop continues 
        
        buff, readout = await(astro.get_readout())
        if not sum(readout[0:2])==510: #avoid printing out if first 2 bytes are "ff ff" (string is just full of ones)
        #if buff>4:
            inc += 1
            if inc<0:
                continue
            hit = readout[:buff] 
            #print(f"hit={hit}, buff={buff}")
            print("print(binascii.hexlify(hit))")
            print(binascii.hexlify(hit))
            readout_data = readout[:buff]
            logger.info(binascii.hexlify(readout_data))
            #print(hex(readout[:buff]))
            #bitfile.write(f"{str(binascii.hexlify(readout))}\n")
            bitfile.write(f"{str(binascii.hexlify(readout_data))}\n")
            print("astro.decode_readout(hit, inc)")
            astro.decode_readout(hit, inc) 
            hits = astro.decode_readout(hit, inc)
        
            event += 1
            if hits.empty:
                continue
            else:
                n_noise += 1
                if args.saveascsv: csvframe = pd.concat([csvframe, hits])
        
        #await(astro.print_status_reg())
    end_intime = time.time()

    astro._wait_progress(2)
    #print("stop injection")
    #await astro.stop_injection()
    #print(f"***** TotEnv at [{pixel[1]},{pixel[0]}] = {event}")
    #print(f"***** noise at [{pixel[1]},{pixel[0]}] = {n_noise}")
    print(f"***** TotEnv at [c{pixel[3]},r{pixel[2]}] = {event}")
    print(f"***** noise at [c{pixel[3]},r{pixel[2]}] = {n_noise}")
    print(f"***** time in one pixel  = {end_intime - start_intime}")
    noisefile.write(f"{pixel[3]}\t{pixel[2]}\t{n_noise}\n") #col, row, noise
    noisefile.flush()

    print("read out buffer")
    buff, readout = await(astro.get_readout())
    #print(binascii.hexlify(readout))
    print(f"{buff} bytes in buffer")

    if args.saveascsv: 
        csvframe.index.name = "dec_order"
        csvframe.to_csv(csvpath) 

    bitfile.close() # Close open file       
    astro.close_connection() # Closes SPI
    logger.info("Program terminated successfully")



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Astropix Driver Code')
    parser.add_argument('-n', '--name', default='APS3-W08-S03', required=False,
                    help='Option to give additional name to output files upon running')

    parser.add_argument('-o', '--outdir', default='../../data/w08s03_noisescan', required=False,
                    help='Output Directory for all datafiles')

    parser.add_argument('-y', '--yaml', action='store', required=False, type=str, default = 'config_v3_none_may28', #Apr4. config/config_v3_none.yml_
                    help = 'filepath (in config/ directory) .yml file containing chip configuration. ')

    parser.add_argument('-c', '--saveascsv', action='store_true', default=False, required=False, 
                    help='save output files as CSV. If False, save as txt')
    
    parser.add_argument('-i', '--inject', action='store_true', default=False, required=False,
                    help =  'Turn on injection. Default: No injection')

    parser.add_argument('-v','--vinj', action='store', default = 0, type=float,
                    help = 'Specify injection voltage (in mV). DEFAULT 0')

    parser.add_argument('-t', '--threshold', type = int, action='store', default=200,
                    help = 'Threshold voltage for digital ToT (in mV). DEFAULT: 200mV')

    parser.add_argument('-r', '--maxruns', type=int, action='store', default=None,
                    help = 'Maximum number of readouts')

    parser.add_argument('-M', '--maxtime', type=float, action='store', default=5,
                    help = 'Maximum run time (in second). Default: 5s')

    parser.add_argument('-C', '--colrange', action='store', default=[0,34], type=int, nargs=2,
                    help =  'Loop over given range of columns. Default: 0 34')

    parser.add_argument('-R', '--rowrange', action='store', default=[0,34], type=int, nargs=2,
                    help =  'Loop over given range of rows. Default: 0 34')

    parser.add_argument
    args = parser.parse_args()
    
#    # Logging
#    loglevel = logging.INFO
#    formatter = logging.Formatter('%(asctime)s:%(msecs)d.%(name)s.%(levelname)s:%(message)s')
#    fh = logging.FileHandler(logname)
#    fh.setFormatter(formatter)
#    sh = logging.StreamHandler()
#    sh.setFormatter(formatter)
#
#    logging.getLogger().addHandler(sh) 
#    logging.getLogger().addHandler(fh)
#    logging.getLogger().setLevel(loglevel)
#
#    logger = logging.getLogger(__name__)

    # Save noise summary to output file
    noisepath = args.outdir + '/' + 'noise_scan_summary_' + args.name + '_' + time.strftime("%Y%m%d_%H%M%S") + '.csv'
    noisefile = open(noisepath,'w')
    noisewriter = csv.writer(noisefile)
    noisewriter.writerow(["Col\tRow\tCount"])

    #loop over full array by default, unless bounds are given as argument
    start_time = time.time()
    for r in range(args.rowrange[0],args.rowrange[1]+1,1):
        for c in range(args.colrange[0],args.colrange[1]+1,1):
            this_start_time = time.time()
            layer, chip = 0,0
            pixel = [layer, chip, r, c] #layer, chip, row, column
            asyncio.run(main(args,pixel))
            end_time = time.time()
            print(f"{c},{r} => {end_time-start_time} from start, {end_time - this_start_time } for loop")
            #time.sleep(2) # to avoid loss of connection to Nexys

    # Close noise scan summary file
    noisefile.close()
