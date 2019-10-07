import whiteboard_client as wbc
import helper_functions as helper
import json
import random
import food.food_config as fc
import requests
from io import BytesIO
from ca_logging import log
from termcolor import colored
import csv
from collections import namedtuple

SentenceParameters = namedtuple("Sentence", [fc.intent, fc.cs, fc.tags])

class NLG(wbc.WhiteBoardClient):
    def __init__(self, clientid, subscribes, publishes):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, "NLG" + clientid, subscribes, publishes)
        self.sentenceDB = {}
        self.ackDB = {}

        self.user_model = None
        self.user_intent = None
        self.food = None
        self.recipe = None
        self.situation = None

        self.features_last_enumareted_on_turn = None

        self.load_sentence_model(fc.NLG_SENTENCE_DB)
        self.load_ack_model(fc.NLG_ACK_DB)

    def load_sentence_model(self, path):
        with open(path, 'r') as f:
            content = csv.reader(f)
            for line_input in content:
                # line_input = line.split(",")
                # print(line_input[2])
                # if self.sentenceDB.get(line_input[0]) is None:
                #     self.sentenceDB[line_input[0]] = {'SD': [], 'VSN': [], 'PR': [], 'HE': [], 'NONE': [], 'QESD': []}
                # self.sentenceDB[line_input[0]][line_input[1]].append(line_input[2])
                sentence_params = SentenceParameters(intent=line_input[0], cs=line_input[1], tags=line_input[2])
                if sentence_params not in self.sentenceDB.keys():
                    self.sentenceDB[sentence_params] = list()
                self.sentenceDB[sentence_params].append(line_input[3])

    def choose_sentence(self, intent, cs=None, tags_list=None):
        # for sentence_params, sentences_list in self.sentenceDB.items():
        sentences_params_list = self.sentenceDB.keys()
        key_res = [s for s in sentences_params_list if s.intent == intent]
        if cs:
            key_res = [s for s in key_res if cs in s.cs]
        if tags_list:
            for tag in tags_list:
                key_res = [s for s in key_res if tag in s.tags]

        if key_res and len(key_res) > 0:
            return random.choice(self.sentenceDB[key_res[0]])
        else:
            error_message = "Can't find a sentence for %s, %s, %s" % (intent, cs.__str__(), tags_list.__str__())
            print(colored())


    def load_ack_model(self, path):
        with open(path) as f:
            self.ackDB = json.load(f)
            # for line in f:
            #     line = line.replace("\n", "")
            #     line_input = line.split(",")
            #     if self.ackDB.get(line_input[0]) is None:
            #         yes_cs_dict = {'SD': [], 'VSN': [], 'PR': [], 'HE': [], 'NONE': [], 'QESD': []}
            #         hungry_cs_dict = {'SD': [], 'VSN': [], 'PR': [], 'HE': [], 'NONE': [], 'QESD': []}
            #         healthy_cs_dict = {'SD': [], 'VSN': [], 'PR': [], 'HE': [], 'NONE': [], 'QESD': []}
            #         time_cs_dict = {'SD': [], 'VSN': [], 'PR': [], 'HE': [], 'NONE': [], 'QESD': []}
            #         no_cs_dict = {'SD': [], 'VSN': [], 'PR': [], 'HE': [], 'NONE': [], 'QESD': []}
            #         not_hungry_cs_dict = {'SD': [], 'VSN': [], 'PR': [], 'HE': [], 'NONE': [], 'QESD': []}
            #         not_healthy_cs_dict = {'SD': [], 'VSN': [], 'PR': [], 'HE': [], 'NONE': [], 'QESD': []}
            #         no_time_cs_dict = {'SD': [], 'VSN': [], 'PR': [], 'HE': [], 'NONE': [], 'QESD': []}
            #         default_cs_dict = {'SD': [], 'VSN': [], 'PR': [], 'HE': [], 'NONE': [], 'QESD': []}
            #         self.ackDB[line_input[0]] = {'yes': yes_cs_dict, 'no': no_cs_dict, 'hungry': hungry_cs_dict, 'not_hungry': not_hungry_cs_dict, 'healthy': healthy_cs_dict, 'not_healthy': not_healthy_cs_dict, 'time': time_cs_dict, 'no_time': no_time_cs_dict, 'default': default_cs_dict}
            #     self.ackDB[line_input[0]][line_input[4]][line_input[2]].append(line_input[3])
            # print(self.ackDB)


    def choose_ack(self, previous_intent, valence=None, CS=None, current_intent=None):
        # print(colored("previous_intent=" + previous_intent.__str__() + ", valence=" + valence.__str__() + ", CS=" + CS.__str__() + ", current_intent="+current_intent.__str__(), "blue"))
        word_valence_list = ["healthy", "time", "hungry"]
        neg_word_valence_list = ["no_"+word for word in word_valence_list] + ["not_"+word for word in word_valence_list]
        if valence and valence in word_valence_list:
            valence = "yes"
        elif valence in neg_word_valence_list:
            valence = "no"
        for ack_sentence, ack_sentence_dict in self.ackDB.items():
            cond_previous_intent = previous_intent == ack_sentence_dict["previous_intent"]
            cond_valence = ((valence and valence == ack_sentence_dict["valence"]) or (not valence and ack_sentence_dict["valence"] == "default"))
            cond_CS = ((CS and CS in ack_sentence_dict["CS"]) or not CS)
            cond_current_intent = ((current_intent and "current_intent" in ack_sentence_dict.keys() and current_intent == ack_sentence_dict["current_intent"]) or not current_intent or "current_intent" not in ack_sentence_dict.keys())
            if cond_previous_intent and cond_valence and cond_CS and cond_current_intent:
                return ack_sentence
        log.warn("Could not find ack for previous_intent=" + previous_intent.__str__() + ", valence=" + valence.__str__() + ", CS=" + CS.__str__() + ", current_intent="+current_intent.__str__())
        return ""

        #  if previous_intent in self.ackDB:
        #     if "yes" in message['user_intent']['intent'] and self.ackDB[message['previous_intent']]['yes']:
        #         ack = self.pick_ack(message['previous_intent'], 'yes', ack_cs)
        #     elif "no" in message['user_intent']['intent'] and self.ackDB[message['previous_intent']]['no']:
        #         ack = self.pick_ack(message['previous_intent'], 'no', ack_cs)
        #     elif message['user_intent']['entity_type'] and "hungry" in message['user_intent']['entity_type']:
        #             if message['user_intent']['entity'] and self.ackDB[message['previous_intent']]['hungry']:
        #                 ack = self.pick_ack(message['previous_intent'], 'hungry', ack_cs)
        #             elif not message['user_intent']['entity'] and self.ackDB[message['previous_intent']]['not_hungry']:
        #                 ack = self.pick_ack(message['previous_intent'], 'not_hungry', ack_cs)
        #     elif message['user_intent']['entity_type'] and "healthy" in message['user_intent']['entity_type']:
        #             if message['user_intent']['entity'] and self.ackDB[message['previous_intent']]['healthy']:
        #                 ack = self.pick_ack(message['previous_intent'], 'healthy', ack_cs)
        #             elif not message['user_intent']['entity'] and self.ackDB[message['previous_intent']]['not_healthy']:
        #                 ack = self.pick_ack(message['previous_intent'], 'not_healthy', ack_cs)
        #     elif message['user_intent']['entity_type'] and "time" in message['user_intent']['entity_type']:
        #             if message['user_intent']['entity'] and self.ackDB[message['previous_intent']]['time']:
        #                 ack = self.pick_ack(message['previous_intent'], 'time', ack_cs)
        #             elif not message['user_intent']['entity'] and self.ackDB[message['previous_intent']]['no_time']:
        #                 ack = self.pick_ack(message['previous_intent'], 'no_time', ack_cs)
        #     else:
        #         if self.ackDB[message['previous_intent']]['default']:
        #             ack = self.pick_ack(message['previous_intent'], 'default', ack_cs)
        #         else:
        #             ack = ""
        # else:
        #     ack = ""


    def treat_message(self, msg, topic):
        message = json.loads(msg)
        recipe_card = None
        self.user_model = message['user_model']
        self.user_intent = message['user_intent']
        self.situation = self.user_model['situation']

        # Todo: Better authoring

        # Content Planning
        #
        # Here we select the different strategies that will be used to deliver the content:
        # Ack + Ack_CS
        # Sentence_CS
        # Explanation

        if fc.NLG_USE_ACKS_CS:
            ack_cs = self.pick_ack_social_strategy()

        if fc.NLG_USE_CS:
            cs = self.pick_social_strategy()

        self.food = message['reco_food']
        if message['recipe']:
            self.recipe = message['recipe']
            recipe_card = self.create_recipe_card(self.recipe)

        # Sentence Planning
        #
        # Based on the strategies selected during the content planning, we generate the sentence.

        # if self.sentenceDB[message['intent']][cs]:
        #     # sentence = random.choice(self.sentenceDB[message['intent']][cs])
        #     sentence = self.choose_sentence(message[fc.intent], cs)
        # else:
            # sentence = random.choice(self.sentenceDB[message['intent']]['NONE'])
        sentence = self.choose_sentence(message[fc.intent], cs=None)

        if fc.NLG_USE_ACKS:
            if message['user_intent']['intent'] in ["yes", "no"]:
                valence = message['user_intent']['intent']
            elif message['user_intent']['entity_type']:
                valence = "yes" if message['user_intent']['entity'] else "no"
            else:
                valence = None
            ack = self.choose_ack(previous_intent=message['previous_intent'], valence=valence, CS=None, current_intent=message["intent"])
        else:
            ack = ""
        final_sentence = self.replace(ack + " " + sentence)

        if message['recipe']:
            if recipe_card:
                msg_to_send = self.msg_to_json(message['intent'], final_sentence, self.recipe['sourceUrl'], recipe_card)
            else:
                msg_to_send = self.msg_to_json(message['intent'], final_sentence, self.recipe['sourceUrl'], None)
        else:
            msg_to_send = self.msg_to_json(intent=message['intent'], sentence=final_sentence, food_recipe=None, food_poster=None)
        self.publish(msg_to_send)

    def create_recipe_card(self, recipe):
        query = fc.SPOONACULAR_API_VISUALIZE + fc.SPOONACULAR_KEY

        imageURL = requests.get(recipe['image'])

        steps_string = ''
        if recipe['analyzedInstructions']:
            for step in recipe['analyzedInstructions'][0]['steps']:
                steps_string = steps_string + step['step'] + "\n"
        else:
            steps_string = "Toss everything in and enjoy!"

        ingredients_string = ''
        for ingredient in recipe['missedIngredients']:
            ingredients_string = ingredients_string + ingredient['originalString'] + "\n"

        files = {
            # "source": recipe['sourceUrl'],
            "backgroundColor": "#ffffff",
            "fontColor": "#333333",
            "title": recipe['title'],
            "backgroundImage": "background1",
            "image": BytesIO(imageURL.content),
            "ingredients": ingredients_string,
            "instructions": steps_string,
            "mask": "potMask",
            "readyInMinutes": recipe['readyInMinutes'],
            "servings": recipe['servings']
        }

        response = requests.post(query, files=files)
        card_json = json.loads(response.text)
        return card_json['url']

    def msg_to_json(self, intent, sentence, food_recipe, food_poster):
        frame = {'intent': intent, 'sentence': sentence, 'food_recipe': food_recipe, 'recipe_card': food_poster}
        #json_msg = json.dumps(frame)
        return frame

    def pick_ack_social_strategy(self):
        #return random.choice(fc.CS_LABELS)
        return "NONE"

    def pick_social_strategy(self):
        #return random.choice(fc.CS_LABELS)
        return "NONE"

    def pick_ack(self, previous_intent, valence, cs):
        potential_options = []
        for option in self.ackDB[previous_intent][valence][cs]:
            if "#entity" in option:
                if self.user_intent['entity']:
                    potential_options.append(option)
            else:
                potential_options.append(option)
        if potential_options:
            return random.choice(potential_options)
        else:
            return ""

    def replace(self, sentence):
        if "#mainfood" in sentence:
            sentence = sentence.replace("#mainfood", self.food['main'])
        if "#secondaryfood" in sentence:
            sentence = sentence.replace("#secondaryfood", self.food['secondary'])
        if "#situation" in sentence:
            sentence = sentence.replace("#situation", self.situation)
        if "#entity" in sentence:
            sentence = sentence.replace("#entity", self.user_intent['entity'])
        if "#recipe" in sentence:
            sentence = sentence.replace("#recipe", self.recipe['title'])
        if "#features" in sentence:
            features_list = []
            if "comfort" in self.user_model['liked_features']:
                features_list.append("are in a bad mood")
            if "filling" in self.user_model['liked_features']:
                features_list.append("feel hungry")
            if "health" in self.user_model['liked_features']:
                features_list.append("want to eat healthy")
            if "time" in self.user_model['liked_features']:
                features_list.append("don't have much time to cook")
            else:
                features_list.append("still have time to cook")
            features_string = ", ".join(features_list[:-1])
            if len(features_list) > 1:
                features_string += " and "
            features_string += features_list[-1] + "."
            sentence = sentence.replace("#features", features_string)
        if "#last_food" in sentence:
            if self.user_model['liked_food']:
                sentence = sentence.replace("#last_food", self.user_model['liked_food'][-1]['main'])
            else:
                sentence = "I know you did not accept any of my recommendations last time but did you eat something instead?"
        return sentence


if __name__ == "__main__":
    fake_msg = {'intent': 'inform(movie)', 'movie': 'John Wick: Chapter 3 – Parabellum'}
    json_msg = json.dumps(fake_msg)
    nlg = NLG("test_subscribe", "test_publishes", "test12345")
    nlg.treat_message(json_msg, "test")
