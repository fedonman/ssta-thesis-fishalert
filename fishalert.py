from facore import *
import config
import os
import sys
import datetime
import argparse
import time
from shutil import copy

def date_to_season(date):
    year, month, day = date.split('-')
    month = int(month)
    day = int(day)
    if month == 12 or month == 1 or month == 2:
        return Season.Winter
    elif month == 3 or month == 4 or month == 5:
        return Season.Spring
    elif month == 6 or month == 7 or month == 8:
        return Season.Summer
    elif month == 9 or (month == 10 and day < 15):
        return Season.EarlyAutumn
    elif (month == 10 and day >= 15) or month == 11:
        return Season.LateAutumn

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Calculate Possible Fishing Zones in the Mediterranean Sea.')
    parser.add_argument('-f', '--fishery', choices=['ALL', 'Anchovy', 'Sardine'], default='Anchovy', help='fishery')
    parser.add_argument('-d', '--date', default='today', help='a date')
    parser.add_argument('-v', '--verbose', help='enable verbose mode', action='store_true')
    parser.add_argument('-p', '--previous-day', help='calculate PFZ for previous date if not all data are available', action='store_true')
    args = parser.parse_args()


    if args.date == 'today':
        date = '{0}'.format(datetime.date.today().isoformat())
    else:
        try:
            date = '{0}'.format(datetime.datetime.strptime(args.date, '%Y-%m-%d').date())
        except ValueError:
            sys.exit('Incorrect date, should be YYYY-MM-DD or today (default)')
    
    season = date_to_season(date)

    fishery = list()
    if args.fishery == 'Anchovy':
        fishery.append(Fishery.Anchovy)
    elif args.fishery == 'Sardine':
        fishery.append(Fishery.Sardine)
    elif args.fishery == 'ALL':
        fishery.append(Fishery.Anchovy)
        fishery.append(Fishery.Sardine)

    verbose = False
    if args.verbose:
        verbose = True

    download_previous_day = False
    if args.previous_day:
        download_previous_day = True

    settings = config.settings
    fish_alert_directory = os.path.dirname(os.path.abspath(__file__))
    workspace_directory = config.settings['workspace']
    motu_path = config.settings['motu_path']
    username = config.settings['cmems_username']
    password = config.settings['cmems_password']
    snappy_path = config.settings['snappypath']

    if not os.path.exists(workspace_directory):
        os.makedirs(workspace_directory)

    os.chdir(workspace_directory)

    current_date_directory = os.path.join(workspace_directory, date)
    if not os.path.exists(current_date_directory):
        os.makedirs(current_date_directory)

    os.chdir(current_date_directory)
    
    if not os.path.isfile('bathymetry.nc'):
        if os.path.isfile('{0}/assets/bathymetry.nc'.format(fish_alert_directory)):
            copy('{0}/assets/bathymetry.nc'.format(fish_alert_directory), '.')
        else:
            sys.exit('Bathymetry file not available. Should be in assets/bathymetry.nc')

    if os.path.isfile('{0}.nc'.format(args.fishery)):
        print 'PFZ is already calculated for {0}.'.format(args.fishery)
        sys.exit()
    
    downloader = Downloader(motu_path, username, password)
    chl_file = 'CHL.nc'
    sst_file = 'SST.nc'
    sla_file = 'SLA.nc'

    if not os.path.isfile(chl_file):
        print chl_file
        downloader.download(current_date_directory, 'CHL.nc', 'CHL', date, True)
    if not os.path.isfile(sst_file):
        print sst_file
        downloader.download(current_date_directory, 'SST.nc', 'SST', date, True)
    if not os.path.isfile(sla_file):
        print sla_file
        downloader.download(current_date_directory, 'SLA.nc', 'SLA', date, True)

    print os.path.isfile(chl_file)
    print os.path.isfile(sst_file)
    print os.path.isfile(sla_file)
    
    if os.path.isfile(chl_file) and os.path.isfile(sst_file) and os.path.isfile(sla_file):
        temp1_file = '_temp1.nc'
        temp2_file = '_temp2.nc'
        final_file = 'final.nc'
        depth_file = 'bathymetry.nc'
        
        collocator = Collocator(snappy_path)
        if not os.path.isfile(temp1_file):
            collocator.Collocate(depth_file, sst_file, temp1_file)
            Utilities.deleteCollocationFlags(temp1_file)
            time.sleep(1)
        if not os.path.isfile(temp2_file):
            collocator.Collocate(temp1_file, chl_file, temp2_file)
            Utilities.deleteCollocationFlags(temp2_file)
            time.sleep(1)
        if not os.path.isfile(final_file):
            collocator.Collocate(temp2_file, sla_file, final_file)
            Utilities.deleteCollocationFlags(final_file)
            time.sleep(1)

        for fish in fishery:
            print fish
            print season
            fuzzifier = Fuzzifier(final_file, season, fish)
            fuzzifier.run()
            fuzzifier.writeData('{0}.nc'.format(fish))
    '''else:
        if download_previous_day:
            previous_date = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
            if verbose:
                print 'Calculating PFZ for {0}'.format(previous_date)
            if os.path.isfile('{0}.nc'.format(previous_date)):
                print 'PFZ is already calculated for {0}.'.format(previous_date)
                sys.exit()
            
            chl_file = '{0}/{1}'.format(previous_date, 'CHL.nc')
            sst_file = '{0}/{1}'.format(previous_date, 'SST.nc')
            sla_file = '{0}/{1}'.format(previous_date, 'SLA.nc')

            if not os.path.isfile(chl_file):
                downloader.download(previous_date, 'CHL', 'CHL', previous_date, True)
            if not os.path.isfile(sst_file):
                downloader.download(previous_date, 'SST', 'SST', previous_date, True)
            if not os.path.isfile(sla_file):
                downloader.download(previous_date, 'SLA', 'SLA', previous_date, True)

            if os.path.isfile(chl_file) and os.path.isfile(sst_file) and os.path.isfile(sla_file):
                temp1_file = '{0}/{1}'.format(previous_date, '_temp1.nc')
                temp2_file = '{0}/{1}'.format(previous_date, '_temp2.nc')
                final_file = '{0}/{1}'.format(previous_date, 'final.nc')
                depth_file = 'bathymetry.nc'
                
                collocator = Collocator(snappy_path)
                if not os.path.isfile(temp1_file):  
                    collocator.Collocate(depth_file, sst_file, temp1_file)
                    Utilities.deleteCollocationFlags(temp1_file)
                    time.sleep(1)
                if not os.path.isfile(temp2_file):
                    collocator.Collocate(temp1_file, chl_file, temp2_file)
                    Utilities.deleteCollocationFlags(temp2_file)
                    time.sleep(1)
                if not os.path.isfile(final_file):
                    collocator.Collocate(temp2_file, sla_file, final_file)
                    Utilities.deleteCollocationFlags(final_file)
                    time.sleep(1)

                fuzzifier = Fuzzifier(final_file, Season.Summer, Fishery.Anchovy)
                fuzzifier.run()
                fuzzifier.writeData('{0}.nc'.format(previous_date))'''