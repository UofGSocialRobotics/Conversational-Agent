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

        self.moviesList = []

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
        print(message)
        sentence = random.choice(self.sentenceDB[message['intent']])
        self.moviesList = message['movies']
        sentence = self.replace(sentence)
        self.publish(sentence)

    def replace(self, sentence):
        if "#title" in sentence:
            movListString = ""
            for mov in self.moviesList:
                movListString = movListString + " " + mov
            sentence = sentence.replace("#title", movListString.replace("?", "e"))
        return sentence
