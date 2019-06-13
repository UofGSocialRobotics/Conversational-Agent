from ca_logging import log
import whiteboard_client as wbc
import helper_functions as helper
import spacy
import json
import dataparser
import argparse
import nlu_functions


####################################################################################################
##                                     rule-based NLU Module                                      ##
####################################################################################################

class RuleBasedNLU(wbc.WhiteBoardClient):
    def __init__(self, subscribes, publishes, clientid):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, name="NLU"+clientid, subscribes=subscribes, publishes=publishes)
        self.voc = dataparser.parse_voc()
        self.spacy_nlp = spacy.load("en_core_web_sm")
        self.cast_dicts = dataparser.get_all_cast()

    def treat_message(self, msg, topic):
        msg_lower = msg.lower()

        formula = nlu_functions.rule_based_nlu(utterance=msg_lower, spacy_nlp=self.spacy_nlp, voc=self.voc, cast_dicts=self.cast_dicts)
        intent, entity, entitytype, polarity = nlu_functions.format_formula(formula=formula)

        new_msg = self.msg_to_json(intent, entity, entitytype, polarity)
        self.publish(new_msg)

    def msg_to_json(self, intent, entity, entity_type, polarity):
        frame = {'intent': intent, 'entity': entity, 'entity_type': entity_type, 'polarity': polarity}
        json_msg = json.dumps(frame)
        return json_msg

####################################################################################################
##                                     Run as stand-alone                                         ##
####################################################################################################

if __name__ == "__main__":

    argp = argparse.ArgumentParser()
    argp.add_argument("--eval", help="To evaluate the performance of NLU on the labeled dataset", action="store_true")
    argp.add_argument("--test", help="To test the NLU module yourself", action="store_true")
    argp.add_argument("--debug", help="Sentence to debug", action="store")

    args = argp.parse_args()

    if args.eval:

        dataset = dataparser.load_dataset()

        nlu_functions.evaluate(dataset, "wrong")

    elif args.test:

        nlu_functions.test_nlu()

    elif args.debug:
        print(args.debug)
        nlu_functions.compare_syntax_analysis(nlu_functions.preprocess(args.debug))

