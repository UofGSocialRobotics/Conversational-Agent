import whiteboard_client as wbc
import helper_functions as helper
import json
from ca_logging import log

class NLU(wbc.WhiteBoardClient):
    def __init__(self, subscribes, publishes, clientid):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, name="NLU"+clientid, subscribes=subscribes, publishes=publishes)

    def treat_message(self,msg,topic):
        msg_lower = msg.lower()

        if "like" in msg_lower or "love" in msg_lower:
            user_intention = 'inform'
            user_entity = 'Tom Cruise'
            entity_polarity = "+"
        else:
            user_intention = 'inform'
            user_entity = 'Jennifer Lawrence'
            entity_polarity = "-"
        new_msg = self.msg_to_json(user_intention, user_entity, entity_polarity)
        self.publish(new_msg)

    def msg_to_json(self, intent, entity, polarity):
        frame = {'intent': intent, 'entity': entity, 'polarity': polarity}
        json_msg = json.dumps(frame)
        return json_msg

