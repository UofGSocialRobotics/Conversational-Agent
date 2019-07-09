import whiteboard_client as wbc
import helper_functions as helper
import spacy
import json
import argparse
from movies import movies_nlu_functions, movie_dataparser
import dataparser
import nlu_helper_functions as nlu_helper


####################################################################################################
##                                     rule-based NLU Module                                      ##
####################################################################################################

class RuleBasedNLU(wbc.WhiteBoardClient):
    def __init__(self, subscribes, publishes, clientid):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, name="NLU"+clientid, subscribes=subscribes, publishes=publishes)
        self.voc = dataparser.parse_voc(f_domain_voc="./movies/resources/nlu/movies_voc.json")
        self.spacy_nlp = spacy.load("en_core_web_sm")
        self.cast_dicts = movie_dataparser.get_all_cast()

    def treat_message(self, msg, topic):
        msg_lower = msg.lower()

        # Todo Distinguish actors and directors

        # formula = movies_nlu_functions.rule_based_nlu(utterance=msg_lower, spacy_nlp=self.spacy_nlp, voc=self.voc, cast_dicts=self.cast_dicts)
        # intent, entity, entitytype, polarity = nlu_helper.format_formula(formula=formula)

        intent, entitytype, entity, polarity = movies_nlu_functions.rule_based_nlu(utterance=msg_lower, spacy_nlp=self.spacy_nlp, voc=self.voc, cast_dicts=self.cast_dicts)

        new_msg = self.msg_to_json(intent, entity, entitytype, polarity)
        self.publish(new_msg)

    def msg_to_json(self, intent, entity, entity_type, polarity):
        frame = {'intent': intent, 'entity_type': entity_type, 'entity': entity, 'polarity': polarity}
        json_msg = json.dumps(frame)
        return json_msg



