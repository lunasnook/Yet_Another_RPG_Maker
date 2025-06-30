from yapsy.IPlugin import IPlugin
import random
import numpy as np
import Create_Civilization_Module.Demographics.Demographics as Demographics
from Library import UI
from Library.UI import OTH, OTW


class BackSimulation_Plugin(IPlugin):
    def initialize(self, **kwargs):
        obj = kwargs["obj"]
        return BackSimulation(obj)


class BackSimulation:
    def __init__(self, obj) -> None:
        self.id = obj["id"]
        self.simulate_years = obj["simulation_years"]
        self.simulated = False
        self.begin_death = obj["begin_death"]
        self.death_probability = obj["death_probability"]
        self.begin_age_marry = obj["begin_age_marry"]
        self.end_age_marry = obj["end_age_marry"]
        self.marry_probability = obj["marry_probability"]
        self.end_age_birth = obj["end_age_birth"]
        self.birth_probability = obj["birth_probability"]
        self.log = []
        self.families = {}
        self.family_counter = 0
        self.total_births = 0
        self.total_deaths = 0
        self.settlement_name = []

        self.require = obj["Require"][0]
        self.name_id = obj["demo_name"]
        self.age_id = obj["demo_age"]
        self.gender_id = obj["demo_gender"]
        self.relation_id = obj["relation_id"]
        self.spouse_id = obj["spouse_id"]
        self.family_id_id = obj["family_id_id"]
        self.settlements_id = obj["settlements_id"]

    def create_family(self, members, peoples, belong):
        family_id = f"family_{self.family_counter}"
        self.family_counter += 1
        self.families[family_id] = [belong]
        self.families[family_id].extend(members)
        for name in members:
            idx = np.where(np.array(peoples.get_attribute(self.name_id)) == name)[0][0]
            peoples.set_attribute_to(self.family_id_id, idx, family_id)

    def remove_from_family(self, name, peoples):
        idx = np.where(np.array(peoples.get_attribute(self.name_id)) == name)[0][0]

        family_id = peoples.get_attribute_from(self.family_id_id, idx)
        if family_id and family_id in self.families:
            self.families[family_id].remove(name)
            if len(self.families[family_id]) == 1:
                del self.families[family_id]
            peoples.set_attribute_to(self.family_id_id, idx, "")

    def get_simulated(self):
        return self.simulated

    def update(self, **kwargs) -> None:
        if self.simulated:
            return

        peoples = kwargs["peoples"]
        peoples.set_attribute(self.relation_id, {})
        peoples.set_attribute(self.spouse_id, "")
        peoples.set_attribute(self.family_id_id, [""] * peoples.get_number())

        settlement_mod = kwargs["mods"][self.require]
        self.settlement_name = settlement_mod.get_settlement_name()

        progress = UI.ntcod_textout(OTH, OTW, OTH, OTW, "simulation progress", False)
        kwargs["window"].add_frame(progress)

        for i in range(self.simulate_years):
            progress.clear()
            progress.add_text(f"year {i+1}/{self.simulate_years}")
            progress.add_text(f"population: {peoples.get_number()} people")
            progress.add_text(f"families: {len(self.families)} households")
            progress.add_text(f"total births: {self.total_births}")
            progress.add_text(f"total deaths: {self.total_deaths}")

            kwargs["window"].display_all(kwargs["context"], kwargs["console"])

            ages = np.array(peoples.get_attribute(self.age_id))
            settlements = np.array(peoples.get_attribute(self.require))
            genders = np.array(peoples.get_attribute(self.gender_id))
            spouses = np.array(peoples.get_attribute(self.spouse_id))

            ready_age = (ages >= self.begin_age_marry) & (ages <= self.end_age_marry)
            unmarried = spouses == ""

            # Marriages
            for idx, eligible in enumerate(ready_age & unmarried):
                if eligible and random.random() < self.marry_probability:
                    candidates = (
                        (settlements == settlements[idx]) &
                        (genders != genders[idx]) &
                        ready_age & unmarried
                    )
                    candidate_indices = np.where(candidates)[0]

                    if candidate_indices.size > 0:
                        spouse_idx = random.choice(candidate_indices)
                        peoples.set_attribute_to(self.spouse_id, idx, peoples.get_attribute_from(self.name_id, spouse_idx))
                        peoples.set_attribute_to(self.spouse_id, spouse_idx, peoples.get_attribute_from(self.name_id, idx))

                        name1 = peoples.get_attribute_from(self.name_id, idx)
                        name2 = peoples.get_attribute_from(self.name_id, spouse_idx)

                        modified_idx = peoples.get_attribute_from(self.relation_id, idx)
                        modified_idx[self.spouse_id] = name2
                        modified_spouse_idx = peoples.get_attribute_from(self.relation_id, spouse_idx)
                        modified_spouse_idx[self.spouse_id] = name1
                        peoples.set_attribute_to(self.relation_id, idx, modified_idx)
                        peoples.set_attribute_to(self.relation_id, spouse_idx, modified_spouse_idx)

                        self.remove_from_family(name1, peoples)
                        self.remove_from_family(name2, peoples)
                        self.create_family([name1, name2], peoples, peoples.get_attribute_from(self.settlements_id, idx))

            # Deaths
            for idx in reversed(range(peoples.get_number())):
                if peoples.get_attribute_from(self.age_id, idx) > self.begin_death and random.random() < self.death_probability:
                    self.total_deaths += 1
                    name = peoples.get_attribute_from(self.name_id, idx)
                    self.remove_from_family(name, peoples)
                    peoples.remove_person(idx)

                    belong_settlement = peoples.get_attribute_from(self.require, idx)
                    new_statistics = settlement_mod.get_statistics()
                    new_statistics[belong_settlement] = new_statistics[belong_settlement] - 1
                    settlement_mod.set_statistics(new_statistics)

            # Births
            spouses = np.array(peoples.get_attribute(self.spouse_id))
            ages = np.array(peoples.get_attribute(self.age_id))

            birth_candidates = (spouses != "") & (ages <= self.end_age_birth)

            for idx in np.where(birth_candidates)[0]:
                if random.random() < self.birth_probability:
                    self.total_births += 1
                    peoples.add_person()
                    newborn_idx = peoples.get_number() - 1

                    parent_name = peoples.get_attribute_from(self.name_id, idx)
                    spouse_name = peoples.get_attribute_from(self.spouse_id, idx)

                    new_name = random.choice(parent_name.split()) + " " + random.choice(Demographics.name_generator().split())
                    gender = random.choice(["Male", "Female"])

                    newborn = {
                        self.name_id: new_name,
                        self.age_id: 0,
                        self.gender_id: gender,
                        self.require: peoples.get_attribute_from(self.require, idx),
                        self.spouse_id: "",
                        self.family_id_id: "",
                        self.relation_id: {
                            "father": parent_name if peoples.get_attribute_from(self.gender_id, idx) == "Male" else spouse_name,
                            "mother": spouse_name if peoples.get_attribute_from(self.gender_id, idx) == "Male" else parent_name
                        }
                    }
                    peoples.set_person(newborn_idx, newborn)

                    spouse_idx = np.where(np.array(peoples.get_attribute(self.name_id)) == spouse_name)[0][0]
                    modified_idx = peoples.get_attribute_from(self.relation_id, idx)
                    if "children" in modified_idx.keys():
                        modified_idx["children"].append(new_name)
                    else:
                        modified_idx["children"] = [new_name]
                    modified_spouse_idx = peoples.get_attribute_from(self.relation_id, spouse_idx)
                    if "children" in modified_spouse_idx.keys():
                        modified_spouse_idx["children"].append(new_name)
                    else:
                        modified_spouse_idx["children"] = [new_name]
                    peoples.set_attribute_to(self.relation_id, idx, modified_idx)
                    peoples.set_attribute_to(self.relation_id, spouse_idx, modified_spouse_idx)

                    belong_settlement = peoples.get_attribute_from(self.require, idx)
                    new_statistics = settlement_mod.get_statistics()
                    new_statistics[belong_settlement] = new_statistics[belong_settlement] + 1
                    settlement_mod.set_statistics(new_statistics)

                    family_id = peoples.get_attribute_from(self.family_id_id, idx)
                    if family_id:
                        self.families[family_id].append(new_name)
                        peoples.set_attribute_to(self.family_id_id, newborn_idx, family_id)

            # Age increment
            peoples.set_attribute(self.age_id, (np.array(peoples.get_attribute(self.age_id)) + 1).tolist())

        kwargs["window"].remove_frame()
        kwargs["window"].display_all(kwargs["context"], kwargs["console"])

        self.simulated = True
        self.log.append(f"population: {peoples.get_number()} people")

        peoples.drop_attribute(self.spouse_id)


    def get_families(self):
        return self.families

    def print(self, **kwargs):
        return ["history", self.log]

    def get_actions(self, **kwargs):
        return

    def act_on_action(self, **kwargs) -> list:
        return []
