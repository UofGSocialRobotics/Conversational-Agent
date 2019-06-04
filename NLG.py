import whiteboard_client as wbc
import helper_functions as helper
import json
import random
import config


class NLG(wbc.WhiteBoardClient):
    def __init__(self, subscribes, publishes, clientid):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, "NLG" + clientid, subscribes, publishes)
        self.sentenceDB = {}
        self.ackDB = {}

        self.user_intent = None
        self.movie = None

        self.use_acks = False

        self.load_sentence_model(config.NLG_SENTENCE_DB)
        # Todo add basic acks
        # self.load_ack_model(config.NLG_ACK_DB)

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
                    if self.ackDB[line_input[0]][line_input[3]]:
                        self.ackDB[line_input[0]][line_input[3]].append(line_input[2])
                    else:
                        self.ackDB[line_input[0]][line_input[3]] = (line_input[2])
                else:
                    self.ackDB[line_input[0]][line_input[3]] = (line_input[2])

    def treat_message(self, msg, topic):
        message = json.loads(msg)
        sentence = random.choice(self.sentenceDB[message['intent']])
        self.movie = message['movie']
        self.user_intent = message['user_intent']
        if self.use_acks:
            if "yes" in msg['user_intent']:
                ack = random.choice(self.ackDB[message['previous_intent']]['yes'])
            elif "no" in msg['user_intent']:
                ack = random.choice(self.ackDB[message['previous_intent']]['no'])
            else:
                ack = random.choice(self.ackDB[message['previous_intent']][''])
        else:
            ack = ""
        final_sentence = self.replace(ack + " " + sentence)
        self.publish(final_sentence)

        # Todo Add acks more smartly

        # Todo Add explanations

    def replace(self, sentence):
        #  Todo Replace adjency pair (#entity)
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
            sentence = sentence.replace("#genres", self.user_intent['entity'])
        return sentence


if __name__ == "__main__":
    fake_msg = {'intent': 'inform(movie)', 'movie': 'John Wick: Chapter 3 – Parabellum'}
    json_msg = json.dumps(fake_msg)
    nlg = NLG("test_subscribe", "test_publishes", "test12345")
    nlg.treat_message(json_msg, "test")
