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
