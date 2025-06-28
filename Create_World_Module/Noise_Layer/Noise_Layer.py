from yapsy.IPlugin import IPlugin
import json
import random
import numpy
import tcod


class Noise_Layer_Plugin(IPlugin):
    def initialize(self, **kwargs):
        local_map = kwargs["map"]
        obj = kwargs["obj"]
        this_mod = Noise_Layer(local_map, obj)
        return this_mod


class Noise_Layer:
    def __init__(self, local_map, obj) -> None:
        self.local_map = local_map
        self.width = local_map.get_width()
        self.height = local_map.get_height()

        self.id = obj["id"]
        self.layers = obj["layers"]
        self.power = obj["power"]
        self.resize = obj["resize"]

        self.update()


    def update(self, **kwargs) -> None:
        if not (("return_directly" in list(kwargs.keys())) and kwargs["return_directly"] is True):
            noise_gen = []
            total_weight = 0
            for this_layer in range(len(self.layers)):
                noise_gen.append(tcod.noise.Noise(dimensions=2, seed=random.randint(0, 2147483647)))
                total_weight = total_weight + self.layers[str(this_layer)][0]

            value = []
            for y in range(self.height):
                value.append([0] * self.width)

            for this_layer in range(len(self.layers)):
                value = value + self.layers[str(this_layer)][0] * \
                        (noise_gen[this_layer][tcod.noise.grid(shape=(self.width, self.height),
                                                               scale=self.layers[str(this_layer)][1])] + 1.0) * 0.5
            value = numpy.array(value)

            value = value / total_weight
            value = numpy.power(value, self.power)
            if self.resize is True:
                value_decrease = value - value.min()
                value = value_decrease / value_decrease.max()
        else:
            noise_gen = []
            total_weight = 0
            for this_layer in range(len(kwargs["parameters"][1])):
                noise_gen.append(tcod.noise.Noise(dimensions=2, seed=random.randint(0, 2147483647)))
                total_weight = total_weight + kwargs["parameters"][1][str(this_layer)][0]

            value = []
            for y in range(kwargs["height"]):
                value.append([0] * kwargs["width"])

            for this_layer in range(len(kwargs["parameters"][1])):
                value = value + kwargs["parameters"][1][str(this_layer)][0] * \
                        (noise_gen[this_layer][tcod.noise.grid(shape=(kwargs["width"], kwargs["height"]),
                                                               scale=kwargs["parameters"][1][str(this_layer)][1])] + 1.0) * 0.5
            value = numpy.array(value)

            value = value / total_weight
            value = numpy.power(value, kwargs["parameters"][2])
            if kwargs["parameters"][2] is True:
                value_decrease = value - value.min()
                value = value_decrease / value_decrease.max()

        if ("return_directly" in list(kwargs.keys())) and kwargs["return_directly"] is True:
            return value
        else:
            self.local_map.set_attribute(self.id, value)
        return

    def run_time_generate(self, height, width, obj):
        return self.update(return_directly=True, height=height, width=width, parameters=[obj["id"], obj["layers"], obj["power"], obj["resize"]])

    def print(self, **kwargs):
        return

    def get_actions(self, **kwargs):
        return

    def act_on_action(self, **kwargs):
        return
