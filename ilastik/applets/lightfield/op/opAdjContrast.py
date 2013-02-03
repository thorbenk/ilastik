'''
Created on Dec 1, 2012

@author: fredo
'''
from lazyflow.graph import Operator, InputSlot, OutputSlot
import NativeUtil as native

class OpAdjContrast(Operator):
    
    name = "OpAdjContrast"
    
    Input = InputSlot()
    
    Brightness = InputSlot(stype="float")
    Contrast = InputSlot(stype="float")
    
    Output = OutputSlot()

    def execute(self, slot, subindex, roi, result):
      
        brightness = self.Brightness.value
        contrast = self.Contrast.value
        lf = self.Input[roi.toSlice()].wait()
        
        native.contrast(lf,-1,brightness,contrast)
        result[...] = lf
    
    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        
    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Input:
            self.Output.setDirty(roi)
        elif slot == self.Brightness or slot == self.Contrast: 
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"
        

