import vigra
import threading
import numpy as np
from scipy.ndimage.interpolation import zoom
from scipy.ndimage import sobel,gaussian_filter
from time import time

#import functions written in cython
import coherenceMerge as cM

#import lazyflow stuff
from lazyflow.graph import Operator, InputSlot, OutputSlot
from ilastik.utility import OperatorSubView

import traceback
import sys

L = threading.Lock()

class OpCalcDepth(Operator):
    """
    @brief: This lazyflow operator needs a 5 dimensional light field as input,
    as well as several parameter slots have to be set. (see below)
    The output is a light field of same shape as the input but
    as single channel float32 containing the labeled disparitities.
    """
    
    name = "OpCalcDepth"
    
    inputLF = InputSlot(level=1)  # define lf input slot -> 5d numpy array lf[h,v,y,x,channel]
    outerScale = InputSlot(stype="float") # define outerscale of structure tensor input slot -> float > 0
    innerScale = InputSlot(stype="float") # define innerscale of structure tensor input slot -> float > 0
    sigmaXStrength = InputSlot(stype="float", optional = True, value = 1.0) #defines a scaling factor for the sigma in x direction
    maxLabel = InputSlot(stype="int", optional = True, value = 4) # define maximum label input slot -> float 
    minLabel = InputSlot(stype="int", optional = True, value = -4) # define minimum label input slot -> float 
    coherenceSmooth = InputSlot(stype="float", optional = True, value = 0.8) # define coherence smooth value input slot -> float > 0 
    colorMode = InputSlot(stype="int", optional = True, value = 1) # defines the color conversion mode, 0: rgb->gray, 1: rgb->hsv->v
    useThreading = InputSlot(stype="bool", optional = True, value = False)
    outputLF = OutputSlot(level=1) # define label output slot
  
  
    def execute(self, slot, subindex, roi, result):
        # the following two lines query the inputs of the
        # operator for the specififed region of interest
        
        #input and output roi are not the same, change output request roi to input roi 
        slic = roi.toSlice()
        slic = (slic[0], slice(0, self.inputLF.meta.shape[1])) + slic[2:4] + (slice(0,3),)
                
        #fetch input lf
        lf = self.inputLF[slic].wait()
        
        tmp = np.zeros((lf.shape[0],lf.shape[1],lf.shape[2],lf.shape[3],3),dtype=np.float32)
        if self.colorMode.value == 0:
            print "convert RGB LF to Gray LF"
            tmp = 0.3*lf[:,:,:,:,0]+0.59*0.3*lf[:,:,:,:,1]+0.11*lf[:,:,:,:,2]
        elif self.colorMode.value == 1:
            print "convert RGB LF to HSV LF"
            from ilastik.applets.lightfield.ImageProcessing.improc import rgbLF2hsvLF
            rgbLF2hsvLF(lf,tmp)
            tmp = tmp[:,:,:,:,2]*255
          
        lf = tmp
        
        params = {"inner":self.innerScale.value,"outer":self.outerScale.value,"sigmaXStrength":self.sigmaXStrength.value,"maxLabel":self.maxLabel.value,"minLabel":self.minLabel.value,"coherenceSmooth":self.coherenceSmooth.value}   
        labeled_h, labeled_v = label(lf,params,self.useThreading.value)
        labeled, coherence = cM._coherenceMerge(labeled_h[:,:,:,:,1],labeled_v[:,:,:,:,1],labeled_h[:,:,:,:,0],labeled_v[:,:,:,:,0])
        
#        result[:,:,:,:,0] = labeled[:]
#        result[...] = coherence.reshape(coherence.shape + (1,))[:]
        #slice the roi and return only the depth
        labeledRoi = labeled[slice(None), roi.toSlice()[1], ...]
        result[...] = labeledRoi.reshape(labeledRoi.shape + (1,))[:]
    
    
    def setupOutputs(self):
        if self.inputLF.meta.shape is None:
            print "inputLF has no shape"
            return
        self.outputLF.meta.assignFrom(self.inputLF.meta)
        shape = self.outputLF.meta.shape
        self.outputLF.meta.shape = (shape[:4] + (1,))
    
        
        # query the shape of the operator inputs
        # by reading the input slots meta dictionary
#        shapeLF = self.inputLF.meta.shape
    
#        # setup the meta dictionary of the output slot
#        self.outputLF.meta.shape = (shapeLF[0],shapeLF[1],shapeLF[2],shapeLF[3],2)
#    
#        # setup the dtype of the output slot
#        self.outputLF.meta.dtype = np.float32
#    
    def propagateDirty(self, slot, subindex, roi):
        if slot == self.inputLF:    
            roi.start[-1] = 0
            roi.stop[-1] = 1
            self.outputLF.setDirty(roi)
        elif slot == self.innerScale or slot == self.outerScale:
            self.outputLF.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"
            
    def addLane(self, laneIndex):
        numLanes = len(self.inputLF)
        assert numLanes == laneIndex, "Image lanes must be appended."        
        self.inputLF.resize(numLanes+1)
        self.outputLF.resize(numLanes+1)
        
    def removeLane(self, laneIndex, finalLength):
        self.inputLF.removeSlot(laneIndex, finalLength)
        self.outputLF.removeSlot(laneIndex, finalLength)

    def getLane(self, laneIndex):
        return OperatorSubView(self, laneIndex)

        
                     


def label(lf,params,useThreading=True):
  result_u = np.zeros((lf.shape[0],lf.shape[1],lf.shape[2],lf.shape[3],2),dtype=np.float32)
  result_v = np.zeros((lf.shape[0],lf.shape[1],lf.shape[2],lf.shape[3],2),dtype=np.float32)
  t0=time()
  
  
  if useThreading:
    threads = []
    if lf.shape[0] > 1:
      t = threading.Thread(target=labelDirection,args=(lf,result_v,params,'v',))
      threads.append(t)
      t.start()
    if lf.shape[1] > 1:
      t = threading.Thread(target=labelDirection,args=(lf,result_u,params,'u',))
      threads.append(t)
      t.start()
    for t in threads:
      t.join()
  else:
    if lf.shape[0] > 1:
      labelDirection(lf,result_v,params,'v')
    if lf.shape[1] > 1:
      labelDirection(lf,result_u,params,'u')
    
  
    
  if lf.shape[0] > 1:
    result_v[:,:,:,:,0]*=-1 #invert v channel TODO check why!
    
  print "duration:",time()-t0,"s"
  return result_u,result_v



def labelDirection(lf,result,params,direction):
  """
  @brief: labels depth regions on epipolar plane space of an 4d input lightfield 
  @param lf:<4d ndarray> input light field
  @param result:<5d ndarray> output depth and coherence structure... 
  result[:,:,:,:,0]:depth in direction, 
  result[:,:,:,:,1]:coherence in direction,
  @param params:<dictionary> parameter: {"inner","outer","maxLabel","minLabel","coherenceSmooth}
  @param direction:<char> segementation direction 'u','v'
  """
  
  if direction == 'u':
    status = lf.shape[0]
    angles = lf.shape[0]
    spatials = lf.shape[2]
  elif direction == 'v':
    status = lf.shape[1]
    angles = lf.shape[1]
    spatials = lf.shape[3]
    
    
  for angle in range(angles):
    print status," ",direction,"subspaces remain"
    status -= 1
    
    
    if direction == 'u':
      subLF = getSubspace(lf,u=angle)
    elif direction == 'v':
      subLF = getSubspace(lf,v=angle)
    
    for spatial in range(spatials):
      
      if direction == 'u':
        epi = subLF[:,spatial,:]
        
      elif direction == 'v':
        epi = subLF[:,:,spatial]
  
      try:
        #L.acquire()
        d,c = getDirections(img=epi, inner=params["inner"], outer=params["outer"], sigmaX=params["sigmaXStrength"], maxLabel=params["maxLabel"], minLabel=params["minLabel"],coherenceSmooth=params["coherenceSmooth"],direction=direction)
        #L.release()
      except Exception as e:
        print "\n\nERROR in label!"
        traceback.print_exc()
        sys.exit()
       
      #L.acquire()
      if direction == 'u':
        result[angle,:,spatial,:,0] = d[:,:]
        result[angle,:,spatial,:,1] = c[:,:]
      elif direction == 'v':     
        result[:,angle,:,spatial,0] = d[:,:]
        result[:,angle,:,spatial,1] = c[:,:]
      #L.release()
 

def getDirections(img,inner,outer,sigmaX,maxLabel,minLabel,coherenceSmooth,direction):
  """
  @brief: Calculates the directions of structures using the 
  structure tensor and returns them as well as the corresponding coherence
  @param img:<2d ndarray> input image
  @param inner:<float> inner scale of structure tensor
  @param outer:<float> outer scale of structure tensor
  @param maxLabel:<float> maximum Labelarity or allowed structure slope
  @param minLabel:<float> minimum Labelarity or allowed structure slope 
  @return: directions:<2d ndarray>, coherence:<2d ndarray>
  """
  useEVs = False
  
  try:  
    tensor,coh = structureTensor(img,inner,outer,sigmaX,coherenceSmooth,with_coherence=True)

    if useEVs:
      #using eigenvector comparison
      dirs = directionsFromTensor(tensor)
  except Exception as e:
    print "\n\nERROR in getDirections tensor and coherence evaluation!"
    traceback.print_exc()
    sys.exit()
    
  if useEVs:
    #using eigenvector comparison
    d = dirs[:,:,1]/(dirs[:,:,0]+1e-16)
  else:
    #using tangens backtransform
    dirs = 1/2.0*vigra.numpy.arctan2(2*tensor[:,:,1],tensor[:,:,2]-tensor[:,:,0])
    d = vigra.numpy.tan(-dirs)
    
      
  sign=1
  if direction == 'v':
    sign=-1
  
  if type(maxLabel)==type([]):
    np.place(d,sign*d>maxLabel[0],-1*sign*10.0)
  else:
    np.place(d,sign*d>maxLabel,-1*sign*10.0)
  if type(minLabel)==type([]):
    np.place(d,sign*d<minLabel[0],-1*sign*10.0)
  else:
    np.place(d,sign*d<minLabel,-1*sign*10.0)

    
  return d,coh



def getSubspace(lf,v=None,u=None):
  """
  @brief: Returns u/v subspaces of a 4D light field
  @param v:<int>[None] angular in v direction
  @param u:<int>[None] angular in u direction
  @return u or v: depends on not None parameter
  """
  
  if u is not None and v is None:
    try:
      return lf[u,:,:,:].astype(np.float32)
    except Exception as e:
      print "\n\nERROR in v getSubspace!"
      traceback.print_exc()
      sys.exit()
  elif v is not None and u is None:
    try:
      return lf[:,v,:,:].astype(np.float32)
    except Exception as e:
      print "\n\nERROR in u getSubspace!"
      traceback.print_exc()
      sys.exit()
    
    


def structureTensor(img,inner,outer,sigmaX,coherenceSmooth,with_coherence=False):
  """
  @brief: Calculates structure tensor and coherence of the structure tensor
  @param inner:<float> inner smoothing scale of the structure tensor
  @param inner:<float> outer smoothing scale of the structure tensor
  @param coherenceSmooth:<float> sigma for gaussian sm,ooth of the coherene
  @param with_coherence:<bool> switch on/off coherence calculation
  @return tensor,coherence:<ndarray>,<ndarray> 
  """
  coherence = None
  zoomed = False
  imshape = None
  
  
  assert len(img.shape) == 2, "Shape error in structure tensor!"

  try:
      
      tensor = vigra.filters.structureTensor(img.astype(np.float32), inner, outer)
  except:
    print "something bad happened"

 
  if zoomed:
    tmp = np.zeros((imshape[0],imshape[1],3),dtype=np.float32)
    for i in range(3):
      tmp[:,:,i] = zoom(tensor[:,:,i],zoom=0.5)
    tensor = tmp
    print "tensor shape again",tensor.shape
    
  if with_coherence:
      coherence = np.sqrt((tensor[:,:,2]-tensor[:,:,0])**2+2*tensor[:,:,1]**2)/(tensor[:,:,2]+tensor[:,:,0]+1e-16)
      if coherenceSmooth > 0:      
        coherence = vigra.filters.gaussianSmoothing(coherence,coherenceSmooth)
  
  return tensor,coherence



def directionsFromTensor(tensor):
    shape = [tensor[:,:,0].shape[0],tensor[:,:,0].shape[1]]
    o = np.zeros((tensor[:,:,0].shape[0],tensor[:,:,0].shape[1],2),dtype=np.float32)
    
    evals = vigra.filters.tensorEigenvalues(tensor)
    evecs1 = np.zeros((shape[0],shape[1],2),dtype=np.float32)
    evecs2 = np.zeros((shape[0],shape[1],2),dtype=np.float32)

    evecs1[:,:,0] = tensor[:,:,1]    
    evecs1[:,:,1] = evals[:,:,0]-tensor[:,:,0]    
    evecs2[:,:,0] = tensor[:,:,1]
    evecs2[:,:,1] = evals[:,:,1]-tensor[:,:,0]

    cM._chooseEigenVector(evals,evecs1,evecs2,o)

    return o













