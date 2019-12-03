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
import time
import threading
import math
import pandas
import string

SentenceParameters = namedtuple("Sentence", [fc.intent, fc.cs, fc.tags])
AckParameters = namedtuple("Ack", [fc.previous_intent, fc.cs, fc.valence, fc.current_intent_should_not_be, fc.current_intent_should_be])

class NLG(wbc.WhiteBoardClient):
    def __init__(self, clientid, subscribes, publishes, tags_explanation_types=[], cs=None, resp_time=False):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, "NLG" + clientid, subscribes, publishes, resp_time)
        self.tags_explanation_types = tags_explanation_types
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
        self.timeit_details = False

        self.cs = cs
        print("NLG, cs", cs)

        self.recipe_cards = dict()

    def load_sentence_model(self, path):
        with open(path, 'r') as f:
            content = csv.reader(f)
            for line_input in content:
                sentence_params = SentenceParameters(intent=line_input[0], cs=line_input[1], tags=line_input[2])
                if sentence_params not in self.sentenceDB.keys():
                    self.sentenceDB[sentence_params] = list()
                self.sentenceDB[sentence_params].append(line_input[3])

    def load_ack_model(self, path):
        with open(path, 'r') as f:
            content = csv.reader(f)
            for i, line_input in enumerate(content):
                if i > 0:
                    # print(line_input[3])
                    valence = list(line_input[3]) if "," in line_input[3] else line_input[3].split(",")
                    valence = [v.strip() for v in valence]
                    ack_params = AckParameters(previous_intent=line_input[0], cs=line_input[1], valence=line_input[3], current_intent_should_not_be=line_input[4], current_intent_should_be=line_input[5])
                    if ack_params not in self.ackDB.keys():
                        self.ackDB[ack_params] = list()
                    self.ackDB[ack_params].append(line_input[2])
        # print(self.ackDB)

    def choose_sentence(self, intent, cs=None, tags_list=None):
        cs = self.cs
        if self.cs == "no_ack":
            cs = "NONE"
        # print(self.sentenceDB)
        start = time.time()
        # for sentence_params, sentences_list in self.sentenceDB.items():
        # print((intent, cs.__str__(), tags_list.__str__()))
        sentences_params_list = self.sentenceDB.keys()
        key_res = [s for s in sentences_params_list if s.intent == intent]
        # print(key_res)
        key_res_tmp = key_res
        if cs:
            key_res = [s for s in key_res if cs in s.cs]
        if not key_res:
            key_res = key_res_tmp
            key_res = [s for s in key_res if (cs in s.cs or s.cs == "NONE")]
        # print(key_res)
        if tags_list:
            for tag in tags_list:
                key_res = [s for s in key_res if tag in s.tags]
        # print(key_res)
        if key_res and len(key_res) > 0:
            to_return = random.choice(self.sentenceDB[key_res[0]])
            # print("to_return", to_return)
            return to_return
        else:
            error_message = "Can't find a sentence for %s, %s, %s" % (intent, cs.__str__(), tags_list.__str__())
            print(colored(error_message, "blue"))
            log.critical(error_message)

        if self.timeit_details:
            print("Response time choose_sentence: %.3f sec" % (time.time() - start))

    def choose_ack(self, previous_intent, valence=None, CS=None, current_intent=None):
        CS = self.cs
        if self.cs == "no_ack":
            return ""

        start = time.time()
        ack_params_list = self.ackDB.keys()
        key_res = [ack_params for ack_params in ack_params_list if ack_params.previous_intent == previous_intent]
        # print(key_res)

        if CS:
            key_res = [ack_params for ack_params in key_res if ack_params.cs == CS]
        # print(key_res)
        key_res_tmp = key_res
        if valence:
            key_res = [ack_params for ack_params in key_res if (valence in ack_params.valence)]
        if not key_res:
            key_res = key_res_tmp
            key_res = [ack_params for ack_params in key_res if (valence in ack_params.valence or ack_params.valence == "NONE")]
        # print(key_res)
        if current_intent:
            key_res = [ack_params for ack_params in key_res if current_intent not in ack_params.current_intent_should_not_be]
            key_res = [ack_params for ack_params in key_res if (ack_params.current_intent_should_be == 'NONE' or current_intent in ack_params.current_intent_should_be)]

        # print(key_res)

        if key_res and len(key_res) > 0:
            to_return = random.choice(self.ackDB[key_res[0]])
        else:
            error_message = "Could not find ack for previous_intent=" + previous_intent.__str__() + ", valence=" + valence.__str__() + ", CS=" + CS.__str__() + ", current_intent="+current_intent.__str__()
            log.warn(error_message)
            # print(colored(error_message, "blue"))
            to_return = ""
        if self.timeit_details:
            print("Response time choose_ack: %.3f sec" % (time.time() - start))
        # print(to_return)
        return to_return

    def get_create_all_cards(self, recipe_list):
        for recipe in recipe_list:
            # print(recipe['id'], type(self.recipe_cards.keys()))
            if recipe["id"] not in self.recipe_cards.keys():
                self.create_recipe_card(recipe)
            # threading.current_thread().join()

    def get_recipe_card(self, recipe):
        # print(recipe['id'], self.recipe_cards)
        # print(self.recipe_cards)
        if recipe["id"] in self.recipe_cards.keys():
            log.debug("found recipe %d in localDB" % recipe["id"])
            return self.recipe_cards[recipe['id']]
        else:
            log.debug("can't find card in localDB for recipe %d" % recipe['id'])
            new_card = self.create_recipe_card(recipe)
            self.recipe_cards[recipe['id']] = new_card
            return new_card


    def treat_message(self, message, topic):
        start = time.time()
        super(NLG, self).treat_message(message, topic)


        if topic == self.subscribes[1]:
            log.debug("Will start fetching recipe cards!")
            self.get_create_all_cards(message)
            return
        else:

            # message = json.loads(msg)
            recipe_card = None
            self.user_model = message['user_model']
            # print(self.user_model)
            self.user_intent = message['user_intent']
            self.situation = self.user_model['situation']

            # Todo: Better authoring

            # Content Planning
            #
            # Here we select the different strategies that will be used to deliver the content:
            # Ack + Ack_CS
            # Sentence_CS
            # Explanation

            intent = message[fc.intent]
            ack_cs = self.pick_ack_social_strategy() if fc.NLG_USE_ACKS_CS else None
            cs = self.pick_social_strategy() if fc.NLG_USE_CS else None
            tags = self.tags_explanation_types if intent == fc.inform_food else []

            # self.food = message['reco_food']
            if message['recipe']:
                self.recipe = message['recipe']
                recipe_card = self.get_recipe_card(self.recipe)

            # Sentence Planning
            #
            # Based on the strategies selected during the content planning, we generate the sentence.

            # if self.sentenceDB[message['intent']][cs]:
            #     # sentence = random.choice(self.sentenceDB[message['intent']][cs])
            #     sentence = self.choose_sentence(message[fc.intent], cs)
            # else:
                # sentence = random.choice(self.sentenceDB[message['intent']]['NONE'])
            sentence = self.choose_sentence(intent, cs=cs, tags_list=tags)
            # print("\n------\n")
            # print(sentence)
            # print("\n------\n")

            if fc.NLG_USE_ACKS:
                if message['user_intent']['intent'] in ["yes", "no"]:
                    valence = message['user_intent']['intent']
                elif message['user_intent']['entity_type']:
                    valence = "yes" if message['user_intent']['entity'] and (message['user_intent']['polarity'] == '+' or message['user_intent']['polarity'] == None) else "no"
                else:
                    valence = None
                current_intent = message[fc.intent] if message[fc.previous_intent] == fc.inform_food else None
                ack = self.choose_ack(previous_intent=message['previous_intent'], valence=valence, CS=None, current_intent=current_intent)
            else:
                ack = ""
            final_sentence = helper.capitalize_after_punctuation(self.replace(ack + " " + sentence))

            if message['recipe']:
                if recipe_card:
                    msg_to_send = self.msg_to_json(message['intent'], final_sentence, self.recipe['sourceUrl'], recipe_card)
                else:
                    msg_to_send = self.msg_to_json(message['intent'], final_sentence, self.recipe['sourceUrl'], None)
            else:
                msg_to_send = self.msg_to_json(intent=message['intent'], sentence=final_sentence, food_recipe=None, food_poster=None)

        if self.timeit_details:
            print("Response time treat_message: %.3f sec" % (time.time() - start))
        self.publish(msg_to_send)

    def create_recipe_card(self, recipe):
        # print(colored("in create_recipe_card for recipe " + recipe['id'].__str__(), "blue"))
        start = time.time()
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
        if self.timeit_details:
            print("Response time create_recipe_card: %.3f sec" % (time.time() - start))
        try:
            url = card_json['url']
            self.recipe_cards[recipe['id']] = url
            return url
        except KeyError as e:
            error_message = "Can't get recipe card! Error: " + e.__str__()
            # print(e)
            # print(card_json)
            log.warn(error_message)
            print(colored(error_message, "green"))
            return None

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
        start = time.time()
        potential_options = []
        for option in self.ackDB[previous_intent][valence][cs]:
            if "#entity" in option:
                if self.user_intent['entity']:
                    potential_options.append(option)
            else:
                potential_options.append(option)
        if potential_options:
            to_return = random.choice(potential_options)
        else:
            to_return = ""
        if self.timeit_details:
            print("Response time pick_ack: %.3f sec" % (time.time() - start))
        return to_return

    def replace_food(self, sentence, food_tag, food_key):
        start = time.time()
        if food_tag in sentence:
            if food_tag == "#mainfood":
                replace_with = self.get_random_ingredient_from_recipe(self.recipe)
            # else:
            #     replace_with = self.food[food_key]
            #     replace_with = replace_with.replace(" dish", "")
            sentence = sentence.replace(food_tag, replace_with)
        if self.timeit_details:
            print("Response time replace_food: %.3f sec" % (time.time() - start))
        return sentence

    def get_random_ingredient_from_recipe(self, recipe):
        start = time.time()
        ingredients = recipe["missedIngredients"] + recipe["usedIngredients"] #+ recipe["unusedIngredients"]
        if 'ingredients' in recipe.keys():
            ingredients += recipe["ingredients"]
        # chosen_ingredient = random.choice(ingredients)
        for ingredient in ingredients:
            if helper.string_contain_common_word(recipe['title'].lower(), ingredient["name"].lower()):
                return ingredient["name"]
        try:
            chosen_ingredient = random.choice(ingredients)
        except IndexError as e:
            # print("recipe", "ingredients")
            # print(recipe, ingredients)
            error_msg = "Can't find ingredients in recipe"
            log.warn(error_msg)
            print(colored(error_msg,"blue"))
            return recipe["seed_ingredient"]
            # raise e
        if self.timeit_details:
            print("Response time get_random_ingredient_from_recipe: %.3f sec" % (time.time() - start))
        return chosen_ingredient["name"]

    def replace_features(self, sentence):
        start = time.time()
        if "#features" in sentence:
            features_list = []
            if "comfort" in self.user_model['liked_features']:
                features_list.append("are in a bad mood")
            if "filling" in self.user_model['liked_features']:
                features_list.append("feel hungry")
            if "health" in self.user_model['liked_features']:
                features_list.append("want to eat healthy")
            if self.user_model[fc.intolerances]:
                features_list.append("are intolerant to " + self.user_model[fc.intolerances])
            if self.user_model[fc.special_diet]:
                features_list.append("are vegan")
            if self.user_model[fc.time_to_cook]:
                hours = math.floor(self.user_model[fc.time_to_cook] / 60)
                hours_str = "" if hours == 0 else helper.int_to_word(hours)
                if hours == 0:
                    hours_str += ""
                elif hours == 1:
                    hours_str += " hour"
                else :
                    hours_str += " hours"
                minutes = self.user_model[fc.time_to_cook] % 60
                minutes_str = "" if minutes == 0 else helper.int_to_word(minutes)
                if hours:
                    minutes_str = " " + minutes_str
                if minutes == 0:
                    minutes_str += ""
                elif minutes == 1:
                    minutes_str += " minute"
                else :
                    minutes_str += " minutes"
                duration_str = hours_str + minutes_str
                features_list.append("don't want to spend more than %s to cook" % duration_str)
            elif "time" in self.user_model['liked_features']:
                features_list.append("don't have much time to cook")
            else:
                features_list.append("have time to cook")
            features_string = ", ".join(features_list[:-1])
            if len(features_list) > 1:
                features_string += " and "
            features_string += features_list[-1]
            sentence = sentence.replace("#features", features_string)
        if self.timeit_details:
            print("Response time replace_features: %.3f sec" % (time.time() - start))
        return sentence


    def replace(self, sentence):
        start = time.time()
        sentence = self.replace_food(sentence, "#mainfood", 'main')
        # sentence = self.replace_food(sentence, "#secondaryfood", 'secondary')
        if "#situation" in sentence:
            sentence = sentence.replace("#situation", self.situation)
        if "#entity" in sentence:
            sentence = sentence.replace("#entity", self.user_intent['entity'])
        if "#usual_dinner" in sentence:
            usual_dinner_str = ', '.join(self.user_model[fc.usual_dinner])
            sentence = sentence.replace("#usual_dinner",  usual_dinner_str)
        if "#recipe" in sentence:
            sentence = sentence.replace("#recipe", self.recipe['title'])
        sentence = self.replace_features(sentence)
        if "#last_food" in sentence:
            if self.user_model['liked_food']:
                sentence = sentence.replace("#last_food", self.user_model['liked_food'][-1]['main'])
            else:
                sentence = "I know you did not accept any of my recommendations last time but did you eat something instead?"
        if "#user_name" in sentence:
            print("NLG here")
            if self.user_model[fc.user_name]:
                sentence = sentence.replace("#user_name", self.user_model[fc.user_name])
            else:
                sentence = sentence.replace(" #user_name", "")
        if self.timeit_details:
            print("Response time replace: %.3f sec" % (time.time() - start))
        return sentence


