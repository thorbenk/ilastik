from ilastik.plugins import ObjectFeaturesPlugin
import vigra
import numpy as np
from lazyflow.request import Request, Pool
from functools import partial

def update_keys(d, prefix=None, suffix=None):
    if prefix is None:
        prefix = ''
    if suffix is None:
        suffix = ''
    return dict((prefix + k + suffix, v) for k, v in d.items())

class VigraObjFeats(ObjectFeaturesPlugin):
    global_features = set(["RegionCenter",
                           "CenterOfMass",
                           "Coord<Minimum>",
                           "Coord<Maximum>",
                           "RegionAxes",
                           "RegionRadii",
                           "Coord<ArgMaxWeight>",
                           "Coord<ArgMinWeight>"])

    def availableFeatures(self):
        names = vigra.analysis.supportedRegionFeatures(np.zeros((3, 3), dtype=np.float32),
                                                       np.zeros((3, 3), dtype=np.uint32))
        return list(f.replace(' ', '') for f in names)

    def execute(self, image, labels, features):
        features = list(set(features).intersection(self.global_features))
        result = vigra.analysis.extractRegionFeatures(image, labels, features, ignoreLabel=0)
        return dict(result.items())

    def execute_local(self, image, features, axes, min_xyz, max_xyz,
                      rawbbox, passed, ccbboxexcl, ccbboxobject):
        features = list(set(features).difference(self.global_features))
        labeled_bboxes = [passed, ccbboxexcl, ccbboxobject]
        feats = [None, None, None]
        pool = Pool()
        for ibox, bbox in enumerate(labeled_bboxes):
            def extractObjectFeatures(ibox):
                feats[ibox] = vigra.analysis.extractRegionFeatures(np.asarray(rawbbox, dtype=np.float32),
                                                                   np.asarray(bbox, dtype=np.uint32),
                                                                   features,
                                                                   histogramRange=[0, 255],
                                                                   binCount = 10,
                                                                   ignoreLabel=0)
            req = pool.request(partial(extractObjectFeatures, ibox))
        pool.wait()

        result = {}
        feats[0] = update_keys(feats[0], suffix='_incl')
        feats[1] = update_keys(feats[1], suffix='_excl')

        return dict(sum((d.items() for d in feats), []))
