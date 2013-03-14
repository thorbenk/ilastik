from collections import defaultdict
import numpy

from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper

from volumina.adaptors import Op5ifyer

from opCarving import OpCarving
from opPreprocessing import OpPreprocessing

from ilastik.utility import OperatorSubView, OpMultiLaneWrapper

class OpPreprocessingTopLevel(Operator):
    name = "OpPreprocessingTopLevel"
    
    RawData = InputSlot(level=1)
    
    PreprocessedData = OutputSlot(level=1)

    ###
    # Multi-lane Operator
    ###
            
    def addLane(self, laneIndex):
        # Just add to our input slot, which will propagate to the rest of the internal connections
        assert len(self.RawData) == laneIndex
        self.RawData.resize(laneIndex+1)
        self.Sigma.resize(laneIndex+1)

    def removeLane(self, index, final_length):
        # Just remove from our input slot, which will propagate to the rest of the internal connections
        assert len(self.RawData) == final_length + 1
        self.RawData.removeSlot( index, final_length )
        self.Sigma.removeSlot( index, final_length )
    
    def getLane(self, laneIndex):
        return OperatorSubView(self, laneIndex)
        
    def __init__(self, parent=None):
        super(OpPreprocessingTopLevel, self).__init__(parent=parent)

        # Convert data to 5d before giving it to the real operators
        op5 = OpMultiLaneWrapper( Op5ifyer, parent=self, graph=self.graph )
        op5.input.connect( self.RawData )
        self.opPreprocessing = OpMultiLaneWrapper( OpPreprocessing, parent=self )
        self.opPreprocessing.RawData.connect( op5.output )
        
        self.PreprocessedData.connect(self.opPreprocessing.PreprocessedData)
