'''
Created on Oct 14, 2012

@author: fredo
'''
from lazyflow.graph import OperatorWrapper
from ilastik.applets.base.standardApplet import StandardApplet
from opLightfield import OpLightfield
from opCalcDepth import OpCalcDepth

class LightfieldApplet( StandardApplet ):
    """
    This is a simple viewer applet
    """
    def __init__( self, projectFileGroupName, workflow ):
        self._topLevelOperator = OpLightfield(parent = workflow)
        super(LightfieldApplet, self).__init__(projectFileGroupName, workflow)

#        self._topLevelOperator = OperatorWrapper( OpLightfield, graph=workflow.graph, promotedSlotNames=set(['InputImage']) )
#        self._topLevelOperator = OpLightfield(parent = workflow)
        
        self._preferencesManager = None
        self._serializableItems = []
#        self._gui = None

    
    @property
    def singleLaneGuiClass(self):
        from lightfieldGui import LightfieldGui
        return LightfieldGui
    
    @property
    def singleLaneOperatorClass(self):
        return OpLightfield
    
    @property
    def broadcastingSlots(self):
        return ["outerScale", "innerScale"]
#        return ["InputImage"]
#        return []
    
    @property
    def dataSerializers(self):
        return self._serializableItems

#    @property
#    def topLevelOperator(self):
#        return self._topLevelOperator
    