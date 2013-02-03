'''
Created on Oct 27, 2012

@author: fredo
'''
from lazyflow.graph import Operator,InputSlot, OutputSlot
import logging
#import NativeUtil as nativeOperations
from opCalcDepth import OpCalcDepth
from ilastik.utility import OperatorSubView, MultiLaneOperatorABC
from lazyflow.stype import ArrayLike


class OpLightfield(Operator):
    """
    @author: Frederik Claus
    @summary: Performs various operations on a lightfield
    """
    
    name="OpLightfield"
    
    
    #===========================================================================
    # MultiImageOperator
    #===========================================================================
#    Input = InputSlot(level = 1, stype = ArrayLike)
#    Output = OutputSlot(level = 1, stype = ArrayLike)


    #===========================================================================
    # SingleImageOperator
    #===========================================================================
    Input = InputSlot(stype = ArrayLike)    
    Output = OutputSlot(stype = ArrayLike)
    
    
    outerScale = InputSlot(stype="float")
    innerScale = InputSlot(stype="float")


    
    
    logger = logging.getLogger(__name__)
    
    def __init__(self, *args, **kwargs):
        super(OpLightfield, self).__init__(*args, **kwargs)
        #=======================================================================
        # connect inputs
        #=======================================================================
#        self.opDepth = OpCalcDepth(parent = self)
#        self.opDepth.inputLF.connect(self.InputImage)
#        self.opDepth.outerScale.connect(self.outerScale)
#        self.opDepth.innerScale.connect(self.innerScale)
        #=======================================================================
        # connect outputs
        #=======================================================================
#        self.opDepth.outputLF.connect(self.Output)
#        self.Output.connect(self.opDepth.outputLF)
        
    
    def setupOutputs(self):
        print "Setting up outputs. Input shape is %s" % str(self.Input.meta.shape)
        self.Output.meta.assignFrom(self.Input.meta)
        

        
    def execute(self, slot, subindex, roi, result):
        raise RuntimeError("It works!")
        

    
    def propagateDirty(self, slot, subindex, roi):
        print "%s has changed. Propagating change." % slot.name
        if slot == self.Input:    
            roi.start[-1] = 0
            roi.stop[-1] = 1
            self.Output.setDirty(roi)
        elif slot == self.innerScale or slot == self.outerScale:
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"
    
    #===========================================================================
    # MultiOperatorABC
    #===========================================================================
    
#    def addLane(self, laneIndex):
#        numLanes = len(self.Input)
#        assert numLanes == laneIndex, "Input lanes must be appended."        
#        self.Input.resize(numLanes+1)
#        self.Output.resize(numLanes+1)
##        return self.opDepth.addLane(laneIndex)
#        
#    def removeLane(self, laneIndex, finalLength):
#        self.Input.removeSlot(laneIndex, finalLength)
#        self.Output.removeSlot(laneIndex, finalLength)
##        return self.opDepth.removeLane(laneIndex, finalLength)
#    
#
#    def getLane(self, laneIndex):
##        return self.opDepth.getLane(laneIndex)
#        return OperatorSubView(self, laneIndex) 
         
#assert issubclass(OpLightfield, MultiLaneOperatorABC)       
    

        
        
        