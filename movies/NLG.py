import whiteboard_client as wbc
import helper_functions as helper
import json
import random
import movies.movie_config as movie_config
import numpy
import os.path

class NLG(wbc.WhiteBoardClient):
    def __init__(self, subscribes, publishes, clientid):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, "NLG" + clientid, subscribes, publishes)
        self.sentenceDB = {}
        self.ackDB = {}

        self.user_model = None
        self.user_intent = None
        self.movie = None

        self.load_sentence_model(movie_config.NLG_SENTENCE_DB)
        self.load_ack_model(movie_config.NLG_ACK_DB)

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
        self.movie = message['movie']
        self.user_model = message['user_model']
        self.user_intent = message['user_intent']
        explanation = ""
        # Content Planning
        #
        # Here we select the different strategies that will be used to deliver the content:
        # Ack + Ack_CS
        # Sentence_CS
        # Explanation

        if "movie" in message['intent'] and movie_config.NLG_USE_EXPLANATIONS:
            explanation_type = self.pick_explanation_type()
            if os.path.isfile(movie_config.GRAMMAR_PATH + explanation_type.lower() + ".gr"):
                explanation_builder = SentenceBuilder(movie_config.GRAMMAR_PATH + explanation_type.lower() + ".gr")
                explanation = explanation_builder.get_sentence()

        if movie_config.NLG_USE_ACKS_CS:
            ack_cs = self.pick_ack_social_strategy()

        if movie_config.NLG_USE_CS:
            cs = self.pick_social_strategy()

        # Sentence Planning
        #
        # Based on the strategies selected during the content planning, we generate the sentence.

        if self.sentenceDB[message['intent']][cs]:
            sentence = random.choice(self.sentenceDB[message['intent']][cs])
        else:
            sentence = random.choice(self.sentenceDB[message['intent']]['NONE'])

        if movie_config.NLG_USE_ACKS and message['previous_intent'] in self.ackDB:
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
        final_sentence = self.replace(ack + " " + sentence + " " + explanation)

        msg_to_send = self.msg_to_json(message['intent'], final_sentence, self.movie['poster'])
        self.publish(msg_to_send)


    def msg_to_json(self, intention, sentence, movie_poster):
        frame = {'intent': intention, 'sentence': sentence, 'image': movie_poster}
        json_msg = json.dumps(frame)
        return json_msg

    def pick_ack_social_strategy(self):
        #return random.choice(movie_config.CS_LABELS)
        return "NONE"

    def pick_social_strategy(self):
        #return random.choice(movie_config.CS_LABELS)
        return "NONE"

    def pick_explanation_type(self):
        expl_type = numpy.random.choice(movie_config.EXPLANATION_TYPE_LABELS, p=list(movie_config.EXPLANATION_TYPE_PROBA))
        if "MF" in expl_type:
            expl_type += "-" + numpy.random.choice(movie_config.MF_EXPLANATION_LABELS, p=list(movie_config.MF_EXPLANATION_PROBA))
        elif "TPO" in expl_type:
            expl_type += "-" + numpy.random.choice(movie_config.TPO_EXPLANATION_LABELS, p=list(movie_config.TPO_EXPLANATION_PROBA))
        elif "PO" in expl_type:
            expl_type += "-" + numpy.random.choice(movie_config.PO_EXPLANATION_LABELS, p=list(movie_config.PO_EXPLANATION_PROBA))
        elif "PE" in expl_type:
            expl_type += "-" + numpy.random.choice(movie_config.PE_EXPLANATION_LABELS, p=list(movie_config.PE_EXPLANATION_PROBA))
        else:
            expl_type = None
        return expl_type

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
        if "#title" in sentence:
            # movListString = ""
            # for mov in self.moviesList:
            #     movListString = movListString + " " + mov
            sentence = sentence.replace("#title", self.movie['title'])
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


class SentenceBuilder:
    def __init__(self, filename):
        self.grammar_dict = {}
        self.final_sentence = ""
        self.build_dict(filename)
        self.build_sentence("ROOT")

    def build_dict(self, filename):
        with open(filename) as f:
            for line in f:
                if not line.startswith("#") and not line.startswith("\n"):
                    line_input = line.split("\t", 2)
                    if self.grammar_dict.get(line_input[1]) is None:
                        self.grammar_dict[line_input[1]] = []
                    self.grammar_dict[line_input[1]].append(line_input[2])

    def build_sentence(self, key):
        RHS = random.choice(self.grammar_dict[key])
        words = RHS.split(' ')
        for word in words:
            word = word.replace('\n', '')
            if word in self.grammar_dict.keys():
                self.build_sentence(word)
            else:
                self.final_sentence += " " + word

    def get_sentence(self):
        return self.final_sentence


if __name__ == "__main__":
    fake_msg = {'intent': 'inform(movie)', 'movie': 'John Wick: Chapter 3 – Parabellum'}
    json_msg = json.dumps(fake_msg)
    nlg = NLG("test_subscribe", "test_publishes", "test12345")
    nlg.treat_message(json_msg, "test")
