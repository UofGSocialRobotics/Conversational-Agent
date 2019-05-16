import whiteboard_client as wbc
import random


class NLG(wbc.WhiteBoardClient):
    def __init__(self, name, msg_subscribe_type, msg_publish_type, whiteboard):
        wbc.WhiteBoardClient.__init__(self,name, msg_subscribe_type, msg_publish_type, whiteboard)

    def generate_idk_answers(self):
        possible_answers = ["I do not understand your question.", "Could you rephrase your question ? I can't understand.",\
                            "I'm very sorry for the inconvenience, but I don't understand your question. Feel free to ask something else.",\
                            "I seem to have trouble understanding your question. Maybe ask me something else ?"]
        return random.choice(possible_answers)

    def generate_positive_answer_to_fever_question(self,temperature):
        possible_answers = ["I'm sorry, your temperature is %.2f, you have fever." % temperature, \
                            "Yes, I'm sorry, your temperature is %.2f, you probably have a cold." % temperature,\
                            "Aaaah!! Your temperature is %.2f, you're probably contagious, stay away from me!!!" % temperature,\
                            "Go to the doctor!!!! Your temperature is %.2f!!!" % temperature]
        return random.choice(possible_answers)

    def generate_negative_answer_to_fever_question(self,temperature):
        possible_answers = ["It looks like you're fine, your temperature is %.2f." % temperature,\
                            "I think you're OK, as your temperature is %.2f" % temperature, \
                            "I'm delighted too tell you that you seem perfectly fine!!! Your temperature is %.2f" % temperature,\
                            "Your temperature is %.2f. Your are fine." % temperature]
        return random.choice(possible_answers)

    def treat_message(self, message, topic):
        if message == "DONT UNDERSTAND":
            new_message = self.generate_idk_answers()
        else:
            splited_msg = message.split(":")
            temperature = float(splited_msg[1].strip())
            if splited_msg[0] == "Yes":
                new_message = self.generate_positive_answer_to_fever_question(temperature)
            else :
                new_message = self.generate_negative_answer_to_fever_question(temperature)
        self.publish(new_message)

