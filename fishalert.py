from facore import *
import config
import os
import sys
import datetime
from shutil import copy

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Calculate Possible Fishing Zones in the Mediterranean Sea.')
    parser.add_argument('-f', '--fishery', choices=['ALL', 'Anchovy', 'Sardine'], default='Anchovy', help='fishery')
    parser.add_argument('-d', '--date', default='date', help='a date')
    parser.add_argument('-v', '--verbose', help='enable verbose mode', action='store_true')
    parser.add_argument('-p', '--previous-day', help='calculate PFZ for previous date if not all data are available', action='store_true')

    if (args.date == 'date'):
        date = dt.date.date().isoformat()
    else:
        try:
            date = dt.datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            sys.exit("Incorrect date, should be YYYY-MM-DD or date (default)")

    verbose = False
    if args.verbose:
        verbose = True

    download_previous_date = False
    if args.previous_date:
        download_previous_date = True

    settings = config.settings
    fish_alert_directory = os.path.dirname(os.path.abspath(__file__))
    workspace_directory = config.settings['workspace']
    motu_path = config.settings['motu_path']
    username = config.settings['cmems_username']
    password = config.settings['cmems_password']
    snappy_path = config.settings['snappypath']

    if not os.path.exists(workspace_directory):
        os.makedirs(workspace_directory)
    if not os.path.isfile('{0}/bathymetry.nc'.format(workspace_directory)):
        if os.path.isfile('{0}/assets/bathymetry.nc'.format(fish_alert_directory)):
            copy('{0}/assets/bathymetry.nc'.format(fish_alert_directory), workspace_directory)
        else:
            sys.exit('Bathymetry file not available. Should be in assets/bathymetry.nc')
    
    os.chdir(workspace_directory)

    if os.path.isfile('{0}.nc'.format(date)):
        print 'PFZ is already calculated for {0}.'.format(date)
        sys.exit()
    
    downloader = Downloader(workspace_directory, motu_path, username, password)
    chl_file = '{0}/{1}'.format(date, 'CHL.nc')
    sst_file = '{0}/{1}'.format(date, 'SST.nc')
    sla_file = '{0}/{1}'.format(date, 'SLA.nc')

    if not os.path.isfile(chl_file):
        downloader.download('CHL', date, True)
    if not os.path.isfile(sst_file):
        downloader.download('SST', date, True)
    if not os.path.isfile(sla_file):
        downloader.download('SLA', date, True)

    if os.path.isfile(chl_file) and os.path.isfile(sst_file) and os.path.isfile(sla_file):
        temp1_file = '{0}/{1}'.format(date, '_temp1.nc')
        temp2_file = '{0}/{1}'.format(date, '_temp2.nc')
        final_file = '{0}/{1}'.format(date, 'final.nc')
        depth_file = 'bathymetry.nc'
        
        collocator = Collocator(snappy_path)
        collocator.Collocate(depth_file, sst_file, temp1_file)
        Utilities.deleteCollocationFlags(temp1_file)
        collocator.Collocate(temp1_file, chl_file, temp2_file)
        Utilities.deleteCollocationFlags(temp2_file)
        collocator.Collocate(temp2_file, sla_file, final_file)
        Utilities.deleteCollocationFlags(final_file)

        fuzzifier = Fuzzifier(final_file, Season.Summer, Fishery.Anchovy)
        fuzzifier.run()
        fuzzifier.writeData({'{0}.nc'}.format(date))
    else:
        if download_previous_date:
            previous_date = (datetime.date.date() - datetime.timedelta(days=1)).isoformat()
            if verbose:
                print 'Calculating PFZ for {0}'.format(previous_date)
            if os.path.isfile('{0}.nc'.format(previous_date)):
                print 'PFZ is already calculated for {0}.'.format(previous_date)
                sys.exit()
            
            chl_file = '{0}/{1}'.format(previous_date, 'CHL.nc')
            sst_file = '{0}/{1}'.format(previous_date, 'SST.nc')
            sla_file = '{0}/{1}'.format(previous_date, 'SLA.nc')

            if not os.path.isfile(chl_file):
                downloader.download('CHL', previous_date, True)
            if not os.path.isfile(sst_file):
                downloader.download('SST', previous_date, True)
            if not os.path.isfile(sla_file):
                downloader.download('SLA', previous_date, True)

            if os.path.isfile(chl_file) and os.path.isfile(sst_file) and os.path.isfile(sla_file):
                temp1_file = '{0}/{1}'.format(previous_date, '_temp1.nc')
                temp2_file = '{0}/{1}'.format(previous_date, '_temp2.nc')
                final_file = '{0}/{1}'.format(previous_date, 'final.nc')
                depth_file = 'bathymetry.nc'
                
                collocator = Collocator(snappy_path)
                collocator.Collocate(depth_file, sst_file, temp1_file)
                Utilities.deleteCollocationFlags(temp1_file)
                collocator.Collocate(temp1_file, chl_file, temp2_file)
                Utilities.deleteCollocationFlags(temp2_file)
                collocator.Collocate(temp2_file, sla_file, final_file)
                Utilities.deleteCollocationFlags(final_file)

                fuzzifier = Fuzzifier(final_file, Season.Summer, Fishery.Anchovy)
                fuzzifier.run()
                fuzzifier.writeData({'{0}.nc'}.format(previous_date))