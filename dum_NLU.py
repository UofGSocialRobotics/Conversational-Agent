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

        if "western" in msg_lower or "love" in msg_lower:
            user_intention = 'inform'
            user_entity = 'western'
            entity_type = 'genre'
            entity_polarity = "+"
        if "tom cruise" in msg_lower or "love" in msg_lower:
            user_intention = 'inform'
            user_entity = 'tom cruise'
            entity_type = 'cast'
            entity_polarity = "+"
        elif "yes" in msg_lower:
            user_intention = 'yes'
        elif "no" in msg_lower:
            user_intention = 'no'
        elif "more" in msg_lower:
            user_intention = 'request_more'
        elif "plot" in msg_lower:
            user_intention = 'askPlot'
        elif "actor" in msg_lower:
            user_intention = 'askActor'
        elif "genre" in msg_lower:
            user_intention = 'askGenre'
        new_msg = self.msg_to_json(user_intention, user_entity, entity_type, entity_polarity)
        self.publish(new_msg)

    def msg_to_json(self, intent, entity, entity_type, polarity):
        frame = {'intent': intent, 'entity': entity, 'entity_type': entity_type, 'polarity': polarity}
        json_msg = json.dumps(frame)
        return json_msg



