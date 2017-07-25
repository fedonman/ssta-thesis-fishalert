import downloader

if __name__ == '__main__':
	downloader = Downloader()

	chl_file = downloader.download('CHL', '2017-06-26', '2017-06-26', True) 
	#print '{0} downloaded'.format(chl_file)

	sst_file = downloader.download('SST', '2017-06-26', '2017-06-26', True) 
    #print '{0} downloaded'.format(sst_file) 

