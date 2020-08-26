import whiteboard_client as wbc
import helper_functions as helper
import json
import food.food_config as fc
import random
from pathlib import Path
import pandas
import urllib.request
from ca_logging import log
from termcolor import colored
from fuzzywuzzy import fuzz
import threading
import copy
import numpy as np
import operator
import multiprocessing
from food.food_dataparser import extensive_food_DBs

class DM(wbc.WhiteBoardClient):
    def __init__(self, clientid, subscribes, publishes, resp_time=False):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        # publishes = {fc.USUAL_DM_MSG : publishes[0] + clientid, fc.RECIPE_DM_MSG: publishes[1] + clientid}
        publishes = [p + clientid for p in publishes]
        wbc.WhiteBoardClient.__init__(self, "DM" + clientid, subscribes, publishes, resp_time)

        self.client_id = clientid

        self.currState = "start"
        # Do we store the users preferences in a user model?
        self.store_pref = True

        self.from_NLU = None
        # self.from_SA = None
        self.food_data = None

        # self.load_food_data()

        self.current_recipe_list = None
        self.current_food_options = {fc.meal: "", fc.dessert: "", fc.drink: "", fc.meat: "", fc.side: ""}
        self.nodes = {}

        state_values = {fc.healthiness: 0, fc.food_fillingness: 0}
        self.user_model = {fc.user_name: None,
                           fc.usual_dinner: [],
                           fc.liked_features: [], fc.disliked_features: [],
                           fc.liked_food: [], fc.disliked_food: [],
                           fc.liked_cuisine: [], fc.disliked_cuisine: [],
                           fc.liked_recipe: [], fc.disliked_recipe: [],
                           fc.diet: [], fc.intolerances: None,
                           fc.time_to_cook: False,
                           fc.situation: "Usual Dinner",
                           fc.food_scores_trait: None, fc.food_scores_state: state_values}
        self.load_model(fc.DM_MODEL)
        ##self.load_user_model(fc.USER_MODELS, clientid)
        self.use_local_recipe_DB = False
        # self.situated_food_matrix = self.get_food_per_situation(self.user_model[fc.situation])
        # self.situated_food_matrix = helper.norm_pandas_matrix(self.situated_food_matrix)

        self.n_recommendations = 0
        self.n_accepted_recommendations = 0
        self.list_sorted_ingredients = list()
        self.current_recipe_list = list()
        self.already_recommended_recipe_list = list()
        self.requery_because_got_new_required_food = False

        self.food_values = None
        self.spoonacular_queries = list()
        self.used_seed_ingredients = list()



    def set_use_local_recipe_DB(self, val):
        self.use_local_recipe_DB = val

    # Parse the model.csv file and transform that into a dict of Nodes representing the scenario
    def load_model(self, path):
        with open(path) as f:
            for line in f:
                line_input = line.replace('\n', '')
                line_input = line_input.split(",")
                node = DMNode(line_input[0], line_input[1], line_input[2])
                for i in range(3, len(line_input)):
                    if "-" in line_input[i]:
                        node.add(line_input[i])
                self.nodes[node.stateName] = node

    def save_user_model(self):
        file = fc.USER_MODELS + self.client_id + ".prefs"
        with open(file, 'w') as outfile:
            json.dump(self.user_model, outfile)

    def load_user_model(self, path, client_id):
        file = Path(path + client_id + ".prefs")
        if file.is_file():
            with open(file) as json_file:
                self.user_model = json.load(json_file)

    def check_if_previous_recommendation_is_liked(self):
        if fc.yes in self.from_NLU[fc.intent]:
            self.user_model[fc.liked_recipe].append(self.current_recipe_list.pop(0))
            self.n_accepted_recommendations += 1
            return True
        return False

    def check_if_previous_recommendation_is_disliked(self):
        user_says_no = fc.no in self.from_NLU[fc.intent]
        user_says_dislike_ingredient = fc.inform in self.from_NLU[fc.intent] and fc.food in self.from_NLU[fc.entity_type] and "-" in self.from_NLU[fc.polarity]
        user_says_want_more = fc.request in self.from_NLU[fc.intent] and fc.more in self.from_NLU[fc.entity_type]
        if user_says_no or user_says_dislike_ingredient or user_says_want_more:
            self.user_model[fc.disliked_recipe].append(self.current_recipe_list.pop(0))
            return True
        return False

    def treat_message(self, msg, topic):

        self.requery_because_got_new_required_food = False
        recipe_ingredients_list = None

        super(DM, self).treat_message(msg, topic)

        # Todo: Second interaction
        # Todo: no then request(sweet/bitter/...)

        if "HealthDiagnostic" in topic:
            self.user_model[fc.food_scores_trait] = msg[fc.food_scores_trait]

        if "RS" in topic:
            subject = msg["msg"]
            if subject == fc.reco_recipes:
                recipes = msg[fc.reco_list]
                self.n_recommendations += 1

                self.move_state_and_publish_for_NLG(recipes=recipes, recipe_ingredients_list=None)

        elif "NLU" in topic:
            self.from_NLU = msg
            self.from_NLU = self.parse_from_NLU(self.from_NLU)

            recipes = None
            self.next_state = self.nodes.get(self.currState).get_action(self.from_NLU)

            if fc.inform_food in self.currState:
                pass

            if fc.inform in self.from_NLU[fc.intent]:
                if fc.user_name in self.from_NLU[fc.entity_type]:
                    self.user_model[fc.user_name] = self.from_NLU[fc.entity]
                if fc.health in self.from_NLU[fc.entity_type]:
                    if isinstance(self.from_NLU[fc.entity], float) or isinstance(self.from_NLU[fc.entity], int):
                        self.user_model[fc.food_scores_state][fc.healthiness] = self.from_NLU[fc.entity]
                    else:
                        if self.from_NLU[fc.entity] is True:
                            self.user_model[fc.liked_features].append(fc.health)
                            self.user_model[fc.food_scores_state][fc.healthiness] = 1
                        elif self.from_NLU[fc.entity] is False:
                            self.user_model[fc.food_scores_state][fc.healthiness] = -1
                if fc.hungry in self.from_NLU[fc.entity_type]:
                    if isinstance(self.from_NLU[fc.entity], float) or isinstance(self.from_NLU[fc.entity], int):
                        self.user_model[fc.food_scores_state][fc.food_fillingness] = self.from_NLU[fc.entity]
                    else:
                        if self.from_NLU[fc.entity] is True:
                            self.user_model[fc.liked_features].append(fc.filling)
                            self.user_model[fc.food_scores_state][fc.food_fillingness] = 1
                        elif self.from_NLU[fc.entity] is False:
                            self.user_model[fc.food_scores_state][fc.food_fillingness] = -1
                if fc.time in self.from_NLU[fc.entity_type] and self.from_NLU[fc.entity] is False:
                    self.user_model[fc.liked_features].append(fc.time)
                if fc.duration in self.from_NLU[fc.entity_type]:
                    self.user_model[fc.time_to_cook] = self.from_NLU[fc.entity]
                if fc.diet in self.from_NLU[fc.entity_type]:
                    self.user_model[fc.diet] = self.from_NLU[fc.entity]
                if fc.intolerances in self.from_NLU[fc.entity_type]:
                    # self.user_model[fc.disliked_food].append(self.from_NLU[fc.entity])
                    self.add_disliked_foods(self.from_NLU[fc.entity].split(","))
                    self.user_model[fc.intolerances] = self.from_NLU[fc.entity]
                if fc.food in self.from_NLU[fc.entity_type]:
                    ingredients_list = self.from_NLU[fc.entity]
                    if self.currState == "request(usual_dinner)" and "+" in self.from_NLU[fc.polarity]:
                        self.user_model[fc.usual_dinner] += ingredients_list
                    else:
                        if "+" in self.from_NLU[fc.polarity]:
                            self.add_liked_foods(ingredients_list)
                        else:
                            self.add_disliked_foods(ingredients_list)
                            self.remove_recipes_with_disliked_ingredients()
                if fc.cuisine in self.from_NLU[fc.entity_type]:
                    cuisines_list = self.from_NLU[fc.entity]
                    if self.currState == "request(usual_dinner)" and "+" in self.from_NLU[fc.polarity]:
                        self.user_model[fc.usual_dinner] += cuisines_list
                    else:
                        if "+" in self.from_NLU[fc.polarity]:
                            self.add_liked_cuisines(cuisines_list)
                        else:
                            self.add_disliked_cuisines(cuisines_list)


            if fc.healthy in self.currState:
                if fc.yes in self.from_NLU[fc.intent]:
                    self.user_model[fc.liked_features].append(fc.health)
            elif fc.filling in self.currState:
                if fc.yes in self.from_NLU[fc.intent]:
                    self.user_model[fc.liked_features].append(fc.filling)
            elif fc.time in self.currState:
                if fc.no in self.from_NLU[fc.intent]:
                    self.user_model[fc.liked_features].append(fc.time)
            wait_for_reco = False
            if fc.inform_food in self.next_state or fc.inform_food in self.currState:
                if self.n_recommendations == fc.MAX_RECOMMENDATIONS:
                    self.next_state = "bye"
                else:
                    # self.recommend(use_local_recipe_DB=self.use_local_recipe_DB)
                    wait_for_reco = True
                    self.ask_for_reco()

            # if the user comes back
            if self.next_state == 'greeting' and (self.user_model['liked_food']):
                self.next_state = "greet_back"

            if not wait_for_reco:
                self.move_state_and_publish_for_NLG(recipes=recipes, recipe_ingredients_list=recipe_ingredients_list)


    def move_state_and_publish_for_NLG(self, recipes, recipe_ingredients_list):

        # saves the user model at the end of the interaction
        if self.next_state == 'bye' and fc.SAVE_USER_MODEL:
            self.save_user_model()
            self.save_reco_data()

        prev_state = self.currState
        self.currState = self.next_state
        new_msg = self.msg_to_json(self.next_state, self.from_NLU, prev_state, self.user_model, recipes, recipe_ingredients_list)
        self.from_NLU = None
        self.publish({"current_state": self.currState}, topic=self.publishes[4])
        self.publish(new_msg, topic=self.publishes[0])


    def add_disliked_foods(self, foods_list):
        self.user_model[fc.disliked_food] += foods_list
        for food in foods_list:
            if food in self.user_model[fc.liked_food]:
                self.user_model[fc.liked_food].remove(food)

    def add_liked_foods(self, foods_list):
        self.requery_because_got_new_required_food = True
        self.user_model[fc.liked_food] += foods_list
        for food in foods_list:
            if food in self.user_model[fc.disliked_food]:
                self.user_model[fc.disliked_food].remove(food)

    def add_disliked_cuisines(self, cuisines_list):
        self.user_model[fc.disliked_cuisine] += cuisines_list
        for cuisine in cuisines_list:
            if cuisine in self.user_model[fc.liked_cuisine]:
                self.user_model[fc.liked_cuisine].remove(cuisine)

    def add_liked_cuisines(self, cuisines_list):
        self.requery_because_got_new_required_food = True
        self.user_model[fc.liked_cuisine] += cuisines_list
        for cuisine in cuisines_list:
            if cuisine in self.user_model[fc.disliked_cuisine]:
                self.user_model[fc.disliked_cuisine].remove(cuisine)

    def save_reco_data(self):
        data_reco = dict()
        data_reco["n_queries"] = len(self.spoonacular_queries)
        data_reco["queries"] = self.spoonacular_queries
        data_reco["n_seed_ingredients"] = len(self.used_seed_ingredients)
        data_reco["seed_ingredients"] = self.used_seed_ingredients
        data_reco["n_reco"] = self.n_recommendations
        data_reco["n_accepted_reco"] = self.n_accepted_recommendations
        data_reco["food_values"] = self.food_values
        data_reco["food_val_trait"] = self.user_model[fc.food_scores_trait]
        data_reco["food_val_state"] = self.user_model[fc.food_scores_state]
        data = {"data_recommendation": data_reco}
        self.publish(data, topic=self.publishes[2])
        self.publish(data, topic=self.publishes[3])


    def msg_to_json(self, intention, user_intent, previous_intent, user_frame, recipes, ingredients=None):
        frame = {fc.intent: intention, fc.user_intent: user_intent, fc.previous_intent: previous_intent, fc.user_model: user_frame, fc.recipes: recipes, fc.ingredients: ingredients}
        # json_msg = json.dumps(frame)
        return frame


    def parse_from_NLU(self, NLU_message):
        if "request" in NLU_message[fc.intent]:
            NLU_message[fc.intent] = NLU_message[fc.intent] + "(" + NLU_message[fc.entity_type] + ")"
        return NLU_message


    def ask_for_reco(self):
        msg = {"msg": fc.set_user_profile,
                      fc.liked_food: self.user_model[fc.liked_food],
                      fc.disliked_food: self.user_model[fc.disliked_food],
                      fc.diet: self.user_model[fc.diet],
                      fc.time_to_cook: self.user_model[fc.time_to_cook]}

        # if self.user_model[fc.diet]:
        #     msg[fc.diet].append(self.user_model[fc.diet])
        # if self.user_model[fc.intolerances]:
        #     msg[fc.diet].append(self.user_model[fc.intolerances])

        self.publish(msg, topic=self.publishes[5])

        self.publish({"msg": fc.get_reco}, topic=self.publishes[5])


    def preprocess_ingredient_name(self, ingredient):
        ingredient = ingredient.replace("dish", "")
        ingredient = ingredient.replace("side", "")
        ingredient = ingredient.replace("meal", "")
        ingredient = ingredient.replace("(only)", "")
        ingredient.strip()
        if "/" in ingredient:
            ingredient = ingredient.split("/")[0]
        ingredient = ingredient.replace(" ", "%20")
        return ingredient


    def get_calories(sel, recipe):
        for elt in recipe["nutrition"]:
            title = elt["title"]
            if title == "Calories":
                return elt["amount"]

    def get_ingredient_info(self, ingredient_name):
        ingredient_info = self.food_data.query("food_name == '" + ingredient_name + "'")
        return ingredient_info

    def get_ingredient_categories(self, ingredient_name):
        ingredient_info = self.get_ingredient_info(ingredient_name)
        types_list = list()
        for index, row in ingredient_info.iterrows():
            t = row[fc.food_type]
            if t not in types_list:
                types_list.append(t)
        return types_list

    def get_ingredient_main_category(self, ingredient_name):
        categories = self.get_ingredient_categories(ingredient_name)
        if "meal" in categories:
            return "meat"
        elif "meat" in categories:
            return "meat"
        else:
            return "side"



    # A node corresponds to a specific state of the dialogue. It contains:
# - a state ID (int)
# - a state name (String)
# - a default state (String) which represents the next state by default, whatever the user says.
# - a set of rules (dict) mapping a specific user intent to another state (e.g. yes-inform() means that if the user says
#   yes, the next state will be inform())
class DMNode:
    def __init__(self, state_name, state_default, state_ack):
        self.stateName = state_name
        self.stateDefault = state_default
        if state_ack.lower() == "true":
            self.stateAck = True
        else:
            self.stateAck = False
        self.rules = {}

    def add(self, string):
        intents = string.split("-")
        self.rules[intents[0]] = intents[1]

    def get_action(self, from_NLU):
        user_intent = from_NLU[fc.intent]
        if user_intent == fc.inform:
            user_intent += "(" + from_NLU[fc.entity_type] + ")"
        if user_intent in self.rules:
            return self.rules.get(user_intent)
        else:
            return self.stateDefault

if __name__ == "__main__":
    DM.load_food_model()
