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

        self.movie = {'title': "", 'year': "", 'plot': "", 'actors': [], 'genres': [], 'poster': ""}
        self.hungry = None
        self.diet = None
        self.current_food = {'meal': "", 'dessert': "", 'drink': "", 'meat': "", 'side': ""}
        self.food_to_save = {'main': "", 'secondary': ""}
        self.nodes = {}
        self.user_model = {"situation": "", "liked_food": [], 'disliked_food': []}
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
        # Todo: find recipes matching recommended food: https://www.quora.com/What-are-the-best-recipe-and-diet-APIs
        # https://www.quora.com/Are-there-any-free-APIs-for-food-recipes

        self.movie['poster'] = None
        if "SA" in topic:
            self.from_SA = msg
        elif "NLU" in topic:
            self.from_NLU = json.loads(msg)
            self.from_NLU = self.parse_from_NLU(self.from_NLU)
        # Wait for both SA and NLU messages before sending something back to the whiteboard
        if self.from_NLU and self.from_SA:
            recommended_food = None
            food_options = None
            food_info = None
            next_state = self.nodes.get(self.currState).get_action(self.from_NLU['intent'])

            if "situation" in self.currState:
                if "yes" in self.from_NLU['intent']:
                    self.user_model['situation'] = "Usual Lunch"
                else:
                    self.user_model['situation'] = "Lunch Out"
            elif "hungry" in self.currState:
                if "yes" in self.from_NLU['intent']:
                    self.hungry_weight = 1
                else:
                    self.hungry_weight = 0
            elif "diet" in self.currState:
                if "yes" in self.from_NLU['intent']:
                    self.diet_weight = 1
                else:
                    self.diet_weight = 0
            if "food" in next_state:
                if "request" in self.from_NLU['intent']:
                    self.user_model['disliked_food'].append(self.current_food)
                    food_options, recommended_food, food_info = self.recommend((self.user_model['situation']), self.from_NLU['entity_type'])
                    self.current_food = food_options
                    self.food_to_save = recommended_food
                else:
                    food_options, recommended_food, food_info = self.recommend(self.user_model['situation'], None)
                    self.current_food = food_options
                    self.food_to_save = recommended_food
            if "food" in self.currState:
                if "yes" in self.from_NLU['intent']:
                    self.user_model['liked_food'].append(self.food_to_save)

            # if the user comes back
            if next_state == 'greeting' and (self.user_model['liked_food']):
                next_state = "greet_back"

            # saves the user model at the end of the interaction
            if next_state == 'bye' and food_config.SAVE_USER_MODEL:
                self.save_user_model()

            prev_state = self.currState
            self.currState = next_state
            new_msg = self.msg_to_json(next_state, self.from_NLU, prev_state, self.user_model, food_options, recommended_food, food_info)
            self.from_NLU = None
            self.from_SA = None
            self.publish(new_msg)

    def msg_to_json(self, intention, user_intent, previous_intent, user_frame, food_options, reco_food, food_info):
        frame = {'intent': intention, 'user_intent': user_intent, 'previous_intent': previous_intent, 'user_model': user_frame, 'food_options': food_options, 'reco_food': reco_food, 'food_info': food_info}
        json_msg = json.dumps(frame)
        return json_msg

    def parse_from_NLU(self, NLU_message):
        if "request" in NLU_message['intent']:
            NLU_message['intent'] = NLU_message['intent'] + "(" + NLU_message['entity_type'] + ")"
        return NLU_message

    def load_food_data(self):
        self.food_data = pandas.read_csv(food_config.FOOD_MODEL_PATH, encoding='utf-8', sep=',')

    def recommend(self, situation, additional_request):
        max_meal_value = -100
        max_dessert_value = -100
        max_drink_value = -100
        max_meat_value = -100
        max_side_value = -100
        best_meal = None
        best_dessert = None
        best_drink = None
        best_meat = None
        best_side = None
        situated_food_matrix = self.get_food_per_situation(situation)
        for index, row in situated_food_matrix.iterrows():
            if additional_request:
                current_food_value = 1 * row['healthiness'] + row[additional_request] + (self.diet_weight * row['fatteningness']) + (self.hungry_weight * row['energy_level_goal'])
            else:
                current_food_value = row['healthiness'] + (self.diet_weight * row['fatteningness']) + (self.hungry_weight * row['energy_level_goal'])
            if 'meal' in row['food_type'] and current_food_value > max_meal_value:
                if row['food_name'] not in self.current_food['meal']:
                    max_meal_value = current_food_value
                    best_meal = row['food_name']
            elif 'dessert' in row['food_type'] and current_food_value > max_dessert_value:
                if row['food_name'] not in self.current_food['dessert']:
                    max_dessert_value = current_food_value
                    best_dessert = row['food_name']
            elif 'drink' in row['food_type'] and current_food_value > max_drink_value:
                if row['food_name'] not in self.current_food['drink']:
                    max_drink_value = current_food_value
                    best_drink = row['food_name']
            elif 'meat' in row['food_type'] and current_food_value > max_meat_value:
                if row['food_name'] not in self.current_food['meat']:
                    max_meat_value = current_food_value
                    best_meat = row['food_name']
            elif 'side' in row['food_type'] and current_food_value > max_side_value:
                if row['food_name'] not in self.current_food['side']:
                    max_side_value = current_food_value
                    best_side = row['food_name']
        best_food = {'meal': best_meal, 'dessert': best_dessert, 'drink': best_drink, 'meat': best_meat, 'side': best_side}
        recommended_food = self.pick_food(best_food)
        edamamURL = food_config.EDAMAM_SEARCH_RECIPE_ADDRESS + "chicken" + food_config.EDAMAM_APP_ID + food_config.EDAMAM_KEY + food_config.EDAMAM_PROPERTY
        data = urllib.request.urlopen(edamamURL)
        result = data.read()
        food_info = json.loads(result)
        return best_food, recommended_food, food_info

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

    def get_headers(self, matrix):
        headers = matrix.keys()
        return headers

    def get_food_per_situation(self, situation):
        situated_food_matrix = self.food_data.query("situation_name == '" + situation + "'")
        return situated_food_matrix
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
