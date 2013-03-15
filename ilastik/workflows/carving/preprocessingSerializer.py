from ilastik.applets.base.appletSerializer import AppletSerializer, getOrCreateGroup, deleteIfPresent
from cylemon.segmentation import MSTSegmentor
import h5py
import numpy

class PreprocessingSerializer( AppletSerializer ):
    def __init__(self, preprocessingTopLevelOperator, *args, **kwargs):
        super(PreprocessingSerializer, self).__init__(*args, **kwargs)
        self._o = preprocessingTopLevelOperator 
        
    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        preproc = getOrCreateGroup(topGroup, "preprocessing")
        
        for imageIndex, opPre in enumerate( self._o.innerOperators ):
            mst = opPre._prepData
            print mst,"serializing"
            deleteIfPresent(preproc, "mst")
            deleteIfPresent(preproc, "sigma")
            
            #preproc.create_dataset("mst", data=newpath)
            preproc.create_dataset("sigma",data= opPre.Sigma.value)
            
            preprocgraph = getOrCreateGroup(preproc, "graph")
            mst.saveH5G(preprocgraph)
            
    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        for i in topGroup["preprocessing"]:
            print i
        sigma = topGroup["preprocessing"]["sigma"].value
        
        for imageIndex, opPre in enumerate( self._o.innerOperators ):
            mst = MSTSegmentor.loadH5G(topGroup["preprocessing"]["graph"])
            print mst
            opPre.Sigma.setValue(sigma)
            opPre._prepData = mst
            opPre.PreprocessedData.setDirty()
           
    def isDirty(self):
		for opPre in self._o.innerOperators:			
			if opPre._prepData is None:
				return True
		return False
	
    #this is present only for the serializer AppletInterface
    def unload(self):
        pass
    
