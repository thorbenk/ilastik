'''
Created on Sep 6, 2012

@author: fredo
'''

from lazyflow.graph import Operator, InputSlot, OutputSlot
import NativeUtil as native

class OpConvlMedian(Operator):
    
    name = "OpConvlMedian"
    
    Input = InputSlot()
    
    Brightness = InputSlot()
    
    Output = OutputSlot()
        
    def execute(self, slot, roi, result):
        lf = self.Input[roi.toSlice()].wait()
        size = self.Brightness.value
        lf = native.median(lf,size)
        result[...] = lf
        
    def setupOutputs(self):
        self.Output.assignFrom(self.Intput.meta.shape)
        
    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Input:
            self.Output.setDirty(roi)
        elif slot == self.Brightness:
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"
    

if __name__ == "__main__":
    
    from LFOp.Read.Blender import connectBlender
    from LFOp import settings
    median = OpConvlMedian()
    median.Brightness.setValue(4)

    connectBlender(median, slize = (0,(0,10)))
    
    from LFOp.View.Simple import viewLf
    from LFOp.Write.PNG import writePNG
    writePNG(median,settings.TEST_384x25_MULTIPLE_MEDIAN_IMAGE)