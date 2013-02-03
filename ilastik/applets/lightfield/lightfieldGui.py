'''
Created on Oct 14, 2012

@author: fredo
'''
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from PyQt4 import uic
import os
useVTK = True
import numpy as np
import logging
from ilastik.utility import bind


class LightfieldGui(LayerViewerGui):
    
    APPLET_DRAWER_PATH = os.path.join(os.path.dirname(__file__),"drawerNew.ui")
    logger = logging.getLogger(__name__)
    
    def __init__(self, toplevelOperatorView):
        self.topLevelOperatorView = toplevelOperatorView
        super(LightfieldGui,self).__init__(toplevelOperatorView)
                
        
    def initAppletDrawerUi(self):
        self._drawers = uic.loadUi(self.APPLET_DRAWER_PATH)
        self._drawers.editDepthSubmit.clicked.connect(self.editDepth)
        
#        def updateDrawerFromOperator():
#            innerScale, outerScale = (0.8,0.6)
#
#            if self.topLevelOperatorView.innerScale.ready():
#                innerScale = self.topLevelOperatorView.ScalingFactor.value
#            if self.topLevelOperatorView.outerScale.ready():
#                outerScale = self.topLevelOperatorView.Offset.value
#
#            self._drawer.editDepthInner.setValue(innerScale)
#            self._drawer.editDepthOuter.setValue(outerScale)
#            
#        self.topLevelOperatorView.innerScale.notifyDirty( bind(updateDrawerFromOperator) )
#        self.topLevelOperatorView.outerScale.notifyDirty( bind(updateDrawerFromOperator) )
        
#        if not self.topLevelOperatorView.innerScale.ready():
#            self.topLevelOperatorView.
        
        
        
    def appletDrawer(self):
#        return [("Lightfield View", self._drawers )]
        return self._drawers
    
    def editDepth(self):
        inner = self._drawers.editDepthInner.value()
        outer = self._drawers.editDepthOuter.value()

        self.topLevelOperatorView.innerScale.setValue(inner)
        self.topLevelOperatorView.outerScale.setValue(outer)
        

    
#    def setupLayers(self ):
#        layers = []
#
#        # Show the Output data
#        outputImageSlot = self.topLevelOperatorView.outputLF
#        if outputImageSlot.ready():
#            outputLayer = self.createStandardLayerFromSlot( outputImageSlot )
#            outputLayer.name = "outputlf"
#            outputLayer.visible = True
#            outputLayer.opacity = 1.0
#            layers.append(outputLayer)
#        
#        return layers
#        # Show the thresholded data
#        outputImageSlot = self.topLevelOperatorView.Output[ currentImageIndex ]
#        if outputImageSlot.ready():
#            outputLayer = self.createStandardLayerFromSlot( outputImageSlot )
#            outputLayer.name = "min <= x <= max"
#            outputLayer.visible = True
#            outputLayer.opacity = 0.75
#            layers.append(outputLayer)
        
#        # Show the  data
#        invertedOutputSlot = self.topLevelOperatorView.InvertedOutput[ currentImageIndex ]
#        if invertedOutputSlot.ready():
#            invertedLayer = self.createStandardLayerFromSlot( invertedOutputSlot )
#            invertedLayer.name = "(x < min) U (x > max)"
#            invertedLayer.visible = True
#            invertedLayer.opacity = 0.25
#            layers.append(invertedLayer)
        
        # Show the raw input data
#        inputImageSlot = self.topLevelOperatorView.InputImage[ currentImageIndex ]
#        if inputImageSlot.ready():
#            inputLayer = self.createStandardLayerFromSlot( inputImageSlot )
#            inputLayer.name = "Raw Input"
#            inputLayer.visible = True
#            inputLayer.opacity = 1.0
#            layers.append(inputLayer)
#
#        return layers
    
        
