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
                last = content[-1] if len(content) > 0 else None
                try:
                    if last and last["client_id"] == self.data["client_id"]:
                        # self.data = {**last, **self.data} #merge 2 dicts
                        self.update_data(last, self.data)
                        content[-1] = self.data
                    else:
                        content.append(self.data)
                except:
                    log.debug("Error while trying to merge data")
                    content.append(self.data)
                data_to_write = json.dumps(content, indent=4)
                # print(data_to_write)
                outfile.write(data_to_write)
            self.saved = True
            log.info("%s: data saved for data collection." % self.name)


    @staticmethod
    def update_data(data_old, data_new):
        for key_new, value_new in data_new:
            if key_new in data_old.keys():
                if isinstance(value_new, list):
                    data_old[key_new] = data_old[key_new] + value_new
                elif isinstance(value_new, dict):
                    data_old[key_new] = {**data_old[key_new], **value_new}
                else:
                    data_old[key_new] = value_new
            else:
                data_old[key_new] = value_new
        return data_old




    def stop_service(self):
        self.save()
        super().stop_service()

