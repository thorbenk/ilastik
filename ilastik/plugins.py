from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
import os
from collections import namedtuple

##########################
# different plugin types #
##########################

class ObjectFeaturesPlugin(IPlugin):
    """Plugins of this class calculate object features"""
    name = "Base object features plugin"

    def availableFeatures(self):
        """returns a list of feature names supported by this plugin."""
        return []

    def execute(self, image, labels, features):
        """calculate the requested features."""
        return dict()

    def execute_local(self, image, features, axes, min_xyz, max_xyz,
                      rawbbox, passed, ccbboxexcl, ccbboxobject):
        """calculated requested features on a single object."""
        return dict()

###############
# the manager #
###############

pluginManager = PluginManager()
pluginManager.setPluginPlaces(["~/.ilastik/plugins",
                               os.path.join(os.path.split(__file__)[0], "plugins"),
                               ])

pluginManager.setCategoriesFilter({
   "ObjectFeatures" : ObjectFeaturesPlugin,
   })

pluginManager.collectPlugins()
for pluginInfo in pluginManager.getAllPlugins():
    pluginManager.activatePluginByName(pluginInfo.name)
