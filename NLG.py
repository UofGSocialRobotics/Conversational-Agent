import whiteboard_client as wbc
import helper_functions as helper
import json
import random
import config

class NLG(wbc.WhiteBoardClient):
    def __init__(self, subscribes, publishes, clientid):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, "NLG"+clientid, subscribes, publishes)
        self.sentenceDB = {}
        self.ackDB = {}

        self.movie_title = ""

        self.load_sentence_model(config.NLG_SENTENCE_DB)
        self.load_ack_model(config.NLG_ACK_DB)

        # Do we generate acknowledgement?
        self.use_acks = False

    def load_sentence_model(self, path):
        with open(path) as f:
            for line in f:
                line_input = line.split(",")
                if self.sentenceDB.get(line_input[0]) is not None:
                    self.sentenceDB.get(line_input[0]).append(line_input[2])
                else:
                    self.sentenceDB[line_input[0]] = [line_input[2]]

    def load_ack_model(self, path):
        with open(path) as f:
            for line in f:
                line_input = line.split(",")
                if self.ackDB.get(line_input[0]) is not None:
                    self.ackDB.get(line_input[0]).append(line_input[2])
                else:
                    self.ackDB[line_input[0]] = [line_input[2]]

    def treat_message(self, msg, topic):
        message = json.loads(msg)
        sentence = random.choice(self.sentenceDB[message['intent']])
        self.movie_title = message['movies']['title']
        if self.use_acks:
            ack = random.choice(self.ackDB[message['intent']])
        else:
            ack = ""
        final_sentence = self.replace(ack + " " + sentence)
        self.publish(final_sentence)

        # Todo Add acks more smartly

        # Todo Add explanations

    def replace(self, sentence):
        # Todo: - Replace movie info (#plot, #actors, #genres, etc...)
        #  - Replace adjency pair (#actor, #director, #genre)
        if "#title" in sentence:
            # movListString = ""
            # for mov in self.moviesList:
            #     movListString = movListString + " " + mov
            sentence = sentence.replace("#title", self.movie_title.replace("?", "e"))
        return sentence



if __name__ == "__main__":
    fake_msg = {'intent': 'inform(movie)', 'movies': 'John Wick: Chapter 3 – Parabellum'}
    json_msg = json.dumps(fake_msg)
    nlg=NLG("test_subscribe", "test_publishes", "test12345")
    nlg.treat_message(json_msg,"test")
