from ilastik.workflow import Workflow

from lazyflow.graph import Graph

from ilastik.applets.dataSelection import DataSelectionApplet

from ilastik.applets.lightfield.lightfieldApplet import LightfieldApplet

class LightfieldWorkflow(Workflow):
    
    def __init__(self, *args, **kwargs):
        graph = Graph()
        self.graph = graph
        super(LightfieldWorkflow, self).__init__( graph = graph, *args, **kwargs)
        self._applets = []

        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.lightfieldApplet = LightfieldApplet("layer Viewer", self)
#        self.lightfieldApplet.gui.dataSelectionOperator = self.dataSelectionApplet.topLevelOperator
#        self.lightfieldApplet = LightfieldApplet2(graph)

        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.lightfieldApplet )
#        self._applets.append( self.lightfieldApplet )
        
        # Connect top-level operators
#        self.lightfieldApplet.topLevelOperator.InputImage.connect( self.dataSelectionApplet.topLevelOperator.Image )

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName
    
    
    def connectLane(self, laneIndex):
        opDataSelection = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opLightfield = self.lightfieldApplet.topLevelOperator.getLane(laneIndex)

        # Connect top-level operators
        opLightfield.Input.connect( opDataSelection.Image )
        
