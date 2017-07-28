import netCDF4 as cdf
import argparse
import random
import string

class Utilities:
    @staticmethod
    def RemoveOtherSeas(file):
        datafile = cdf.Dataset(file, 'r+')

        print datafile.variables

        # remove atlantic ocean
        variables = datafile.variables.keys()
        if 'analysed_sst' in variables:
            datafile['analysed_sst'][0:300, 0:450] = -32768
        
        if 'elevation' in variables:
            datafile['elevation'][0:300, 0:450] = float('nan')
            datafile['elevation'][0:600, 2550:] = float('nan')
        
        datafile.close()

    @staticmethod
    def deleteCollocationFlags(file):
        dsin = cdf.Dataset(file, 'r+')
        dsin.renameVariable('collocation_flags', 'collocation_flags_'.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5)))
        dsin.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Utility functions needed in the generation of PFZs')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-r', '--removeOtherSeas', type=str, help='Remove other seas like Atlantic Ocean or Black Sea. Requires filename as parameter.')
    group.add_argument('-d', '--deleteCollocationFlags', type=str, help='Remove collocation flags from file by creating a new file.')
    args = parser.parse_args()

    if args.removeOtherSeas is not None:
        print 'TODO'
    if args.deleteCollocationFlags is not None:
        Utilities.deleteCollocationFlags(args.deleteCollocationFlags)


