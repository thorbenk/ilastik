'''
Created on Dec 2, 2012

@author: fredo
'''
from unittest import TestCase

from opAdjColourChannel import OpAdjColorChannels
from opAdjGamma import OpAdjGamma
from opAdjContrast import OpAdjContrast

from lazyflow.graph import Graph
import numpy as np

class opTest(TestCase):
    
    def setUp(self):
        self.graph = Graph()
        
    def testColorChannels(self):
        op = OpAdjColorChannels(graph=self.graph)
        lf = np.ones((3,3,3))
        op.Input.setValue(lf)
        op.BlueScale.setValue(0)
        op.RedScale.setValue(2)
        op.GreenScale.setValue(0.5)
        lf = op.Output[0,0].wait()
        expected = np.array([2, 0.5, 0])
        self.assertNpEqual(expected, lf)
        
    def testGamma(self):
        op = OpAdjGamma(graph=self.graph)
        lf = self.oneRow(100)
        op.Input.setValue(lf)
        op.Gamma.setValue(0.5)
        lf = op.Output[:].wait()
        expected = self.oneRow(38)
        self.assertNpEqual(expected, lf)
        
    def testContrast(self):
        lf = self.oneRow(100)
        op = OpAdjContrast(graph=self.graph)
        op.Input.setValue(lf)
        op.Brightness.setValue(1.2)
        op.Contrast.setValue(1.0)
        lf = op.Output[:].wait()
        print lf
        
    def oneRow(self, value):
        return np.array([[[[[value, value, value]]]]], dtype=np.uint8)
    
    def assertNpEqual(self, expected, actual):
        self.assertTrue((expected == actual).all())