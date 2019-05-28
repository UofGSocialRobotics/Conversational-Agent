import whiteboard_client as wbc
import helper_functions as helper
import urllib.request
from ca_logging import log


class DM(wbc.WhiteBoardClient):
    def __init__(self, subscribes, publishes, clientid):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, "DM"+clientid, subscribes, publishes)

        self.currState = "start"
        # Do we store the users preferences in a user model?
        self.storePref = True
        # Do we generate acknowledgement?
        self.useAcks = True

        self.from_NLU = None
        self.from_SA = None
        self.nodes = {}
        #user_likes = []
        #user_dislikes = []
        self.user_model = {"likes": [], "dislikes": []}
        self.load_model("./resources/dm/Model.csv")

    # Parse the model.csv file and transform that into a dict of Nodes representing the scenario
    def load_model(self, path):
        with open(path) as f:
            for line in f:
                line_input = line.split(",")
                node = DMNode(line_input[0], line_input[1], line_input[2])
                for i in range(3, len(line_input)):
                    if "-" in line_input[i]:
                        node.add(line_input[i])
                self.nodes[node.stateName] = node

    def treat_message(self, msg, topic):

        if "SA" in topic:
            self.from_SA = msg
        elif "NLU" in topic:
            self.from_NLU = msg
        # Wait for both SA and NLU messages before sending something back to the whiteboard
        if self.from_NLU and self.from_SA:

            # Store entities (actors,directors, genres) in the user frame)
            # Todo: Actually store preferred entities
            if "inform" in msg:
                self.user_model["likes"].append(msg)

            next_state = self.nodes.get(self.currState).get_action(self.from_NLU)

            if "inform(movie)" in next_state:
                reco = MovieQuery.recommend()
                next_state = next_state + " " + reco

            self.currState = next_state
            self.from_NLU = None
            self.from_SA = None
            self.publish(next_state)

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

# To query the movie DB and get a movie title
class MovieQuery:
    def __init__(self, state_name, state_default, state_ack):
        self.movieDB_key = "6e3c2d4a2501c86cd7e0571ada291f55"
        self.discover_address = "https://api.themoviedb.org/3/discover/movie?api_key="
        self.property = "&sort_by=popularity.desc"

    def recommend(self):
        movies_list = self.queryMoviesList()
        return movies_list[0]

    def queryMoviesList(self):
        query_url = self.discover_address + self.movieDB_key + self.property
        data = urllib.request.urlopen(query_url)
        result = data.read()
        return result