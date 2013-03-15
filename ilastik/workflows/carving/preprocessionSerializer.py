from ilastik.applets.base.appletSerializer import AppletSerializer, getOrCreateGroup, deleteIfPresent
import numpy

class PreprocessionSerializer( AppletSerializer ):
    def __init__(self, preprocessionTopLevelOperator, *args, **kwargs):
        super(PreprocessionSerializer, self).__init__(*args, **kwargs)
        self._o = preprocessionTopLevelOperator 
        
    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        preproc = getOrCreateGroup(topGroup, "preprocession")
        
        for imageIndex, opPre in enumerate( self._o.innerOperators ):
            mst = opPre.PreprocessedData
            print mst,"serializing"
            deleteIfPresent(preproc, "mst")
               
			g.create_dataset("mst", data=mst)
			
            opPre._dirtyObjects = set()
        
    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        obj = topGroup["objects"]
        
        for imageIndex, opCarving in enumerate( self._o.opCarving.innerOperators ):
            mst = opCarving._mst 
            
            for i, name in enumerate(obj):
                print " loading object with name='%s'" % name
                try:
                    g = obj[name]
                    fg_voxels = g["fg_voxels"]
                    bg_voxels = g["bg_voxels"]
                    fg_voxels = [fg_voxels[:,k] for k in range(3)]
                    bg_voxels = [bg_voxels[:,k] for k in range(3)]
                    
                    sv = g["sv"].value
                  
                    mst.object_names[name]           = i+1 
                    mst.object_seeds_fg_voxels[name] = fg_voxels
                    mst.object_seeds_bg_voxels[name] = bg_voxels
                    mst.object_lut[name]             = sv
                    mst.bg_priority[name]            = g["bg_prio"].value
                    mst.no_bias_below[name]          = g["no_bias_below"].value
                    
                    print "[CarvingSerializer] de-serializing %s, with opCarving=%d, mst=%d" % (name, id(opCarving), id(mst))
                    print "  %d voxels labeled with green seed" % fg_voxels[0].shape[0] 
                    print "  %d voxels labeled with red seed" % bg_voxels[0].shape[0] 
                    print "  object is made up of %d supervoxels" % sv.size
                    print "  bg priority = %f" % mst.bg_priority[name]
                    print "  no bias below = %d" % mst.no_bias_below[name]
                except Exception as e:
                    print 'object %s could not be loaded due to exception: %s'% (name,e)
                
            opCarving._buildDone()
           
    def isDirty(self):
        if self._o.writeProtect:return False
        return True
    
    #this is present only for the serializer AppletInterface
    def unload(self):
        pass
    
