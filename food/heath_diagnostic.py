import whiteboard_client as wbc
from ca_logging import log
import helper_functions as helper
import food.food_config as fc



class HealthDiagnostic(wbc.WhiteBoardClient):
    def __init__(self, clientid, subscribes, publishes, resp_time=False):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, name="HealthDiagnostic"+clientid, subscribes=subscribes, publishes=publishes, resp_time=resp_time)
        self.food_diagnostic_score = None


    def treat_message(self, msg, topic):
        if self.food_diagnostic_score is None:
            self.food_diagnostic_score = 0
            answers_dict = dict()
            h, f, c = 0, 0, 0
            for key, value in msg.items():
                if "question" in key:
                    answers_dict[int(key[len("question"):])] = int(value)
            for key, value in answers_dict.items():
                if key == 1: # broccoli
                    h += value
                elif key == 2: # Chips
                    h -= value
                elif key == 3: # carrots
                    h += value
                elif key == 4: # pizza
                    h -= value
                    f += value
                    c += value
                elif key == 5: # tomatoes
                    f -= value
                    c -= value
                elif key == 6: # pasta
                    f += value
                    c += value
                elif key == 7: # lettuce
                    f -= value
                    c -= value

            h, f, c = float(h) / 50, float(f) / 50, float(c) / 60
            log.info("Food diagnostic, user trait values are: healthiness %.3f, fillingness %.3f, confort %.3f" % (h, f, c))
            self.food_diagnostic_score = [h, f, c]
            data = {fc.food_scores_trait: {fc.healthiness: h, fc.food_fillingness: f, fc.comfort: c}}
            self.publish(data)
        else:
            log.debug("Already calculated health score (%.2f)" % self.food_diagnostic_score)
