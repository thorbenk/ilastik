'''
Created on Sep 6, 2012

@author: fredo
'''

from lazyflow.graph import Operator, InputSlot, OutputSlot
import NativeUtil as native
from scipy.ndimage.filters import convolve

class OpConvlGauss(Operator):
    
    """
    @author: Frederik Claus
    @summary: Applies a gaussion blur to the lf
    @param Radius: radius of the blur in pixel. If Radius == 0 lf is left untouched.
    @param inLf: input lf
    """
    name = "OpConvlGauss"
      
    Input = InputSlot()
    
    Radius = InputSlot()
    
    Output = OutputSlot()
    
    def execute(self, slot, roi, result):
        lf = self.Input[roi.toSlice()].wait()
        radius = self.Radius.value
        if radius != 0:
            lf = native.gauss(lf,radius)
        result[...] = lf
    
    def setupOutputs(self):
        self.Output.assignFrom(self.Intput.meta.shape)
        
    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Input:
            self.Output.setDirty(roi)
        elif slot == self.Radius:
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"
    
    

if __name__ == "__main__":
    
    from LFOp.Read.Blender import connectBlender
    gauss = OpConvlGauss()
  

    connectBlender(gauss, slize =(0,(0,10)))
    gauss.Radius.setValue(5)
    
    from LFOp.Write.PNG import writePNG
    from LFOp.View.Simple import viewLf
    from LFOp import settings
    writePNG(gauss,settings.TEST_384x25_MULTIPLE_GAUSSIAN_IMAGE)