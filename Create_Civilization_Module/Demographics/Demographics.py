from yapsy.IPlugin import IPlugin
import json
import random


class Demographics_Plugin(IPlugin):
    def initialize(self, **kwargs):
        obj = kwargs["obj"]
        this_map = kwargs["peoples"]
        this_mod = Demographics(obj, this_map)
        return this_mod


def name_generator():
    this_name = ""
    qs = ['b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'w', 'x', 'y', 'z']
    es = ['a', 'e', 'i', 'o', 'u', 'v']
    for i in list(range(2)):
        for j in list(range(random.choice(list(range(2))) + 1)):
            if j == 0:
                this_name = this_name + random.choice(qs).upper()
            else:
                this_name = this_name + random.choice(qs)
            for k in list(range(random.choice(list(range(2))) + 1)):
                this_name = this_name + random.choice(es)
        this_name = this_name + " "
    this_name = this_name.removesuffix(" ")
    return this_name


class Demographics:
    def __init__(self, obj, this_map) -> None:
        self.name_id = obj["name_id"]
        self.age_id = obj["age_id"]
        self.gender_id = obj["gender_id"]
        age_group = obj["age in 10"]
        gender_name = list(obj["gender"].keys())
        gender_group = list(obj["gender"].values())
        count = this_map.get_number()

        this_map.set_attribute(self.name_id, "")
        this_map.set_attribute(self.age_id, -1)
        this_map.set_attribute(self.gender_id, "")
        for index in list(range(count)):
            # name generator
            this_name = name_generator()
            this_map.set_attribute_to(self.name_id, index, this_name)
            # age generator
            age_group_random = random.randint(0, 99) + 1
            for i in list(range(10)):
                if age_group_random <= age_group[i]:
                    this_age = random.randint(i * 10 + 1, i * 10 + 10)
                    this_map.set_attribute_to(self.age_id, index, this_age)
                    break
            # gender generator
            gender_group_random = random.randint(0, 99) + 1
            for i in list(range(len(gender_name))):
                if gender_group_random <= gender_group[i]:
                    this_gender = gender_name[i]
                    this_map.set_attribute_to(self.gender_id, index, this_gender)
                    break

        return

    def update(self, **kwargs) -> None:
        return

    def print(self, **kwargs):
        return

    def get_actions(self, **kwargs):
        return

    def act_on_action(self, **kwargs):
        return
