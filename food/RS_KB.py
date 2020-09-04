import json
import copy
import random
import operator
from termcolor import colored
import pandas as pd

import config
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
                     "ketonic": 5,
                     "low_carbs": 5,
                     "ingredient": 5,
                     "time": 2}

with open(consts.json_xUsers_Xrecipes_path, 'r') as f:
    recipes_data = json.load(f)['recipes_data']
    TOTAL_RECIPES = len(list(recipes_data.keys()))


def get_health_score(rid):
    rdata = recipes_data[rid]
    return rdata['FSAscore']

def get_avg_healthScore(rids_list):
    sum = 0
    for rid in rids_list:
        sum += get_health_score(rid)
    return float(sum/len(rids_list))

def is_recipe_dessert(rid):
    for word in ['cake', 'cookie', 'marshmallow', 'muffin', 'macaroons', 'magic-peanut-butter-middles', "smoothie", 'brownies',
                 'eileens-spicy-gingerbread-men', 'apple-squares', 'peanut-butter-temptations-ii', 'pecan-sandies', 'gobble-up-granola-snacks',
                 'thin-mint-crackers', 'chocolate-crinkles-ii', 'cranberry-pistachio-biscotti', 'peppermint-meringues', 'biscotti', 'chocolate-rum-balls-i',
                 'gingerbread-men']:
        if word in rid:
            return True
    return False
    

class KBRSModule(wbc.WhiteBoardClient):
    def __init__(self, clientid, subscribes, publishes, resp_time=False):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        # publishes = {fc.USUAL_DM_MSG : publishes[0] + clientid, fc.RECIPE_DM_MSG: publishes[1] + clientid}
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, "KBRS" + clientid, subscribes, publishes, resp_time)

        self.client_id = clientid
        # self.kbrs = KBRS()
        self.hybridrs = KBCFhybrid(clientid=clientid)
        self.user_ratings_set_bool = False



    def set_user_ratings_for_cf(self, ratings):
        self.user_ratings_set_bool = True
        self.hybridrs.set_user_ratings_list(ratings)


    def treat_message(self, msg, topic):
        super(KBRSModule, self).treat_message(msg, topic)

        if 'liked_recipes' in msg.keys():
            ratings = [(rid, 5) for rid in msg['liked_recipes']]
            self.set_user_ratings_for_cf(ratings)
            return


        subject = msg['msg']
        if subject == fc.set_user_profile:
            #TODO: get ratings from user for cf.

            if not self.user_ratings_set_bool:
                df = pd.read_csv(consts.csv_xUsers_Xrecipes_path)
                ratings = [(rid, 5) for rid in rs_utils.get_recipes(df, "chicken")] + [(rid, 5) for rid in rs_utils.get_recipes(df, "chocolate")]
                self.set_user_ratings_for_cf(ratings)
                error_msg = "WARNING: randomly selecting recipes for cf user profile!!"
                log.warn(error_msg)
                print(colored(error_msg, "red"))

            self.set_user_profile(liked_ingredients=msg[fc.liked_food], disliked_ingredients=msg[fc.disliked_food], diets=msg[fc.diet], time_val=msg[fc.time_to_cook])
        elif subject == fc.get_reco:

            reco_list = list()

            if config.chi_study_comparison_mode == config.chi_study_no_comp:
                reco1 = self.get_reco_pref()
                reco2 = self.get_reco_healthier_than_pref()
                identical_recipes = True if reco1 == reco2 else False
                reco_list.append(self.get_reco_data(reco2, reco_mode=fc.reco_mode_healthier, identical_recipes=identical_recipes))

            elif config.chi_study_comparison_mode == config.chi_study_comp_healthier:
                reco1 = self.get_reco_pref()
                reco2 = self.get_reco_healthier_than_pref()
                identical_recipes = True if (reco2 == None or reco1 == reco2) else False
                reco_list.append(self.get_reco_data(reco1, reco_mode=fc.reco_mode_pref, identical_recipes=identical_recipes))
                if not identical_recipes:
                    reco_list.append(self.get_reco_data(reco2, reco_mode=fc.reco_mode_healthier, identical_recipes=identical_recipes))

            elif config.chi_study_comparison_mode == config.chi_study_comp_bad_options:
                reco1 = self.get_reco_pref()
                reco2 = self.get_reco_healthier_than_pref()

                identical_recipes = True if (reco2 == None or reco1 == reco2) else False
                reco_list.append(self.get_reco_data(reco1, reco_mode=fc.reco_mode_pref, identical_recipes=identical_recipes))

                if not identical_recipes:
                    reco_list.append(self.get_reco_data(reco2, reco_mode=fc.reco_mode_healthier, identical_recipes=identical_recipes))
                    reco3 = self.get_reco_less_healthy_less_pref()
                    if reco3:
                        reco_list.append(self.get_reco_data(reco3, reco_mode=fc.reco_mode_bad_reco, identical_recipes=identical_recipes))


            self.publish({"msg": fc.reco_recipes, fc.reco_list: reco_list})



    def get_reco_data(self, reco, reco_mode, identical_recipes=False):
        reco_id = reco[0]
        reco_data = copy.deepcopy(recipes_data[reco_id])
        reco_data['reviews'] = None
        del reco_data['reviews']
        reco_data['id'] = reco_id
        reco_data['utility'] = reco[1]
        reco_data['cf_score'] = reco[2]
        reco_data['relaxed_constraints'] = self.hybridrs.get_relaxed_constraints(reco_id)
        reco_data['reco_mode'] = reco_mode
        reco_data['identical_recipes'] = identical_recipes
        return reco_data


    def set_user_profile(self, liked_ingredients, disliked_ingredients, diets, time_val):
        self.hybridrs.set_user_profile(liked_ingredients=liked_ingredients, disliked_ingredients=disliked_ingredients, diets=diets, time_val=time_val)

    # def get_reco(self, n_reco):
    #     return self.kbrs.get_recipe_for_user(n_recipes=n_reco)

    def get_reco_pref(self):
        return self.hybridrs.get_recipe_pref()

    def get_reco_healthier_than_pref(self):
        return self.hybridrs.get_recipe_healthier_than_pref()

    def get_reco_less_healthy_less_pref(self):
        return self.hybridrs.get_reco_less_healthy_less_prefered()

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
        # we sometimes get recommendations that don't match the user profile. We need to know how we obtained those reco (i.e. which contraints we relaxed)
        self.reco_rid_to_user_profile = dict()
        self.reco_rid_to_relaxed_constraint = dict()
        self.rid_to_utility = dict()

        # reco list --> list of lists that will help get order the elements of the reco dict
        self.reco_list = list()

    def reset_reco_data(self):
        ## Number of recipes in the list that best fit the required criteria; i.e. when we don't recipes matching one of the user's constraints, we put the ones that match in the beginning of the list and we keep the rest at the end...
        self.best_match_recipes = list()

        self.reco_dict = dict()
        self.n_recipes_in_reco_dict = 0
        self.all_recipes_in_reco_dict = list()
        # we sometimes get recommendations that don't match the user profile. We need to know how we obtained those reco (i.e. which contraints we relaxed)
        self.reco_rid_to_user_profile = dict()
        self.reco_rid_to_relaxed_constraint = dict()
        self.rid_to_utility = dict()

        # reco list --> list of lists that will help get order the elements of the reco dict
        self.reco_list = list()

    def reset_user_profile(self):
        self.user_profile = {
            "liked_ingredients": list(),
            "disliked_ingredients": list(),
            "diets": list(),
            "time": None,
            "hungry": None,
            "healthy": None
        }

    def set_user_profile(self, liked_ingredients, disliked_ingredients, diets, time_val, hungry=None, healthy=None):
        self.reset_user_profile()
        self.reset_reco_data()

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


    def add_item_to_reco_dict(self, utility, rid_list, relaxed_constraint, user_profile):
        # print(utility, rid_list, relaxed_constraint, user_profile)
        if rid_list and len(rid_list):
            if utility not in self.reco_dict.keys():
                self.reco_dict[utility] = {"rids": list(), "relaxed_constraints": list()}
            # self.reco_dict[utility]['rids'] += rid_list
            for rid in rid_list:
                if rid not in self.all_recipes_in_reco_dict:
                    self.all_recipes_in_reco_dict.append(rid)
                    self.reco_dict[utility]['rids'].append(rid)
                    self.n_recipes_in_reco_dict += 1
                    self.reco_rid_to_user_profile[rid] = user_profile
                    self.reco_rid_to_relaxed_constraint[rid] = relaxed_constraint
                    self.rid_to_utility[rid] = utility
            self.reco_dict[utility]["relaxed_constraints"].append(relaxed_constraint)



    def get_recipes_with_relaxed_liked_ingredient_constraint(self, user_profile, previous_costs=0, previous_constraints_str="", print_user_profile=False):

        for ingredient in user_profile['liked_ingredients']:
            new_user_profile2 = copy.deepcopy(user_profile)
            new_user_profile2['liked_ingredients'].remove(ingredient)
            recipes = list(self.get_recipes_matching_constraints(new_user_profile2, print_user_profile).keys())
            self.add_item_to_reco_dict(100-(previous_costs+CONSTRAINTS_COSTS['ingredient']), rid_list=recipes, relaxed_constraint=previous_constraints_str+ingredient, user_profile=new_user_profile2)


    def get_recipes_with_relaxed_DISliked_ingredient_constraint(self, user_profile, previous_costs=0, previous_constraints_str="", print_user_profile=False):

        for ingredient in user_profile['disliked_ingredients']:
            new_user_profile2 = copy.deepcopy(user_profile)
            new_user_profile2['disliked_ingredients'].remove(ingredient)
            recipes = list(self.get_recipes_matching_constraints(new_user_profile2, print_user_profile).keys())
            self.add_item_to_reco_dict(100-(previous_costs+CONSTRAINTS_COSTS['ingredient']), rid_list=recipes, relaxed_constraint=previous_constraints_str+ingredient, user_profile=new_user_profile2)


    def get_recipes_with_relaxed_diet_constraint(self, user_profile, previous_costs=0, previous_constraints_str="", print_user_profile=False):

        for x in user_profile['diets']:
            new_user_profile2 = copy.deepcopy(user_profile)
            new_user_profile2['diets'].remove(x)
            recipes = list(self.get_recipes_matching_constraints(new_user_profile2, print_user_profile).keys())
            self.add_item_to_reco_dict(100-(previous_costs+CONSTRAINTS_COSTS[x]), rid_list=recipes, relaxed_constraint=previous_constraints_str+x, user_profile=new_user_profile2)


    def get_recipes_for_user(self, n_recipes=5, print_user_profile=False):
        self.get_recipes_for_user_rec(self.user_profile, n_recipes=n_recipes, print_user_profile=print_user_profile)
        for utility, reco_item in self.reco_dict.items():
            rids = reco_item['rids']
            self.reco_list.append([rids, utility])
        self.reco_list = sorted(self.reco_list, key=operator.itemgetter(1), reverse=True)


    def get_recipes_for_user_rec(self, user_profile, previous_cost=0, n_recipes=5, print_user_profile=False):

        #################################################
        ##      When too many ingredients directly relax constraints
        if len(user_profile['liked_ingredients']) > 3:
            new_user_profile = copy.deepcopy(user_profile)
            random.shuffle(new_user_profile['liked_ingredients'])
            new_user_profile['liked_ingredients'] = new_user_profile['liked_ingredients'][:3]
            self.get_recipes_for_user_rec(new_user_profile, n_recipes=n_recipes, previous_cost=5*(len(user_profile['liked_ingredients']) - 3), print_user_profile=print_user_profile)


        #################################################
        ##      Perfect match
        recipes_matching_all_criteria = list(self.get_recipes_matching_constraints(user_profile, print_user_profile).keys())
        self.add_item_to_reco_dict(100-previous_cost, recipes_matching_all_criteria, None, user_profile=user_profile)

        #################################################
        ##      Relax one constraint

        # Relax time (+15min)
        if self.n_recipes_in_reco_dict < n_recipes:
            # we don't have enough recipes, let's relax some constraints
            new_user_profile = copy.deepcopy(user_profile)
            if new_user_profile["time"]:
                new_user_profile['time'] += 15
                recipes_matching_all_criteria_but_time = list(self.get_recipes_matching_constraints(new_user_profile, print_user_profile).keys())
                self.add_item_to_reco_dict(100-previous_cost-CONSTRAINTS_COSTS['time'], rid_list=recipes_matching_all_criteria_but_time, relaxed_constraint="time", user_profile=new_user_profile)

        # Relax time (cancelled)
        if self.n_recipes_in_reco_dict < n_recipes:
            new_user_profile = copy.deepcopy(user_profile)
            if new_user_profile["time"]:
                new_user_profile['time'] = 1000
                recipes_matching_all_criteria_but_time = list(self.get_recipes_matching_constraints(new_user_profile, print_user_profile).keys())
                self.add_item_to_reco_dict(100-previous_cost-(CONSTRAINTS_COSTS['time']*2), rid_list=recipes_matching_all_criteria_but_time, relaxed_constraint="time2", user_profile=new_user_profile)

        # Relax liked ingredient, disliked ingredient, diet
        if self.n_recipes_in_reco_dict < n_recipes:
            self.get_recipes_with_relaxed_liked_ingredient_constraint(user_profile, previous_costs=previous_cost, print_user_profile=print_user_profile)
            self.get_recipes_with_relaxed_diet_constraint(user_profile, previous_costs=previous_cost, print_user_profile=print_user_profile)
            self.get_recipes_with_relaxed_DISliked_ingredient_constraint(user_profile, previous_costs=previous_cost, print_user_profile=print_user_profile)


        #################################################
        ##      Relax 2 constraints

        if self.n_recipes_in_reco_dict < n_recipes:
            self.get_recipes_2_contraints_relaxed(user_profile, previous_costs=previous_cost, print_user_profile=print_user_profile)


        #################################################
        ##      Relax 3 constraints

        if self.n_recipes_in_reco_dict < n_recipes:
            self.get_recipes_3_contraints_relaxed(user_profile, previous_costs=previous_cost, print_user_profile=print_user_profile)


        #################################################
        ##      If more than 3 constraints to relax, just pick at random constraint to keep
        if self.n_recipes_in_reco_dict < n_recipes:
            if len(user_profile['liked_ingredients']) > 3:
                new_user_profile = copy.deepcopy(user_profile)
                random.shuffle(new_user_profile['liked_ingredients'])
                new_user_profile['liked_ingredients'] = new_user_profile['liked_ingredients'][:3]
                self.get_recipes_for_user_rec(new_user_profile, n_recipes=n_recipes, previous_cost=5*(len(user_profile['liked_ingredients']) - 3), print_user_profile=print_user_profile)

            if len(user_profile['disliked_ingredients']) > 3:
                new_user_profile = copy.deepcopy(user_profile)
                random.shuffle(new_user_profile['disliked_ingredients'])
                new_user_profile['disliked_ingredients'] = new_user_profile['disliked_ingredients'][:3]
                self.get_recipes_for_user_rec(new_user_profile, n_recipes=n_recipes, previous_cost=5*(len(user_profile['disliked_ingredients']) - 3), print_user_profile=print_user_profile)

            if len(user_profile['diets']) > 3:
                new_user_profile = copy.deepcopy(user_profile)
                random.shuffle(new_user_profile['diets'])
                new_user_profile['diets'] = new_user_profile['diets'][:3]
                self.get_recipes_for_user_rec(new_user_profile, n_recipes=n_recipes, previous_cost=5*(len(user_profile['diets']) - 3), print_user_profile=print_user_profile)


    def get_recipes_3_contraints_relaxed(self, user_profile, previous_costs=0, previous_constraints_str="", print_user_profile=False):
        #Relax liked ingredients and 2 others
        for ingredient in user_profile['liked_ingredients']:
            new_user_profile = copy.deepcopy(user_profile)
            new_user_profile['liked_ingredients'].remove(ingredient)
            self.get_recipes_2_contraints_relaxed(new_user_profile, previous_costs=previous_costs+CONSTRAINTS_COSTS['ingredient'], previous_constraints_str=previous_constraints_str+ingredient+"+", print_user_profile=print_user_profile)
        #Relax disliked ingredients and 2 others
        for ingredient in user_profile['disliked_ingredients']:
            new_user_profile = copy.deepcopy(user_profile)
            new_user_profile['disliked_ingredients'].remove(ingredient)
            self.get_recipes_2_contraints_relaxed(new_user_profile, previous_costs=previous_costs+CONSTRAINTS_COSTS['ingredient'], previous_constraints_str=previous_constraints_str+ingredient+"+", print_user_profile=print_user_profile)
        #Relax diets and 2 others
        for diet in user_profile['diets']:
            new_user_profile = copy.deepcopy(user_profile)
            new_user_profile['diets'].remove(diet)
            self.get_recipes_2_contraints_relaxed(new_user_profile, previous_costs=previous_costs+CONSTRAINTS_COSTS[diet], previous_constraints_str=previous_constraints_str+diet+"+", print_user_profile=print_user_profile)


    def get_recipes_2_contraints_relaxed(self, user_profile, previous_costs=0, previous_constraints_str="", print_user_profile=False):
        #################################################
        ##      Relax 2 constraints

        # Relax time (+15min) and another
        new_user_profile = copy.deepcopy(user_profile)
        if new_user_profile["time"]:
            new_user_profile['time'] += 15
            self.get_recipes_with_relaxed_liked_ingredient_constraint(new_user_profile, previous_costs=previous_costs+CONSTRAINTS_COSTS['time'], previous_constraints_str=previous_constraints_str+"time+", print_user_profile=print_user_profile)
            self.get_recipes_with_relaxed_diet_constraint(new_user_profile, previous_costs=previous_costs+CONSTRAINTS_COSTS['time'], previous_constraints_str=previous_constraints_str+"time+", print_user_profile=print_user_profile)
            self.get_recipes_with_relaxed_DISliked_ingredient_constraint(new_user_profile, previous_costs=previous_costs+CONSTRAINTS_COSTS['time'], previous_constraints_str=previous_constraints_str+"time+", print_user_profile=print_user_profile)

        # Relax time (cancelled) and another
        new_user_profile = copy.deepcopy(user_profile)
        if new_user_profile["time"]:
            new_user_profile['time'] = 1000
            self.get_recipes_with_relaxed_liked_ingredient_constraint(new_user_profile, previous_costs=previous_costs+CONSTRAINTS_COSTS['time']*2, previous_constraints_str=previous_constraints_str+"time2+", print_user_profile=print_user_profile)
            self.get_recipes_with_relaxed_diet_constraint(new_user_profile, previous_costs=previous_costs+CONSTRAINTS_COSTS['time']*2, previous_constraints_str=previous_constraints_str+"time2+", print_user_profile=print_user_profile)
            self.get_recipes_with_relaxed_DISliked_ingredient_constraint(new_user_profile, previous_costs=previous_costs+CONSTRAINTS_COSTS['time']*2, previous_constraints_str=previous_constraints_str+"time2+", print_user_profile=print_user_profile)


        # Relax liked ingredient and another (disliked ingredient or diet)
        for ingredient in user_profile['liked_ingredients']:
            new_user_profile = copy.deepcopy(user_profile)
            new_user_profile['liked_ingredients'].remove(ingredient)
            self.get_recipes_with_relaxed_diet_constraint(new_user_profile, previous_costs=previous_costs+CONSTRAINTS_COSTS['ingredient'], previous_constraints_str=previous_constraints_str+ingredient+"+", print_user_profile=print_user_profile)
            self.get_recipes_with_relaxed_DISliked_ingredient_constraint(new_user_profile, previous_costs=previous_costs+CONSTRAINTS_COSTS['ingredient'], previous_constraints_str=previous_constraints_str+ingredient+"+", print_user_profile=print_user_profile)


        #Relax diet and disliked ingredient
        for diet in user_profile['diets']:
            new_user_profile = copy.deepcopy(user_profile)
            new_user_profile['diets'].remove(diet)
            self.get_recipes_with_relaxed_DISliked_ingredient_constraint(new_user_profile, previous_costs=previous_costs+CONSTRAINTS_COSTS[diet], previous_constraints_str=previous_constraints_str+diet+"+", print_user_profile=print_user_profile)


        #Relax 2 liked ingredients (if more than 2 asked by user)
        if len(user_profile['liked_ingredients']) >= 2:
            for ingredient in user_profile['liked_ingredients']:
                new_user_profile = copy.deepcopy(user_profile)
                new_user_profile['liked_ingredients'].remove(ingredient)
                self.get_recipes_with_relaxed_liked_ingredient_constraint(new_user_profile, previous_costs=previous_costs+CONSTRAINTS_COSTS['ingredient'], previous_constraints_str=previous_constraints_str+ingredient+"+", print_user_profile=print_user_profile)

        #Relax 2 liked diets (if more than 2 asked by user)
        if len(user_profile['diets']) >= 2:
            for x in user_profile['diets']:
                new_user_profile = copy.deepcopy(user_profile)
                new_user_profile['diets'].remove(x)
                self.get_recipes_with_relaxed_diet_constraint(new_user_profile, previous_costs=previous_costs+CONSTRAINTS_COSTS[diet], previous_constraints_str=previous_constraints_str+diet+"+", print_user_profile=print_user_profile)

        #Relax 2 disliked infredients (if more than 2 asked by user)
        if len(user_profile['disliked_ingredients']) >= 2:
            for x in user_profile['disliked_ingredients']:
                new_user_profile = copy.deepcopy(user_profile)
                new_user_profile['disliked_ingredients'].remove(x)
                self.get_recipes_with_relaxed_DISliked_ingredient_constraint(new_user_profile, previous_costs=previous_costs+CONSTRAINTS_COSTS['ingredient'], previous_constraints_str=previous_constraints_str+x+"+", print_user_profile=print_user_profile)




    def get_recipes_matching_constraints(self, user_profile, print_user_profile=False):
        if print_user_profile:
            print(user_profile)

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
            if diet not in rdata['diets'].keys():
                pass
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

        self.rid_to_cfscore = dict()

        # list of lists of reco
        self.reco_list = list()

        self.cf_profile_hs = None

    def set_user_ratings_list(self, ratings_list):
        self.user_ratings_list = ratings_list
        self.cf_profile_hs = get_avg_healthScore([rid for [rid, _] in ratings_list])


    def set_user_profile(self, liked_ingredients, disliked_ingredients, diets, time_val, hungry=None, healthy=None):
        self.reco_list = list()
        self.kbrs.set_user_profile(liked_ingredients, disliked_ingredients, diets, time_val, hungry, healthy)
        self.get_cfrs_ratings_dict()


    def get_cfrs_ratings_dict(self):
        cfrs_ratings = self.cfrs.get_reco(self.user_name, self.user_ratings_list, n_reco=TOTAL_RECIPES)
        for [_, rid, rating] in cfrs_ratings:
            self.rid_to_cfscore[rid] = rating


    def get_reco(self):
        self.kbrs.get_recipes_for_user(TOTAL_RECIPES-len(self.user_ratings_list))
        for [rids_list, utility] in self.kbrs.reco_list:
            if rids_list:
                sublist = list()
                for rid in rids_list:
                    if rid in self.rid_to_cfscore.keys():
                        rid_w_cf_rating = [rid, self.rid_to_cfscore[rid]]
                        sublist.append(rid_w_cf_rating)
                    # else:
                    #     print(colored("USED IN CF PROFILE!!!!!!", "green"))
                if sublist:
                    sublist = sorted(sublist, key=operator.itemgetter(1), reverse=True)
                    self.reco_list.append([utility, sublist])




    def get_recipe_pref(self):
        '''
        :return: the recipe that best corresponds to the user's tastes; i.e. recipe with the hight (utility, cf-score).
        '''
        if not self.reco_list:
            self.get_reco()
        # print(self.reco_list[:3])
        try:
            rid = self.reco_list[0][1][0][0]
            utility = self.reco_list[0][0]
            cf_score = self.reco_list[0][1][0][1]
            health_score = get_health_score(rid)
            return rid, utility, cf_score, health_score
        except IndexError as e:
            print(self.reco_list)
            raise  IndexError(e)


    def get_recipe_healthier_than_pref(self):
        '''
        :return: a recipe that still corresponds to the user's tastes; but that has a higher health score.
        '''
        if not self.reco_list:
            self.get_reco()
        rid_pref, utility_pref, cf_score_pref, health_score_pref = self.get_recipe_pref()

        is_dessert_pref = is_recipe_dessert(rid_pref)

        # reco_with_healthscores_list = list()
        for [utility, sublist] in self.reco_list:
            for [rid, cf_score] in sublist:
                health_score = get_health_score(rid)
                is_dessert_health = is_recipe_dessert(rid)
                if health_score < health_score_pref and is_dessert_pref == is_dessert_health and self.cf_profile_hs > health_score:
                    return rid, utility, cf_score, health_score
        #         reco_with_healthscores_list.append([rid, get_health_score(rid)])
        # reco_with_healthscores_list = sorted(reco_with_healthscores_list, key=operator.itemgetter(1))
        # rid = reco_with_healthscores_list[0][0]
        # utility = self.kbrs.rid_to_utility[rid]
        # cf_score = self.rid_to_cfscore[rid]
        # health_score = reco_with_healthscores_list[0][1]
        # return rid, utility, cf_score, health_score


    def get_reco_less_healthy_less_prefered(self):
        rid_pref, utility_pref, cf_score_pref, health_score_pref = self.get_recipe_pref()
        is_dessert_pref = is_recipe_dessert(rid_pref)
        rid_h, utility_h, cf_score_h, health_score_h = self.get_recipe_healthier_than_pref()
        rid_to_return, u_to_return, cfs_to_return, hs_to_return = None, None, None, None
        for [utility, sublist] in self.reco_list:
            for [rid, cf_score] in sublist:
                health_score = get_health_score(rid)
                is_dessert_current = is_recipe_dessert(rid)
                # healthiER than pref but NOT healthier than the one we want the user to choose (healthier recipe)
                cond_health = health_score < health_score_pref and health_score >= health_score_h
                if rid != rid_h and cond_health and utility < utility_pref and is_dessert_current == is_dessert_pref:
                    # try to get utility of bad reco worse than utility of healthier reco
                    if not rid_to_return:
                        rid_to_return, u_to_return, cfs_to_return, hs_to_return = rid, utility, cf_score, health_score
                    if utility < utility_h:
                        return rid, utility, cf_score, health_score
        if rid_to_return:
            return rid_to_return, u_to_return, cfs_to_return, hs_to_return
        print(colored("ALERT! Did not find 3rd recipe!!", "magenta"))


    def get_relaxed_constraints(self, rid):
        return self.kbrs.reco_rid_to_relaxed_constraint[rid]


if __name__ == "__main__":
    # kbrs = KBRS()
    #
    # kbrs.set_user_profile(liked_ingredients=['broccoli', 'steak', 'chicken', "tomato", "pasta", "rice"], disliked_ingredients=['ginger', 'onion', 'garlic'], diets=['keto', 'gluten_free'], time_val=15)
    # kbrs.get_recipes_for_user(n_recipes=5)
    #
    # kbrs.print_current_DB_ids()

    # hybridrs = KBCFhybrid("lucile")
    #
    # df = pd.read_csv(consts.csv_xUsers_Xrecipes_path)
    # # print(df.shape)
    # ratings = [(rid, 5) for rid in rs_utils.get_recipes(df, "chicken")] + [(rid, 5) for rid in rs_utils.get_recipes(df, "chocolate")]
    # print(ratings)
    # hybridrs.set_user_ratings_list(ratings)
    #
    # # ingredients_to_check = ["Beef", "Chicken", "Duck", "Eggs", "Lamb", "Pork", "Turkey", "Veal"]
    # # ingredients_to_check = ["Alaska pollock", "Clams", "Cod", "Crab", "Haddock", "Halibut", "Prawns", "salmon", "Seabass", "Shrimp", "Tilapia", "Tuna"] # ["Clams", "Shrimp", "Tilapia"]
    # # ingredients_to_check = ["Aspargus", "Avocado", "Beetroots", "Broccoli", "Brussels sprouts", "Cabbage", "Carrots", "Cauliflower", "Celery", "Chilies", "Corn", "Cucumbers", "Eggplant", "Garlic", "Green beans", "Kale", "Kidney beans", "Lettuce", "Mushrooms", "Onions", "Peas", "Peppers", "Potato", "Red cabbage", "Spinach", "Spring onions", "Sweetcorn", "Sweet potato", "Tomatoes", "Turnips", "Zucchini"]
    # # ingredients_to_check = ["Avocado", "Broccoli", "Brussels sprouts", "Cabbage", "Carrots", "Cauliflower", "Celery", "Chilies", "Corn", "Garlic", "Green beans", "Kale", "Kidney beans", "Lettuce", "Mushrooms", "Onions", "Peas", "Peppers", "Potato", "Spinach", "Sweet potato", "Tomatoes", "Zucchini"]
    # # ingredients_to_check = ["Apples", "Bananas", "Blueberries", "Cantaloupe", "Cherries", "Grapes", "Lemons", "Limes", "Oranges", "Peaches", "Pineapple", "Strawberries", "Watermelon"]
    # # ingredients_to_check = ["Apples", "Bananas", "Blueberries", "Cherries", "Grapes", "Lemons", "Limes", "Oranges", "Peaches", "Pineapple", "Strawberries"]
    # # ingredients_to_check = ["Brown rice", "Chickpeas", "Couscous", "Kidney beans", "Lentils", "Pasta", "Potatoes", "Quinoa", "Rice", "Tofu"]
    # # ingredients_to_check = ["Brown rice", "Kidney beans", "Lentils", "Pasta", "Potatoes", "Rice", "Tofu"]
    # ingredients_to_check = ["Apples", "Bananas", "Blueberries", "Cantaloupe", "Cherries", "Grapes", "Lemons", "Limes", "Oranges", "Peaches", "Pineapple", "Strawberries", "Watermelon"]
    #
    # for ingredient in ingredients_to_check:
    #     print("Checking " + ingredient)
    #
    #     hybridrs.set_user_profile(liked_ingredients=[ingredient], disliked_ingredients=[], diets=[], time_val=1000)
    #
    #     rid, utility, cf_score, health_score = hybridrs.get_recipe_pref()
    #     print(rid, utility)
    #
    #     if utility != 100:
    #         print(colored("No recipe with " + ingredient, 'red'))

    print(is_recipe_dessert("6854/streusel-topped-blueberry-muffins/"), is_recipe_dessert("9870/easy-sugar-cookies/"))
    print(is_recipe_dessert("6854/streusel-topped-blueberry-muffins/") == is_recipe_dessert("9870/easy-sugar-cookies/"))
