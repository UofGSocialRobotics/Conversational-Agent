import whiteboard_client as wbc
import helper_functions as helper
import spacy
import json
import argparse
from movies import nlu_functions, movie_dataparser


####################################################################################################
##                                     rule-based NLU Module                                      ##
####################################################################################################

class NLU(wbc.WhiteBoardClient):
    def __init__(self, subscribes, publishes, clientid):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, name="NLU"+clientid, subscribes=subscribes, publishes=publishes)
        self.voc = movie_dataparser.parse_voc()
        self.spacy_nlp = spacy.load("en_core_web_sm")

    def treat_message(self, msg, topic):
        msg_lower = msg.lower()

        # Todo Distinguish actors and directors

        formula = nlu_functions.rule_based_nlu(utterance=msg_lower, spacy_nlp=self.spacy_nlp, voc=self.voc)
        intent, entity, entitytype, polarity = nlu_functions.format_formula(formula=formula)

        new_msg = self.msg_to_json(intent, entity, entitytype, polarity)
        self.publish(new_msg)

    def msg_to_json(self, intent, entity, entity_type, polarity):
        frame = {'intent': intent, 'entity': entity, 'entity_type': entity_type, 'polarity': polarity}
        json_msg = json.dumps(frame)
        return json_msg
