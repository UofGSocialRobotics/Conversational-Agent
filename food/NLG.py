import whiteboard_client as wbc
import helper_functions as helper
import json
import random
import food.food_config as food_config
import requests
from io import BytesIO


class NLG(wbc.WhiteBoardClient):
    def __init__(self, subscribes, publishes, clientid):
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

        self.load_sentence_model(food_config.NLG_SENTENCE_DB)
        self.load_ack_model(food_config.NLG_ACK_DB)

    def load_sentence_model(self, path):
        with open(path) as f:
            for line in f:
                line_input = line.split(",")
                if self.sentenceDB.get(line_input[0]) is None:
                    self.sentenceDB[line_input[0]] = {'SD': [], 'VSN': [], 'PR': [], 'HE': [], 'NONE': [], 'QESD': []}
                self.sentenceDB[line_input[0]][line_input[1]].append(line_input[2])

    def load_ack_model(self, path):
        with open(path) as f:
            for line in f:
                line = line.replace("\n", "")
                line_input = line.split(",")
                if self.ackDB.get(line_input[0]) is None:
                    yes_cs_dict = {'SD': [], 'VSN': [], 'PR': [], 'HE': [], 'NONE': [], 'QESD': []}
                    hungry_cs_dict = {'SD': [], 'VSN': [], 'PR': [], 'HE': [], 'NONE': [], 'QESD': []}
                    healthy_cs_dict = {'SD': [], 'VSN': [], 'PR': [], 'HE': [], 'NONE': [], 'QESD': []}
                    time_cs_dict = {'SD': [], 'VSN': [], 'PR': [], 'HE': [], 'NONE': [], 'QESD': []}
                    no_cs_dict = {'SD': [], 'VSN': [], 'PR': [], 'HE': [], 'NONE': [], 'QESD': []}
                    not_hungry_cs_dict = {'SD': [], 'VSN': [], 'PR': [], 'HE': [], 'NONE': [], 'QESD': []}
                    not_healthy_cs_dict = {'SD': [], 'VSN': [], 'PR': [], 'HE': [], 'NONE': [], 'QESD': []}
                    no_time_cs_dict = {'SD': [], 'VSN': [], 'PR': [], 'HE': [], 'NONE': [], 'QESD': []}
                    default_cs_dict = {'SD': [], 'VSN': [], 'PR': [], 'HE': [], 'NONE': [], 'QESD': []}
                    self.ackDB[line_input[0]] = {'yes': yes_cs_dict, 'no': no_cs_dict, 'hungry': hungry_cs_dict, 'not_hungry': not_hungry_cs_dict, 'healthy': healthy_cs_dict, 'not_healthy': not_healthy_cs_dict, 'time': time_cs_dict, 'no_time': no_time_cs_dict, 'default': default_cs_dict}
                self.ackDB[line_input[0]][line_input[4]][line_input[2]].append(line_input[3])

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

        if food_config.NLG_USE_ACKS_CS:
            ack_cs = self.pick_ack_social_strategy()

        if food_config.NLG_USE_CS:
            cs = self.pick_social_strategy()

        self.food = message['reco_food']
        if message['recipe']:
            self.recipe = message['recipe']
            recipe_card = self.create_recipe_card(self.recipe)

        # Sentence Planning
        #
        # Based on the strategies selected during the content planning, we generate the sentence.

        if self.sentenceDB[message['intent']][cs]:
            sentence = random.choice(self.sentenceDB[message['intent']][cs])
        else:
            sentence = random.choice(self.sentenceDB[message['intent']]['NONE'])

        if food_config.NLG_USE_ACKS and message['previous_intent'] in self.ackDB:
            if "yes" in message['user_intent']['intent'] and self.ackDB[message['previous_intent']]['yes']:
                ack = self.pick_ack(message['previous_intent'], 'yes', ack_cs)
            elif "no" in message['user_intent']['intent'] and self.ackDB[message['previous_intent']]['no']:
                ack = self.pick_ack(message['previous_intent'], 'no', ack_cs)
            elif message['user_intent']['entity_type'] and "hungry" in message['user_intent']['entity_type']:
                    if message['user_intent']['entity'] and self.ackDB[message['previous_intent']]['hungry']:
                        ack = self.pick_ack(message['previous_intent'], 'hungry', ack_cs)
                    elif not message['user_intent']['entity'] and self.ackDB[message['previous_intent']]['not_hungry']:
                        ack = self.pick_ack(message['previous_intent'], 'not_hungry', ack_cs)
            elif message['user_intent']['entity_type'] and "healthy" in message['user_intent']['entity_type']:
                    if message['user_intent']['entity'] and self.ackDB[message['previous_intent']]['healthy']:
                        ack = self.pick_ack(message['previous_intent'], 'healthy', ack_cs)
                    elif not message['user_intent']['entity'] and self.ackDB[message['previous_intent']]['not_healthy']:
                        ack = self.pick_ack(message['previous_intent'], 'not_healthy', ack_cs)
            elif message['user_intent']['entity_type'] and "time" in message['user_intent']['entity_type']:
                    if message['user_intent']['entity'] and self.ackDB[message['previous_intent']]['time']:
                        ack = self.pick_ack(message['previous_intent'], 'time', ack_cs)
                    elif not message['user_intent']['entity'] and self.ackDB[message['previous_intent']]['no_time']:
                        ack = self.pick_ack(message['previous_intent'], 'no_time', ack_cs)
            else:
                if self.ackDB[message['previous_intent']]['default']:
                    ack = self.pick_ack(message['previous_intent'], 'default', ack_cs)
                else:
                    ack = ""
        else:
            ack = ""
        final_sentence = self.replace(ack + " " + sentence)

        if message['recipe']:
            if recipe_card:
                msg_to_send = self.msg_to_json(message['intent'], final_sentence, self.recipe['sourceUrl'], recipe_card)
            else:
                msg_to_send = self.msg_to_json(message['intent'], final_sentence, self.recipe['sourceUrl'], None)
        else:
            msg_to_send = self.msg_to_json(intent=None, sentence=final_sentence, food_recipe=None, food_poster=None)
        self.publish(msg_to_send)

    def create_recipe_card(self, recipe):
        query = food_config.SPOONACULAR_API_VISUALIZE + food_config.SPOONACULAR_KEY

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
        #return random.choice(food_config.CS_LABELS)
        return "NONE"

    def pick_social_strategy(self):
        #return random.choice(food_config.CS_LABELS)
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
            features_string = ""
            if "comfort" in self.user_model['liked_features']:
                features_string = features_string + " are in a bad mood,"
            if "filling" in self.user_model['liked_features']:
                features_string = features_string + " feel hungry,"
            if "health" in self.user_model['liked_features']:
                features_string = features_string + " want to eat healthy,"
            if "time" in self.user_model['liked_features']:
                features_string = features_string + " and don't have much time to cook."
            else:
                features_string = features_string + " and still have time to cook."
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
