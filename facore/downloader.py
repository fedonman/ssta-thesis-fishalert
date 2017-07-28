import argparse
import subprocess
import signal
import os
import sys
import datetime as dt

class Downloader:
    def __init__(self, motupath, username, password):
        self.motuPath = motupath
        self.username = username
        self.password = password
        self.urls = {'CHL': 'http://cmems-oc.isac.cnr.it/motu-web/Motu', 'SST': 'http://cmems.isac.cnr.it/mis-gateway-servlet/Motu', 'SLA': 'http://motu.sltac.cls.fr/motu-web/Motu'}
        self.services = {'CHL': 'OCEANCOLOUR_MED_CHL_L4_NRT_OBSERVATIONS_009_041-TDS', 'SST': 'SST_MED_SST_L4_NRT_OBSERVATIONS_010_004-TDS', 'SLA': 'SEALEVEL_MED_PHY_L4_NRT_OBSERVATIONS_008_050-TDS'}
        self.products = {'CHL': 'dataset-oc-med-chl-multi-l4-interp_1km_daily-rt-v02', 'SST': 'SST_MED_SST_L4_NRT_OBSERVATIONS_010_004_c_V2', 'SLA': 'dataset-duacs-nrt-medsea-merged-allsat-phy-l4-v3'}
        self.variables = {'CHL': ['CHL'], 'SST': ['analysed_sst', 'analysis_error'], 'SLA': ['sla']}
        self.geo = {'CHL': '-x -6 -X 36.500480651855 -y 30 -Y 45.998546600342', 'SST': '-x -18.120832443237 -X 36.245834350586 -y 30.254167556763 -Y 45.995834350586', 'SLA': '-x -5.9375 -X 36.9375 -y 30.0625 -Y 45.9375'}

    def _prepareCmd(self, directory, filename, parameter, date):
        variables = ''
        for v in self.variables[parameter]:
            variables += '-v {0} '.format(v)
        cmd = 'python {0} -u {1} -p {2} -m {3} -s {4} -d {5} {6} -t "{7}" -T "{8}" {9} -o {10} -f {11}.nc'.format(self.motuPath, self.username, self.password, self.urls[parameter], self.services[parameter], self.products[parameter], self.geo[parameter], date, date, variables, directory, filename)
        return cmd

    def download(self, directory, filename, parameter, date, verbose=False, force_copy=False):
        if not os.path.exists(directory):
            os.makedirs(directory)

        if os.path.isfile('{0}/{1}'.format(directory, filename)) and not force_copy:
            if verbose:
                print '{0} has already been downloaded. Skipping...'.format(parameter)
            return True;
        
        cmd = self._prepareCmd(directory, filename, parameter, date)
        
        if verbose is True:
            print 'Downloading {0}...'.format(parameter)
        
        tries = 0
        while True:
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            returncode = p.wait()
            print returncode
            if returncode == 0:
                if verbose is True:
                    print '{0} downloaded successfully'.format(parameter)
                return True 
            if returncode == 1:
                tries += 1
                if tries == 3:
                    if verbose is True:
                        print '{0} is not available'.format(parameter)
                    return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download SST, SLA and CHL L4 daily data for Mediterranean Sea.')
    parser.add_argument('-d', '--directory', default='.', help='directory to download parameters')
    parser.add_argument('-m', '--motupath', help='the path to motu client')
    parser.add_argument('-u', '--username', help='CMEMS username')
    parser.add_argument('-x', '--password', help='CMEMS password')
    parser.add_argument('-p', '--parameters', choices=['ALL', 'CHL', 'SST', 'SLA'], default='ALL', help='the param to download')
    parser.add_argument('-d', '--date', default='today', help='a date or range of dates')
    parser.add_argument("-v", "--verbose", help="enable verbose mode", action="store_true")
    parser.add_argument("-f", "--force-copy", help="force copy if file exists", action="store_true")
    args = parser.parse_args()

    if not os.path.exists(args.directory):
        os.makedirs(args.directory)

    if (args.date == 'today'):
        date = dt.date.today().isoformat()
    else:
        try:
            date = dt.datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            sys.exit("Incorrect date, should be YYYY-MM-DD or today (default)")

    verbose = False
    if args.verbose:
        verbose = True

    force_copy = False
    if args.force_copy:
        force_copy = True

    downloader = Downloader(args.motupath, args.username, args.password)

    if args.parameters == 'CHL':
        downloader.download(args.directory, 'CHL.nc', 'CHL', date, verbose, force_copy)
    elif args.parameters == 'SST':
        downloader.download(args.directory, 'SST.nc', 'SST', date, verbose, force_copy)
    elif args.parameters == 'SLA':
        downloader.download(args.directory, 'SLA.nc', 'SLA', date, verbose, force_copy)
    elif args.parameters == 'ALL':
        downloader.download(args.directory, 'CHL.nc', 'CHL', date, verbose, force_copy)
        downloader.download(args.directory, 'SST.nc', 'SST', date, verbose, force_copy)
        downloader.download(args.directory, 'SLA.nc', 'SLA', date, verbose, force_copy)