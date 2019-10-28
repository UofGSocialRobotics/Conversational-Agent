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

        self.user_model = {fc.liked_features: [], fc.disliked_features: [], fc.liked_food: [], fc.disliked_food: [], fc.liked_recipe: [], fc.disliked_recipe: [], fc.special_diet: [], fc.situation: "Usual Dinner", fc.health_diagnostic_score: None}
        self.load_model(fc.DM_MODEL)
        self.load_user_model(fc.USER_MODELS, clientid)
        self.use_local_recipe_DB = False


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

    def treat_message(self, msg, topic):

        super(DM, self).treat_message(msg, topic)

        # Todo: Second interaction
        # Todo: no then request(sweet/bitter/...)

        if "SA" in topic:
            self.from_SA = msg
        elif "NLU" in topic:
            self.from_NLU = msg
            self.from_NLU = self.parse_from_NLU(self.from_NLU)
        elif "HealthDiagnostic" in topic:
            self.user_model[fc.health_diagnostic_score] = msg[fc.health_diagnostic_score]
        # Wait for both SA and NLU messages before sending something back to the whiteboard
        if self.from_NLU and self.from_SA:
            recommended_food = None
            food_options = None
            food_recipe_list = None
            recipe = None
            next_state = self.nodes.get(self.currState).get_action(self.from_NLU)


            if fc.inform_food in self.currState:
                if fc.yes in self.from_NLU[fc.intent]:
                    self.user_model[fc.liked_recipe].append(self.current_recipe_list.pop(0))
                elif fc.no in self.from_NLU[fc.intent]:
                    self.user_model[fc.disliked_recipe].append(self.current_recipe_list.pop(0))
                elif fc.inform in self.from_NLU[fc.intent] and fc.food in self.from_NLU[fc.entity_type] and "-" in self.from_NLU[fc.polarity]:
                    self.user_model[fc.disliked_recipe].append(self.current_recipe_list.pop(0))


            #Todo need to manage diet, time, and food

            # Todo: Add vegan thingy in the requests
            if fc.inform in self.from_NLU[fc.intent]:
                if fc.health in self.from_NLU[fc.entity_type] and self.from_NLU[fc.entity] is True:
                    self.user_model[fc.liked_features].append(fc.health)
                if fc.hungry in self.from_NLU[fc.entity_type] and self.from_NLU[fc.entity] is True:
                    self.user_model[fc.liked_features].append(fc.filling)
                if fc.time in self.from_NLU[fc.entity_type] and self.from_NLU[fc.entity] is False:
                    self.user_model[fc.liked_features].append(fc.time)
                if fc.vegan in self.from_NLU[fc.entity_type] and self.from_NLU[fc.entity] is True:
                    self.user_model[fc.special_diet].append(fc.vegan)
                    fc.EDAMAM_ADDITIONAL_DIET = "&health=vegan"
                if fc.food in self.from_NLU[fc.entity_type]:
                    if "+" in self.from_NLU[fc.polarity]:
                        # self.user_model[fc.liked_food].append(self.from_NLU[fc.entity])
                        self.user_model[fc.liked_food] += self.from_NLU[fc.entity]
                    else:
                        self.user_model[fc.disliked_food] += self.from_NLU[fc.entity]
                        # self.user_model[fc.disliked_food].append(self.from_NLU[fc.entity])

            if fc.healthy in self.currState:
                if fc.yes in self.from_NLU[fc.intent]:
                    self.user_model[fc.liked_features].append(fc.health)
            elif fc.greeting in self.currState:
                if fc.no in self.from_NLU[fc.intent]:
                    self.user_model[fc.liked_features].append(fc.comfort)
            elif fc.filling in self.currState:
                if fc.yes in self.from_NLU[fc.intent]:
                    self.user_model[fc.liked_features].append(fc.filling)
            elif fc.time in self.currState:
                if fc.no in self.from_NLU[fc.intent]:
                    self.user_model[fc.liked_features].append(fc.time)
            if fc.inform_food in next_state:
                if "request" in self.from_NLU[fc.intent] and "more" not in self.from_NLU[fc.entity_type]:
                    log.debug("trying to get 1st recommendation")
                    food_options, recommended_food, self.current_recipe_list = self.recommend(self.from_NLU[fc.entity_type], use_local_recipe_DB=self.use_local_recipe_DB)
                elif "request" in self.from_NLU[fc.intent] and "more" in self.from_NLU[fc.entity_type]:
                    log.debug("trying to get other recommendation")
                    self.current_recipe_list.pop(0)
                else:
                    log.debug("Not sure when we go in here")
                    food_options, recommended_food, self.current_recipe_list = self.recommend(None, use_local_recipe_DB=self.use_local_recipe_DB)

                if self.current_recipe_list:
                    recipe = self.current_recipe_list[0]
                else:
                    next_state = "bye"

            # if the user comes back
            if next_state == 'greeting' and (self.user_model['liked_food']):
                next_state = "greet_back"

            # saves the user model at the end of the interaction
            if next_state == 'bye' and fc.SAVE_USER_MODEL:
                self.save_user_model()

            prev_state = self.currState
            self.currState = next_state
            new_msg = self.msg_to_json(next_state, self.from_NLU, prev_state, self.user_model, recommended_food, recipe)
            self.from_NLU = None
            self.from_SA = None
            self.publish(new_msg, topic=self.publishes[0])



    def msg_to_json(self, intention, user_intent, previous_intent, user_frame, reco_food, recipe):
        frame = {fc.intent: intention, fc.user_intent: user_intent, fc.previous_intent: previous_intent, fc.user_model: user_frame, fc.reco_food: reco_food, fc.recipe: recipe}
        # json_msg = json.dumps(frame)
        return frame

    def parse_from_NLU(self, NLU_message):
        if "request" in NLU_message[fc.intent]:
            NLU_message[fc.intent] = NLU_message[fc.intent] + "(" + NLU_message[fc.entity_type] + ")"
        return NLU_message

    def load_food_data(self):
        self.food_data = pandas.read_csv(fc.FOOD_MODEL_PATH, encoding='utf-8', sep=',')

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
        print("in remove_recipes_with_disliked_ingredients")
        if not self.user_model[fc.disliked_food]:
            return self.current_recipe_list
        new_recipe_list = list()
        for recipe in self.current_recipe_list:
            disliked_ingredient_in_recipe = False
            ingredients_list = self.get_all_ingredients(recipe)
            for ingredient in ingredients_list:
                if ingredient in self.user_model[fc.disliked_food]:
                    msg = "Removing recipe %s because it has disliked ingredient (%s)" % (recipe['title'], ingredient)
                    log.debug(msg)
                    print(colored(msg, "green"))
                    disliked_ingredient_in_recipe = True
                    break
            if not disliked_ingredient_in_recipe:
                new_recipe_list.append(recipe)
        self.current_recipe_list = new_recipe_list

    def recommend(self, additional_request, use_local_recipe_DB=False):
        food_options = self.get_food_options(additional_request)
        recommended_food = self.pick_food(food_options)
        # TODO: need to change that and update it each time?
        if not self.current_recipe_list:
            if use_local_recipe_DB:
                with open(fc.LOCAL_FOOD_DB, 'rb') as f:
                    content = json.load(f)
                    self.current_recipe_list = list()
                    for i in range(5):
                        self.current_recipe_list.append(content[i])
                    # self.current_recipe_list = json.load(f)
            else:
                self.current_recipe_list = self.get_recipe_list_with_spoonacular(recommended_food)
        self.remove_recipes_likely_to_be_disliked()
        self.remove_recipes_with_disliked_ingredients()

        #Sending recipes to NLG so that NLG can start fetching recipe cards
        thread = threading.Thread(name=self.name+"/RecipeCards", target=self.publish, args=(self.current_recipe_list, self.publishes[1],))
        thread.setDaemon(True)
        thread.start()

        # log.debug((food_options,recommended_food,recipe_list))
        if not self.current_recipe_list:
            log.critical(colored("No recipe to recommend","cyan"))
        return food_options, recommended_food, self.current_recipe_list

    def get_food_options(self, request):
        max_meal_value = max_dessert_value = max_drink_value = max_meat_value = max_side_value = -100
        best_meal = best_dessert = best_drink = best_meat = best_side = None
        situated_food_matrix = self.get_food_per_situation(self.user_model[fc.situation])

        if fc.health in self.user_model[fc.liked_features]:
            healthy_weight = 1
        else:
            healthy_weight = 0
        if fc.comfort in self.user_model[fc.liked_features]:
            comfort_weight = 1
        else:
            comfort_weight = 0
        if fc.filling in self.user_model[fc.liked_features]:
            filling_weight = 1
        else:
            filling_weight = 0



        for index, row in situated_food_matrix.iterrows():
            if request:
                current_food_value = healthy_weight * row[fc.healthiness] + row[request] + (comfort_weight * row[fc.emotional_satisfaction]) + (filling_weight * row[fc.food_fillingness])
            else:
                current_food_value = healthy_weight * row[fc.healthiness] + (comfort_weight * row[fc.emotional_satisfaction]) + (filling_weight * row[fc.food_fillingness])
            if fc.meal in row[fc.food_type] and current_food_value > max_meal_value:
                if row[fc.food_name] not in self.user_model[fc.disliked_food]:
                    max_meal_value = current_food_value
                    best_meal = row[fc.food_name]
            elif fc.meat in row[fc.food_type] and current_food_value > max_meat_value:
                if row[fc.food_name] not in self.user_model[fc.disliked_food]:
                    max_meat_value = current_food_value
                    best_meat = row[fc.food_name]
            elif fc.side in row[fc.food_type] and current_food_value > max_side_value:
                if row[fc.food_name] not in self.user_model[fc.disliked_food]:
                    max_side_value = current_food_value
                    best_side = row[fc.food_name]
        # best_food = {fc.meal: best_meal, fc.dessert: best_dessert, fc.drink: best_drink, fc.meat: best_meat, fc.side: best_side}
        best_food = {fc.meal: best_meal, fc.meat: best_meat, fc.side: best_side}
        return best_food

    def pick_food(self, food):
        recommended_food = {fc.main: "", fc.other_main: ""}
        if randint(0, 1) == 1:
            recommended_food[fc.main] = food[fc.meal]
            recommended_food[fc.other_main] = food[fc.meat] + " with " + food[fc.side]
        else:
            recommended_food[fc.main] = food[fc.meat] + " with " + food[fc.side]
            recommended_food[fc.other_main] = food[fc.meal]
        # if randint(0, 1) == 1:
        #     recommended_food[fc.secondary] = food[fc.dessert]
        # else:
        #     recommended_food[fc.secondary] = food[fc.drink]
        return recommended_food

    # def get_recipe_list_with_edamam(self, recommended_food):
    #     if "with" in recommended_food[fc.main]:
    #         request_food = recommended_food[fc.main].replace(" with ", "%20and%20")
    #         request_food = request_food.replace("side ", "")
    #     else:
    #         request_food = recommended_food[fc.main].replace(" dish", "")
    #     edamamURL = fc.EDAMAM_SEARCH_RECIPE_ADDRESS + request_food + fc.EDAMAM_APP_ID + fc.EDAMAM_KEY + fc.EDAMAM_PROPERTY + fc.EDAMAM_ADDITIONAL_DIET
    #     data = urllib.request.urlopen(edamamURL)
    #     result = data.read()
    #     json_recipe_list = json.loads(result)
    #     recipe_list = json_recipe_list['hits']
    #     return recipe_list

    def format_recommended_food(self, recommended_food):
        to_replace_pairs = [["with", ""], ["side", ""], ["dish", ""]]
        for to_replace, to_replace_with in to_replace_pairs:
            if to_replace in recommended_food:
                recommended_food = recommended_food.replace(to_replace, to_replace_with)
        recommended_food = ' '.join(recommended_food.split(' '))
        recommended_food = recommended_food.replace(" ", "%20")
        recommended_food = '%20'.join(recommended_food.split('%20'))
        return recommended_food


    def get_recipe_from_spoonacular_with_specific_food_request(self, food_to_request, liked_food):
        request_food = self.format_recommended_food(food_to_request)
        log.debug(request_food)
        if fc.time in self.user_model[fc.liked_features]:
            max_time = 21
        else:
            max_time = 5000
        time_str = fc.SPOONACULAR_API_MAX_TIME + str(max_time)
        diet_str = fc.SPOONACULAR_API_DIET + "vegan" if "vegan" in self.user_model[fc.special_diet] else ""
        liked_food_str = "%20" + self.user_model['liked_food'][0] if liked_food and self.user_model['liked_food'][0] not in request_food else ""
        exclude_ingredients_str = fc.SPOONACULAR_API_EXCLUDE_INGREDIENTS + ",".join(self.user_model[fc.disliked_food]) if self.user_model[fc.disliked_food] else ""
        query = request_food + liked_food_str + time_str + diet_str + exclude_ingredients_str + fc.SPOONACULAR_API_SEARCH_ADDITIONAL_INFO + fc.SPOONACULAR_API_SEARCH_ADDITIONAL_INFO + fc.SPOONACULAR_API_SEARCH_RESULTS_NUMBER
        log.debug(query)
        recipe_list = self.query_spoonacular(self.generate_soonacular_url(query))
        return recipe_list

    def get_recipe_list_with_spoonacular(self, recommended_food):
        print(colored("in get_recipe_list_with_spoonacular", "blue"))
        recipe_list = []
        recipe_list += self.get_recipe_from_spoonacular_with_specific_food_request(recommended_food["main"], self.user_model['liked_food'])
        # log.debug(recipe_list)


        if not recipe_list or len(recipe_list)<5 and "mashed" in recommended_food["main"]:
            recipe_list += self.get_recipe_from_spoonacular_with_specific_food_request(recommended_food["main"].replace("mashed",""), self.user_model['liked_food'])
        if not recipe_list or len(recipe_list)<5:
            recipe_list += self.get_recipe_from_spoonacular_with_specific_food_request(recommended_food["other_main"], self.user_model['liked_food'])
            # log.debug(recipe_list)
        if not recipe_list or len(recipe_list)<5:
            recipe_list += self.get_recipe_from_spoonacular_with_specific_food_request(recommended_food["main"], liked_food=None)
            # log.debug(recipe_list)
            # log.debug(recipe_list)
        if not recipe_list or len(recipe_list)<5:
            recipe_list += self.get_recipe_from_spoonacular_with_specific_food_request(recommended_food["other_main"], liked_food=None)
            # log.debug(recipe_list)

        log.debug("Got %d recipes with Spoonacular" % len(recipe_list))
        return recipe_list

    def generate_soonacular_url(self, query):
        tmp = fc.SPOONACULAR_API_SEARCH + fc.SPOONACULAR_KEY + "&query=" + query
        log.debug(tmp)
        return tmp

    def query_spoonacular(self, spoonURL):
        data = urllib.request.urlopen(spoonURL)
        result = data.read()
        json_recipe_list = json.loads(result)
        recipe_list = json_recipe_list['results']
        return  recipe_list

    def get_headers(self, matrix):
        headers = matrix.keys()
        return headers

    def get_food_per_situation(self, situation):
        situated_food_matrix = self.food_data.query("situation_name == '" + situation + "'")
        return situated_food_matrix

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
