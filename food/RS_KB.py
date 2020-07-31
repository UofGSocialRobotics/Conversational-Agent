import json
import copy
from termcolor import colored

import whiteboard_client as wbc
import helper_functions as helper
import food.food_config as fc
import food.resources.recipes_DB.allrecipes.nodejs_scrapper.consts as consts
import food.RS_utils as rs_utils
from ca_logging import log

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
        with open(consts.json_xUsers_Xrecipes_withDiets_path, 'r') as recipes_file:
            content = json.load(recipes_file)
        self.recipe_DB_all = content['recipes_data']
        self.recipe_DB = copy.copy(self.recipe_DB_all)
        self.user_profile = {
            "liked_ingredients": list(),
            "disliked_ingredients": list(),
            "diets": list(),
            "time": None,
            "hungry": None,
            "healthy": None
        }
        ## Number of recipes in the list that best fit the required criteria; i.e. when we don't recipes matching one of the user's constraints, we put the ones that match in the beginning of the list and we keep the rest at the end...
        self.best_match_recipes = list()

    def set_user_profile(self, liked_ingredients, disliked_ingredients, diets, time_val, hungry, healthy):
        if isinstance(liked_ingredients, list):
            for elt in liked_ingredients:
                if not isinstance(elt, str):
                    raise TypeError("Liked ingredients are supposed to be strings (list of strings)")
            self.user_profile['liked_ingredients'] = liked_ingredients
        else:
            raise TypeError("Was expecting a list of (liked) ingredients (strings)")
        if isinstance(disliked_ingredients, list):
            for elt in disliked_ingredients:
                if not isinstance(elt, str):
                    raise TypeError("Disliked ingredients are supposed to be strings (list of strings)")
            self.user_profile['disliked_ingredients'] = disliked_ingredients
        else:
            raise TypeError("Was expecting a list of (disliked) ingredients (strings)")
        if isinstance(diets, list):
            for elt in diets:
                if not isinstance(elt, str):
                    raise TypeError("Diets are supposed to be strings (list of strings)")
            self.user_profile['diets'] = diets
        else:
            raise TypeError("Was expecting a list of diets (strings)")
        if isinstance(time_val, int):
            self.user_profile['time'] = time_val
        else:
            raise TypeError("Time should be int")
        if isinstance(hungry, float) or isinstance(hungry, int):
            if -1 <= hungry <= 1:
                self.user_profile['hungry'] = hungry
            else:
                raise ValueError("\"Hungry\" should be between -1 and 1")
        else:
            raise TypeError("\"Hungry\" should be a float between -1 and 1")
        if isinstance(healthy, float) or isinstance(healthy, int):
            if -1 <= healthy <= 1:
                self.user_profile['healthy'] = healthy
            else:
                raise ValueError("\"Hungry\" should be between -1 and 1")
        else:
            raise TypeError("\"Hungry\" should be a float between -1 and 1")


    def check_new_recipes_and_set_new_DB(self, n_recipes, OK_recipes, constraint_type_str, constraint_str):
        if self.best_match_recipes:
            OK_recipes = copy.copy(self.best_match_recipes) + OK_recipes
            log.info("Keeping %d favorite (best match) recipes in the list even though they may not validate new constraint %s" % (len(self.best_match_recipes), constraint_type_str))
        if OK_recipes:
            if len(OK_recipes) >= n_recipes:
                self.set_current_DB(OK_recipes)
            else:
                log.info("Can't get enough recipes with set %s %s (got %d)" % (constraint_type_str, constraint_str, len(OK_recipes)))
                log.info(OK_recipes)
                new_OK_recipes = OK_recipes
                self.best_match_recipes = copy.copy(OK_recipes)
                for rid in self.recipe_DB.keys():
                    if rid not in new_OK_recipes:
                        new_OK_recipes.append(rid)
                self.set_current_DB(new_OK_recipes)
        else:
            log.info("Can't any recipes with set %s %s" % (constraint_type_str, constraint_str))

    def get_recipe_for_user(self, n_recipes=5):
        '''
        Filter recipes according to user profile. We MUST return something, so always check the current user recipeDB is not empty.
        :return:
        '''
        if self.user_profile['diets']:
            for diet in self.user_profile['diets']:
                OK_recipes = self.get_recipes_with_diet(diet)
                self.check_new_recipes_and_set_new_DB(n_recipes, OK_recipes, "diet", diet)

        if self.user_profile['disliked_ingredients']:
            for ingredient in self.user_profile['disliked_ingredients']:
                OK_recipes = self.get_recipes_without_ingredient(ingredient)
                self.check_new_recipes_and_set_new_DB(n_recipes, OK_recipes, "disliked ingredient", ingredient)

        if self.user_profile['liked_ingredients']:
            for ingredient in self.user_profile['liked_ingredients']:
                OK_recipes = self.get_recipes_with_ingredient(ingredient)
                self.check_new_recipes_and_set_new_DB(n_recipes, OK_recipes, "liked ingredient", ingredient)

        if self.user_profile['time']:
            OK_recipes = self.get_recipes_ready_in_time(self.user_profile['time'])
            self.check_new_recipes_and_set_new_DB(n_recipes, OK_recipes, "time", self.user_profile['time'])

        if self.user_profile['hungry']:
            if self.user_profile['hungry'] < 0.5:
                OK_recipes = self.get_light_recipes()
            elif self.user_profile['hungry'] > 0.5:
                OK_recipes = self.get_heavy_recipes()
            else:
                OK_recipes = self.get_normal_calories_recipes()
            self.check_new_recipes_and_set_new_DB(n_recipes, OK_recipes, "hungry value", self.user_profile['hungry'].__str__())

        if self.user_profile['healthy']:
            if self.user_profile['healthy'] < 0.5:
                OK_recipes = self.get_FSAred_recipes()
            elif self.user_profile['healthy'] > 0.5:
                OK_recipes = self.get_FSAgreen_recipes()
            else:
                OK_recipes = self.get_FSAamber_recipes()
            self.check_new_recipes_and_set_new_DB(n_recipes, OK_recipes, "healthy value", self.user_profile['healthy'].__str__())




    def reset_current_DB(self):
        self.recipe_DB = copy.copy(self.recipe_DB_all)

    def set_current_DB(self, rid_list):
        self.recipe_DB = dict()
        for rid in rid_list:
            self.recipe_DB[rid] = self.recipe_DB_all[rid]

    def print_current_DB_ids(self):
        print(len(self.recipe_DB.keys()))
        for rid in self.recipe_DB.keys():
            print(rid)

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
        # self.set_current_DB(recipes_w_ingredient)
        return recipes_w_ingredient

    def get_recipes_without_ingredient(self, ingredient):
        ingredient = ingredient.lower().strip()
        res = list()
        for rid, rdata in self.recipe_DB.items():
            if ingredient not in rdata[fc.title].lower():
                res.append(rid)
            else:
                ingredient_in_recipe_bool = False
                for r_ingredient in rdata[fc.ingredients]:
                    if ingredient in r_ingredient.lower():
                        ingredient_in_recipe_bool = True
                if not ingredient_in_recipe_bool:
                    res.append(rid)
        # self.set_current_DB(res)
        return res

    def get_recipes_with_diet(self, diet):
        recipes_to_return = list()
        for rid, rdata in self.recipe_DB.items():
            # print(rdata)
            if diet not in rdata['diets'].keys():
                print(colored("Missing diet info for recipe %s!" % rid, "red"))
            else:
                if rdata['diets'][diet]:
                    recipes_to_return.append(rid)
        # self.set_current_DB(recipes_to_return)
        return recipes_to_return

    def get_recipes_with_N_calories(self, n_calories, operator):
        return self.get_recipes_with_attribute_val_in_range("calories", n_calories, operator)

    def get_FSAgreen_recipes(self):
        return self.get_recipes_with_attribute_val_in_range("FSAscore", FSA_HEALTHY, "less")

    def get_FSAamber_recipes(self):
        return self.get_recipes_with_attribute_val_in_range("FSAscore", FSA_UNHEALTHY, "less")
        return self.get_recipes_with_attribute_val_in_range("FSAscore", FSA_HEALTHY, "more")

    def get_FSAred_recipes(self):
        return self.get_recipes_with_attribute_val_in_range("FSAscore", FSA_UNHEALTHY, "more")

    def get_recipes_with_attribute_val_in_range(self, attribute, n, operator):
        recipes_to_return = list()
        for rid, rdata in self.recipe_DB.items():
            if attribute == "calories":
                att_val = rdata["nutrition"]["calories"]
            elif attribute == "FSAscore":
                att_val = rdata[attribute]
            if (operator == "more" and att_val >= n) or (operator == "less" and att_val < n):
                recipes_to_return.append(rid)
        # self.set_current_DB(recipes_to_return)
        return recipes_to_return

    def get_light_recipes(self):
        return self.get_recipes_with_N_calories(N_CALORIES_LIGHT_DINNER, "less")

    def get_heavy_recipes(self):
        return self.get_recipes_with_N_calories(N_CALORIES_HEAVY_DINNER, "more")

    def get_normal_calories_recipes(self):
        return self.get_recipes_with_N_calories(N_CALORIES_LIGHT_DINNER, "more")
        return self.get_recipes_with_N_calories(N_CALORIES_HEAVY_DINNER, "less")

    def get_recipes_ready_in_time(self, minutes_max):
        recipes_to_return = list()
        for rid, rdata in self.recipe_DB.items():
            if "Total" in rdata["time_info"].keys():
                total_time = rs_utils.convert_timestring_to_intminutes(rdata["time_info"]["Total"])
                if minutes_max >= total_time:
                    recipes_to_return.append(rid)
            else:
                recipes_to_return.append(rid)
        # self.set_current_DB(recipes_to_return)
        return recipes_to_return



if __name__ == "__main__":
    kbrs = KBRS()

    kbrs.set_user_profile(liked_ingredients=['apple', 'broccoli'], disliked_ingredients=['nut'], diets=['vegan'], time_val=60, hungry=0, healthy=0)
    kbrs.get_recipe_for_user()

    kbrs.print_current_DB_ids()
