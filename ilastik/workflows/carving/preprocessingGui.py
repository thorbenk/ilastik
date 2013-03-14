from PyQt4.QtCore import Qt, QVariant
from PyQt4.QtGui import *
from PyQt4 import uic

from ilastik.applets.dataSelection.opDataSelection import OpDataSelection, DatasetInfo
from ilastik.applets.dataSelection.dataSelectionGui import DataSelectionGui
from ilastik.applets.base.appletGuiInterface import AppletGuiInterface

from functools import partial
import os
import copy
import glob
import threading
import h5py

from volumina.utility import PreferencesManager
from volumina.volumeEditor import VolumeEditor
from volumina.volumeEditorWidget import VolumeEditorWidget
from volumina.api import LayerStackModel
from volumina.adaptors import Op5ifyer

from ilastik.shell.gui.iconMgr import ilastikIcons
from ilastik.utility import bind
from ilastik.utility.gui import ThreadRouter, threadRouted
from ilastik.utility.pathHelpers import getPathVariants

from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

from ilastik.applets.base.applet import ControlCommand

from preprocessingViewerGui import PreprocessingViewerGui

import vigra

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)
from lazyflow.utility import Tracer

class Column():
    """ Enum for table column positions """
    Name = 0
    Location = 1
    InternalID = 2
    LabelsAllowed = 3 # Note: For now, this column must come last because it gets removed in batch mode.
    
    NumColumns = 4

class LocationOptions():
    """ Enum for location menu options """
    Project = 0
    AbsolutePath = 1
    RelativePath = 2

class GuiMode():
    Normal = 0
    Batch = 1


class PreprocessingGui(QMainWindow):
    def __init__(self, topLevelOperatorView):
        super(PreprocessingGui,self).__init__()
        
        self.drawer = None
        self.threadRouter = ThreadRouter(self)
        self.guiMode = 1
        self.topLevelOperatorView = topLevelOperatorView
        self.initAppletDrawerUic()
        self.centralGui = PreprocessingViewerGui(self.topLevelOperatorView)
        
    def initAppletDrawerUic(self):
        """
        Load the ui file for the applet drawer, which we own.
        """
        with Tracer(traceLogger):
            # Load the ui file (find it in our own directory)
            localDir = os.path.split(__file__)[0]+'/'
            # (We don't pass self here because we keep the drawer ui in a separate object.)
            self.drawer = uic.loadUi(localDir+"/PreprocessingDrawer.ui")
            
            # Set up radiobox layout
            self.filterbuttons = [self.drawer.filter1,
                                    self.drawer.filter2,
                                    self.drawer.filter3,
                                    self.drawer.filter4,
                                    self.drawer.filter5]
            
            self.filterbuttons[self.topLevelOperatorView.Filter.value].setChecked(True)
            self.correspondingSigmaMins = [0.9,0.9,0.6,-float("infinity"),-float("infinity")]
            
            # Set up our handlers
            for f in self.filterbuttons:
                f.clicked.connect(self.handleFilterChanged)
            
            self.drawer.runButton.clicked.connect(self.handleRunButtonClicked)
            self.drawer.runButton.setIcon( QIcon(ilastikIcons.Play) )
            
            self.drawer.sigmaSpin.setValue(self.topLevelOperatorView.Sigma.value)
            self.drawer.sigmaSpin.valueChanged.connect(self.handleSigmaValueChanged)
            
            self.drawer.writeprotectBox.clicked.connect(self.handleWriterprotectBoxClicked)
    
    def handleFilterChanged(self):
        choice =  [f.isChecked() for f in self.filterbuttons].index(True)
        
        #update lower bound for sigma
        self.drawer.sigmaSpin.setMinimum(self.correspondingSigmaMins[choice])
        self.topLevelOperatorView.Filter.setValue(choice)
        
    def handleSigmaValueChanged(self):
        self.topLevelOperatorView.Sigma.setValue(self.drawer.sigmaSpin.value())
    
    def handleRunButtonClicked(self):
        print self.topLevelOperatorView.PreprocessedData[:].wait()
        self.topLevelOperatorView.PreprocessedData[:].wait()
        
    def handleWriterprotectBoxClicked(self):
        self.topLevelOperatorView.setWriteProtect(self.drawer.writeprotectBox.checkState())
    
    def centralWidget( self ):
        return self.centralGui
        #return QWidget()
    
    def appletDrawer( self ):
        return self.drawer
        
    def menus( self ):
        return []
        
    def viewerControlWidget(self):
        return QWidget()
    
    def setImageIndex(self,imageIndex):
        pass
    def laneAdded(self,imageIndex):
        pass
    def laneRemoved(self,laneIndex,finalLength):
        pass
    def stopAndCleanUp(self):
        #ToDo: Clea Up!
        pass
    
    
    
