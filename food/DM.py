import whiteboard_client as wbc
import helper_functions as helper
import json
import food.food_config as food_config
from pathlib import Path
import pandas


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
        self.food_model = None

        self.load_food_model()

        self.movie = {'title': "", 'year': "", 'plot': "", 'actors': [], 'genres': [], 'poster': ""}
        self.situation = None
        self.nodes = {}
        self.user_model = {"liked_cast": [], "disliked_cast": [], "liked_genres": [], 'disliked_genres': [],
                           'liked_movies': [], 'disliked_movies': []}
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
        self.movie['poster'] = None
        if "SA" in topic:
            self.from_SA = msg
        elif "NLU" in topic:
            self.from_NLU = json.loads(msg)
            self.from_NLU = self.parse_from_NLU(self.from_NLU)
        # Wait for both SA and NLU messages before sending something back to the whiteboard
        if self.from_NLU and self.from_SA:

            next_state = self.nodes.get(self.currState).get_action(self.from_NLU['intent'])

            if "situation" in self.currState:
                if "yes" in self.from_NLU['intent']:
                    self.situation = "Lunch Out"
                else:
                    self.situation = "Usual Lunch"


            # if the user comes back
            if next_state == 'greeting' and (self.user_model['liked_movies'] or self.user_model['disliked_movies']):
                next_state = "greet_back"

            # saves the user model at the end of the interaction
            if next_state == 'bye' and food_config.SAVE_USER_MODEL:
                self.save_user_model()

            prev_state = self.currState
            self.currState = next_state
            new_msg = self.msg_to_json(next_state, self.from_NLU, prev_state, self.user_model)
            self.from_NLU = None
            self.from_SA = None
            self.publish(new_msg)

    def msg_to_json(self, intention, user_intent, previous_intent, user_frame):
        frame = {'intent': intention, 'user_intent': user_intent, 'previous_intent': previous_intent, 'user_model': user_frame}
        json_msg = json.dumps(frame)
        return json_msg

    def parse_from_NLU(self, NLU_message):
        if "request" in NLU_message['intent']:
            NLU_message['intent'] = NLU_message['intent'] + "(" + NLU_message['entity_type'] + ")"
        return NLU_message

    def load_food_model(self):
        self.food_data = pandas.read_csv(food_config.FOOD_MODEL_PATH, encoding='utf-8', sep=',')
        print(self.food_data)

    def recommend(self):
        movies_list = self.queryMoviesList()
        for movie in movies_list:
            if movie['title'] not in self.user_model['liked_movies'] and movie['title'] not in self.user_model['disliked_movies']:
                if food_config.HIGH_QUALITY_POSTER:
                    self.movie['poster'] = food_config.MOVIEDB_POSTER_PATH + movie['poster_path']
                return movie['title']


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
