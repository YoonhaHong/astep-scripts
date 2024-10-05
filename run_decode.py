import asyncio
from astep import astepRun
import time
import binascii
import logging
import csv
import argparse #add
import pandas as pd
import sys
import logging

layer, chip = 0,0
pixel = [layer, chip, 0, 11] #layer, chip, row, column
async def main(args):

    print("setup logger")

    fname = f"THR{args.threshold}_{args.name}_{time.strftime("%Y%m%d_%H%M%S")}" 
    bitpath = args.outdir+"/run_"+fname+".log"
    logname = args.outdir+"/runlog_"+fname+".log"
    csvpath = args.outdir+'/'+fname+".csv"

    bitfile = open(bitpath,'w')
    
    formatter = logging.Formatter('%(asctime)s:%(msecs)d.%(name)s.%(levelname)s:%(message)s')
    fh = logging.FileHandler(logname)
    fh.setFormatter(formatter)
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logging.getLogger().addHandler(sh) 
    logging.getLogger().addHandler(fh)
    logging.getLogger().setLevel(logging.INFO)
    logger = logging.getLogger(__name__)

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


    print("creating object")
#    print(f"pixel[r,c]={pixel}")
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
    print(f"Header: {astro.get_log_header(layer, chip)}")

    print("initializing voltage")
    #await astro.init_voltages() ## th in mV
    await astro.init_voltages(vthreshold=args.threshold) ## th in mV

    #print("FUNCTIONALITY CHECK")
    #await astro.functionalityCheck(holdBool=True)

    #print("update threshold")
    await astro.update_pixThreshold(layer, chip, vThresh=args.threshold)

    for r in range(0,35,1):
        for c in range(3,35,1):
            await astro.enable_pixel(layer,chip,r,c)
    """
    # Masking pixels
    # Read noise scan summary file
    if args.noisescaninfo is not None:
        print("masking pixels")
        noise_input_file = open(args.noisescaninfo, 'r')
        lines = noise_input_file.readlines()
    #print(lines[0])
        del lines[0] # remove header
    # Get counts
        count_vals=0
        for line in lines:
            noise_val = int(line.split('\t')[2])
            col_val = int(line.split('\t')[0])
            row_val = int(line.split('\t')[1])
            if noise_val > 10:
                #astro.disable_pixel(col_val,row_val)
                await astro.disable_pixel(row_val,col_val)
                print("(",col_val,",",row_val,")=",noise_val," larger than 10")
                count_vals = count_vals+1
# for beam_test.py
            else:
                await astro.enable_pixel(row_val,col_val)
        print(count_vals, " pixels are disable !")
        print("Active pixels ~ ",1-(count_vals/(35*35)), " %.")
    """



    #print("init injection")
    #await astro.init_injection(inj_voltage=300)

    print("final configs")
    #print(f"Header: {astro.get_log_header()}")
    #await astro.asic_configure()
    print(f"Header: {astro.get_log_header(layer, chip)}")
    await astro.asic_configure(layer)
    
    print("setup readout")
    #await astro.setup_readout(0, autoread=0) #disable autoread
    await astro.setup_readout(layer, autoread=0) #disable autoread


#    i = 0
#    #strPix = "_col"+str(pixel[1])+"_row"+str(pixel[0])
#    strPix = "_"
#    fname=strPix if not args.name else args.name+strPix+"_"
## add example_loop.py  
#    # And here for the text files/logs
#    bitpath = args.outdir + '/' + fname + time.strftime("%Y%m%d_%H%M%S") + '.log'
#    #bitpath =  'noiselog'+strPix + time.strftime("_%Y%m%d_%H%M%S") + '.log'
#    # textfiles are always saved so we open it up 
#    bitfile = open(bitpath,'w')
#    # Writes all the config information to the file
#    bitfile.write(astro.get_log_header(layer, chip))
#    bitfile.write(str(args))
#    bitfile.write("\n")


    n_noise = 0
    event = 0
    if args.maxtime is not None: 
        end_time=time.time()+(args.maxtime) # second! not minute
    t0 = time.time()
    dataf = b''
    inc = -2
    start_intime = time.time()
    while (time.time() < end_time): # Loop continues 
        buff, readout = await(astro.get_readout())
        if not sum(readout[0:2])==510: #avoid printing out if first 2 bytes are "ff ff" (string is just full of ones)
        #if buff>4:
            inc += 1
            if inc<0:
                continue
            hit = readout[:buff] 
            #print(f"hit={hit}, buff={buff}")
            #print("print(binascii.hexlify(hit))")
            #print(binascii.hexlify(hit))
            readout_data = readout[:buff]
            logger.info(binascii.hexlify(readout_data))
            #print(hex(readout[:buff]))
            #bitfile.write(f"{str(binascii.hexlify(readout))}\n")
            bitfile.write(f"{str(binascii.hexlify(readout_data))}\n")
            #print("astro.decode_readout(hit, inc)")
            astro.decode_readout(hit, inc) 
            hits = astro.decode_readout(hit, inc)
            csvframe = pd.concat([csvframe, hits])
        
            event += 1        

        
    end_intime = time.time()

    astro._wait_progress(5)
    #print("stop injection")
    #await astro.stop_injection()
    print(f"***** TotEnv = {event}")
    print(f"***** time = {end_intime - start_intime}")
#add example_loop.py

    print("read out buffer")
    buff, readout = await(astro.get_readout())
    print(binascii.hexlify(readout))
    print(f"{buff} bytes in buffer")

    csvframe.index.name = "dec_order"
    csvframe.to_csv(csvpath, sep='\t') 

    bitfile.close() # Close open file       
    astro.close_connection() # Closes SPI
    logger.info("Program terminated successfully")




if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Astropix Driver Code')
    parser.add_argument('-n', '--name', default='APS3-W08-S03', required=False,
                    help='Option to give additional name to output files upon running')

    parser.add_argument('-o', '--outdir', default='../../data', required=False,
                    help='Output Directory for all datafiles')

    parser.add_argument('-y', '--yaml', action='store', required=False, type=str, default = 'config_v3_none_may28', #Apr4. config/config_v3_none.yml_
                    help = 'filepath (in config/ directory) .yml file containing chip configuration. ')

    parser.add_argument('-ns', '--noisescaninfo', action='store', required=False, type=str, default ='noise_scan_summary_apr29_newfw_aps3w08s05_noise_t100_3s.csv',
                    help = 'filepath noise scan summary file containing chip noise infomation.')
    
#    parser.add_argument('-i', '--inject', action='store_true', default=False, required=False,
#                    help =  'Turn on injection. Default: No injection')
#
#    parser.add_argument('-v','--vinj', action='store', default = None, type=float,
#                    help = 'Specify injection voltage (in mV). DEFAULT 300 mV')

    parser.add_argument('-t', '--threshold', type = int, action='store', default=100,
                    help = 'Threshold voltage for digital ToT (in mV). DEFAULT 100mV')

    parser.add_argument('-r', '--maxruns', type=int, action='store', default=None,
                    help = 'Maximum number of readouts')

    parser.add_argument('-M', '--maxtime', type=float, action='store', default=5,
                    help = 'Maximum run time (in second)')


    parser.add_argument
    args = parser.parse_args()
    
    start_time = time.time()
    asyncio.run(main(args))
    end_time = time.time()
    print(f"{end_time-start_time} : time for this run")

