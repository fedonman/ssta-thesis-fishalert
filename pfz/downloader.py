import argparse
import subprocess
import os

class Downloader:
    def __init__(self, destDir='./'):
        self.motuPath = '~/git/motu-client-python/src/python/motu-client.py'
        self.destDir = destDir
        self.username = 'vvasileiadis'
        self.password = 'VyronCMEMS2016'
        self.urls = {'CHL': 'http://cmems-oc.isac.cnr.it/motu-web/Motu', 'SST': 'http://cmems.isac.cnr.it/mis-gateway-servlet/Motu'}
        self.services = {'CHL': 'OCEANCOLOUR_MED_CHL_L4_NRT_OBSERVATIONS_009_041-TDS', 'SST': 'SST_MED_SST_L4_NRT_OBSERVATIONS_010_004-TDS'}
        self.products = {'CHL': 'dataset-oc-med-chl-multi-l4-interp_1km_daily-rt-v02', 'SST': 'SST_MED_SST_L4_NRT_OBSERVATIONS_010_004_c_V2'}
        self.variables = {'CHL': ['CHL'], 'SST': ['analysed_sst', 'analysis_error']}
        self.geo = {'CHL': '-x -6 -X 36.500480651855 -y 30 -Y 45.998546600342', 'SST': '-x -18.120832443237 -X 36.245834350586 -y 30.254167556763 -Y 45.995834350586'}

    def _prepareCmd(self, parameter, date1, date2, filename):
        variables = ''
        for v in self.variables[parameter]:
            variables += '-v {0} '.format(v)
        cmd = 'python {0} -u {1} -p {2} -m {3} -s {4} -d {5} {6} -t "{7}" -T "{8}" {9} -o {10} -f {11}.nc'.format(self.motuPath, self.username, self.password, self.urls[parameter], self.services[parameter], self.products[parameter], self.geo[parameter], date1, date2, variables, self.destDir, filename)
        return cmd

    def download(self, parameter, date1, date2=None, verbose=False):
        if not os.path.exists(self.destDir):
            os.makedirs(self.destDir)
        filename = ''
        if date2 is None:
            filename = '{0}-{1}'.format(parameter, date1)
            date2 = date1
        elif date1 == date2:
            filename = '{0}-{1}'.format(parameter, date1)
        else:
            filename = '{0}-{1}-{2}'.format(parameter, date1, date2)
        
        cmd = self._prepareCmd(parameter, date1, date2, filename)
        
        if verbose is True:
            print 'Downloading {0}...'.format(parameter)
        
        while True:
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            returncode = p.wait()
            #for line in p.stdout.readlines():
                #print line
            if returncode == 0:
                if verbose is True:
                    print '{0} downloaded successfully'.format(parameter)
                break

        return filename


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download CHL & SST L4 daily data for Mediterranean Sea.')
    parser.add_argument('-p', '--params', choices=['ALL', 'CHL', 'SST'], default='ALL', help='the param to download')
    parser.add_argument('-d', '--date', nargs='*', default='today', help='a date or range of dates')
    parser.add_argument('-o', '--dir', default='./', help='destination directory')
    parser.add_argument("-v", "--verbose", help="enable verbose mode", action="store_true")
    args = parser.parse_args()

    if (args.date[0] == 'today'):
        date1 = date.today().isoformat()
    else:
        date1 = args.date[0]

    if len(args.date) == 1:
        date2 = date1
    else:
        date2 = args.date[1]

    verbose = False
    if args.verbose:
        verbose = True

    downloader = Downloader(args.dir)

    if args.params == 'CHL':
        downloader.download('CHL', date1, date2, verbose)
    elif args.params == 'SST':
        downloader.download('SST', date1, date2, verbose)
    elif args.params == 'ALL':
        downloader.download('CHL', date1, date2, verbose)
        downloader.download('SST', date1, date2, verbose)