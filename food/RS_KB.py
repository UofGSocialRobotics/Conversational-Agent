import json
import copy

import whiteboard_client as wbc
import helper_functions as helper
import food.food_config as fc
import food.resources.recipes_DB.allrecipes.nodejs_scrapper.consts as consts
import food.RS_utils as rs_utils

N_CALORIES_LIGHT_DINNER = 300
N_CALORIES_HEAVY_DINNER = 450

FSA_HEALTHY = 7
FSA_UNHEALTHY = 10

class KBRSModule(wbc.WhiteBoardClient):
    def __init__(self, clientid, subscribes, publishes, resp_time=False):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        # publishes = {fc.USUAL_DM_MSG : publishes[0] + clientid, fc.RECIPE_DM_MSG: publishes[1] + clientid}
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, "KBRS" + clientid, subscribes, publishes, resp_time)

        self.client_id = clientid


class KBRS():
    def __init__(self):
        with open(consts.json_xUsers_Xrecipes_path, 'r') as recipes_file:
            content = json.load(recipes_file)
        self.recipe_DB_all = content['recipes_data']
        self.recipe_DB = copy.copy(self.recipe_DB_all)

    def reset_current_DB(self):
        self.recipe_DB = copy.copy(self.recipe_DB_all)

    def set_current_DB(self, rid_list):
        self.recipe_DB = dict()
        for rid in rid_list:
            self.recipe_DB[rid] = self.recipe_DB_all[rid]

    def print_current_DB_ids(self):
        print(len(self.recipe_DB.keys()))

    def get_recipes_with_ingredient(self, ingredient):
        ingredient = ingredient.lower().strip()
        recipes_w_ingredient = list()
        for rid, rdata in self.recipe_DB.items():
            if ingredient in rdata[fc.title].lower():
                recipes_w_ingredient.append(rid)
            else:
                for r_ingredient in rdata[fc.ingredients]:
                    if ingredient in r_ingredient.lower():
                        recipes_w_ingredient.append(rid)
        self.set_current_DB(recipes_w_ingredient)

    def get_recipes_with_additional_characteristic(self, characteristic):
        recipes_to_return = list()
        for recipe in self.recipe_DB:
            if characteristic in recipe['additional_info']:
                recipes_to_return.append(recipe)
        return recipes_to_return

    def get_recipes_with_N_calories(self, n_calories, operator):
        self.get_recipes_with_attribute_val_in_range("calories", n_calories, operator)

    def get_FSAgreen_recipes(self):
        self.get_recipes_with_attribute_val_in_range("FSAscore", FSA_HEALTHY, "less")

    def get_FSAamber_recipes(self):
        self.get_recipes_with_attribute_val_in_range("FSAscore", FSA_UNHEALTHY, "less")
        self.get_recipes_with_attribute_val_in_range("FSAscore", FSA_HEALTHY, "more")

    def get_FSAred_recipes(self):
        self.get_recipes_with_attribute_val_in_range("FSAscore", FSA_UNHEALTHY, "more")

    def get_recipes_with_attribute_val_in_range(self, attribute, n, operator):
        recipes_to_return = list()
        for rid, rdata in self.recipe_DB.items():
            if attribute == "calories":
                att_val = rdata["nutrition"]["calories"]
            elif attribute == "FSAscore":
                att_val = rdata[attribute]
            if (operator == "more" and att_val >= n) or (operator == "less" and att_val < n):
                recipes_to_return.append(rid)
        self.set_current_DB(recipes_to_return)

    def get_light_recipes(self):
        self.get_recipes_with_N_calories(N_CALORIES_LIGHT_DINNER, "less")

    def get_heavy_recipes(self):
        self.get_recipes_with_N_calories(N_CALORIES_HEAVY_DINNER, "more")

    def get_normal_calories_recipes(self):
        self.get_recipes_with_N_calories(N_CALORIES_LIGHT_DINNER, "more")
        self.get_recipes_with_N_calories(N_CALORIES_HEAVY_DINNER, "less")

    def get_vegetarian_recipes(self):
        return self.get_recipes_with_additional_characteristic('Vegetarian')

    def get_vegan_recipes(self):
        return self.get_recipes_with_additional_characteristic('Vegan')

    def get_glutenfree_recipes(self):
        return self.get_recipes_with_additional_characteristic("Gluten-free")

    def get_dairyfree_recipes(self):
        return self.get_recipes_with_additional_characteristic('Dairy-free')

    def get_healthy_recipes(self):
        return self.get_recipes_with_additional_characteristic('Healthy')

    def get_recipes_ready_in_time(self, minutes_max):
        recipes_to_return = list()
        for rid, rdata in self.recipe_DB.items():
            if "Total" in rdata["time_info"].keys():
                total_time = rs_utils.convert_timestring_to_intminutes(rdata["time_info"]["Total"])
                if minutes_max >= total_time:
                    recipes_to_return.append(rid)
            else:
                recipes_to_return.append(rid)
        self.set_current_DB(recipes_to_return)

    def get_recipes(self, ingredient, total_time):
        self.get_recipes_with_ingredient(ingredient)
        self.get_recipes_ready_in_time(total_time)



if __name__ == "__main__":
    kbrs = KBRS()
    kbrs.get_recipes("chicken", 60)
    kbrs.get_heavy_recipes()
    kbrs.get_FSAred_recipes()
    kbrs.print_current_DB_ids()
