import numpy
from scipy.ndimage.measurements import label
from yapsy.IPlugin import IPlugin

from Library import UI


class Map_Feature_Extraction_Plugin(IPlugin):
    def initialize(self, **kwargs):
        local_map = kwargs["map"]
        obj = kwargs["obj"]
        this_mod = Map_Feature_Extraction(local_map, obj)
        return this_mod


class Map_Feature_Extraction:
    def __init__(self, local_map, obj) -> None:
        self.id = obj["id"]
        elevation = obj['elevation']
        biome = obj['biome']
        self.feature = obj['feature']
        names = obj['names']
        self.showonmap = obj["show_on_map"]
        self.icononmap = obj["icon_on_map"]
        self.addedicon = False
        self.icon_color = obj["icon_color"]

        self.database = {}
        self.labeled = []

        if elevation:
            self.percentile_of_elevation = obj['percentile_of_elevation']
            elevation = local_map.get_attribute('elevation')
            feature_layer = elevation > numpy.percentile(elevation, (1-self.percentile_of_elevation) * 100)
        elif biome:
            biomes = local_map.get_attribute('biomes')
            feature_layer = biomes == obj['feature_index']
            invert = obj['index_invert']
            if invert:
                feature_layer = biomes != obj['feature_index']

        self.labeled, number_feature = label(input=feature_layer)
        if number_feature < len(names):
            feat_names = numpy.random.choice(names, number_feature, False)
            for i in range(number_feature):
                j = i + 1
                posi = numpy.transpose((self.labeled == j).nonzero())
                self.database[len(self.database)] = {
                    "module": "Map_Feature", "feature": self.feature, "feat_id": j,
                    "feat_name": feat_names[i],
                    "position": posi[numpy.random.randint(0, len(posi))]
                }
        else:
            feat_names = numpy.random.choice(names, len(names), False)
            for i in range(len(names)):
                j = i + 1
                posi = numpy.transpose((self.labeled == j).nonzero())
                self.database[len(self.database)] = {
                    "module": "Map_Feature", "feature": self.feature, "feat_id": j,
                    "feat_name": feat_names[i],
                    "position": posi[numpy.random.randint(0, len(posi))]
                }
        local_map.set_attribute(self.feature, self.labeled)

    def update(self, **kwargs) -> None:
        if not self.addedicon:
            if self.showonmap:
                for i in range(kwargs["map"].get_height()):
                    for j in range(kwargs["map"].get_width()):
                        if self.labeled[i][j] != 0:
                            this_icon = UI.ntcod_entity(self.icononmap, self.icon_color, i, j, kwargs["window"].get(0)[0], self.feature)
                self.addedicon = True
        return

    def print(self, **kwargs):
        if "rpgplayer" in list(kwargs["mods"].keys()):
            mods = kwargs["mods"]
            posi_x = mods["rpgplayer"].get_position()[1]
            posi_y = mods["rpgplayer"].get_position()[0]
            label_layer = kwargs["map"].get_attribute(self.feature)

            location_feat = label_layer[posi_y][posi_x]
            if location_feat != 0:
                for id, items in self.database.items():
                    if items["module"] == "Map_Feature":
                        if (items["feature"] == self.feature) and (items["feat_id"] == location_feat):
                            return {"title": "World", 0: {"title": "Environment", 0: [self.feature + ": " + items["feat_name"], 1, 0]}}

    def get_feat_name(self):
        return self.feature

    def get_actions(self, **kwargs):
        return

    def act_on_action(self, **kwargs):
        return
