import whiteboard_client as wbc
import helper_functions as helper
import json
import food.food_config as food_config
from random import randint
from pathlib import Path
import pandas
import urllib.request


class DM(wbc.WhiteBoardClient):
    def __init__(self, subscribes, publishes, clientid):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, "DM" + clientid, subscribes, publishes)

        self.client_id = clientid

        self.currState = "start"
        # Do we store the users preferences in a user model?
        self.store_pref = True

        self.from_NLU = None
        self.from_SA = None
        self.food_data = None

        self.load_food_data()

        self.current_recipe_list = None
        self.current_food_options = {'meal': "", 'dessert': "", 'drink': "", 'meat': "", 'side': ""}
        self.nodes = {}

        self.user_model = {"liked_features": [], "disliked_features": [], "liked_food": [], 'disliked_food': [], "liked_recipe": [], "disliked_recipe": [], 'special_diet': [], 'situation': "Usual Dinner"}
        self.load_model(food_config.DM_MODEL)
        self.load_user_model(food_config.USER_MODELS, clientid)

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
        file = food_config.USER_MODELS + self.client_id + ".prefs"
        with open(file, 'w') as outfile:
            json.dump(self.user_model, outfile)

    def load_user_model(self, path, client_id):
        file = Path(path + client_id + ".prefs")
        if file.is_file():
            with open(file) as json_file:
                self.user_model = json.load(json_file)

    def treat_message(self, msg, topic):

        # Todo: Second interaction
        # Todo: no then request(sweet/bitter/...)

        if "SA" in topic:
            self.from_SA = msg
        elif "NLU" in topic:
            self.from_NLU = json.loads(msg)
            self.from_NLU = self.parse_from_NLU(self.from_NLU)
        # Wait for both SA and NLU messages before sending something back to the whiteboard
        if self.from_NLU and self.from_SA:
            recommended_food = None
            food_options = None
            food_recipe_list = None
            recipe = None
            next_state = self.nodes.get(self.currState).get_action(self.from_NLU['intent'])

            #Todo need to manage diet, time, and food

            # Todo: Add vegan thingy in the requests
            if "inform" in self.from_NLU['intent']:
                if "health" in self.from_NLU['entity_type'] and self.from_NLU['entity'] is True:
                    self.user_model['liked_features'].append('health')
                if "hungry" in self.from_NLU['entity_type'] and self.from_NLU['entity'] is True:
                    self.user_model['liked_features'].append('filling')
                if "time" in self.from_NLU['entity_type'] and self.from_NLU['entity'] is False:
                    self.user_model['liked_features'].append('time')
                if "vegan" in self.from_NLU['entity_type'] and self.from_NLU['entity'] is True:
                    self.user_model['special_diet'].append('vegan')
                    food_config.EDAMAM_ADDITIONAL_DIET = "&health=vegan"
                if "food" in self.from_NLU['entity_type']:
                    if "+" in self.from_NLU['polarity']:
                        self.user_model['liked_food'].append(self.from_NLU['entity'])
                    else:
                        self.user_model['disliked_food'].append(self.from_NLU['entity'])

            if "healthy" in self.currState:
                if "yes" in self.from_NLU['intent']:
                    self.user_model['liked_features'].append('health')
            elif "greeting" in self.currState:
                if "no" in self.from_NLU['intent']:
                    self.user_model['liked_features'].append('comfort')
            elif "filling" in self.currState:
                if "yes" in self.from_NLU['intent']:
                    self.user_model['liked_features'].append('filling')
            elif "time" in self.currState:
                if "no" in self.from_NLU['intent']:
                    self.user_model['liked_features'].append('time')
            if "inform(food)" in next_state:
                if "request" in self.from_NLU['intent'] and "more" not in self.from_NLU['entity_type']:
                    food_options, recommended_food, self.current_recipe_list = self.recommend(self.from_NLU['entity_type'])
                elif "request" in self.from_NLU['intent'] and "more" in self.from_NLU['entity_type']:
                    self.current_recipe_list.pop(0)
                else:
                    food_options, recommended_food, self.current_recipe_list = self.recommend(None)
                recipe = self.current_recipe_list[0]
            if "food" in self.currState:
                if "yes" in self.from_NLU['intent']:
                    self.user_model['liked_recipe'].append(self.current_recipe_list.pop(0))

            # if the user comes back
            if next_state == 'greeting' and (self.user_model['liked_food']):
                next_state = "greet_back"

            # saves the user model at the end of the interaction
            if next_state == 'bye' and food_config.SAVE_USER_MODEL:
                self.save_user_model()

            prev_state = self.currState
            self.currState = next_state
            new_msg = self.msg_to_json(next_state, self.from_NLU, prev_state, self.user_model, recommended_food, recipe)
            self.from_NLU = None
            self.from_SA = None
            self.publish(new_msg)

    def msg_to_json(self, intention, user_intent, previous_intent, user_frame, reco_food, recipe):
        frame = {'intent': intention, 'user_intent': user_intent, 'previous_intent': previous_intent, 'user_model': user_frame, 'reco_food': reco_food, 'recipe': recipe}
        json_msg = json.dumps(frame)
        return json_msg

    def parse_from_NLU(self, NLU_message):
        if "request" in NLU_message['intent']:
            NLU_message['intent'] = NLU_message['intent'] + "(" + NLU_message['entity_type'] + ")"
        return NLU_message

    def load_food_data(self):
        self.food_data = pandas.read_csv(food_config.FOOD_MODEL_PATH, encoding='utf-8', sep=',')

    def recommend(self, additional_request):
        food_options = self.get_food_options(additional_request)
        recommended_food = self.pick_food(food_options)
        recipe_list = self.get_recipe_list_with_spoonacular(recommended_food)
        return food_options, recommended_food, recipe_list

    def get_food_options(self, request):
        max_meal_value = max_dessert_value = max_drink_value = max_meat_value = max_side_value = -100
        best_meal = best_dessert = best_drink = best_meat = best_side = None
        situated_food_matrix = self.get_food_per_situation(self.user_model['situation'])

        if "health" in self.user_model['liked_features']:
            healthy_weight = 1
        else:
            healthy_weight = 0
        if "comfort" in self.user_model['liked_features']:
            comfort_weight = 1
        else:
            comfort_weight = 0
        if "filling" in self.user_model['liked_features']:
            filling_weight = 1
        else:
            filling_weight = 0

        for index, row in situated_food_matrix.iterrows():
            if request:
                current_food_value = healthy_weight * row['healthiness'] + row[request] + (comfort_weight * row['emotional_satisfaction']) + (filling_weight * row['food_fillingness'])
            else:
                current_food_value = healthy_weight * row['healthiness'] + (comfort_weight * row['emotional_satisfaction']) + (filling_weight * row['food_fillingness'])
            if 'meal' in row['food_type'] and current_food_value > max_meal_value:
                if row['food_name'] not in self.user_model['disliked_food']:
                    max_meal_value = current_food_value
                    best_meal = row['food_name']
            elif 'dessert' in row['food_type'] and current_food_value > max_dessert_value:
                if row['food_name'] not in self.user_model['disliked_food']:
                    max_dessert_value = current_food_value
                    best_dessert = row['food_name']
            elif 'drink' in row['food_type'] and current_food_value > max_drink_value:
                if row['food_name'] not in self.user_model['disliked_food']:
                    max_drink_value = current_food_value
                    best_drink = row['food_name']
            elif 'meat' in row['food_type'] and current_food_value > max_meat_value:
                if row['food_name'] not in self.user_model['disliked_food']:
                    max_meat_value = current_food_value
                    best_meat = row['food_name']
            elif 'side' in row['food_type'] and current_food_value > max_side_value:
                if row['food_name'] not in self.user_model['disliked_food']:
                    max_side_value = current_food_value
                    best_side = row['food_name']
        best_food = {'meal': best_meal, 'dessert': best_dessert, 'drink': best_drink, 'meat': best_meat, 'side': best_side}
        return best_food

    def pick_food(self, food):
        recommended_food = {'main': "", 'secondary': ""}
        if randint(0, 1) == 1:
            recommended_food['main'] = food['meal']
        else:
            recommended_food['main'] = food['meat'] + " with " + food['side']
        if randint(0, 1) == 1:
            recommended_food['secondary'] = food['dessert']
        else:
            recommended_food['secondary'] = food['drink']
        return recommended_food

    def get_recipe_list_with_edamam(self, recommended_food):
        if "with" in recommended_food['main']:
            request_food = recommended_food['main'].replace(" with ", "%20and%20")
            request_food = request_food.replace("side ", "")
        else:
            request_food = recommended_food['main'].replace(" dish", "")
        edamamURL = food_config.EDAMAM_SEARCH_RECIPE_ADDRESS + request_food + food_config.EDAMAM_APP_ID + food_config.EDAMAM_KEY + food_config.EDAMAM_PROPERTY + food_config.EDAMAM_ADDITIONAL_DIET
        data = urllib.request.urlopen(edamamURL)
        result = data.read()
        json_recipe_list = json.loads(result)
        recipe_list = json_recipe_list['hits']
        return recipe_list

    def get_recipe_list_with_spoonacular(self, recommended_food):
        #Todo Do something if no recipe
        if "with" in recommended_food['main']:
            request_food = recommended_food['main'].replace(" with ", "%20and%20")
            request_food = request_food.replace("side ", "")
        else:
            request_food = recommended_food['main'].replace(" dish", "")
        request_food = request_food.replace(" ", "%20")
        if "time" in self.user_model['liked_features']:
            max_time = 21
        else:
            max_time = 5000
        if not self.user_model['liked_food']:
            spoonURL = food_config.SPOONACULAR_API_SEARCH + food_config.SPOONACULAR_KEY + "&query=" + request_food + food_config.SPOONACULAR_API_MAX_TIME + str(max_time) + food_config.SPOONACULAR_API_SEARCH_ADDITIONAL_INFO + food_config.SPOONACULAR_API_SEARCH_RESULTS_NUMBER
        else:
            spoonURL = food_config.SPOONACULAR_API_SEARCH + food_config.SPOONACULAR_KEY + "&query=" + request_food + food_config.SPOONACULAR_API_MAX_TIME + str(max_time) + food_config.SPOONACULAR_API_ADDITIONAL_INGREDIENTS + self.user_model['liked_food'][0] + food_config.SPOONACULAR_API_SEARCH_ADDITIONAL_INFO + food_config.SPOONACULAR_API_SEARCH_RESULTS_NUMBER
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

    def get_action(self, user_intent):
        if user_intent in self.rules:
            return self.rules.get(user_intent)
        else:
            return self.stateDefault

if __name__ == "__main__":
    DM.load_food_model()
