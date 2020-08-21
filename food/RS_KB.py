import json
import copy
from termcolor import colored
import pandas as pd

import whiteboard_client as wbc
import helper_functions as helper
import food.food_config as fc
import food.resources.recipes_DB.allrecipes.nodejs_scrapper.consts as consts
import food.RS_utils as rs_utils
from ca_logging import log

from food.CF_implicit_ratings import ImplicitCFRS

N_CALORIES_LIGHT_DINNER = 300
N_CALORIES_HEAVY_DINNER = 450

FSA_HEALTHY = 7
FSA_UNHEALTHY = 10

CONSTRAINTS_COSTS = {"vegan": 10,
                     "vegetarian": 10,
                     "gluten_free": 10,
                     "dairy_free": 10,
                     "pescetarian": 10,
                     "keto": 5,
                     "low_carbs": 5,
                     "ingredient": 5,
                     "time": 3}

with open(consts.json_xUsers_Xrecipes_withDiets_path, 'r') as f:
    TOTAL_RECIPES = len(list(json.load(f)['recipes_data'].keys()))

class KBRSModule(wbc.WhiteBoardClient):
    def __init__(self, clientid, subscribes, publishes, resp_time=False):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        # publishes = {fc.USUAL_DM_MSG : publishes[0] + clientid, fc.RECIPE_DM_MSG: publishes[1] + clientid}
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, "KBRS" + clientid, subscribes, publishes, resp_time)

        self.client_id = clientid
        self.kbrs = KBRS()


    def treat_message(self, msg, topic):
        super(KBRSModule, self).treat_message(msg, topic)

        subject = msg['msg']
        if subject == fc.set_user_profile:
            self.set_user_profile(liked_ingredients=msg[fc.liked_food], disliked_ingredients=msg[fc.disliked_food], diets=msg[fc.diet], time_val=msg[fc.time_to_cook])
        elif subject == fc.get_reco:
            reco = self.get_reco(n_reco=5)
            self.publish({"msg": fc.reco_recipes, fc.recipes_list: reco})

    def set_user_profile(self, liked_ingredients, disliked_ingredients, diets, time_val):
        self.kbrs.set_user_profile(liked_ingredients=liked_ingredients, disliked_ingredients=disliked_ingredients, diets=diets, time_val=time_val)

    def get_reco(self, n_reco):
        return self.kbrs.get_recipe_for_user(n_recipes=n_reco)


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

        self.reco_dict = dict()
        self.n_recipes_in_reco_dict = 0
        self.all_recipes_in_reco_dict = list()

    def set_user_profile(self, liked_ingredients, disliked_ingredients, diets, time_val, hungry=None, healthy=None):
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

        if hungry:
            if isinstance(hungry, float) or isinstance(hungry, int):
                if -1 <= hungry <= 1:
                    self.user_profile['hungry'] = hungry
                else:
                    raise ValueError("\"Hungry\" should be between -1 and 1")
            else:
                raise TypeError("\"Hungry\" should be a float between -1 and 1")

        if healthy:
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


    def add_item_to_reco_dict(self, utility, rid_list, relaxed_constraint):
        if utility not in self.reco_dict.keys():
            self.reco_dict[utility] = {"rids": list(), "relaxed_constraints": list()}
        # self.reco_dict[utility]['rids'] += rid_list
        for rid in rid_list:
            if rid not in self.all_recipes_in_reco_dict:
                self.all_recipes_in_reco_dict.append(rid)
                self.reco_dict[utility]['rids'].append(rid)
                self.n_recipes_in_reco_dict += 1
        self.reco_dict[utility]["relaxed_constraints"].append(relaxed_constraint)


    def get_recipes_with_relaxed_liked_ingredient_constraint(self, user_profile, previous_costs=0, previous_constraints_str=""):

        for ingredient in user_profile['liked_ingredients']:
            new_user_profile2 = copy.deepcopy(user_profile)
            new_user_profile2['liked_ingredients'].remove(ingredient)
            print(new_user_profile2)
            recipes = list(self.get_recipes_matching_constraints(new_user_profile2).keys())
            self.add_item_to_reco_dict(100-(previous_costs+CONSTRAINTS_COSTS['ingredient']), rid_list=recipes, relaxed_constraint=previous_constraints_str+ingredient)

    def get_recipes_for_user(self, n_recipes=5):
        recipes_matching_all_criteria = list(self.get_recipes_matching_constraints(self.user_profile).keys())
        self.add_item_to_reco_dict(100, recipes_matching_all_criteria, None)

        #################################################
        ##      Relax one constraint

        if self.n_recipes_in_reco_dict < n_recipes:
            # we don't have enough recipes, let's relax some constraints
            new_user_profile = copy.deepcopy(self.user_profile)
            if new_user_profile["time"]:
                new_user_profile['time'] += 15
                print(new_user_profile)
                recipes_matching_all_criteria_but_time = list(self.get_recipes_matching_constraints(new_user_profile).keys())
                self.add_item_to_reco_dict(100-CONSTRAINTS_COSTS['time'], rid_list=recipes_matching_all_criteria_but_time, relaxed_constraint="time")

        if self.n_recipes_in_reco_dict < n_recipes:
            new_user_profile = copy.deepcopy(self.user_profile)
            if new_user_profile["time"]:
                new_user_profile['time'] = 1000
                print(new_user_profile)
                recipes_matching_all_criteria_but_time = list(self.get_recipes_matching_constraints(new_user_profile).keys())
                self.add_item_to_reco_dict(100-(CONSTRAINTS_COSTS['time']*2), rid_list=recipes_matching_all_criteria_but_time, relaxed_constraint="time")

        if self.n_recipes_in_reco_dict < n_recipes:

            self.get_recipes_with_relaxed_liked_ingredient_constraint(self.user_profile)

            # relax diet constraints
            for diet in self.user_profile['diets']:
                new_user_profile = copy.deepcopy(self.user_profile)
                new_user_profile['diets'].remove(diet)
                print(new_user_profile)
                recipes_matching_all_criteria_but_one_diet = list(self.get_recipes_matching_constraints(new_user_profile).keys())
                self.add_item_to_reco_dict(100-(CONSTRAINTS_COSTS[diet]), rid_list=recipes_matching_all_criteria_but_one_diet, relaxed_constraint=diet)

            # relax disliked ingredients contraint
            for ingredient in self.user_profile['disliked_ingredients']:
                new_user_profile = copy.deepcopy(self.user_profile)
                new_user_profile['disliked_ingredients'].remove(ingredient)
                print(new_user_profile)
                recipes_matching_all_criteria_but_one_ingredient = list(self.get_recipes_matching_constraints(new_user_profile).keys())
                self.add_item_to_reco_dict(100-(CONSTRAINTS_COSTS['ingredient']), rid_list=recipes_matching_all_criteria_but_one_ingredient, relaxed_constraint=ingredient)


        if self.n_recipes_in_reco_dict < n_recipes:

        #################################################
        ##      Relax 2 constraints

            # Relax time (+15min) and another
            new_user_profile = copy.deepcopy(self.user_profile)
            if new_user_profile["time"]:
                new_user_profile['time'] += 15

                self.get_recipes_with_relaxed_liked_ingredient_constraint(new_user_profile, previous_costs=CONSTRAINTS_COSTS['time'], previous_constraints_str="time+")

                for diet in self.user_profile['diets']:
                    new_user_profile2 = copy.deepcopy(new_user_profile)
                    new_user_profile2['diets'].remove(diet)
                    print(new_user_profile2)
                    recipes_matching_all_criteria_but_2_criteria = list(self.get_recipes_matching_constraints(new_user_profile2).keys())
                    self.add_item_to_reco_dict(100-(CONSTRAINTS_COSTS['time']+CONSTRAINTS_COSTS[diet]), rid_list=recipes_matching_all_criteria_but_2_criteria, relaxed_constraint="time+"+diet)


                for ingredient in self.user_profile['disliked_ingredients']:
                    new_user_profile2 = copy.deepcopy(new_user_profile)
                    new_user_profile2['disliked_ingredients'].remove(ingredient)
                    print(new_user_profile2)
                    recipes_matching_all_criteria_but_2_criteria = list(self.get_recipes_matching_constraints(new_user_profile2).keys())
                    self.add_item_to_reco_dict(100-(CONSTRAINTS_COSTS['time']+CONSTRAINTS_COSTS['ingredient']), rid_list=recipes_matching_all_criteria_but_2_criteria, relaxed_constraint="time+"+ingredient)

            # Relax time (cancelled) and another
            new_user_profile = copy.deepcopy(self.user_profile)
            if new_user_profile["time"]:
                new_user_profile['time'] = 1000

                self.get_recipes_with_relaxed_liked_ingredient_constraint(new_user_profile, previous_costs=CONSTRAINTS_COSTS['time'], previous_constraints_str="time+")

                for diet in self.user_profile['diets']:
                    new_user_profile2 = copy.deepcopy(new_user_profile)
                    new_user_profile2['diets'].remove(diet)
                    print(new_user_profile2)
                    recipes_matching_all_criteria_but_2_criteria = list(self.get_recipes_matching_constraints(new_user_profile2).keys())
                    self.add_item_to_reco_dict(100-(CONSTRAINTS_COSTS['time']*2+CONSTRAINTS_COSTS[diet]), rid_list=recipes_matching_all_criteria_but_2_criteria, relaxed_constraint="time+"+diet)


                for ingredient in self.user_profile['disliked_ingredients']:
                    new_user_profile2 = copy.deepcopy(new_user_profile)
                    new_user_profile2['disliked_ingredients'].remove(ingredient)
                    print(new_user_profile2)
                    recipes_matching_all_criteria_but_2_criteria = list(self.get_recipes_matching_constraints(new_user_profile2).keys())
                    self.add_item_to_reco_dict(100-(CONSTRAINTS_COSTS['time']*2+CONSTRAINTS_COSTS['ingredient']), rid_list=recipes_matching_all_criteria_but_2_criteria, relaxed_constraint="time+"+ingredient)


            # Relax liked ingredient and another (disliked ingredient or diet)
            for ingredient in self.user_profile['liked_ingredients']:
                new_user_profile = copy.deepcopy(self.user_profile)
                new_user_profile['liked_ingredients'].remove(ingredient)

                for diet in self.user_profile['diets']:
                    new_user_profile2 = copy.deepcopy(new_user_profile)
                    new_user_profile2['diets'].remove(diet)
                    print(new_user_profile2)
                    recipes_matching_all_criteria_but_2_criteria = list(self.get_recipes_matching_constraints(new_user_profile2).keys())
                    self.add_item_to_reco_dict(100-(CONSTRAINTS_COSTS['ingredient']+CONSTRAINTS_COSTS[diet]), rid_list=recipes_matching_all_criteria_but_2_criteria, relaxed_constraint=ingredient+"+"+diet)

                for dingredient in self.user_profile['disliked_ingredients']:
                    new_user_profile2 = copy.deepcopy(new_user_profile)
                    new_user_profile2['disliked_ingredients'].remove(dingredient)
                    print(new_user_profile2)
                    recipes_matching_all_criteria_but_2_criteria = list(self.get_recipes_matching_constraints(new_user_profile2).keys())
                    self.add_item_to_reco_dict(100-(2*CONSTRAINTS_COSTS['ingredient']), rid_list=recipes_matching_all_criteria_but_2_criteria, relaxed_constraint=ingredient+"+"+dingredient)


            #Relax diet and disliked ingredient
            for diet in self.user_profile['diets']:
                new_user_profile = copy.deepcopy(self.user_profile)
                new_user_profile['diets'].remove(diet)

                for dingredient in self.user_profile['disliked_ingredients']:
                    new_user_profile2 = copy.deepcopy(new_user_profile)
                    new_user_profile2['disliked_ingredients'].remove(dingredient)
                    print(new_user_profile2)
                    recipes_matching_all_criteria_but_2_criteria = list(self.get_recipes_matching_constraints(new_user_profile2).keys())
                    self.add_item_to_reco_dict(100-(CONSTRAINTS_COSTS[diet]+CONSTRAINTS_COSTS['ingredient']), rid_list=recipes_matching_all_criteria_but_2_criteria, relaxed_constraint=diet+"+"+dingredient)


            #Relax 2 liked ingredients (if more than 2 asked by user)
            if len(self.user_profile['liked_ingredients']) > 2:
                for ingredient in self.user_profile['liked_ingredients']:
                    new_user_profile = copy.deepcopy(self.user_profile)
                    new_user_profile['liked_ingredients'].remove(ingredient)

                    self.get_recipes_with_relaxed_liked_ingredient_constraint(new_user_profile, previous_costs=CONSTRAINTS_COSTS['time'], previous_constraints_str="time+")


            #Relax 2 liked diets (if more than 2 asked by user)
            if len(self.user_profile['diets']) > 2:
                for x in self.user_profile['diets']:
                    new_user_profile = copy.deepcopy(self.user_profile)
                    new_user_profile['diets'].remove(x)
                    for x2 in new_user_profile['diets']:
                        new_user_profile2 = copy.deepcopy(new_user_profile)
                        new_user_profile2['diets'].remove(x2)
                        print(new_user_profile2)
                        recipes_matching_all_criteria_but_2_criteria = list(self.get_recipes_matching_constraints(new_user_profile2).keys())
                        self.add_item_to_reco_dict(100-(CONSTRAINTS_COSTS[x]+CONSTRAINTS_COSTS[x2]), rid_list=recipes_matching_all_criteria_but_2_criteria, relaxed_constraint=x+"+"+x2)


            #Relax 2 liked disliked infredients (if more than 2 asked by user)
            if len(self.user_profile['disliked_ingredients']) > 2:
                for x in self.user_profile['disliked_ingredients']:
                    new_user_profile = copy.deepcopy(self.user_profile)
                    new_user_profile['disliked_ingredients'].remove(x)
                    for x2 in new_user_profile['disliked_ingredients']:
                        new_user_profile2 = copy.deepcopy(new_user_profile)
                        new_user_profile2['disliked_ingredients'].remove(x2)
                        print(new_user_profile2)
                        recipes_matching_all_criteria_but_2_criteria = list(self.get_recipes_matching_constraints(new_user_profile2).keys())
                        self.add_item_to_reco_dict(100-(CONSTRAINTS_COSTS['ingredient']+CONSTRAINTS_COSTS['ingredient']), rid_list=recipes_matching_all_criteria_but_2_criteria, relaxed_constraint=x+"+"+x2)


        print(self.n_recipes_in_reco_dict, self.reco_dict)



    def get_recipes_matching_constraints(self, user_profile):
        '''
        Filter recipes according to user profile. We MUST return something, so always check the current user recipeDB is not empty.
        :return:
        '''
        self.reset_current_DB()

        if user_profile['diets']:
            for diet in user_profile['diets']:
                OK_recipes = self.get_recipes_with_diet(diet)
                # self.check_new_recipes_and_set_new_DB(n_recipes, OK_recipes, "diet", diet)
                self.set_current_DB(OK_recipes)

        if user_profile['disliked_ingredients']:
            for ingredient in user_profile['disliked_ingredients']:
                OK_recipes = self.get_recipes_without_ingredient(ingredient)
                # self.check_new_recipes_and_set_new_DB(n_recipes, OK_recipes, "disliked ingredient", ingredient)
                self.set_current_DB(OK_recipes)

        if user_profile['liked_ingredients']:
            for ingredient in user_profile['liked_ingredients']:
                OK_recipes = self.get_recipes_with_ingredient(ingredient)
                # self.check_new_recipes_and_set_new_DB(n_recipes, OK_recipes, "liked ingredient", ingredient)
                self.set_current_DB(OK_recipes)

        if user_profile['time']:
            OK_recipes = self.get_recipes_ready_in_time(user_profile['time'])
            # self.check_new_recipes_and_set_new_DB(n_recipes, OK_recipes, "time", self.user_profile['time'])
            self.set_current_DB(OK_recipes)

        if user_profile['hungry']:
            if user_profile['hungry'] < 0.5:
                OK_recipes = self.get_light_recipes()
            elif user_profile['hungry'] > 0.5:
                OK_recipes = self.get_heavy_recipes()
            else:
                OK_recipes = self.get_normal_calories_recipes()
            # self.check_new_recipes_and_set_new_DB(n_recipes, OK_recipes, "hungry value", self.user_profile['hungry'].__str__())
            self.set_current_DB(OK_recipes)

        if user_profile['healthy']:
            if user_profile['healthy'] < 0.5:
                OK_recipes = self.get_FSAred_recipes()
            elif user_profile['healthy'] > 0.5:
                OK_recipes = self.get_FSAgreen_recipes()
            else:
                OK_recipes = self.get_FSAamber_recipes()
            # self.check_new_recipes_and_set_new_DB(n_recipes, OK_recipes, "healthy value", self.user_profile['healthy'].__str__())
            self.set_current_DB(OK_recipes)

        return self.recipe_DB

        # reco = list()
        # for rid, rdata in self.recipe_DB.items():
        #     list_of_keys_to_copy = list(rdata.keys())
        #     list_of_keys_to_copy.remove("reviews")
        #     new_reco = {'id': rid}
        #     for k in list_of_keys_to_copy:
        #         new_reco[k] = rdata[k]
        #     reco.append(new_reco)
        # print(colored(self.best_match_recipes, 'blue'))
        # return reco[:n_recipes]


    def reset_current_DB(self):
        self.recipe_DB = copy.copy(self.recipe_DB_all)

    def set_current_DB(self, rid_list):
        self.recipe_DB = dict()
        for rid in rid_list:
            self.recipe_DB[rid] = self.recipe_DB_all[rid]

    def print_current_DB_ids(self):
        print(len(self.recipe_DB.keys()))
        for rid, rdata in self.recipe_DB.items():
            print(rid, rdata['FSAscore'])

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
                ingredient_in_recipe_bool = False
                for r_ingredient in rdata[fc.ingredients]:
                    if ingredient in r_ingredient.lower():
                        ingredient_in_recipe_bool = True
                if not ingredient_in_recipe_bool:
                    res.append(rid)
                # else:
                #     print("ingredient %s in recipe %s" % (ingredient, rid))
        return res

    def get_recipes_with_diet(self, diet):
        recipes_to_return = list()
        for rid, rdata in self.recipe_DB.items():
            # print(rdata)
            if diet not in rdata['diets'].keys():
                pass
                # print(colored("Missing diet info for recipe %s!" % rid, "red"))
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
        # return self.get_recipes_with_attribute_val_in_range("FSAscore", FSA_UNHEALTHY, "less")
        # return self.get_recipes_with_attribute_val_in_range("FSAscore", FSA_HEALTHY, "more")
        raise ValueError("To implement")

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
        raise ValueError("To implement")
        # return self.get_recipes_with_N_calories(N_CALORIES_LIGHT_DINNER, "more")
        # return self.get_recipes_with_N_calories(N_CALORIES_HEAVY_DINNER, "less")

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



class KBCFhybrid():
    def __init__(self, clientid):
        self.kbrs = KBRS()
        self.cfrs = ImplicitCFRS()
        self.cfrs.set_healthy_bias(healthy_bias=False)
        self.cfrs.start()

        self.user_name = clientid

        self.user_ratings_list = list()

        self.cfrs_ratings_dict = dict()


    def set_user_ratings_list(self, ratings_list):
        self.user_ratings_list = ratings_list


    def set_user_profile(self, liked_ingredients, disliked_ingredients, diets, time_val, hungry=None, healthy=None):
        self.kbrs.set_user_profile(liked_ingredients, disliked_ingredients, diets, time_val, hungry, healthy)
        self.get_cfrs_ratings_dict()


    def get_cfrs_ratings_dict(self):
        cfrs_ratings = self.cfrs.get_reco(self.user_name, self.user_ratings_list, n_reco=TOTAL_RECIPES)
        for [_, rid, rating] in cfrs_ratings:
            self.cfrs_ratings_dict[rid] = rating


    def get_reco(self, n_reco=10):
        kbrs_reco = self.kbrs.get_recipe_for_user(n_reco)
        kbrs_reco = [rdata['id'] for rdata in kbrs_reco]
        print(kbrs_reco)

        print(cfrs_reco[:10])





if __name__ == "__main__":
    kbrs = KBRS()

    kbrs.set_user_profile(liked_ingredients=['broccoli', 'steak', 'chicken'], disliked_ingredients=['ginger', 'onion', 'garlic'], diets=['keto', 'gluten_free'], time_val=15)
    kbrs.get_recipes_for_user()

    kbrs.print_current_DB_ids()

    # hybridrs = KBCFhybrid("lucile")
    #
    # df = pd.read_csv(consts.csv_xUsers_Xrecipes_path)
    # ratings = [(rid, 5) for rid in rs_utils.get_recipes(df, "chicken")] + [(rid, 5) for rid in rs_utils.get_recipes(df, "chocolate")]
    # hybridrs.set_user_ratings_list(ratings)
    #
    # hybridrs.set_user_profile(liked_ingredients=['broccoli', 'steak'], disliked_ingredients=[], diets=[], time_val=20)
    #
    # hybridrs.get_reco()
