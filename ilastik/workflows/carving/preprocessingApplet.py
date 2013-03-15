from ilastik.applets.dataSelection.dataSelectionApplet import DataSelectionApplet
from ilastik.applets.dataSelection.dataSelectionGui import DataSelectionGui ,GuiMode
from ilastik.applets.dataSelection.opDataSelection import OpMultiLaneDataSelection
from ilastik.applets.dataSelection.dataSelectionSerializer import DataSelectionSerializer, Ilastik05DataSelectionDeserializer
from ilastik.applets.base.standardApplet import StandardApplet

from opCarvingTopLevel import OpCarvingTopLevel
from carvingSerializer import CarvingSerializer
from carvingGui import CarvingGui
from preprocessingSerializer import PreprocessingSerializer
from opPreprocessingTopLevel import OpPreprocessingTopLevel
from preprocessingGui import PreprocessingGui
from opPreprocessing import OpPreprocessing
import functools

class PreprocessingApplet(StandardApplet):

    def __init__(self, workflow, title, projectFileGroupName, supportIlastik05Import=False, batchDataGui=False, force5d=False):
        super(PreprocessingApplet, self).__init__( title, workflow)
        
        self._serializableItems = [ PreprocessingSerializer(self.topLevelOperator, "preprocessing") ]
        if supportIlastik05Import:
            self._serializableItems.append(Ilastik05DataSelectionDeserializer(self.topLevelOperator))
        
        self._gui = None
        self._batchDataGui = batchDataGui
        self._title = title
    
    #
    # GUI
    #
    '''
    def createSingleLaneGui( self , laneIndex):
        guiMode = { True: GuiMode.Batch, False: GuiMode.Normal }[self._batchDataGui]
        self._gui = PreprocessingGui( self.topLevelOperator.getLane(laneIndex))
        return self._gui
    
    @property
    def topLevelOperator(self):
        return self._topLevelOperator
    '''
    @property
    def singleLaneGuiClass(self):
        return PreprocessingGui
    
    @property
    def dataSerializers(self):
        return self._serializableItems
    
    @property
    def singleLaneOperatorClass(self):
        return OpPreprocessing
    
    @property
    def broadcastingSlots(self):
        return ["Sigma","RawData"]
    
