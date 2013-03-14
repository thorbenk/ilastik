from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.operators.ioOperators import OpStreamingHdf5Reader, OpInputDataReader
from ilastik.utility.operatorSubView import OperatorSubView

from lazyflow.operators import Op5ifyer

from cylemon.segmentation import MSTSegmentor
import vigra
import numpy
import uuid

class OpPreprocessing(Operator):
    """
    The top-level operator for the pre-procession applet
    """
    name = "Preprocessing"
    
    #Image before preprocess
    RawData = InputSlot()
    Sigma = InputSlot(value = 1.6)
    Filter = InputSlot(value = 0)
    
    #Image after preprocess
    PreprocessedData = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpPreprocessing, self).__init__(*args, **kwargs)
        self._writeprotect = None
        self._prepData = None
    
    def setSigma(self,s):
        #ToDo: SetDirty!
        self.Sigma.setValue(s)
        print "sigma set!"
    
    def setWriteProtect(self,wp):
        self._writeprotect = wp
        if wp:print "You ordered write-protect!"
        else:print "You gave up write-protect!"
    
    def propagateDirty(self,slot,subindex,roi):
        print "DIRT IN PREP"
        if slot == self.RawData:
            self.PreprocessedData.setDirty(roi)
            print "and now: the preprocess"
        print "HIER"
        self._prepData = None
        self.PreprocessedData.setDirty()
    
    def setupOutputs(self):
        self.PreprocessedData.meta.shape = (1,)
        
    def execute(self,slot,subindex,roi,result):
        print self._prepData
        if self._prepData is not None:return self._prepData
        volume5d = self.RawData[:].wait()
        sigma = self.Sigma[:].wait()
        
        #Hack: Remove Channel
        volume = numpy.add.reduce(volume5d,3)
        
        print "input volume shape: ", volume.shape
        print "input volume size: ", volume.nbytes / 1024**2, "MB"
        fvol = volume.astype(numpy.float32)

        #Choose filter selected by user
        volume_filter = self.Filter.value
        
        print "applying filter",
        if volume_filter == 0:
            volume_feat = vigra.filters.hessianOfGaussianEigenvalues(fvol,sigma)[:,:,:,0]
            print "lowest eigenvalue of Hessian of Gaussian"
        
        elif volume_filter == 1:
            volume_feat = vigra.filters.hessianOfGaussianEigenvalues(fvol,sigma)[:,:,:,2]
            print "greatest eigenvalue of Hessian of Gaussian"
            
        elif volume_filter == 2:
            volume_feat = vigra.filters.gaussianGradientMagnitude(fvol,sigma)
            print "Gaussian Gradient Magnitude"
        
        elif volume_filter == 3:
            volume_feat = vigra.filters.gaussianSmoothing(fvol,sigma)
            print "Gaussian Smoothing"
        
        elif volume_filter == 4:
            volume_feat = vigra.filters.gaussianSmoothing(-fvol,sigma)
            print "negative Gaussian Smoothing"
        
        volume_ma = numpy.max(volume_feat)
        volume_mi = numpy.min(volume_feat)
        volume_feat = (volume_feat - volume_mi) * 255.0 / (volume_ma-volume_mi)
        print "Watershed..."
        labelVolume = vigra.analysis.watersheds(volume_feat)[0].astype(numpy.int32)
        
        print labelVolume.shape, labelVolume.dtype
        result = MSTSegmentor(labelVolume, volume_feat.astype(numpy.float32), edgeWeightFunctor = "minimum")
        result.raw = volume#5d
        
        self._prepData = result
        return result
