import whiteboard_client as wbc
import helper_functions as helper
import json
import food.food_config as fc
from random import randint
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
        self.from_SA = None
        self.food_data = None

        self.load_food_data()

        self.current_recipe_list = None
        self.current_food_options = {fc.meal: "", fc.dessert: "", fc.drink: "", fc.meat: "", fc.side: ""}
        self.nodes = {}

        state_values = {fc.healthiness: 0, fc.food_fillingness: 0}
        self.user_model = {fc.user_name: None, fc.usual_dinner: [], fc.liked_features: [], fc.disliked_features: [], fc.liked_food: [], fc.disliked_food: [], fc.liked_recipe: [], fc.disliked_recipe: [], fc.special_diet: [], fc.intolerances: None, fc.time_to_cook: False, fc.situation: "Usual Dinner", fc.food_scores_trait: None, fc.food_scores_state: state_values}
        self.load_model(fc.DM_MODEL)
        ##self.load_user_model(fc.USER_MODELS, clientid)
        self.use_local_recipe_DB = False
        self.situated_food_matrix = self.get_food_per_situation(self.user_model[fc.situation])
        self.situated_food_matrix = helper.norm_pandas_matrix(self.situated_food_matrix)

        self.n_recommendations = 0
        self.n_accepted_recommendations = 0
        self.list_sorted_ingredients = list()
        self.current_recipe_list = list()

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
        print(self.nodes)

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

        # print(self.currState)

        super(DM, self).treat_message(msg, topic)

        # Todo: Second interaction
        # Todo: no then request(sweet/bitter/...)

        if "SA" in topic:
            self.from_SA = msg
        elif "NLU" in topic:
            self.from_NLU = msg
            self.from_NLU = self.parse_from_NLU(self.from_NLU)
        elif "HealthDiagnostic" in topic:
            self.user_model[fc.food_scores_trait] = msg[fc.food_scores_trait]
        # Wait for both SA and NLU messages before sending something back to the whiteboard
        if self.from_NLU and self.from_SA:

            recipe = None
            next_state = self.nodes.get(self.currState).get_action(self.from_NLU)

            if fc.inform_food in self.currState:
                liked_bool = self.check_if_previous_recommendation_is_liked()
                disliked_bool = self.check_if_previous_recommendation_is_disliked()
                if not liked_bool and not disliked_bool:
                    self.current_recipe_list.pop(0)

            # if self.currState == "greeting":
            #     if fc.yes in self.from_NLU[fc.intent]:
            #         self.user_model[fc.food_scores_state][fc.comfort] = -1
            #     elif fc.no in self.from_NLU[fc.intent]:
            #         self.user_model[fc.food_scores_state][fc.comfort] = 1

            if fc.inform in self.from_NLU[fc.intent]:
                print(self.from_NLU)
                if fc.user_name in self.from_NLU[fc.entity_type]:
                    print("DM here user_name")
                    self.user_model[fc.user_name] = self.from_NLU[fc.entity]
                    print(self.user_model[fc.user_name])
                if fc.health in self.from_NLU[fc.entity_type]:
                    if self.from_NLU[fc.entity] is True:
                        self.user_model[fc.liked_features].append(fc.health)
                        self.user_model[fc.food_scores_state][fc.healthiness] = 1
                    elif self.from_NLU[fc.entity] is False:
                        self.user_model[fc.food_scores_state][fc.healthiness] = -1
                if fc.hungry in self.from_NLU[fc.entity_type]:
                    if self.from_NLU[fc.entity] is True:
                        self.user_model[fc.liked_features].append(fc.filling)
                        self.user_model[fc.food_scores_state][fc.food_fillingness] = 1
                    elif self.from_NLU[fc.entity] is False:
                        self.user_model[fc.food_scores_state][fc.food_fillingness] = -1
                if fc.time in self.from_NLU[fc.entity_type] and self.from_NLU[fc.entity] is False:
                    self.user_model[fc.liked_features].append(fc.time)
                if fc.duration in self.from_NLU[fc.entity_type]:
                    self.user_model[fc.time_to_cook] = self.from_NLU[fc.entity]
                if fc.vegan in self.from_NLU[fc.entity_type] and self.from_NLU[fc.entity] is True:
                    print(colored("user is vegan", "green"))
                    self.user_model[fc.special_diet].append(fc.vegan)
                    fc.EDAMAM_ADDITIONAL_DIET = "&health=vegan"
                if fc.intolerances in self.from_NLU[fc.entity_type]:
                    self.user_model[fc.disliked_food].append(self.from_NLU[fc.entity])
                    self.user_model[fc.intolerances] = self.from_NLU[fc.entity]
                if fc.food in self.from_NLU[fc.entity_type]:
                    ingredients_list = self.from_NLU[fc.entity]
                    if self.currState == "request(usual_dinner)" and "+" in self.from_NLU[fc.polarity]:
                        self.user_model[fc.usual_dinner] += ingredients_list
                    if "+" in self.from_NLU[fc.polarity] and self.currState == "request(food)":
                        self.user_model[fc.liked_food] += ingredients_list
                    else:
                        self.user_model[fc.disliked_food] += ingredients_list
                        self.remove_recipes_with_disliked_ingredients()
                        # print("there", self.from_NLU[fc.polarity])


            if fc.healthy in self.currState:
                if fc.yes in self.from_NLU[fc.intent]:
                    self.user_model[fc.liked_features].append(fc.health)
            # elif fc.greeting in self.currState:
            #     if fc.no in self.from_NLU[fc.intent]:
            #         self.user_model[fc.liked_features].append(fc.comfort)
            elif fc.filling in self.currState:
                if fc.yes in self.from_NLU[fc.intent]:
                    self.user_model[fc.liked_features].append(fc.filling)
            elif fc.time in self.currState:
                if fc.no in self.from_NLU[fc.intent]:
                    self.user_model[fc.liked_features].append(fc.time)
            if fc.inform_food in next_state:
                if self.n_recommendations == fc.MAX_RECOMMENDATIONS:
                    next_state = "bye"
                else:
                    # if "request" in self.from_NLU[fc.intent] and "more" not in self.from_NLU[fc.entity_type]:
                    #     log.debug("trying to get 1st recommendation")
                    #     # food_options, recommended_food, self.current_recipe_list = self.recommend(use_local_recipe_DB=self.use_local_recipe_DB)
                    #     self.recommend(use_local_recipe_DB=self.use_local_recipe_DB)
                    self.recommend(use_local_recipe_DB=self.use_local_recipe_DB)

                    if self.current_recipe_list:
                        recipe = self.current_recipe_list[0]
                        self.n_recommendations += 1
                    else:
                        next_state = "bye"


            if next_state == "request(another)" and self.n_recommendations == fc.MAX_RECOMMENDATIONS:
                next_state = "bye"

            # if the user comes back
            if next_state == 'greeting' and (self.user_model['liked_food']):
                next_state = "greet_back"

            # saves the user model at the end of the interaction
            if next_state == 'bye' and fc.SAVE_USER_MODEL:
                self.save_user_model()
                self.save_reco_data()

            prev_state = self.currState
            self.currState = next_state
            new_msg = self.msg_to_json(next_state, self.from_NLU, prev_state, self.user_model, recipe)
            self.from_NLU = None
            self.from_SA = None
            self.publish({"current_state": self.currState}, topic=self.publishes[4])
            self.publish(new_msg, topic=self.publishes[0])

    def save_reco_data(self):
        # print(colored("Did %d queries to Spoonacular\nWorked with ingredients: %s" % (len(self.spoonacular_queries), ", ".join(self.used_seed_ingredients)), "blue"))
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
        print(colored(data_reco, "blue"))
        data = {"data_recommendation": data_reco}
        self.publish(data, topic=self.publishes[2])
        self.publish(data, topic=self.publishes[3])


    def msg_to_json(self, intention, user_intent, previous_intent, user_frame, recipe):
        frame = {fc.intent: intention, fc.user_intent: user_intent, fc.previous_intent: previous_intent, fc.user_model: user_frame, fc.recipe: recipe}
        # json_msg = json.dumps(frame)
        return frame

    def parse_from_NLU(self, NLU_message):
        if "request" in NLU_message[fc.intent]:
            NLU_message[fc.intent] = NLU_message[fc.intent] + "(" + NLU_message[fc.entity_type] + ")"
        return NLU_message

    def load_food_data(self):
        self.food_data = pandas.read_csv(fc.FOOD_MODEL_PATH, encoding='utf-8', sep=',')
        # print(self.food_data)



    def remove_recipes_likely_to_be_disliked(self):
        new_recipe_list = list()
        log.debug("Before removing disliked foods: "+ len(self.current_recipe_list).__str__())
        for recipe in self.current_recipe_list:
            bool_recipe_disliked = False
            for disliked_recipe in self.user_model[fc.disliked_recipe]:
                shortest_recipe_title = recipe[fc.title] if len(recipe[fc.title]) < len(disliked_recipe[fc.title]) else disliked_recipe[fc.title]
                longest_recipe_title = recipe[fc.title] if len(recipe[fc.title]) >= len(disliked_recipe[fc.title]) else disliked_recipe[fc.title]
                if shortest_recipe_title in longest_recipe_title:
                    bool_recipe_disliked = True
                    break
                similarity_score = fuzz.token_sort_ratio(recipe[fc.title], disliked_recipe[fc.title])
                if similarity_score > 85:
                    bool_recipe_disliked = True
                    log.debug("Removing "+recipe[fc.title])
                    break
            if not bool_recipe_disliked:
                new_recipe_list.append(recipe)
        self.current_recipe_list = new_recipe_list
        log.debug("After removing disliked foods: " + len(self.current_recipe_list).__str__())

    def get_all_ingredients(self, recipe):
        ingredients = recipe['usedIngredients'] + recipe["missedIngredients"]
        return [ingredient['name'] for ingredient in ingredients]

    def remove_recipes_with_disliked_ingredients(self):
        if not self.user_model[fc.disliked_food]:
            return self.current_recipe_list
        new_recipe_list = list()
        for recipe in self.current_recipe_list:
            # Check disliked ingredients are not in recipe title
            disliked_ingredient_in_recipe_title = False
            for disliked_i in self.user_model[fc.disliked_food]:
                if disliked_i.lower() in recipe["title"].lower():
                    disliked_ingredient_in_recipe_title = True
                    msg = "Removing recipe %s because it has disliked ingredient (%s)" % (recipe['title'], disliked_i)
                    print(colored(msg, "green"))
                    break
                # if disliked ingredient is a category (e.g. fish), check each word of recipe title
                elif extensive_food_DBs.is_category(disliked_i):
                    for word in recipe["title"].lower().split():
                        if extensive_food_DBs.is_food_in_category(word, disliked_i):
                            disliked_ingredient_in_recipe_title = True
                            msg = "Removing recipe %s because it has a disliked ingredient (%s)" % (recipe['title'], disliked_i)
                            print(colored(msg, "green"))
                            break
                        if disliked_ingredient_in_recipe_title:
                            break
            # Check disliked ingredients are not in ingredients list
            disliked_ingredient_in_recipe = False
            if not disliked_ingredient_in_recipe_title:
                ingredients_list = self.get_all_ingredients(recipe)
                for ingredient in ingredients_list:
                    for disliked_i in self.user_model[fc.disliked_food]:
                        if disliked_i.lower() in ingredient.lower() or ingredient.lower() in disliked_i.lower():
                            msg = "Removing recipe %s because it has disliked ingredient (%s)" % (recipe['title'], ingredient)
                            print(colored(msg, "green"))
                            disliked_ingredient_in_recipe = True
                            break
                        # if disliked ingredient is a category, check that ingredients are not in disliked category
                        elif extensive_food_DBs.is_category(disliked_i):
                            for word in ingredient.lower().split():
                                # print(word, disliked_i)
                                if extensive_food_DBs.is_food_in_category(word, disliked_i):
                                    msg = "Removing recipe %s because it has an ingredient %s in disliked category %s" % (recipe['title'], ingredient, disliked_i)
                                    print(colored(msg, "green"))
                                    disliked_ingredient_in_recipe = True
                                    break
                    if disliked_ingredient_in_recipe:
                        break
            if not disliked_ingredient_in_recipe and not disliked_ingredient_in_recipe_title:
                new_recipe_list.append(recipe)
        self.current_recipe_list = new_recipe_list
        # print("len(self.current_recipe_list)", len(self.current_recipe_list))

    def recommend(self, use_local_recipe_DB=False):

        if not self.list_sorted_ingredients:
            self.sort_ingredients_to_recommend()

        # TODO: need to change that and update it each time?
        if not self.current_recipe_list:
            if use_local_recipe_DB:
                with open(fc.LOCAL_FOOD_DB, 'rb') as f:
                    content = json.load(f)
                    self.current_recipe_list = list()
                    for i in range(fc.N_RESULTS):
                        self.current_recipe_list.append(content[i])
                    # self.current_recipe_list = json.load(f)
            else:
                got_recipe = False
                n_trials = 0
                while got_recipe is False and n_trials < 3:
                    got_recipe = self.get_recipe_list_with_spoonacular_in_no_more_than_two_seconds()
        self.remove_recipes_likely_to_be_disliked()
        self.remove_recipes_with_disliked_ingredients()

        #Sending recipes to NLG so that NLG can start fetching recipe cards
        thread = threading.Thread(name=self.name+"/RecipeCards", target=self.publish, args=(self.current_recipe_list, self.publishes[1],))
        thread.setDaemon(True)
        thread.start()

        # log.debug((food_options,recommended_food,recipe_list))
        if not self.current_recipe_list:
            log.critical(colored("No recipe to recommend","cyan"))


    def get_desired_food_values(self):
        trait_values = self.user_model[fc.food_scores_trait] 
        state_values = self.user_model[fc.food_scores_state]
        if not trait_values:
            waning_msg = "No trait values for food diagnostic. Generating random values!"
            print(colored(waning_msg, "green"))
            log.warn(waning_msg)
            trait_values = {fc.healthiness: np.random.uniform(-1,1), fc.food_fillingness: np.random.uniform(-1,1)}
        print(colored((trait_values, state_values), "blue"))

        return min(1,((trait_values[fc.healthiness] + state_values[fc.healthiness]) / float(2)) + 0.5), (trait_values[fc.food_fillingness] + state_values[fc.food_fillingness]) / float(2)
        
        # return np.random.uniform(-2, 2), np.random.uniform(-2, 2), np.random.uniform(-2, 2)
        # return 0.413, -.603, -2.016

    def sort_ingredients_to_recommend(self):
        if fc.vegan in self.user_model[fc.special_diet]:
            expected_food_type = ["meal", "side"]
        else:
            expected_food_type = ["meal", "meat", "side"]
        d_h, d_f = self.get_desired_food_values()
        self.food_values = {fc.healthiness: d_h, fc.food_fillingness: d_f}
        all_foods = list()
        for index, row in self.situated_food_matrix.iterrows():
            if row[fc.food_type] in expected_food_type:
                h, f, c = row[fc.healthiness], row[fc.food_fillingness], row[fc.emotional_satisfaction]
                distance = abs(h - d_h) + abs(f - d_f)
                all_foods.append((self.preprocess_ingredient_name(row[fc.food_name]), distance, (h, f)))
        # all_foods.append(("salmon", 0, (1, 1)))
        self.list_sorted_ingredients = sorted(all_foods, key=operator.itemgetter(1))

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

    def get_recipe_from_spoonacular_with_specific_food_request(self):
        if self.user_model[fc.liked_food]:
            ingredients_str = self.user_model[fc.liked_food].pop(0)
        else:
            ingredients_str = self.list_sorted_ingredients.pop(0)[0]
        self.used_seed_ingredients.append(ingredients_str)
        if self.user_model[fc.time_to_cook]:
            max_time = self.user_model[fc.time_to_cook] + 1
        else:
            if fc.time in self.user_model[fc.liked_features]:
                max_time = 21
            else:
                max_time = 5000
        time_str = fc.SPOONACULAR_API_MAX_TIME + str(max_time)
        diet_str = fc.SPOONACULAR_API_DIET + "vegan" if "vegan" in self.user_model[fc.special_diet] else ""
        intolerances_str = fc.SPOONACULAR_API_INTOLERANCES + self.user_model[fc.intolerances] if self.user_model[fc.intolerances] else ""
        # liked_food_str = "%20" + self.user_model['liked_food'][0] if liked_food and self.user_model['liked_food'][0] not in request_food else ""
        exclude_ingredients_str = fc.SPOONACULAR_API_EXCLUDE_INGREDIENTS + ",".join(self.user_model[fc.disliked_food]) if self.user_model[fc.disliked_food] else ""
        query = ingredients_str + time_str + diet_str + intolerances_str + exclude_ingredients_str + fc.SPOONACULAR_API_SEARCH_ADDITIONAL_INFO + fc.SPOONACULAR_API_SEARCH_ADDITIONAL_INFO + fc.SPOONACULAR_API_SEARCH_RESULTS_NUMBER
        log.debug(query)
        recipe_list = self.query_spoonacular(self.generate_soonacular_url(query))

        if not recipe_list or len(recipe_list) < fc.N_RESULTS and "mashed" in ingredients_str:
            ingredients_str = ingredients_str.replace("mashed", "")
            ingredients_str = ingredients_str.strip()
            query = ingredients_str + time_str + diet_str + exclude_ingredients_str + fc.SPOONACULAR_API_SEARCH_ADDITIONAL_INFO + fc.SPOONACULAR_API_SEARCH_ADDITIONAL_INFO + fc.SPOONACULAR_API_SEARCH_RESULTS_NUMBER
            log.debug(query)
            recipe_list = self.query_spoonacular(self.generate_soonacular_url(query))

        return recipe_list, ingredients_str

    def get_recipe_list_with_spoonacular_in_no_more_than_two_seconds(self):
        p = multiprocessing.Process(target=self.get_recipe_list_with_spoonacular(), name=self.name+"/get_recipe_list_with_spoonacular", args=(self,))
        p.start()
        p.join(2)
        if p.is_alive():
            error_msg = "Getting recipe with Spoonacular is taking too long"
            print(colored(error_msg,"green"))
            log.warn(error_msg)
            p.terminate()
            p.join()
            return False
        else:
            return True

    def get_recipe_list_with_spoonacular(self):
        print(colored("in get_recipe_list_with_spoonacular", "blue"))
        self.current_recipe_list = list()
        potential_new_recipes, seed_ingredient = self.get_recipe_from_spoonacular_with_specific_food_request()
        self.add_new_recipes(potential_new_recipes, seed_ingredient)
        while len(self.current_recipe_list) < fc.N_RESULTS and len(self.list_sorted_ingredients) > 0:
            potential_new_recipes, seed_ingredient = self.get_recipe_from_spoonacular_with_specific_food_request()
            self.add_new_recipes(potential_new_recipes, seed_ingredient)
        log.debug("Got %d recipes with Spoonacular" % len(self.current_recipe_list))

    def add_new_recipes(self, potential_new_recipes_list, seed_ingredient):
        tmp_copy = copy.deepcopy(self.current_recipe_list)
        for recipe in potential_new_recipes_list:
            if recipe['title'] not in [r['title'] for r in tmp_copy]:
                recipe ['seed_ingredient'] = seed_ingredient
                self.current_recipe_list.append(recipe)

    def generate_soonacular_url(self, query):
        tmp = fc.SPOONACULAR_API_SEARCH + fc.SPOONACULAR_KEY + "&query=" + query
        log.debug(tmp)
        self.spoonacular_queries.append(query)
        # print(tmp)
        return tmp

    def query_spoonacular(self, spoonURL):
        data = urllib.request.urlopen(spoonURL)
        result = data.read()
        json_recipe_list = json.loads(result)
        recipe_list = json_recipe_list['results']
        return recipe_list

    def get_headers(self, matrix):
        headers = matrix.keys()
        return headers

    def get_food_per_situation(self, situation):
        situated_food_matrix = self.food_data.query("situation_name == '" + situation + "'")
        return situated_food_matrix

    def get_ingredient_info(self, ingredient_name):
        ingredient_info = self.food_data.query("food_name == '" + ingredient_name + "'")
        return ingredient_info

    def get_ingredient_categories(self, ingredient_name):
        ingredient_info = self.get_ingredient_info(ingredient_name)
        types_list = list()
        for index, row in ingredient_info.iterrows():
            t = row[fc.food_type]
            # print(t)
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

    def save_recipes_as_pdf(self):
        import pdfkit
        pdfkit.from_url('https://www.google.co.in/', './shaurya.pdf')


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
