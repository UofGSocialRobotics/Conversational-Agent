import whiteboard_client as wbc
import helper_functions as helper
import spacy
import csv
# from movies import movies_nlu_functions, movie_dataparser
import nlu_helper_functions as nlu_helper
import food.food_dataparser as food_dataparser
import dataparser
import nltk
from ca_logging import log
import food.food_config as fc
import config
import string

def preprocess_foodNLU(sentence):
    s = sentence.lower()
    s = " " + s + " "
    s = s.replace(" veg ", " vegetables ")
    s = s.replace(" veggies ", " vegetables ")
    s = s.replace(" veg.", " vegetables.")
    s = s.replace(" veggies.", " vegetables.")
    s = s.replace(" veg,", " vegetables,")
    s = s.replace(" veggies,", " vegetables,")
    s.strip()
    s = ' '.join(s.split())
    return s

def inform_food(document, sentence, food_list, voc_no, voc_dislike, threshold=100):
    # print(voc_no)
    sentence = nlu_helper.remove_punctuation(sentence)
    # print(sentence)
    ingredients_list = list()
    negation = False
    if len(sentence) > 1:
        bigrams = nltk.bigrams(sentence.split())
        j = 0
        for i, bg in enumerate(bigrams):
            if document[i].text in string.punctuation:
                j += 1
            bg_text = ' '.join(bg)
            if bg_text in food_list:
                ingredients_list.append(bg_text)
            elif j + 1 < len(document):
                lemma_w1, lemma_w2 = document[j].lemma_, document[j+1].lemma_
                lemma_bg = lemma_w1 + " " + lemma_w2
                if lemma_bg in food_list:
                    # ingredients_list.append(bg_text)
                    ingredients_list.append(lemma_bg)
            j += 1

    for token in document:
        # print(token.text)
        score_token, word_token = nlu_helper.NLU_string_in_list_fuzz(token.text, food_list, threshold=threshold)
        score_lemma, word_lemma = nlu_helper.NLU_string_in_list_fuzz(token.lemma_, food_list, threshold=threshold)
        # print(token.text, score_token, token.lemma_, score_lemma)
        # print(score_token, word_token, score_lemma, word_lemma)
        if ((score_token and not score_lemma) or score_lemma < score_token) and not any(token.text in bg_text for bg_text in ingredients_list):
            ingredients_list.append(word_token)
        elif score_lemma and not any(token.lemma_ in bg_text for bg_text in ingredients_list):
            ingredients_list.append(word_lemma)
        else:
            negation_tmp = nlu_helper.is_negation(token, voc_no)
            if not negation_tmp:
                negation_tmp = nlu_helper.is_negation(token, voc_dislike)
            if negation_tmp:
                negation = True
        # print(negation)
    if ingredients_list:
        # print(ingredients_list)
        valence = "-" if negation else "+"
        if "vegetable" in ingredients_list:
            ingredients_list.remove("vegetable")
            ingredients_list.append("vegetables")
        return ("inform", "food", ingredients_list, valence)

    # if "oats" in sentence:
    #     return ("inform", "food", ['cereals'], valence)
    # if "salsa" in sentence:
    #     return ("inform", "food", ['salsa'], valence)
    # if "wurst" in sentence:
    #     return ("inform", "food", ['sausage'], valence)
    # if "raisin" in sentence:
    #     return ("inform", "food", ['raisin'], valence)
    # if "brownie mix" in sentence:
    #     return ("inform", "food", ['brownie mix'], valence)

    valence = "-" if negation else "+"
    if "half-and-half" in sentence or "halfandhalf" in sentence:
        return ("inform", "food", ['half-and-half'], valence)
    if "rum" in sentence:
        return ("inform", "food", ['rum'], valence)


    return False




def inform_cuisine(document, voc_cuisine, voc_no):
    cuisine_list, negation = list(), False
    for token in document:
        score, word = nlu_helper.NLU_token_in_list_fuzz(token, voc_cuisine)
        if word:
            cuisine_list.append(word)
        elif nlu_helper.is_negation(token, voc_no):
            negation = True
    if cuisine_list:
        if negation:
            return ("inform", "cuisine", cuisine_list, '-')
        else:
            return ("inform", "cuisine", cuisine_list, '+')
    return False


def inform_hungry_with_quantifier(document, sentence, voc_no, voc_quantifiers):
    list_quantifiers = list()
    if nlu_helper.is_dont_know(document, voc_no) or nlu_helper.is_dont_care(document, voc_no) or nlu_helper.is_doesnt_matter(document, voc_no):
        list_quantifiers.append(0)
    if "so and so" in sentence:
        list_quantifiers.append(0)
    if "hungry" in sentence or "peckish" in sentence:
        list_quantifiers.append(0.75)
    if "starv" in sentence or "famish" in sentence:
        list_quantifiers.append(1)
    if "hungryish" in sentence:
        list_quantifiers.append(0.5)
    if "light" in sentence or "diet" in sentence:
        list_quantifiers.append(-0.75)
    if "balanced" in sentence:
        list_quantifiers.append(0)
    quantifiers2 = nlu_helper.get_quantifiers(document, sentence, voc_quantifiers)
    list_quantifiers += quantifiers2
    list_quantifiers_floats = [float(v) for v in list_quantifiers]
    # print(list_quantifiers, list_quantifiers_floats)
    if list_quantifiers_floats:
        if nlu_helper.NLU_string_in_sentence_bool("hungry", sentence):
            if 0.75 in list_quantifiers_floats and len(list_quantifiers_floats) > 1:
                list_quantifiers_floats.remove(0.75)
        quantifier = min(list_quantifiers_floats)
        # print(quantifier)
        negation = False
        for token in document:
            if nlu_helper.is_negation(token, voc_no):
                negation = True
        if negation:
            v = -1 * quantifier
        else:
            v = quantifier
        return ("inform", "hungry", v, None)
    else:
        return None

def inform_healthy_with_quantifier(document, sentence, voc_no, voc_quantifiers):
    list_quantifiers = list()
    if nlu_helper.is_dont_know(document, voc_no) or nlu_helper.is_dont_care(document, voc_no) or nlu_helper.is_doesnt_matter(document, voc_no):
        list_quantifiers.append(0)
    if "so and so" in sentence:
        list_quantifiers.append(0)
    if "unhealthy" in sentence:
        list_quantifiers.append(-0.75)
    if "healthy" in sentence or "balanced" in sentence:
        list_quantifiers.append(0.75)
    if "healthyish" in sentence:
        list_quantifiers.append(0.5)
    quantifiers2 = nlu_helper.get_quantifiers(document, sentence, voc_quantifiers)
    list_quantifiers += quantifiers2
    list_quantifiers_floats = [float(v) for v in list_quantifiers]
    # print(list_quantifiers, list_quantifiers_floats)
    if list_quantifiers_floats:
        if nlu_helper.NLU_string_in_sentence_bool("healthy", sentence):
            if 0.75 in list_quantifiers_floats and len(list_quantifiers_floats) > 1:
                list_quantifiers_floats.remove(0.75)
        quantifier = min(list_quantifiers_floats)
        # print(quantifier)
        negation = False
        for token in document:
            if nlu_helper.is_negation(token, voc_no):
                negation = True
        if negation:
            v = -1 * quantifier
        else:
            v = quantifier
        return ("inform", "healthy", v, None)
    else:
        return None


def inform_healthy(document, voc_no, voc_healthy):
    healthy, negation = False, False
    for token in document:
        if nlu_helper.NLU_token_in_list_bool(token, voc_healthy):# token.lemma_ in voc_healthy:
            healthy = True
        elif nlu_helper.is_negation(token, voc_no):
            negation = True
    if healthy:
        if negation:
            return ("inform", "healthy", -1, None)
        else:
            return ("inform", "healthy", 0.75, None)

def inform_comfort(document, voc_no, voc_comfort):
    comfort, negation = False, False
    for token in document:
        if nlu_helper.NLU_token_in_list_bool(token, voc_comfort):# token.lemma_ in voc_comfort:
            comfort = True
        elif nlu_helper.is_negation(token, voc_no):
            negation = True
    if comfort:
        if negation:
            return ("inform", "comfort", False, None)
        else:
            return ("inform", "comfort", True, None)

def inform_time(document, voc_no, voc_time, voc_no_time, voc_constraint):
    time, no_time, negation, constraint = False, False, False, False
    for token in document:
        # if token.lemma_ in voc_time:
        if nlu_helper.NLU_token_in_list_bool(token, voc_time):
            time = True
        elif nlu_helper.NLU_token_in_list_bool(token, voc_no_time): #token.lemma_ in voc_no_time:
            no_time = True
        elif nlu_helper.is_negation(token, voc_no):
            negation = True

    if constraint and negation:
        return ("inform", "time", True, None)
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

def inform_hungry(document, voc_no, voc_hungry, voc_light):
    positive, hungry, empty, stomach, light = True, None, False, False, False
    for token in document:
        # if token.lemma_ in voc_hungry:
        if nlu_helper.NLU_token_in_list_bool(token, voc_hungry):
            hungry = True
        elif nlu_helper.is_negation(token, voc_no=voc_no):
            positive = False
        elif token.lemma_ == "stomach":
            stomach = True
        elif token.lemma_ == "empty":
            empty = True
        # elif token.lemma_ in voc_light:
        elif nlu_helper.NLU_token_in_list_bool(token, voc_light):
            light = True
    if (hungry or (empty and stomach)) and positive:
        return ("inform", "hungry", True, None)
    if (hungry and not positive):
        return ("inform", "hungry", False, None)
    if light:
        return ("inform", "hungry", not positive, None)
    return False

def inform_diet(document, utterance, voc_diet):
    diets = list()
    if "gluten free" in utterance.lower():
        diets.append("gluten_free")
    if "dairy free" in utterance.lower():
        diets.append("dairy_free")
    if "low carbs" in utterance.lower():
        diets.append("low_carbs")
    for token in document:
        score, word = nlu_helper.NLU_token_in_list_fuzz(token, voc_diet)
        if word:
            if word == "gluten" or word == "dairy":
                word += "_free"
            diets.append(word)
            # return ("inform", "diet", word, None)
        elif nlu_helper.NLU_token_in_list_bool(token, ["keto"]):
            # return ("inform", "diet", "ketonic", None)
            diets.append("ketonic")
    if diets:
        return ("inform", "diet", diets, None)
    return False

def is_but_no_inform_food(sentence):
    if "but" in sentence:
        return ("no", None, None, None)
    return False


def inform_intolerance(document, uttenrance, voc_intolerances):
    intolerances = list()
    for token in document:
        if token.lemma_ in voc_intolerances:
            intolerances.append(token.lemma_)
        elif token.text in voc_intolerances:
            intolerances.append(token.text)
    if nlu_helper.NLU_string_in_sentence_bool("lactose", uttenrance):
        intolerances.append("dairy")

    new_intolerances = list()
    for w in intolerances:
        new_intolerances.append(w + '_free')

    if new_intolerances:
        return ("inform", "intolerances", ",".join(new_intolerances), None)
    else:
        return False

def user_likes_recipe(document, sentence, voc_like, voc_dislike, voc_no):
    res = {"yes": ("yes", None, None, None), "no": ("no", None, None, None)}
    like_bool, dislike_bool, negation = False, False, False
    for token in document:
        # if token.lemma_ in voc_like or token.text in voc_like or helper.remove_duplicate_consecutive_char_from_string(token.text) in voc_like:
        if nlu_helper.NLU_token_in_list_bool(token, voc_like):
            like_bool = True
        # elif token.lemma_ in voc_dislike or token.text in voc_dislike:
        elif nlu_helper.NLU_token_in_list_bool(token, voc_dislike):
            # print("dislike", token.text)
            dislike_bool = True
        elif nlu_helper.is_negation(token, voc_no):
            # print("negation", token.text)
            negation = True
    if like_bool and negation:
        return res['no']
    elif like_bool:
        return res['yes']
    elif dislike_bool and negation:
        return res['yes']
    elif dislike_bool:
        return res['no']
    return None

def get_intent_depending_on_conversation_stage(stage, document, utterance, voc, food_list):
    # print("in get_intent_depending_on_conversation_stage, stage = " + stage)
    f = None
    if stage == "greeting":
        f = nlu_helper.name_in_my_name_is_sentence(document)
        if not f:
            f = nlu_helper.name_in_one_word_sentence(document)
    elif stage == "request(mood)":
        f = nlu_helper.user_feels_good(document=document, sentence=utterance, voc_feel_good=voc["feel_good"], voc_feel_bad=voc["feel_bad"], voc_feel_tired=voc["feel_tired"], voc_no=voc['no']["all_no_words"])
    elif stage == "request(filling)":
        f = inform_hungry_with_quantifier(document, sentence=utterance, voc_no=voc['no']['all_no_words'], voc_quantifiers=voc["quantifiers"])
        if not f:
            f = inform_hungry(document, voc_no=voc["no"]["all_no_words"], voc_hungry=voc["hungry"], voc_light=voc["light"])
        if not f:
            f = nlu_helper.is_yes_no(document, utterance, voc_yes=voc["yes"], voc_no=voc["no"])
        if f:
            if f[0] == "yes":
                f = ("inform", "hungry", 0.75, None)
            elif f[0] == "no":
                f = ("inform", "hungry", -1, None)
    elif stage == "request(healthy)":
        f = inform_healthy_with_quantifier(document, sentence=utterance, voc_no=voc["no"]['all_no_words'], voc_quantifiers=voc["quantifiers"])
        if not f:
            f = inform_healthy(document, voc_no=voc["no"]["all_no_words"], voc_healthy=voc["healthy"])
        if not f:
            f = nlu_helper.is_yes_no(document, utterance, voc_yes=voc["yes"], voc_no=voc["no"])
        if f:
            if f[0] == "yes":
                f = ("inform", "healthy", 0.75, None)
            elif f[0] == "no":
                f = ("inform", "healthy", -1, None)
    elif stage == "request(diet)":
        f = inform_diet(document, utterance=utterance, voc_diet=voc['diet'])
        if not f:
            f = inform_intolerance(document, uttenrance=utterance, voc_intolerances=voc["spoonacular_intolerances"])
        if not f:
            f = inform_food(document, utterance, food_list, voc_no=voc["no"]["all_no_words"], voc_dislike=voc["dislike"])
        if not f:
            f = inform_cuisine(document, voc_cuisine=voc["cuisines"], voc_no=voc['no']["all_no_words"])
    elif stage == "request(time)":
        f = nlu_helper.is_duration(document, utterance, voc["numbers"], voc["duration_units"], voc["duration_unit_division"])
        if not f:
            f = inform_time(document, voc_no=voc["no"]["all_no_words"], voc_time=voc["time"], voc_no_time=voc["no_time"], voc_constraint=voc["constraint"])
    elif stage == "request(food)":
        f = inform_food(document, utterance, food_list, voc_no=voc["no"]["all_no_words"], voc_dislike=voc["dislike"])
        if not f:
            f = inform_cuisine(document, voc_cuisine=voc["cuisines"], voc_no=voc['no']["all_no_words"])
    elif stage == "inform(food)":
        f = inform_food(document, utterance, food_list, voc_no=voc["no"]["all_no_words"], voc_dislike=voc["dislike"])
        if not f:
            f = inform_cuisine(document, voc_cuisine=voc["cuisines"], voc_no=voc['no']["all_no_words"])
        if not f:
            f = user_likes_recipe(document, utterance, voc_like=voc["like"], voc_dislike=voc['dislike'], voc_no=voc['no']["all_no_words"])
        if not f:
            f = is_but_no_inform_food(utterance)
        if not f:
            f = nlu_helper.is_yes_no(document, utterance, voc_yes=voc["yes"], voc_no=voc["no"])
        if not f:
            f = nlu_helper.is_requestmore(document, voc_request_more=voc["request_more"])
    elif stage == "request(another)":
        f = inform_food(document, utterance, food_list, voc_no=voc["no"]["all_no_words"], voc_dislike=voc["dislike"])
        if not f:
            f = inform_cuisine(document, voc_cuisine=voc["cuisines"], voc_no=voc['no']["all_no_words"])
        if not f:
            f = nlu_helper.iamgood_means_no(document, voc_yes=voc["yes"])
        if not f:
            f = nlu_helper.is_yes_no(document, utterance, voc_yes=voc["yes"], voc_no=voc["no"])
    else:
        f = get_intent_default(document, utterance, voc, food_list)

    if not f:
        f = nlu_helper.is_yes_no(document, utterance, voc_yes=voc["yes"], voc_no=voc["no"])
    if not f:
        f = "IDK", None, None, None

    return f[0], f[2], f[1], f[3]

def get_intent_default(document, utterance, voc, food_list):
    # print("in get_intent_default")
    f = inform_food(document, utterance, food_list, voc_no=voc["no"]["all_no_words"], voc_dislike=voc["dislike"])
    if not f:
        f = inform_hungry(document, voc_no=voc["no"]["all_no_words"], voc_hungry=voc["hungry"], voc_light=voc["light"])
    if not f:
        f = inform_healthy(document, voc_no=voc["no"]["all_no_words"], voc_healthy=voc["healthy"])
    if not f:
        f = inform_time(document, voc_no=voc["no"]["all_no_words"], voc_time=voc["time"], voc_no_time=voc["no_time"], voc_constraint=voc["constraint"])
    if not f:
        # f = inform_vegan(document, voc_no=voc["no"]["all_no_words"], voc_vegan=voc["vegan"], voc_no_vegan=voc["no_vegan"])
        f = inform_diet(document, utterance=utterance, voc_diet=voc['diet'])
    if not f:
        f = inform_intolerance(document, uttenrance=utterance, voc_intolerances=voc["spoonacular_intolerances"])
    if not f:
        f = nlu_helper.is_goodbye(document, utterance, voc_bye=voc["bye"])
    if not f:
        f = nlu_helper.user_feels_good(document=document, sentence=utterance, voc_feel_good=voc["feel_good"], voc_feel_bad=voc["feel_bad"], voc_feel_tired=voc["feel_tired"], voc_no=voc['no']["all_no_words"])
    if not f:
        f = nlu_helper.is_yes_no(document, utterance, voc_yes=voc["yes"], voc_no=voc["no"])
    if not f:
        f = nlu_helper.is_greeting(document, voc_greetings=voc["greetings"])
    if not f:
        f = nlu_helper.is_requestmore(document, voc_request_more=voc["request_more"])
    if not f:
        f = nlu_helper.is_duration(document, utterance, voc_numbers=voc["numbers"], voc_duration=voc["duration_units"], voc_fractions=voc["duration_unit_division"])
    if not f:
        f = user_likes_recipe(document, utterance, voc_like=voc["like"], voc_dislike=voc['dislike'], voc_no=voc['no']["all_no_words"])
    if not f:
        f = "IDK", None, None, None
    return f


def rule_based_nlu(utterance, spacy_nlp, voc, food_list, conversation_stage):

    utterance = nlu_helper.preprocess(utterance)
    utterance = preprocess_foodNLU(utterance)
    # print(utterance)
    document = spacy_nlp(utterance)
    capitalized_document = spacy_nlp(utterance.title())
    return get_intent_depending_on_conversation_stage(stage=conversation_stage, document=document, utterance=utterance, voc=voc, food_list=food_list)

####################################################################################################
##                                     rule-based NLU Module                                      ##
####################################################################################################

class NLU(wbc.WhiteBoardClient):
    def __init__(self, clientid, subscribes, publishes, resp_time=False):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, name="NLU"+clientid, subscribes=subscribes, publishes=publishes, resp_time=resp_time)
        self.voc = dataparser.parse_voc(f_domain_voc="food/resources/nlu/food_voc.json")
        self.spacy_nlp = spacy.load("en_core_web_sm")
        self.food_list = food_dataparser.extensive_food_DBs.all_foods_list
        # print(self.food_list)

        self.conversation_stages = self.read_convesation_stages()
        self.current_stage = self.conversation_stages.pop(0)
        # self.next_conversation_stage()

    def read_convesation_stages(self):
        path = fc.DM_MODEL
        with open(path, 'r') as f:
            content = csv.reader(f)
            conversation_stages = list()
            for row in content:
                conversation_stages.append(row[0])
            return conversation_stages


    def treat_message(self, msg, topic):
        # print(msg, topic)
        super(NLU, self).treat_message(msg,topic)

        if topic[:len(config.MSG_DM_CONV_STATE)] == config.MSG_DM_CONV_STATE:
            self.current_stage = msg["current_state"]
            return True

        msg_lower = msg.lower()

        # Todo Distinguish actors and directors

        intent, entitytype, entity, polarity = rule_based_nlu(utterance=msg_lower, spacy_nlp=self.spacy_nlp, voc=self.voc, food_list=self.food_list, conversation_stage=self.current_stage)
        # print(intent, entitytype, entity, polarity)

        new_msg = self.msg_to_json(intent, entity, entitytype, polarity)

        self.publish(new_msg)

        # self.next_conversation_stage()

    def msg_to_json(self, intent, entity, entity_type, polarity):
        frame = {'intent': intent, 'entity_type': entity, 'entity': entity_type, 'polarity': polarity}
        # json_msg = json.dumps(frame)
        return frame

