import whiteboard_client as wbc
import helper_functions as helper
import json
import random

class NLG(wbc.WhiteBoardClient):
    def __init__(self, subscribes, publishes, clientid):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, "NLG"+clientid, subscribes, publishes)
        self.sentenceDB = {}
        self.load_model("./resources/nlg/sentence_db.csv")

        self.movie = ""

    def load_model(self, path):
        with open(path) as f:
            for line in f:
                line_input = line.split(",")
                if self.sentenceDB.get(line_input[0]) is not None:
                    self.sentenceDB.get(line_input[0]).append(line_input[2])
                else:
                    self.sentenceDB[line_input[0]] = [line_input[2]]

    def treat_message(self, msg, topic):
        message = json.loads(msg)
        sentence = random.choice(self.sentenceDB[message['intent']])
        self.movie = message['movies']
        sentence = self.set_movie_tile_in_sentence(sentence)
        self.publish(sentence)

    def set_movie_tile_in_sentence(self, sentence):
        if "#title" in sentence:
            # movListString = ""
            # for mov in self.moviesList:
            #     movListString = movListString + " " + mov
            sentence = sentence.replace("#title", self.movie.replace("?", "e"))
        return sentence

if __name__ == "__main__":
    fake_msg = {'intent': 'inform(movie)', 'movies': 'John Wick: Chapter 3 – Parabellum'}
    json_msg = json.dumps(fake_msg)
    nlg=NLG("test_subscribe", "test_publishes", "test12345")
    nlg.treat_message(json_msg,"test")
