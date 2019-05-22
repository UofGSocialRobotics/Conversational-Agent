import whiteboard_client as wbc
import helper_functions as helper
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
        # self.states = []
        self.nodes = {}
        self.load_model("./resources/dm/Model.csv")

    # Parse the model.csv file and transform that into a dict of Nodes representing the scenario
    def load_model(self, path):
        with open(path) as f:
            for line in f:
                line_input = line.split(",")
                node = DMNode(self.states.size(), line_input[0], line_input[1], line_input[2])
                print(node.stateName)
            for i in range(3, line_input.length):
                node.add(line_input[i])
            # self.states.add(node)
            self.nodes.put(node.name, node)

    def get_action_state_id(self, intent):
        if intent in self.nodes:
            return self.nodes.get(intent)
        else:
            return 0

    def treat_message(self, msg, topic):

        if "SA" in topic:
            self.from_SA = msg
        elif "NLU" in topic:
            self.from_NLU = msg

        # Wait for both SA and NLU messages before sending something back to the whiteboard
        if self.from_NLU and self.from_SA:

            if self.currState.equals("start"):
                next_state = self.nodes.get("start").getAction("greet")
            else:
                next_state = self.nodes.get(self.currState).getAction(self.NLU)

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
    def __init__(self, state_id, state_name, state_default, state_ack):
        self.stateID = state_id
        self.stateName = state_name
        self.stateDefault = state_default
        if state_ack.lower().equals("true"):
            self.stateAck = True
        else:
            self.stateAck = False
        self.rules = {}

    def add(self, string):
        intents = string.split("-")
        self.rules.put(intents[0], intents[1])

    def get_action(self, user_intent):
        if user_intent in self.rules:
            return self.rules.get(user_intent)
        else:
            return self.defaultRule

    def get_name(self):
        return self.name
