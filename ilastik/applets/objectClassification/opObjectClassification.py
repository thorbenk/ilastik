import numpy
import vigra
import warnings

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import List
from lazyflow.operators import OpValueCache
from lazyflow.request import Request, RequestPool
from functools import partial

from ilastik.utility import OperatorSubView, MultiLaneOperatorABC, OpMultiLaneWrapper
from ilastik.utility.mode import mode

from ilastik.applets.objectExtraction import config

# WARNING: since we assume the input image is binary, we also assume
# that it only has one channel. If there are multiple channels, only
# features from the first channel are used in this operator.

class OpObjectClassification(Operator, MultiLaneOperatorABC):
    name = "OpObjectClassification"
    category = "Top-level"

    ###############
    # Input slots #
    ###############
    BinaryImages = InputSlot(level=1) # for visualization
    RawImages = InputSlot(level=1) # for visualization
    SegmentationImages = InputSlot(level=1) #connected components
    ObjectFeatures = InputSlot(rtype=List, stype=Opaque, level=1)
    LabelsAllowedFlags = InputSlot(stype='bool', level=1)
    LabelInputs = InputSlot(stype=Opaque, rtype=List, optional=True, level=1)

    ################
    # Output slots #
    ################
    NumLabels = OutputSlot()
    Classifier = OutputSlot()
    LabelImages = OutputSlot(level=1)
    Predictions = OutputSlot(level=1, stype=Opaque, rtype=List)
    Probabilities = OutputSlot(level=1, stype=Opaque, rtype=List)
    PredictionImages = OutputSlot(level=1) #Labels, by the majority vote
    PredictionProbabilityChannels = OutputSlot(level=2) # Classification predictions, enumerated by channel
    SegmentationImagesOut = OutputSlot(level=1) #input connected componen

    # TODO: not actually used
    Eraser = OutputSlot()
    DeleteLabel = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpObjectClassification, self).__init__(*args, **kwargs)

        # internal operators
        opkwargs = dict(parent=self)
        self.opTrain = OpObjectTrain(parent=self)
        self.opPredict = OpMultiLaneWrapper(OpObjectPredict, **opkwargs)
        self.opLabelsToImage = OpMultiLaneWrapper(OpRelabelSegmentation, **opkwargs)
        self.opPredictionsToImage = OpMultiLaneWrapper(OpRelabelSegmentation, **opkwargs)
        self.opProbabilityChannelsToImage = OpMultiLaneWrapper(OpMultiRelabelSegmentation, **opkwargs)

        self.classifier_cache = OpValueCache(parent=self)

        # connect inputs
        self.opTrain.inputs["Features"].connect(self.ObjectFeatures)
        self.opTrain.inputs['Labels'].connect(self.LabelInputs)
        self.opTrain.inputs['FixClassifier'].setValue(False)

        self.classifier_cache.inputs["Input"].connect(self.opTrain.outputs['Classifier'])

        # Find the highest label in all the label images
        self.opMaxLabel = OpMaxLabel( parent=self, graph=self.graph)
        self.opMaxLabel.Inputs.connect( self.LabelInputs )

        self.opPredict.inputs["Features"].connect(self.ObjectFeatures)
        self.opPredict.inputs["Classifier"].connect(self.classifier_cache.outputs['Output'])
        self.opPredict.inputs["LabelsCount"].connect(self.opMaxLabel.Output)

        self.opLabelsToImage.inputs["Image"].connect(self.SegmentationImages)
        self.opLabelsToImage.inputs["ObjectMap"].connect(self.LabelInputs)
        self.opLabelsToImage.inputs["Features"].connect(self.ObjectFeatures)

        self.opPredictionsToImage.inputs["Image"].connect(self.SegmentationImages)
        self.opPredictionsToImage.inputs["ObjectMap"].connect(self.opPredict.Predictions)
        self.opPredictionsToImage.inputs["Features"].connect(self.ObjectFeatures)
        
        self.opProbabilityChannelsToImage.inputs["Image"].connect(self.SegmentationImages)
        self.opProbabilityChannelsToImage.inputs["ObjectMaps"].connect(self.opPredict.ProbabilityChannels)
        self.opProbabilityChannelsToImage.inputs["Features"].connect(self.ObjectFeatures)
        
        
        
        # connect outputs
        self.NumLabels.connect( self.opMaxLabel.Output )
        self.LabelImages.connect(self.opLabelsToImage.Output)
        self.Predictions.connect(self.opPredict.Predictions)
        self.Probabilities.connect(self.opPredict.Probabilities)
        self.PredictionImages.connect(self.opPredictionsToImage.Output)
        self.PredictionProbabilityChannels.connect(self.opProbabilityChannelsToImage.Output)
        #self.Classifier.connect(self.opTrain.Classifier)
        self.Classifier.connect(self.classifier_cache.Output)

        self.SegmentationImagesOut.connect(self.SegmentationImages)
        
        

        self.Eraser.setValue(100)
        self.DeleteLabel.setValue(-1)

        def handleNewInputImage(multislot, index, *args):
            def handleInputReady(slot):
                self.setupCaches(multislot.index(slot))
            multislot[index].notifyReady(handleInputReady)

        self.SegmentationImages.notifyInserted(handleNewInputImage)

    def setupCaches(self, imageIndex):
        """Setup the label input to correct dimensions"""
        numImages=len(self.SegmentationImages)
        self.LabelInputs.resize(numImages)
        self.LabelInputs[imageIndex].meta.shape = (1,)
        self.LabelInputs[imageIndex].meta.dtype = object
        self.LabelInputs[imageIndex].meta.mapping_dtype = numpy.uint8
        self.LabelInputs[imageIndex].meta.axistags = None
        self._resetLabelInputs(imageIndex)

    def _resetLabelInputs(self, imageIndex, roi=None):
        labels = dict()
        for t in range(self.SegmentationImages[imageIndex].meta.shape[0]):
            labels[t] = numpy.zeros((2,))
        self.LabelInputs[imageIndex].setValue(labels)

    def setupOutputs(self):
        pass

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def propagateDirty(self, slot, subindex, roi):
        pass

    def assignObjectLabel(self, imageIndex, coordinate, assignedLabel):
        """
        Update the assigned label of the object located at the given coordinate.
        Does nothing if no object resides at the given coordinate.
        """
        segmentationShape = self.SegmentationImagesOut[imageIndex].meta.shape
        assert len(coordinate) == len( segmentationShape ), "Coordinate: {} is has the wrong length for this image, which is of shape: {}".format( coordinate, segmentationShape )
        slicing = tuple(slice(i, i+1) for i in coordinate)
        arr = self.SegmentationImagesOut[imageIndex][slicing].wait()
        
        objIndex = arr.flat[0]
        if objIndex == 0: # background; FIXME: do not hardcode
            return
        timeCoord = coordinate[0]
        labelslot = self.LabelInputs[imageIndex]
        labelsdict = labelslot.value
        labels = labelsdict[timeCoord]

        nobjects = len(labels)
        if objIndex >= nobjects:
            newLabels = numpy.zeros((objIndex + 1),)
            newLabels[:nobjects] = labels[:]
            labels = newLabels
        labels[objIndex] = assignedLabel
        labelsdict[timeCoord] = labels
        labelslot.setValue(labelsdict)
        labelslot.setDirty([(timeCoord, objIndex)])

    def addLane(self, laneIndex):
        numLanes = len(self.SegmentationImages)
        assert numLanes == laneIndex, "Image lanes must be appended."
        for slot in self.inputs.values():
            if slot.level > 0 and len(slot) == laneIndex:
                slot.resize(numLanes + 1)

    def removeLane(self, laneIndex, finalLength):
        for slot in self.inputs.values():
            if slot.level > 0 and len(slot) == finalLength + 1:
                slot.removeSlot(laneIndex, finalLength)

    def getLane(self, laneIndex):
        return OperatorSubView(self, laneIndex)


def _atleast_nd(a, ndim):
    """Like numpy.atleast_1d and friends, but supports arbitrary ndim,
    always puts extra dimensions last, and resizes.

    """
    if ndim < a.ndim:
        return
    nnew = ndim - a.ndim
    newshape = tuple(list(a.shape) + [1] * nnew)
    a.resize(newshape)


def _concatenate(arrays, axis):
    """wrapper to numpy.concatenate that resizes arrays first."""
    arrays = list(a for a in arrays if 0 not in a.shape)
    if len(arrays) == 0:
        return numpy.array([])
    maxd = max(max(a.ndim for a in arrays), 2)
    for a in arrays:
        _atleast_nd(a, maxd)
    return numpy.concatenate(arrays, axis=axis)


class OpObjectTrain(Operator):
    name = "TrainRandomForestObjects"
    description = "Train a random forest on multiple images"
    category = "Learning"

    Labels = InputSlot(level=1, stype=Opaque, rtype=List)
    Features = InputSlot(level=1, rtype=List, stype=Opaque)
    FixClassifier = InputSlot(stype="bool")
    ForestCount = InputSlot(stype="int", value=1)

    Classifier = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpObjectTrain, self).__init__(*args, **kwargs)
        self._tree_count = 100
        self.FixClassifier.setValue(False)

    def setupOutputs(self):
        if self.inputs["FixClassifier"].value == False:
            self.outputs["Classifier"].meta.dtype = object
            self.outputs["Classifier"].meta.shape = (self.ForestCount.value,)
            self.outputs["Classifier"].meta.axistags = None

    def execute(self, slot, subindex, roi, result):
        featMatrix = []
        labelsMatrix = []

        for i in range(len(self.Labels)):
            feats = self.Features[i]([]).wait()

            # TODO: we should be able to use self.Labels[i].value,
            # but the current implementation of Slot.value() does not
            # do the right thing.
            labels = self.Labels[i]([]).wait()

            for t in sorted(feats.keys()):
                featsMatrix_tmp = []
                labelsMatrix_tmp = []
                lab = labels[t].squeeze()
                index = numpy.nonzero(lab)
                labelsMatrix_tmp.append(lab[index])

                #check that all requested features are present
                for featname in config.selected_features:
                    for channel in feats[t]:
                        if not featname in channel.keys():
                            print "Feature", featname, "has not been computed in the previous step"
                            print "We only have the following features now:", channel.keys()
                            result[:] = None
                            return
                        else:
                            value = channel[featname]
                            ft = numpy.asarray(value.squeeze())
                            featsMatrix_tmp.append(ft[index])
                
                featMatrix.append(_concatenate(featsMatrix_tmp, axis=1))
                labelsMatrix.append(_concatenate(labelsMatrix_tmp, axis=1))

        featMatrix = _concatenate(featMatrix, axis=0)
        labelsMatrix = _concatenate(labelsMatrix, axis=0)
        print "training on matrix:", featMatrix.shape
        
        if len(featMatrix) == 0 or len(labelsMatrix) == 0:
            result[:] = None
            return
        oob = [0]*self.ForestCount.value
        try:
            # Ensure there are no NaNs in the feature matrix
            # TODO: There should probably be a better way to fix this...
            featMatrix = numpy.asarray(featMatrix, dtype=numpy.float32)
            nanFeatMatrix = numpy.isnan(featMatrix)
            if nanFeatMatrix.any():
                warnings.warn("Feature matrix has NaN values!  Replacing with 0.0...")
                featMatrix[numpy.where(nanFeatMatrix)] = 0.0
            # train and store forests in parallel
            pool = RequestPool()
            for i in range(self.ForestCount.value):
                def train_and_store(number):
                    result[number] = vigra.learning.RandomForest(self._tree_count)
                    oob[number] = result[number].learnRF(featMatrix, numpy.asarray(labelsMatrix, dtype=numpy.uint32))
                    print "intermediate oob:", oob[number]
                req = Request( partial(train_and_store, i) )
                pool.add( req )
            pool.wait()
            pool.clean()
        except:
            print ("couldn't learn classifier")
            raise
        oob_total = numpy.mean(oob)
        print "training finished, out of bag error:", oob_total
        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot is not self.FixClassifier and \
           self.inputs["FixClassifier"].value == False:
            slcs = (slice(0, self.ForestCount.value, None),)
            self.outputs["Classifier"].setDirty(slcs)


class OpObjectPredict(Operator):
    # WARNING: right now we predict and cache a whole time slice. We
    # expect this to be fast because there are relatively few objects
    # compared to the number of pixels in pixel classification. If
    # this should be too slow, we should instead cache at the object
    # level, and only predict for objects visible in the roi.

    name = "OpObjectPredict"

    Features = InputSlot(rtype=List, stype=Opaque)
    Classifier = InputSlot()
    LabelsCount = InputSlot(stype='integer')

    Predictions = OutputSlot(stype=Opaque, rtype=List)
    Probabilities = OutputSlot(stype=Opaque, rtype=List)
    ProbabilityChannels = OutputSlot(stype=Opaque, rtype=List, level=1)
    
    #SegmentationThreshold = 0.5

    def setupOutputs(self):
        self.Predictions.meta.shape = self.Features.meta.shape
        self.Predictions.meta.dtype = object
        self.Predictions.meta.axistags = None
        self.Predictions.meta.mapping_dtype = numpy.uint8

        self.Probabilities.meta.shape = self.Features.meta.shape
        self.Probabilities.meta.dtype = object
        self.Probabilities.meta.mapping_dtype = numpy.float32
        self.Probabilities.meta.axistags = None

        if self.LabelsCount.ready():
            nlabels = self.LabelsCount[:].wait()
            nlabels = int(nlabels[0])
            self.ProbabilityChannels.resize(nlabels)
            for oslot in self.ProbabilityChannels:
                oslot.meta.shape = self.Features.meta.shape
                oslot.meta.dtype = object
                oslot.meta.axistags = None
                oslot.meta.mapping_dtype = numpy.float32
        

        self.prob_cache = dict()

    def execute(self, slot, subindex, roi, result):
        assert slot == self.Predictions or slot == self.Probabilities or slot == self.ProbabilityChannels

        times = roi._l
        if len(times) == 0:
            # we assume that 0-length requests are requesting everything
            times = range(self.Predictions.meta.shape[0])

        forests=self.inputs["Classifier"][:].wait()
        if forests is None or forests[0] is None:
            # this happens if there was no data to train with
            return dict((t, numpy.array([])) for t in times)

        feats = {}
        prob_predictions = {}
        for t in times:
            if t in self.prob_cache:
                continue

            ftsMatrix = []
            tmpfeats = self.Features([t]).wait()
            for channel in sorted(tmpfeats[t]):
                for featname in sorted(channel.keys()):
                    value = channel[featname]
                    if not featname in config.selected_features:
                        continue
                    tmpfts = numpy.asarray(value, dtype=numpy.float32)
                    _atleast_nd(tmpfts, 2)
                    ftsMatrix.append(tmpfts)

            feats[t] = _concatenate(ftsMatrix, axis=1)
            prob_predictions[t] = [0] * len(forests)

        def predict_forest(_t, forest_index):
            # Note: We can't use RandomForest.predictLabels() here because we're training in parallel,
            #        and we have to average the PROBABILITIES from all forests.
            #       Averaging the label predictions from each forest is NOT equivalent.
            #       For details please see wikipedia:
            #       http://en.wikipedia.org/wiki/Electoral_College_%28United_States%29#Irrelevancy_of_national_popular_vote
            #       (^-^)
            prob_predictions[_t][forest_index] = forests[forest_index].predictProbabilities(feats[_t])

        # predict the data with all the forests in parallel
        pool = RequestPool()
        for t in times:
            if t in self.prob_cache:
                continue
            for i, f in enumerate(forests):
                req = Request( partial(predict_forest, t, i) )
                pool.add(req)

        pool.wait()
        pool.clean()

        for t in times:
            if t not in self.prob_cache:
                # prob_predictions is a dict-of-lists-of-arrays, indexed as follows:
                # prob_predictions[t][forest_index][object_index, class_index]
                
                # Stack the forests together and average them.
                stacked_predictions = numpy.array( prob_predictions[t] )
                averaged_predictions = numpy.average( stacked_predictions, axis=0 )
                assert averaged_predictions.shape[0] == len(feats[t])
                self.prob_cache[t] = averaged_predictions
                self.prob_cache[t][0] = 0 # Background probability is always zero

        if slot == self.Probabilities:
            return { t : self.prob_cache[t] for t in times }
        elif slot == self.Predictions:
            # FIXME: Support SegmentationThreshold again...
            labels = { t : 1 + numpy.argmax(self.prob_cache[t], axis=1) for t in times }
            for t in times:
                labels[t][0] = 0 # Background gets the zero label
            return labels
        elif slot == self.ProbabilityChannels:
            prob_single_channel = {t: self.prob_cache[t][:, subindex[0]] for t in times}
            return prob_single_channel 
        
        else:
            assert False, "Unknown input slot"

    def propagateDirty(self, slot, subindex, roi):
        self.pred_cache = dict()
        self.prob_cache = dict()
        self.Predictions.setDirty(())
        self.Probabilities.setDirty(())
        self.ProbabilityChannels.setDirty(())


class OpRelabelSegmentation(Operator):
    """Takes a segmentation image and a mapping and returns the
    mapped image.

    For instance, map prediction labels onto objects.

    """
    name = "OpToImage"
    Image = InputSlot()
    ObjectMap = InputSlot(stype=Opaque, rtype=List)
    Features = InputSlot(rtype=List, stype=Opaque) #this is needed to limit dirty propagation to the object bbox
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Image.meta)
        self.Output.meta.dtype = self.ObjectMap.meta.mapping_dtype

    def execute(self, slot, subindex, roi, result):
        img = self.Image(roi.start, roi.stop).wait()
        for t in range(roi.start[0], roi.stop[0]):
            map_ = self.ObjectMap([t]).wait()
            tmap = map_[t]
            # FIXME: necessary because predictions are returned
            # enclosed in a list.
            if isinstance(tmap, list):
                tmap = tmap[0]

            tmap = tmap.squeeze()

            warnings.warn("FIXME: This should be cached (and reset when the input becomes dirty)")
            idx = img.max()
            if len(tmap) <= idx:
                newTmap = numpy.zeros((idx + 1,)) # And maybe this should be cached, too?
                newTmap[:len(tmap)] = tmap[:]
                tmap = newTmap
            
            result[t-roi.start[0]] = tmap[img[t-roi.start[0]]]
        
        return result
    
    def propagateDirty(self, slot, subindex, roi):
        if slot is self.Image:
            self.Output.setDirty(roi)

        elif slot is self.ObjectMap or slot is self.Features:
            # this is hacky. the gui's onClick() function calls
            # setDirty with a (time, object) pair, while elsewhere we
            # call setDirty with ().
            if len(roi._l) == 0:
                self.Output.setDirty(slice(None))
            elif isinstance(roi._l[0], int):
                for t in roi._l:
                    self.Output.setDirty(slice(t))
            else:
                assert len(roi._l[0]) == 2
                # for each dirty object, only set its bounding box dirty
                ts = list(set(t for t, _ in roi._l))
                feats = self.Features(ts).wait()
                for t, obj in roi._l:
                    try:
                        min_coords = feats[t][0]['Coord<Minimum>'][obj]
                        max_coords = feats[t][0]['Coord<Maximum>'][obj]
                    except KeyError:
                        min_coords = feats[t][0]['Coord<Minimum >'][obj]
                        max_coords = feats[t][0]['Coord<Maximum >'][obj]
                    slcs = list(slice(*args) for args in zip(min_coords, max_coords))
                    slcs = [slice(t, t+1),] + slcs + [slice(None),]
                    self.Output.setDirty(slcs)
                    
class OpMultiRelabelSegmentation(Operator):
    """Takes a segmentation image and multiple mappings and returns the
    mapped images.

    For instance, map prediction probabilities for different classes onto objects.

    """
    name = "OpToImageMulti"
    Image = InputSlot()
    ObjectMaps = InputSlot(stype=Opaque, rtype=List, level=1)
    Features = InputSlot(rtype=List, stype=Opaque) #this is needed to limit dirty propagation to the object bbox
    Output = OutputSlot(level=1)
    
    def __init__(self, *args, **kwargs):
        super(OpMultiRelabelSegmentation, self).__init__(*args, **kwargs)
        self._innerOperators = []
        
    def setupOutputs(self):
        nmaps = len(self.ObjectMaps)
        for islot in self.ObjectMaps:
            op = OpRelabelSegmentation(parent=self)
            op.Image.connect(self.Image)
            op.ObjectMap.connect(islot)
            op.Features.connect(self.Features)
            self._innerOperators.append(op)
        self.Output.resize(nmaps)
        for i, oslot in enumerate(self.Output):
            oslot.connect(self._innerOperators[i].Output)
            
    def propagateDirty(self, slot, subindex, roi):
        pass
            
class OpMaxLabel(Operator):
    """ Finds the maximum label value in the input labels
        More or less copied from opPixelClassification::OpMaxValue
    """
    name = "OpMaxLabel"
    Inputs = InputSlot(level=1, stype=Opaque)
    Output = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpMaxLabel, self).__init__(*args, **kwargs)
        self.Output.meta.shape = (1,)
        self.Output.meta.dtype = object
        self._output = 0 #internal cache 
    
    
    def setupOutputs(self):
        self.updateOutput()
        self.Output.setValue(self._output)

    def execute(self, slot, subindex, roi, result):
        result[0] = self._output
        return result

    def propagateDirty(self, inputSlot, subindex, roi):
        self.updateOutput()
        self.Output.setValue(self._output)

    def updateOutput(self):
        # Return the max value of all our inputs
        maxValue = None
        for i, inputSubSlot in enumerate(self.Inputs):
            # Only use inputs that are actually configured
            if inputSubSlot.ready():
                subSlotMax = numpy.max(inputSubSlot.value)
                #subSlotMax = 0
                #print inputSubSlot.value
                #for label_array in inputSubSlot.value.items():
                #    localMax = numpy.max(label_array)
                #    subSlotMax = max(subSlotMax, localMax)
                    
                if maxValue is None:
                    maxValue = subSlotMax
                else:
                    maxValue = max(maxValue, subSlotMax)

        self._output = maxValue

