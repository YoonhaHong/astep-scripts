import asyncio
from astep import astepRun
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
    #await astro.asic_init(yaml="test_quadchip_new", analog_col=[0,pixel[1]], chipsPerRow=2)
    #await astro.asic_init(yaml="test_quadchip", analog_col=pixel[1])
    #await astro.asic_init(yaml="config_v3_none", analog_col=[0,0,pixel[3]])
    await astro.asic_init(yaml="config_v3_none_may28", analog_col=[layer, chip ,pixel[3]])
    #await astro.asic_init(yaml="test_quadchip", analog_col=[layer, chip ,pixel[3]])
    #print(f"Header: {astro.get_log_header()}")

    print("initializing voltage")
    #await astro.init_voltages() ## th in mV
    await astro.init_voltages(vthreshold=args.threshold) ## th in mV, same as previous fw
#    await astro.update_pixThreshold(layer, chip, vthreshold=args.threshold)

    #print("FUNCTIONALITY CHECK")
    #await astro.functionalityCheck(holdBool=True)

    print("update threshold")
    #await astro.update_pixThreshold(100)
    #await astro.update_pixThreshold(vThresh=args.threshold)
    await astro.update_pixThreshold(layer, chip,0)

    print("enable pixel")
    #await astro.enable_pixel(pixel[0], pixel[1])
    await astro.enable_pixel(layer, chip, pixel[2], pixel[3])
    #print("disable pixel col15,row0 [r,c]")
    #await astro.disable_pixel(pixel[0], pixel[1])

    #print("disable pixel col15,row0 [r,c]")
    #await astro.disable_pixel(0, 15)

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
#            else:
#                await astro.enable_pixel(row_val,col_val)
        print(count_vals, " pixels are disable !")
        print("Active pixels ~ ",1-(count_vals/(35*35)), " %.")
    """
    #print("init injection")
    #await astro.init_injection(inj_voltage=300)

#    print("final configs")
#    print(f"Header: {astro.get_log_header()}")
#    await astro.asic_configure()
    print("final configs")
    print(f"Header: {astro.get_log_header(layer, chip)}")
    await astro.asic_configure(layer)
    
    print("setup readout")
    await astro.setup_readout(layer, autoread=0) #disable autoread


    i = 0
    strPix = "_layer"+str(layer)+"_chip"+str(chip)+"_col"+str(pixel[3])+"_row"+str(pixel[2])
    fname=strPix if not args.name else args.name+strPix+"_"
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
        
        #await(astro.print_status_reg())
    end_intime = time.time()

    astro._wait_progress(5)
    #print("stop injection")
    #await astro.stop_injection()
    #print(f"***** TotEnv at [{pixel[1]},{pixel[0]}] = {event}")
    #print(f"***** noise at [{pixel[1]},{pixel[0]}] = {n_noise}")
    print(f"***** TotEnv at [c{pixel[3]},r{pixel[2]}] = {event}")
    print(f"***** noise at [c{pixel[3]},r{pixel[2]}] = {n_noise}")
    print(f"***** time in one pixel  = {end_intime - start_intime}")
#add example_loop.py
    #noisefile.write(f"{pixel[1]}\t{pixel[0]}\t{n_noise}\n") #col, row, noise
    noisefile.write(f"{pixel[3]}\t{pixel[2]}\t{n_noise}\n") #col, row, noise
    noisefile.flush()

    print("read out buffer")
    buff, readout = await(astro.get_readout())
    #print(binascii.hexlify(readout))
    print(f"{buff} bytes in buffer")

    bitfile.close() # Close open file       
    astro.close_connection() # Closes SPI
    logger.info("Program terminated successfully")


#        pixel=[r,c]
#pixel=[0,15]
#asyncio.run(main(args,pixel))
#pixel=[1,0]
#asyncio.run(main(pixel))
#pixel=[2,0]
#asyncio.run(main(pixel))
#pixel=[3,0]
#asyncio.run(main(pixel))
#pixel=[4,0]
#asyncio.run(main(pixel))
#pixel=[5,0]
#asyncio.run(main(pixel))

#for r in range(1):
#    for c in range(20):
#        print(f"{r},{c}")
#        pixel=[r,c]
#        print(pixel)
#        asyncio.run(main(pixel))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Astropix Driver Code')
    parser.add_argument('-n', '--name', default='', required=False,
                    help='Option to give additional name to output files upon running')

    parser.add_argument('-o', '--outdir', default='.', required=False,
                    help='Output Directory for all datafiles')

    parser.add_argument('-y', '--yaml', action='store', required=False, type=str, default = 'config_v3_none', #Apr4. config/config_v3_none.yml_
                    help = 'filepath (in config/ directory) .yml file containing chip configuration. Default: config/config_v3_none.yml (All pixels off)')

#    parser.add_argument('-ns', '--noisescaninfo', action='store', required=False, type=str, default ='noise_scan_summary_Apr22_APS3w08s05_NoiseScan_configv3none_t100_5s.csv',
#                    help = 'filepath noise scan summary file containing chip noise infomation.')
    
    parser.add_argument('-c', '--saveascsv', action='store_true', 
                    default=False, required=False, 
                    help='save output files as CSV. If False, save as txt')
    
    parser.add_argument('-i', '--inject', action='store_true', default=False, required=False,
                    help =  'Turn on injection. Default: No injection')

    parser.add_argument('-v','--vinj', action='store', default = 0, type=float,
                    help = 'Specify injection voltage (in mV). DEFAULT 0')

    #parser.add_argument('-t', '--threshold', type = float, action='store', default=None,
    parser.add_argument('-t', '--threshold', type = int, action='store', default=100,
                    help = 'Threshold voltage for digital ToT (in mV). DEFAULT: 100mV')

    parser.add_argument('-r', '--maxruns', type=int, action='store', default=None,
                    help = 'Maximum number of readouts')

    parser.add_argument('-M', '--maxtime', type=float, action='store', default=3,
                    help = 'Maximum run time (in second). Default: 3s')

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
