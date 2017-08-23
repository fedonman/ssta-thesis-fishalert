from contextlib import contextmanager
import os
import sys

# Define a context manager to suppress stdout and stderr. 
# From: https://stackoverflow.com/questions/11130156/suppress-stdout-stderr-print-from-python-functions
class suppress_stdout_stderr(object):
    '''
    A context manager for doing a "deep suppression" of stdout and stderr in 
    Python, i.e. will suppress all print, even if the print originates in a 
    compiled C/Fortran sub-function.
       This will not suppress raised exceptions, since exceptions are printed
    to stderr just before a script exits, and after the context manager has
    exited (at least, I think that is why it lets exceptions through).      

    '''
    def __init__(self):
        # Open a pair of null files
        self.null_fds =  [os.open(os.devnull,os.O_RDWR) for x in range(2)]
        # Save the actual stdout (1) and stderr (2) file descriptors.
        self.save_fds = (os.dup(1), os.dup(2))

    def __enter__(self):
        # Assign the null pointers to stdout and stderr.
        os.dup2(self.null_fds[0],1)
        os.dup2(self.null_fds[1],2)

    def __exit__(self, *_):
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(self.save_fds[0],1)
        os.dup2(self.save_fds[1],2)
        # Close the null files
        os.close(self.null_fds[0])
        os.close(self.null_fds[1])

class Collocator:
    def __init__(self, snappypath):
        self.name = 'Collocator'
        sys.path.append(snappypath) #/home/fedonman/.snap/snap-python

    def isSNAPproduct(self, prod):
        return 'snap.core.datamodel.Product' in str(type(prod))

    def readProduct(self, file):
        import snappy
        # input parameter is already a SNAP product
        if self.isSNAPproduct(file):
            return file
        # input parameter is file, then convert it to SNAP product
        if os.path.isfile(file):
            prod = snappy.ProductIO.readProduct(file)
        elif os.path.exists(file):
            prod = None
        else:
            prod = None
        return prod

    def Collocate(self, masterFile, slaveFile, targetFile, verbose=True):
        import snappy
        if verbose is True:
            print 'Collocating {0} and {1} into {2}'.format(slaveFile, masterFile, targetFile) 
        
        # Supress stdout because snappy raises warnings
        with suppress_stdout_stderr():
            # read master and slave products
            masterProduct = self.readProduct(masterFile)
            slaveProduct = self.readProduct(slaveFile)

            # import necessary Java types
            CollocateOp = snappy.jpy.get_type('org.esa.snap.collocation.CollocateOp')
            ResamplingType = snappy.jpy.get_type('org.esa.snap.collocation.ResamplingType')

            # create operator and set parameters
            ColOp = CollocateOp()
            ColOp.setParameterDefaultValues()
            ColOp.setMasterProduct(masterProduct)
            ColOp.setSlaveProduct(slaveProduct)
            ColOp.setResamplingType(ResamplingType.BILINEAR_INTERPOLATION)
            ColOp.setMasterComponentPattern('${ORIGINAL_NAME}')
            ColOp.setSlaveComponentPattern('${ORIGINAL_NAME}')

            # Apply operator
            targetProduct = ColOp.getTargetProduct()

            # Write target product as netcdf file
            snappy.ProductIO.writeProduct(targetProduct, targetFile, 'NetCDF-BEAM')
            
            # dispose resources
            masterProduct.dispose()
            slaveProduct.dispose()
            del ColOp
            del CollocateOp
            del ResamplingType
            
            if verbose is True:
                print 'Collocation successful.'

            # return target filename
            return targetFile