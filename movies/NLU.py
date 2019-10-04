import whiteboard_client as wbc
import helper_functions as helper
import spacy
import json
import argparse
from movies import movies_nlu_functions, movie_dataparser
import dataparser
import nlu_helper_functions as nlu_helper
import time


####################################################################################################
##                                     rule-based NLU Module                                      ##
####################################################################################################

class RuleBasedNLU(wbc.WhiteBoardClient):
    def __init__(self, clientid, subscribes, publishes):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, name="NLU"+clientid, subscribes=subscribes, publishes=publishes)
        self.voc = dataparser.parse_voc(f_domain_voc="./movies/resources/nlu/movies_voc.json")
        self.spacy_nlp = spacy.load("en_core_web_sm")
        self.directors_dicts = movie_dataparser.get_all_directors()
        self.actors_dicts = movie_dataparser.get_all_actors()

    def treat_message(self, msg, topic):
        msg_lower = msg.lower()

        intent, entitytype, entity, polarity = movies_nlu_functions.rule_based_nlu(utterance=msg_lower, spacy_nlp=self.spacy_nlp, voc=self.voc, directors_dicts=self.directors_dicts, actors_dicts=self.actors_dicts)
        new_msg = self.msg_to_json(intent, entity, entitytype, polarity)
        self.publish(new_msg)

    def msg_to_json(self, intent, entity, entity_type, polarity):
        frame = {'intent': intent, 'entity_type': entity_type, 'entity': entity, 'polarity': polarity}
        json_msg = json.dumps(frame)
        return json_msg



