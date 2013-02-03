'''
Created on Aug 22, 2012

@author: fredo
'''

'''
Created on Jul 9, 2012

@author: fredo
'''


from lazyflow.graph import Operator, InputSlot, OutputSlot
import NativeUtil as native

class OpAdjGamma(Operator):
    
    name = "OpAdjGamma"

    Input = InputSlot()
    
    Gamma = InputSlot()
    
    Output = OutputSlot()
    
    def execute(self, slot, subindex, roi, result):
        lf = self.Input[roi.toSlice()].wait()
        gamma = self.Gamma.value
  #      print "before: ",lf
        native.gamma(lf, gamma, -1)
  #      print "after: ",lf
        result[...] = lf
        
    def setupOutputs(self):
        assert len(self.Input.meta.shape) == 5, "Input must have at least 5 dimensions"
        self.Output.meta.assignFrom(self.Input.meta)
        
    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Input:
            self.Output.setDirty(roi)
        elif slot == self.Gamma:
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"


if __name__ == "__main__":
    from LFOp.Read.Blender import connectBlender
    from LFOp import settings
    gamma = OpAdjGamma()
    
    connectBlender(gamma,slize = (0,(0,10)))
    gamma.Gamma.setValue(0.2)
    
    from LFOp.View.Simple import viewLf
    from LFOp.Write.PNG import writePNG
    writePNG(gamma,settings.TEST_384x25_MULTIPLE_GAMMA_IMAGE)