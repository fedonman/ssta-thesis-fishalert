import netCDF4 as cdf
import argparse

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
    def deleteCollocationFlags(inputfile, outputfile):
        #input file
        dsin = cdf.Dataset(inputfile, 'r+')
        
        #output file
        dsout = cdf.Dataset(outputfile, 'w', format='NETCDF4_CLASSIC')
        
        #Copy dimensions
        for dname, the_dim in dsin.dimensions.iteritems():
            print dname, len(the_dim)
            dsout.createDimension(dname, len(the_dim) if not the_dim.isunlimited() else None)
        
        # Copy variables
        for v_name, varin in dsin.variables.iteritems():
            if v_name == 'collocation_flags':
                continue
            outVar = dsout.createVariable(v_name, varin.datatype, varin.dimensions)
            print varin.datatype
            
            # Copy variable attributes
            outVar.setncatts({k: varin.getncattr(k) for k in varin.ncattrs()})
            
            outVar[:] = varin[:]
        
        # close the files
        dsin.close()
        dsout.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Utility functions needed in the generation of PFZs')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-r', '--removeOtherSeas', type=str, help='Remove other seas like Atlantic Ocean or Black Sea. Requires filename as parameter.')
    group.add_argument('-d', '--deleteCollocationFlags', nargs=2, type=str, help='Remove collocation flags from file by creating a new file.')
    args = parser.parse_args()

    print args.removeOtherSeas
    #print len(args.removeOtherSeas)
    print args.deleteCollocationFlags
    #print len(args.deleteCollocationFlags)

    if args.removeOtherSeas is not None:
        print 'TODO'
    if args.deleteCollocationFlags is not None:
        Utilities.deleteCollocationFlags(args.deleteCollocationFlags[0], args.deleteCollocationFlags[1])


