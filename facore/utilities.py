import netCDF4 as cdf
import argparse
import random
import string

class Utilities:
    @staticmethod
    def deleteCollocationFlags(file):
        dsin = cdf.Dataset(file, 'r+')
        dsin.renameVariable('collocation_flags', 'collocation_flags_'.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5)))
        dsin.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Utility functions needed in the generation of PFZs')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-d', '--deleteCollocationFlags', type=str, help='Remove collocation flags from file by creating a new file.')
    args = parser.parse_args()

    if args.deleteCollocationFlags is not None:
        Utilities.deleteCollocationFlags(args.deleteCollocationFlags)


