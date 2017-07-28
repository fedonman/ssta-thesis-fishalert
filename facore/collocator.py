from contextlib import contextmanager
import os
import sys

@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = devnull
        sys.stderr = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

class Collocator:
    def __init__(self, snappypath):
        self.name = 'Collocator'
        sys.path.append(snappypath) #/home/fedonman/.snap/snap-python

    def isSNAPproduct(self, prod):
        return 'snap.core.datamodel.Product' in str(type(prod))

    def readProduct(self, file):
        import snappy
        if self.isSNAPproduct(file):
            # input parameter is already a SNAP product
            return file
        if os.path.isfile(file):
            prod = snappy.ProductIO.readProduct(file)
        elif os.path.exists(file):
            print('ERROR 1')
            prod = None
        else:
            print('ERROR 2')
            prod = None
        return prod

    def Collocate(self, masterFile, slaveFile, targetFile, verbose=True):
        import snappy
        # read master and slave products
        if verbose is True:
            print 'Collocating {0} into {1}'.format(slaveFile, masterFile) 
        
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
        
        # return target filename
        return targetFile