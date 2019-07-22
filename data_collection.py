import whiteboard_client as wbc
import helper_functions as helper
import json
from ca_logging import log
import config_data_collection
import os.path



class DataCollector(wbc.WhiteBoardClient):
    def __init__(self, subscribes, publishes, clientid, ack_msg):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, name="DataCollector"+clientid, subscribes=subscribes, publishes=publishes)
        self.file_name = 'data_collection.json'
        self.conversation_count = 0
        self.data = dict()
        self.data[config_data_collection.DIALOG] = list()
        self.ack_msg = ack_msg
        self.n_q_anwers_msg = 0
        self.saved = False


    def treat_message(self, msg, topic):
        key = list(msg.keys())[0]
        if config_data_collection.DIALOG in msg.keys():
            self.data[config_data_collection.DIALOG].append(msg[config_data_collection.DIALOG])
        elif config_data_collection.ANSWERS in msg.keys():
            if config_data_collection.ANSWERS in self.data.keys():
                self.data[config_data_collection.ANSWERS] = {**self.data[config_data_collection.ANSWERS], **msg[config_data_collection.ANSWERS]}
            else:
                self.data[config_data_collection.ANSWERS] = msg[config_data_collection.ANSWERS]
        elif key in config_data_collection.ALL:
            self.data[key] = msg[key]
        else:
            log.warning("data collection module : don't know what to do with message!")


        if key in config_data_collection.TO_ACK:
            self.publish(self.ack_msg)

        if key == config_data_collection.ANSWERS:
            if self.n_q_anwers_msg == 0:
                self.n_q_anwers_msg += 1
            elif self.n_q_anwers_msg == 1:
                self.save()
            else:
                log.warn("Received too many answer-to-questionnaire messages (%d) Last ones are not saved." %  self.n_q_anwers_msg)


    def save(self):
        if not self.saved:
            content = []
            if os.path.isfile(self.file_name):
                with open(self.file_name, 'r') as infile:
                    content = json.load(infile)
            with open(self.file_name, 'w') as outfile:
                content.append(self.data)
                data_to_write = json.dumps(content, indent=4)
                # print(data_to_write)
                outfile.write(data_to_write)
            self.saved = True
            log.info("%s: data saved for data collection." % self.name)


    def stop_service(self):
        self.save()
        super().stop_service()

