import whiteboard_client as wbc
import helper_functions as helper
import spacy
import json
# from movies import movies_nlu_functions, movie_dataparser
import nlu_helper_functions as nlu_helper
import food.food_dataparser as food_dataparser


def inform_food(document, food_list):
    for token in document:
        if token.text in food_list:
            return "inform", "food", token.text, "+"
    return False


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


def inform_alone(document, voc_no, voc_alone, voc_not_alone):
    alone, together, negation = None, None, False
    anybody = False
    for token in document:
        if token.text in voc_alone:
            alone = True
        elif token.text in voc_not_alone:
            together = True
        elif token.text == "anybody":
            anybody = True
        elif nlu_helper.is_negation(token, voc_no):
            negation = True
    if (alone and not negation) or (together and negation) or (negation and anybody):
        return ("inform", "alone", True, None)
    if (together and not negation) or (alone and negation):
        return ("inform", "alone", False, None)


def inform_diet(document, voc_no, voc_diet):
    diet, negation = False, False
    for token in document:
        if token.lemma_ in voc_diet:
            diet = True
        elif nlu_helper.is_negation(token, voc_no):
            negation = True
    if diet:
        if negation:
            return ("inform", "diet", False, None)
        else:
            return ("inform", "diet", True, None)


def rule_based_nlu(utterance, spacy_nlp, voc, food_list):

    utterance = nlu_helper.preprocess(utterance)
    document = spacy_nlp(utterance)
    capitalized_document = spacy_nlp(utterance.title())
    f = inform_food(document, food_list)
    if not f:
        f = inform_hungry(document, voc_no=voc["no"], voc_hungry=voc["hungry"])
    if not f:
        f = inform_alone(document, voc_no=voc["no"], voc_alone=voc["alone"], voc_not_alone=voc["not_alone"])
    if not f:
        f = inform_diet(document, voc_no=voc["no"], voc_diet=voc["diet"])
    if not f:
        f = nlu_helper.is_goodbye(document, utterance, voc_bye=voc["bye"])
    if not f:
        f = nlu_helper.is_yes_no(document, utterance, voc_yes=voc["yes"], voc_no=voc["no"])
    if not f:
        f = nlu_helper.is_greeting(document, voc_greetings=voc["greetings"])
    if not f:
        f = "IDK"
    return f



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
        self.food_list = food_dataparser.get_food_names()

    def treat_message(self, msg, topic):
        msg_lower = msg.lower()

        formula = rule_based_nlu(utterance=msg_lower, spacy_nlp=self.spacy_nlp, voc=self.voc, food_list=self.food_list)
        intent, entity, entitytype, polarity = movies_nlu_functions.format_formula(formula=formula)

        new_msg = self.msg_to_json(intent, entity, entitytype, polarity)
        self.publish(new_msg)

    def msg_to_json(self, intent, entity, entity_type, polarity):
        frame = {'intent': intent, 'entity': entity, 'entity_type': entity_type, 'polarity': polarity}
        json_msg = json.dumps(frame)
        return json_msg

