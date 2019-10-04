import whiteboard_client as wbc
from ca_logging import log
import helper_functions as helper



class HealthDiagnostic(wbc.WhiteBoardClient):
    def __init__(self, clientid, subscribes, publishes):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, name="HealthDiagnostic"+clientid, subscribes=subscribes, publishes=publishes)
        self.food_diagnostic_score = None


    def treat_message(self, msg, topic):
        if self.food_diagnostic_score is None:
            self.food_diagnostic_score = 0
            answers_dict = dict()
            for key, value in msg.items():
                if "question" in key:
                    answers_dict[int(key[len("question"):])] = int(value)
            answers_for_healthy_food = [value for key, value in answers_dict.items() if key <= 5]
            answers_for_non_healthy_food = [value for key, value in answers_dict.items() if key > 5]
            print(answers_dict, answers_for_healthy_food, answers_for_non_healthy_food)
            for a in answers_for_healthy_food:
                self.food_diagnostic_score += 1 * a
            for a in answers_for_non_healthy_food:
                self.food_diagnostic_score -= 1 * a
            self.food_diagnostic_score = float(self.food_diagnostic_score) / 50
            log.info("Health score is (%.2f)" % self.food_diagnostic_score)
            data = {"health_diagnostic_score": self.food_diagnostic_score}
            self.publish(data)
        else:
            log.debug("Already calculated health score (%.2f)" % self.food_diagnostic_score)
