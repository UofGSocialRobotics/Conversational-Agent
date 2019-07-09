import whiteboard_client as wbc
import helper_functions as helper
import json
from ca_logging import log
import config_data_collection
import os.path



class AMT_info(wbc.WhiteBoardClient):
    def __init__(self, subscribes, publishes, clientid, ack_msg):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, name="AMT_info"+clientid, subscribes=subscribes, publishes=publishes)
        self.file_name = 'data_collection.json'
        self.conversation_count = 0
        self.data = dict()
        self.data[config_data_collection.DIALOG] = list()
        self.ack_msg = ack_msg
        self.saved = False


    def treat_message(self, msg, topic):
        key = list(msg.keys())[0]
        # if config_data_collection.AMT_ID in msg.keys():
        #     self.data[config_data_collection.AMT_ID] = msg[config_data_collection.AMT_ID]
        #     # print(self.amt_id)
        #     self.publish(self.ack_msg)
        # elif config_data_collection.ANSWERS in msg.keys():
        #     self.data[config_data_collection.ANSWERS] = msg[config_data_collection.ANSWERS]
        #     self.publish(self.ack_msg)
        if config_data_collection.DIALOG in msg.keys():
            self.data[config_data_collection.DIALOG].append(msg[config_data_collection.DIALOG])
        elif key in config_data_collection.ALL:
            self.data[key] = msg[key]
        else:
            log.warning("data collection module : don't know what to do with message!")

        if key in config_data_collection.TO_ACK:
            self.publish(self.ack_msg)

        if key == config_data_collection.ANSWERS:
            self.save()


    def save(self):
        if not self.saved:
            content = []
            if os.path.isfile(self.file_name):
                with open(self.file_name, 'r') as infile:
                    content = json.load(infile)
            with open(self.file_name, 'w') as outfile:
                content.append(self.data)
                data_to_write = json.dumps(content, indent=4)
                print(data_to_write)
                outfile.write(data_to_write)
            self.saved = True


    def stop_service(self):
        self.save()
        self.unsubscribe()
        self.service_started = False

