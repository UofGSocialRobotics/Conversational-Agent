import json
import random
import requests
from io import BytesIO
from ca_logging import log
from termcolor import colored
import csv
from collections import namedtuple
import time
import math
import nltk.data
import config
import time

import food.food_config as fc
import whiteboard_client as wbc
import helper_functions as helper
import config


SentenceParameters = namedtuple("Sentence", [fc.intent, fc.cs, fc.tags])
AckParameters = namedtuple("Ack", [fc.previous_intent, fc.cs, fc.valence, fc.current_intent_should_not_be, fc.current_intent_should_be])


def html_emphasis(text):
    return "<b><i>" + text + "</b></i>"


class NLG(wbc.WhiteBoardClient):
    def __init__(self, clientid, subscribes, publishes, tags_explanation_types=[], cs=None, resp_time=False, delay=False, cut_message=False):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, "NLG" + clientid, subscribes, publishes, resp_time)
        self.tags_explanation_types = tags_explanation_types
        self.delay_bool = config.DELAY_MESSAGES
        self.cut_message_bool = config.CUT_MESSAGES
        self.sentenceDB = {}
        self.ackDB = {}

        self.user_model = None
        self.user_intent = None
        self.food = None
        self.recipes = None
        self.situation = None

        self.features_last_enumareted_on_turn = None

        self.load_sentence_model(fc.NLG_SENTENCE_DB)
        self.load_ack_model(fc.NLG_ACK_DB)
        self.timeit_details = False

        self.cs = cs

        # self.recipe_cards = dict()

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
        # print("Looking for ack with", previous_intent, valence, CS, current_intent)
        CS = self.cs
        if self.cs == "no_ack":
            return ""

        start = time.time()
        ack_params_list = self.ackDB.keys()
        key_res = [ack_params for ack_params in ack_params_list if ack_params.previous_intent == previous_intent]

        if CS:
            key_res = [ack_params for ack_params in key_res if ack_params.cs == CS]
        key_res_tmp = key_res
        if valence:
            key_res = [ack_params for ack_params in key_res if (valence in ack_params.valence)]
        elif valence == None:
            key_res = [ack_params for ack_params in key_res if ("NONE" in ack_params.valence)]
        if not key_res:
            key_res = key_res_tmp
            key_res = [ack_params for ack_params in key_res if (valence in ack_params.valence or ack_params.valence == "NONE")]
        if current_intent:
            key_res = [ack_params for ack_params in key_res if current_intent not in ack_params.current_intent_should_not_be]
            key_res = [ack_params for ack_params in key_res if (ack_params.current_intent_should_be == 'NONE' or current_intent in ack_params.current_intent_should_be)]

        if key_res and len(key_res) > 0:
            to_return = random.choice(self.ackDB[key_res[0]])
        else:
            error_message = "Could not find ack for previous_intent=" + previous_intent.__str__() + ", valence=" + valence.__str__() + ", CS=" + CS.__str__() + ", current_intent="+current_intent.__str__()
            log.warn(error_message)
            to_return = ""
        if self.timeit_details:
            print("Response time choose_ack: %.3f sec" % (time.time() - start))
        return to_return

    def get_recipe_card(self, recipe):
        rid = recipe['id']
        rid_no_slash = rid.replace('/', '')
        rid_no_slash = rid_no_slash.replace('-', '')
        return 'food/resources/img/recipe_card/small/PNGs/reduced' + rid_no_slash + 'html.png'

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
            self.user_intent = message['user_intent']
            self.situation = self.user_model['situation']

            intent = message[fc.intent]
            ack_cs = self.pick_ack_social_strategy() if fc.NLG_USE_ACKS_CS else None
            cs = self.pick_social_strategy() if fc.NLG_USE_CS else None
            tags = self.tags_explanation_types if intent == fc.inform_food else []

            # self.food = message['reco_food']
            self.recipes = None
            if message['recipes']:
                self.recipes = message['recipes']
                recipe_cards = list()
                for recipe in self.recipes:
                    recipe_cards.append(self.get_recipe_card(recipe))

            sentence = self.choose_sentence(intent, cs=cs, tags_list=tags)

            if fc.NLG_USE_ACKS:
                if message['user_intent']['intent'] in ["yes", "no"]:
                    valence = message['user_intent']['intent']
                elif message['user_intent']['entity_type'] == "duration":
                    valence = "yes" if message['user_intent']['entity'] > 30 else "no"
                elif message['user_intent']['entity_type']:
                    if message['user_intent']['entity_type'] == "hungry" or message['user_intent']['entity_type'] == "healthy":
                        valence = "yes" if message['user_intent']['entity'] > 0 else "no"
                    else:
                        valence = "yes" if message['user_intent']['entity'] and (message['user_intent']['polarity'] == '+' or message['user_intent']['polarity'] == None) else "no"
                else:
                    valence = None
                current_intent = message[fc.intent] if message[fc.previous_intent] == fc.inform_food else None
                ack = self.choose_ack(previous_intent=message['previous_intent'], valence=valence, CS=None, current_intent=current_intent)
            else:
                ack = ""
            #to avoid none type errors further down
            if not ack:
                ack = ""
            if not sentence:
                sentence = ""

            capitalize = True
            if self.recipes:

                capitalize = False

                if config.chi_study_comparison_mode == config.chi_study_no_comp or (len(self.recipes) == 1 and self.recipes[0]['identical_recipes']):
                    if config.chi_study_explanation_mode == config.chi_study_explanations:
                        sentence = self.generate_explanation_one_recipe()
                    elif config.chi_study_explanation_mode == config.chi_study_no_explanations:
                        sentence = "What do you think about " + self.recipes[0][fc.title] + "?"

                elif config.chi_study_comparison_mode == config.chi_study_comp_healthier or len(self.recipes) == 2:
                    if config.chi_study_explanation_mode == config.chi_study_explanations:
                        sentence = self.generate_explanation_pref_vs_healthier()
                    elif config.chi_study_explanation_mode == config.chi_study_no_explanations:
                        sentence = "What do you think about " + self.recipes[0][fc.title] + " or " + self.recipes[1][fc.title] + "?"

                elif config.chi_study_comparison_mode == config.chi_study_comp_bad_options and len(self.recipes) == 3:
                    if config.chi_study_explanation_mode == config.chi_study_explanations:
                        sentence = self.generate_explanation_bad_option()
                    elif config.chi_study_explanation_mode == config.chi_study_no_explanations:
                        sentence = "I have three otptions for you. What do you think about " + self.recipes[0][fc.title] + " or " + self.recipes[1][fc.title] + " or " + self.recipes[2]['title'] + "?"

                else:
                    raise ValueError("got %d recipes, and identical_recipes flag set to %s" % (len(self.recipes), self.recipes[0]['identical_recipes'].__str__()))

            final_sentence = self.replace(ack + " " + sentence)
            if capitalize:
                final_sentence = helper.capitalize_after_punctuation(final_sentence)

            if message['recipes']:
                recipes = self.recipes
                if not recipe_cards:
                    recipe_cards = None
                # ingredients_list = message[fc.ingredients]
            else:
                recipes, recipe_cards, ingredients_list = None, None, None
                # msg_to_send = self.msg_to_json(intent=message['intent'], sentence=final_sentence, food_recipe=None, food_poster=None)
            # msg_to_send = self.msg_to_json(intent=message['intent'], message=final_sentence, food_recipe=recipe, food_poster=recipe_card, ingredients_list=ingredients_list)
            msg_to_send = self.msg_to_json(intent=message['intent'], message=final_sentence, food_recipe=recipes, food_poster=recipe_cards, ingredients_list=None)

        if self.timeit_details:
            print("Response time treat_message: %.3f sec" % (time.time() - start))
        self.publish(msg_to_send)



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
        # start = time.time()
        # if food_tag in sentence:
        #     if food_tag == "#mainfood":
        #         replace_with = self.get_random_ingredient_from_recipe(self.recipe)
        #     # else:
        #     #     replace_with = self.food[food_key]
        #     #     replace_with = replace_with.replace(" dish", "")
        #     sentence = sentence.replace(food_tag, replace_with)
        # if self.timeit_details:
        #     print("Response time replace_food: %.3f sec" % (time.time() - start))
        return sentence


    def get_random_ingredient_from_recipe(self, recipe):
        # TODO: rewrite function to work with local KBRS
        return "chicken"


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
            if len(self.user_model[fc.usual_dinner])>1:
                usual_dinner_str = ', '.join(self.user_model[fc.usual_dinner][:-1]) + " or " + self.user_model[fc.usual_dinner][-1]
                sentence = sentence.replace("#usual_dinner",  usual_dinner_str)
            elif len(self.user_model[fc.usual_dinner])==1:
                usual_dinner_str = self.user_model[fc.usual_dinner][0]
                sentence = sentence.replace("#usual_dinner", usual_dinner_str)
            else:
                usual_dinner_str = "that"
                sentence = sentence.replace("#usual_dinner", usual_dinner_str)
        if "#recipe" in sentence:
            # print(colored(sentence, 'blue'))
            # print(colored(self.recipe, 'blue'))
            sentence = sentence.replace("#recipe", self.recipes[0]['title'])
        sentence = self.replace_features(sentence)
        if "#last_food" in sentence:
            if self.user_model['liked_food']:
                sentence = sentence.replace("#last_food", self.user_model['liked_food'][-1]['main'])
            else:
                sentence = "I know you did not accept any of my recommendations last time but did you eat something instead?"
        if "#user_name" in sentence:
            if self.user_model[fc.user_name]:
                sentence = sentence.replace("#user_name", self.user_model[fc.user_name])
            else:
                sentence = sentence.replace(" #user_name", "")
        if self.timeit_details:
            print("Response time replace: %.3f sec" % (time.time() - start))
        sentence = sentence.strip()
        return sentence


    def generate_explanation_relaxed_constraints(self, recipe, r_to_compare_with=None, positive_phrasing=True):
        relaxed_constraint_str = recipe['relaxed_constraints'].replace("time2","TWO")
        if r_to_compare_with and r_to_compare_with['relaxed_constraints']:
            constraints_to_eliminate = r_to_compare_with['relaxed_constraints'].replace("time2","TWO").split("+")
            for c in constraints_to_eliminate:
                relaxed_constraint_str = relaxed_constraint_str.replace(c, "")
                relaxed_constraint_str = relaxed_constraint_str.replace("++", "+")
                if relaxed_constraint_str and relaxed_constraint_str[0] == "+":
                    relaxed_constraint_str = relaxed_constraint_str[1:]
                if relaxed_constraint_str and relaxed_constraint_str[-1] == "+":
                    relaxed_constraint_str = relaxed_constraint_str[:-1]
        if relaxed_constraint_str:
            relaxed_constraint_str = relaxed_constraint_str.replace("keto", "ketonic")
            relaxed_constraint_str = relaxed_constraint_str.replace("low_cal", "low calory")
            relaxed_constraint_str = relaxed_constraint_str.replace("_", "")
            relaxed_constraints_list = relaxed_constraint_str.split('+')
            if positive_phrasing:
                explanation = html_emphasis(recipe['title']) + " corresponds to your preferences except that"
            else:
                explanation = " but"
            args_list = list()
            missing_liked_ingredients = list()
            added_disliked_ingredients = list()
            for constraint in relaxed_constraints_list:
                if "time2" == constraint:
                    args_list.append(" it takes longer to prepare")
                elif "time" == constraint:
                    args_list.append(" it takes a bit longer to prepare")
                elif constraint in ["vegan", "vegetarian", "pescetarian", 'dairy free', 'gluten free']:
                    args_list.append(" it is not " + constraint)
                elif constraint in ["keto", "low cal"]:
                    args_list.append(" it does not correspond to a " + constraint + " diet")
                else:
                    if constraint in self.user_model[fc.liked_food]:
                        missing_liked_ingredients.append(constraint)
                    elif constraint in self.user_model[fc.disliked_food]:
                        added_disliked_ingredients.append(constraint)
                    else:
                        print(colored("Don't know what to do with %s" % constraint, "red"))
            if missing_liked_ingredients:
                missing_ingredients_str = " it does not contain "
                if len(missing_liked_ingredients) == 1:
                    missing_ingredients_str += missing_liked_ingredients[0]
                else:
                    missing_ingredients_str += ", ".join(missing_liked_ingredients[:-1]) + " or " + missing_liked_ingredients[-1]
                args_list.append(missing_ingredients_str)
            if added_disliked_ingredients:
                added_ingredients_str = " it contains "
                if len(added_disliked_ingredients) == 1:
                    added_ingredients_str += added_disliked_ingredients[0]
                else:
                    added_ingredients_str += ", ".join(added_disliked_ingredients[:-1]) + " and " + added_disliked_ingredients[-1]
                args_list.append(added_ingredients_str)

            if len(args_list) == 1:
                explanation += args_list[0]
            elif len(args_list) > 1:
                explanation += "; ".join(args_list[:-1]) + " and" + args_list[-1]
            return explanation
        return ""


    def generate_explanation_one_recipe(self):
        if self.recipes:
            recipe = self.recipes[0]
            explanation = self.generate_explanation_relaxed_constraints(recipe)

            if explanation:
                explanation += "; but it is healthier than other options (contains less fat, sugar or salt)."
                explanation += " What do you think?"

            else:
                explanation = recipe[fc.title] + " is the healthiest recipe corresponding to your preferences! What do you think?"

            return explanation


    def generate_comparison_pref_vs_healtier(self, pref_recipe, healthier_recipe):
        explanation =  html_emphasis(pref_recipe[fc.title]) + " best matches your preferences but " + html_emphasis(healthier_recipe[fc.title]) + " is healthier, " #. What do you think?"
        r1_has_less_than_r2 = helper.compare_fat_sugar_salt(healthier_recipe, pref_recipe)
        if r1_has_less_than_r2:
            if len(r1_has_less_than_r2) == 1:
                explanation += "as it contains less " + r1_has_less_than_r2[0]
            else:
                explanation += "as it contains less " + ", ".join(r1_has_less_than_r2[:-1]) + " and " + r1_has_less_than_r2[-1]
        explanation = explanation.replace("total fat", "fat")
        explanation = explanation.replace("sodium", "salt")
        return explanation


    def generate_explanation_pref_vs_healthier(self):
        if self.recipes:
            if self.recipes[0][fc.reco_mode] == fc.reco_mode_pref:
                healthier_recipe = self.recipes[1]
                pref_recipe = self.recipes[0]
            else:
                healthier_recipe = self.recipes[0]
                pref_recipe = self.recipes[1]
            explanation = self.generate_comparison_pref_vs_healtier(pref_recipe, healthier_recipe)
            explanation += ". What do you think?"
            return explanation

    def generate_explanation_bad_option(self):
        if self.recipes:
            explanation = self.generate_comparison_pref_vs_healtier(self.recipes[0], self.recipes[1])
            print(explanation)
            explanation += ". " + html_emphasis(self.recipes[2]['title']) \
                           + " is also healthier" \
                           + self.generate_explanation_relaxed_constraints(self.recipes[2], r_to_compare_with=self.recipes[1], positive_phrasing=False)
            explanation += ". What do you think?"
            return explanation




    def cut_message(self, message):
        tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
        return tokenizer.tokenize(message)


    def delay_answer(self, sentence):
        setence_wo_spaces = sentence.replace(" ", '')
        n_char = len(setence_wo_spaces)
        delay = float(n_char) * 60 / config.DELAY_ANSWER_N_CHAR_PER_MINUTE
        return delay
        # print("Delaying answer by %.2f sec" % delay)
        # time.sleep(delay)


    def msg_to_json(self, intent, message, food_recipe, food_poster, ingredients_list):
        if self.cut_message_bool:
            sentences = self.cut_message(message)
            sentences_and_delays = list()
            for sentence in sentences:
                delay = self.delay_answer(sentence) if self.delay_bool else 0
                sentences_and_delays.append({'sentence': sentence, 'delay': delay})
            return self.single_msg_to_json(intent, sentences_and_delays, food_recipe, food_poster, ingredients_list)
        else:
            delay = 0
            if self.delay_bool:
                delay = self.delay_answer(message)
            return self.single_msg_to_json(intent, [{'sentence': message, 'delay': delay}], food_recipe, food_poster, ingredients_list)

    def single_msg_to_json(self, intent, sentences_and_delays, food_recipes, food_posters, ingredients_list):
        if food_recipes and food_posters:
            if len(food_recipes) != len(food_posters):
                raise AttributeError("We should have the same number of recipes and of posters! (got %d and %d)" % (len(food_recipes), len(food_posters)))
        # recipes_data = list()
        rids, titles, utilities, cf_scores, relaxed_constraints = list(), list(), list(), list(), list()
        if food_recipes:
            for i, recipe in enumerate(food_recipes):
                rids.append(recipe['id'])
                titles.append(recipe['title'])
                utilities.append(recipe['utility'])
                cf_scores.append(recipe['cf_score'].__str__())
                relaxed_constraints.append(recipe['relaxed_constraints'])
        frame = {'intent': intent,
                 'sentences_and_delays': sentences_and_delays,
                 'recipe_cards': food_posters,
                 'rids': rids,
                 'titles': titles,
                 'utilities': utilities,
                 'cf_scores': cf_scores,
                 'relaxed_constraints': relaxed_constraints,
                 fc.ingredients: ingredients_list}
        return frame
