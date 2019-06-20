import whiteboard_client as wbc
import helper_functions as helper
import json
import random
import food.food_config as food_config
import numpy


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
                    no_cs_dict = {'SD': [], 'VSN': [], 'PR': [], 'HE': [], 'NONE': [], 'QESD': []}
                    default_cs_dict = {'SD': [], 'VSN': [], 'PR': [], 'HE': [], 'NONE': [], 'QESD': []}
                    self.ackDB[line_input[0]] = {'yes': yes_cs_dict, 'no': no_cs_dict, 'default': default_cs_dict}
                self.ackDB[line_input[0]][line_input[4]][line_input[2]].append(line_input[3])

    def treat_message(self, msg, topic):
        message = json.loads(msg)
        self.user_model = message['user_model']
        self.user_intent = message['user_intent']
        self.food = message['food']

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
            else:
                if self.ackDB[message['previous_intent']]['default']:
                    ack = self.pick_ack(message['previous_intent'], 'default', ack_cs)
                else:
                    ack = ""
        else:
            ack = ""
        final_sentence = self.replace(ack + " " + sentence)

        msg_to_send = self.msg_to_json(final_sentence)
        self.publish(msg_to_send)


    def msg_to_json(self, sentence):
        frame = {'sentence': sentence}
        json_msg = json.dumps(frame)
        return json_msg

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
        print(potential_options)
        if potential_options:
            return random.choice(potential_options)
        else:
            return ""

    def replace(self, sentence):
        if "#food" in sentence:
            # movListString = ""
            # for mov in self.moviesList:
            #     movListString = movListString + " " + mov
            sentence = sentence.replace("#food", self.food)
        if "#plot" in sentence:
            if self.movie['plot']:
                sentence = sentence.replace("#plot", self.movie['plot'])
            else:
                sentence = "Sorry, I have no idea what this movie is about..."
        if "#actors" in sentence:
            if self.movie['actors']:
                sentence = sentence.replace("#actors", self.movie['actors'])
            else:
                sentence = "Sorry, I don't remember who plays in this one..."
        if "#genres" in sentence:
            if self.movie['genres']:
                sentence = sentence.replace("#genres", self.movie['genres'])
            else:
                sentence = "Sorry, I'm not sure about this movie's genres..."
        if "#entity" in sentence:
            sentence = sentence.replace("#entity", self.user_intent['entity'])
        if "#last_movie" in sentence:
            if self.user_model['liked_movies']:
                sentence = sentence.replace("#last_movie", self.user_model['liked_movies'][-1])
            else:
                sentence = "I know you did not accept any of my recommendations last time but did you watch something cool recently?"
        return sentence


if __name__ == "__main__":
    fake_msg = {'intent': 'inform(movie)', 'movie': 'John Wick: Chapter 3 – Parabellum'}
    json_msg = json.dumps(fake_msg)
    nlg = NLG("test_subscribe", "test_publishes", "test12345")
    nlg.treat_message(json_msg, "test")
