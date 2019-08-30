import whiteboard_client as wbc
import helper_functions as helper
import spacy
import json
# from movies import movies_nlu_functions, movie_dataparser
import nlu_helper_functions as nlu_helper
import food.food_dataparser as food_dataparser
import dataparser


def inform_food(document, food_list):
    ingredients_list = list()
    for token in document:
        if token.text in food_list:
            ingredients_list.append(token.text)
    if ingredients_list:
        return "inform", "food", ",".join(ingredients_list), "+"
    return False

def inform_healthy(document, voc_no, voc_healthy):
    healthy, negation = False, False
    for token in document:
        if token.lemma_ in voc_healthy:
            healthy = True
        elif nlu_helper.is_negation(token, voc_no):
            negation = True
    if healthy:
        if negation:
            return ("inform", "healthy", False, None)
        else:
            return ("inform", "healthy", True, None)

def inform_comfort(document, voc_no, voc_comfort):
    comfort, negation = False, False
    for token in document:
        if token.lemma_ in voc_comfort:
            healthy = True
        elif nlu_helper.is_negation(token, voc_no):
            negation = True
    if comfort:
        if negation:
            return ("inform", "comfort", False, None)
        else:
            return ("inform", "comfort", True, None)

def inform_time(document, voc_no, voc_time, voc_no_time):
    time, no_time, negation = False, False, False
    for token in document:
        if token.lemma_ in voc_time:
            time = True
        elif token.lemma_ in voc_no_time:
            no_time = True
        elif nlu_helper.is_negation(token, voc_no):
            negation = True
    if time:
        if negation:
            return ("inform", "time", False, None)
        else:
            return ("inform", "time", True, None)
    elif no_time:
        if negation:
            return ("inform", "time", True, None)
        else:
            return ("inform", "time", False, None)

def inform_hungry(document, voc_no, voc_hungry):
    positive, hungry, empty, stomach = True, None, False, False
    for token in document:
        if token.lemma_ in voc_hungry:
            hungry = True
        elif nlu_helper.is_negation(token, voc_no=voc_no):
            positive = False
        elif token.lemma_ == "stomach":
            stomach = True
        elif token.lemma_ == "empty":
            empty = True
    if (hungry or (empty and stomach)) and positive:
        return ("inform", "hungry", True, None)
    if (hungry and not positive):
        return ("inform", "hungry", False, None)
    return False

def inform_vegan(document, voc_no, voc_vegan, voc_no_vegan):
    vegan, no_vegan, negation = False, False, False
    for token in document:
        if token.lemma_ in voc_vegan:
            vegan = True
        elif token.lemma_ in voc_no_vegan:
            no_vegan = False
        elif nlu_helper.is_negation(token, voc_no):
            negation = True
    if vegan:
        if negation:
            return ("inform", "vegan", False, None)
        else:
            return ("inform", "vegan", True, None)
    elif no_vegan:
        if negation:
            return ("inform", "vegan", True, None)
        else:
            return ("inform", "vegan", False, None)


def rule_based_nlu(utterance, spacy_nlp, voc, food_list):

    utterance = nlu_helper.preprocess(utterance)
    document = spacy_nlp(utterance)
    capitalized_document = spacy_nlp(utterance.title())
    f = inform_food(document, food_list)
    if not f:
        f = inform_hungry(document, voc_no=voc["no"], voc_hungry=voc["hungry"])
    if not f:
        f = inform_healthy(document, voc_no=voc["no"], voc_healthy=voc["healthy"])
    if not f:
        f = inform_time(document, voc_no=voc["no"], voc_time=voc["time"], voc_no_time=voc["no_time"])
    if not f:
        f = inform_vegan(document, voc_no=voc["no"], voc_vegan=voc["vegan"], voc_no_vegan=voc["no_vegan"])
    if not f:
        f = nlu_helper.is_goodbye(document, utterance, voc_bye=voc["bye"])
    if not f:
        f = nlu_helper.is_yes_no(document, utterance, voc_yes=voc["yes"], voc_no=voc["no"])
    if not f:
        f = nlu_helper.is_greeting(document, voc_greetings=voc["greetings"])
    if not f:
        f = "IDK", None, None, None
    return f



####################################################################################################
##                                     rule-based NLU Module                                      ##
####################################################################################################

class NLU(wbc.WhiteBoardClient):
    def __init__(self, subscribes, publishes, clientid):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, name="NLU"+clientid, subscribes=subscribes, publishes=publishes)
        self.voc = dataparser.parse_voc(f_domain_voc="food/resources/nlu/food_voc.json")
        self.spacy_nlp = spacy.load("en_core_web_sm")
        self.food_list = food_dataparser.get_food_names()

    def treat_message(self, msg, topic):
        msg_lower = msg.lower()

        # Todo Distinguish actors and directors

        intent, entitytype, entity, polarity = rule_based_nlu(utterance=msg_lower, spacy_nlp=self.spacy_nlp, voc=self.voc, food_list=self.food_list)

        new_msg = self.msg_to_json(intent, entity, entitytype, polarity)
        self.publish(new_msg)

    def msg_to_json(self, intent, entity, entity_type, polarity):
        frame = {'intent': intent, 'entity': entity, 'entity_type': entity_type, 'polarity': polarity}
        json_msg = json.dumps(frame)
        return json_msg

