'''
Created on Aug 22, 2012

@author: fredo
'''

import cython
import math
import numpy as np
cimport numpy as np
from scipy.ndimage import filters

#ctypedef np.int32_t int32_t
ctypedef np.uint8_t int_t
ctypedef Py_ssize_t index_t

def append(np.ndarray src, np.ndarray dest, tuple start):
    """
    @author: Frederik Claus
    @summary: Append the src array to the end of the dest array starting with the indices of the start tuple
    """
    _append(src,dest,start)

@cython.boundscheck(False)
@cython.wraparound(False)  
cdef _append(np.ndarray src, np.ndarray dest, tuple start):
    cdef int k,l
    cdef list kRange = range(src.shape[0])
    cdef list lRange = range(src.shape[1])
    
    for k in kRange:
        for l in lRange:
            dest[k][l+start[1]] = src[k,l]

def put(np.ndarray src, np.ndarray dest):
    """
    @author: Frederik Claus
    @summary: puts data from src array into the same position of dest array. 
    This differs from the numpy.put, because it keeps all the data in their original position
    @param src: source array must be smaller than destination array with the same dimension
    @param dest: destination array must be bigger than source array with the same dimension
    """
    _put(src,dest)
  
@cython.boundscheck(False)
@cython.wraparound(False)   
cdef _put(np.ndarray src, np.ndarray dest):
    cdef int k,l,m
    cdef list kRange = range(src.shape[2])
    cdef list lRange = range(src.shape[3])
    cdef list mRange = range(src.shape[4])
    
    for k in kRange:
        for l in lRange:
            for m in mRange:
                dest[0,0,k,l,m] = src[0,0,k,l,m]

def median(np.ndarray lf, int channel, int size):
  
    return filter(lf,filters.median_filter,{"size" : size})
 

def gauss(np.ndarray lf, int channel, float radius):

    return filter(lf,filters.gaussian_filter,{"sigma" : radius})  


"""
  convolving manually:
    tmp = lf[i,j,:,:]
    filters.convolve1d(tmp,kernel,output = tmp,axis=0)
    filters.convolve1d(tmp,kernel,output = tmp,axis=1)
    lf[i,j,:,:] = tmp
"""

@cython.boundscheck(False)
@cython.wraparound(False)
cdef filter(np.ndarray lf, filter, kwargs = None):
  
    cdef int vRes = lf.shape[0]
    cdef int hRes = lf.shape[1]
    cdef int ndim = lf.ndim
    cdef np.ndarray[int_t, ndim = 2] tmp = np.zeros(shape=(lf.shape[2],lf.shape[3]),dtype = np.uint8)
  
    if kwargs is None:
        kwargs = {}
  

    print kwargs
    for i in range(vRes):
        for j in range(hRes):
            if ndim == 4:
                tmp = lf[i,j,:,:]
                kwargs["output"] = tmp
                apply(filter,args = (tmp,),kwargs = kwargs)
                lf[i,j,:,:] = tmp
            elif ndim == 5:
                for k in range(lf.shape[4]):
                    tmp = lf[i,j,:,:,k]
                    kwargs["output"] = tmp
                    apply(filter,(tmp,),kwargs)
                    lf[i,j,:,:,k] = tmp 
    
    return lf
    
@cython.boundscheck(False)
@cython.wraparound(False)
def contrast(np.ndarray lf, int channel, float brightness, float contrast):
    cdef np.ndarray[int_t, ndim = 1] table = np.zeros(shape = 255, dtype = np.uint8)
  
    for i in range(255):
        value = (i/255.0 * brightness) - 0.5
        value = (value * contrast) + 0.5

    if i < 0:
        table[i] = 0
    elif i > 255:
        table[i] = 255
    else:
        table[i] = 255 * value
       
    if channel == -1:
        filterLf(lf,channel,table,table,table)
    else:
        for channel in range(lf.shape[4]):
            filterLf(lf, channel, table, table, table)
    
def channel(np.ndarray lf, int channel, float red, float green, float blue):
  
    cdef np.ndarray[int_t, ndim = 1] rTable = np.zeros(shape = 255, dtype = np.uint8)
    cdef np.ndarray[int_t, ndim = 1] gTable = rTable.copy()
    cdef np.ndarray[int_t, ndim = 1] bTable = rTable.copy()
  
    _channel(rTable,red)
    if green == red:
        gTable = rTable.copy()
    else:
        _channel(gTable,green)
        
    if blue == red:
        bTable = rTable.copy()
    elif blue == green:
        bTable = gTable.copy()
    else:
        _channel(bTable,blue)
      
    filterLf(lf,channel,rTable,gTable,bTable)
    
@cython.boundscheck(False)
@cython.wraparound(False)
cdef _channel(np.ndarray[int_t, ndim = 1] table, float weight):
  
    for i in range(255):
        table[i] = int(weight * i)


@cython.boundscheck(False)
@cython.wraparound(False)
def gamma(np.ndarray lf, float gamma, int channel):
    cdef np.ndarray[int_t,ndim = 1] table = np.zeros(shape = 255,dtype = np.uint8)
    
    for i in range(255):
        value = 255.0 * pow(i/255.0,1.0/gamma) + 0.5
        if value > 255:
            value = 255
        table[i] = int(value)
        
    if channel != -1:
        filterLf(lf,channel,table,table,table)
    else:
        for channel in range(lf.shape[4]):
            filterLf(lf, channel, table, table, table)

@cython.boundscheck(False)
@cython.wraparound(False)
cdef filterLf(np.ndarray lf,
              int channel,
              np.ndarray[int_t, ndim = 1] rTable, 
              np.ndarray[int_t, ndim = 1] gTable,
              np.ndarray[int_t, ndim = 1] bTable):

    cdef int ndim = lf.ndim
    
    cdef int vRes,hRes
    vRes = lf.shape[0]
    hRes = lf.shape[1]
    
    if channel == 0:
        selectedTable = rTable
    elif channel == 1:
        selectedTable = gTable
    else:
        selectedTable = bTable
  
    for i in range(vRes):
        for j in range(hRes):
#            yRes = lf.shape[2]
#            xRes = lf.shape[3]
#            
#            for k in range(yRes):
#                for l in range(xRes):
#                    index = lf[i,j,k,l,channel]
#                    lf[i,j,k,l,channel] = selectedTable[index - 1]

            _filter(lf[i,j,:,:,channel],selectedTable)
                        
    
    
@cython.boundscheck(False)
@cython.wraparound(False)
cdef _filter(np.ndarray[int_t, ndim = 2] im, np.ndarray[int_t,ndim = 1] table):

    cdef int yRes = im.shape[0]
    cdef int xRes = im.shape[1]
    

    for i in range(yRes):
        for j in range(xRes):
            index = im[i,j]
            im[i,j] = table[index - 1]

#@cython.boundscheck(False)
#@cython.wraparound(False)
#cpdef (np.ndarray[int_t, ndim=3] evals, np.ndarray[float_t, ndim=3] evecs1, np.ndarray[float_t, ndim=3] evecs2, np.ndarray[float_t, ndim=3] o):
#
#  cdef int shape_0 = evals.shape[0]
#  cdef int shape_1 = evals.shape[1]
#  cdef index_t i,j
#  
#  for i in range(shape_0):
#    for j in range(shape_1):
#      if evals[i,j,0] < evals[i,j,1]:
#        o[i,j,0] = evecs1[i,j,0]
#        o[i,j,1] = evecs1[i,j,1]
#      else:
#        o[i,j,0] = evecs2[i,j,0]
#        o[i,j,1] = evecs2[i,j,1]

#@cython.boundscheck(False)
#@cython.wraparound(False)
#def _makegausskernel(float radius):
#  
#  cdef int r = math.ceil(radius)
#  cdef int rows = r * 2+1
#  cdef np.ndarray matrix = np.zeros(shape = rows)
#  cdef float sigma = radius/3
#  cdef float sigma22 = 2*sigma*sigma
#  cdef float sigmaPi2 = 2*math.pi*sigma
#  cdef float sqrtSigmaPi2 = math.sqrt(sigmaPi2)
#  cdef float radius2 = radius*radius
#  cdef float total = 0.0
#  cdef int index = 0
#  cdef list nRows = range(rows)
#  cdef int row,i
#  
#  nRows.reverse()
#  
#  for row in nRows:
#    distance = row*row;
#    if (distance > radius2):
#        matrix[index] = 0
#    else:
#        matrix[index] = math.exp(-(distance)/sigma22) / sqrtSigmaPi2
#    total += matrix[index]
#    index += 1
#    
#  for i in range(rows):
#    matrix[i] /= total
#    
#  return matrix