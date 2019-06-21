import whiteboard_client as wbc
import helper_functions as helper
import json


class NLU(wbc.WhiteBoardClient):
    def __init__(self, subscribes, publishes, clientid):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, name="NLU"+clientid, subscribes=subscribes, publishes=publishes)

    def treat_message(self, msg, topic):
        msg_lower = msg.lower()

        user_intention = 'yes'
        user_entity = ''
        entity_type = ''
        entity_polarity = ''

        # Todo make sure dum_nlu works (yes/no does not seem to work)

        if "yes" or "out" or "hungry" or "good" in msg_lower:
            user_intention = 'yes'
        elif "no" or "not" or "home" in msg_lower:
            user_intention = 'no'
        if "sweet" in msg_lower:
            user_intention = 'request'
            entity_type = 'sweetness'
        if "salty" in msg_lower:
            user_intention = 'request'
            entity_type = 'saltiness'
        if "bitter" in msg_lower:
            user_intention = 'request'
            entity_type = 'bitterness'
        if "friends" in msg_lower:
            user_intention = 'request'
            entity_type = 'connectedness'
        new_msg = self.msg_to_json(user_intention, user_entity, entity_type, entity_polarity)
        self.publish(new_msg)

    def msg_to_json(self, intent, entity, entity_type, polarity):
        frame = {'intent': intent, 'entity': entity, 'entity_type': entity_type, 'polarity': polarity}
        json_msg = json.dumps(frame)
        return json_msg



