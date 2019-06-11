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

        self.user_model = None
        self.user_intent = None
        self.movie = None

        self.use_acks = True

        self.load_sentence_model(config.NLG_SENTENCE_DB)
        self.load_ack_model(config.NLG_ACK_DB)

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
                line_input = line.replace("\n", '')
                line_input = line_input.split(",")

                if self.ackDB.get(line_input[0]) is not None:
                    if self.ackDB[line_input[0]][line_input[4]]:
                        self.ackDB[line_input[0]][line_input[4]].append(line_input[3])
                    else:
                        self.ackDB[line_input[0]][line_input[4]].append(line_input[3])
                else:
                    self.ackDB[line_input[0]] = {'no': [], 'yes': [], 'default': []}
                    self.ackDB[line_input[0]][line_input[4]].append(line_input[3])

    def treat_message(self, msg, topic):
        message = json.loads(msg)
        sentence = random.choice(self.sentenceDB[message['intent']])
        self.movie = message['movie']
        self.user_model = message['user_model']
        self.user_intent = message['user_intent']
        if self.use_acks and message['previous_intent'] in self.ackDB:
            if "yes" in message['user_intent']['intent'] and self.ackDB[message['previous_intent']]['yes']:
                ack = self.pick_ack(message['previous_intent'], 'yes')
            elif "no" in message['user_intent']['intent'] and self.ackDB[message['previous_intent']]['no']:
                ack = self.pick_ack(message['previous_intent'], 'no')
            else:
                if self.ackDB[message['previous_intent']]['default']:
                    ack = self.pick_ack(message['previous_intent'], 'default')
                else:
                    ack = ""
        else:
            ack = ""
        final_sentence = self.replace(ack + " " + sentence)
        msg_to_send = self.msg_to_json(final_sentence, self.movie['poster'])
        self.publish(msg_to_send)

        # Todo Add explanations

    def msg_to_json(self, sentence, movie_poster):
        frame = {'sentence': sentence, 'movie_poster': movie_poster}
        json_msg = json.dumps(frame)
        return json_msg

    def pick_ack(self, previous_intent, valence):
        potential_options = []
        for option in self.ackDB[previous_intent][valence]:
            if "#entity" in option:
                if self.user_intent['entity']:
                    potential_options.append(option)
            else:
                potential_options.append(option)
        print(potential_options)
        return random.choice(potential_options)

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


if __name__ == "__main__":
    fake_msg = {'intent': 'inform(movie)', 'movie': 'John Wick: Chapter 3 – Parabellum'}
    json_msg = json.dumps(fake_msg)
    nlg = NLG("test_subscribe", "test_publishes", "test12345")
    nlg.treat_message(json_msg, "test")
