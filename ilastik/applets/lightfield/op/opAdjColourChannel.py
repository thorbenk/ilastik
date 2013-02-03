'''
Created on Nov 13, 2012

@author: fredo
'''

from lazyflow.graph import Operator,InputSlot,OutputSlot

class OpAdjColorChannels(Operator):
    
    name = "OpAdjColorChannels"
    
    Input = InputSlot()
    
    RedScale = InputSlot()
    GreenScale = InputSlot()
    BlueScale = InputSlot()
    
    Output = OutputSlot()

    def setupOutputs(self):
        assert self.Input.meta.shape[-1] == 3
        self.Output.meta.assignFrom(self.Input.meta)

    def execute(self, slot, subindex, roi, result):
        result[:] = self.Input.get(roi).wait()

        result[...,0] = result[...,0] * self.RedScale.value
        result[...,1] = result[...,1] * self.GreenScale.value
        result[...,2] = result[...,2] * self.BlueScale.value

        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Input:
            self.Output.setDirty(roi)
        elif slot == self.RedScale or slot == self.GreenScale or slot == self.BlueScale:
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"