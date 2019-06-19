from ca_logging import log
import json
import random

def write_json(file_name,dictionary):
    with open(file_name, 'w') as fp:
        json.dump(dictionary, fp, indent=4)
    print('Wrote in '+file_name)

def write_yaml(file_name,dictionary):
    with open(file_name, 'w') as outfile:
        yaml.dump(dictionary, outfile, default_flow_style=False)
    print('Wrote in '+file_name)

def print_message(name,action,msg_txt,topic):
    log.info("%s: %-10s message: TOPIC = %-20s | CONTENT = %s" % (name,action,topic,msg_txt))

def append_c_to_elts(my_list,c):
    return [elt + c for elt in my_list]

def random_id():
    s = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM123456789"
    tmp = ''.join(random.sample(s,len(s)))
    id = tmp[:10]
    return id

# def raise_error(client,error_msg,level):
#     if level == paho.MQTT_LOG_WARNING:
#         print_error_fct = log.warning
#     elif level == paho.MQTT_LOG_ERR:
#         print_error_fct = log.error
#     else :
#         return
#     print_error_fct("%s: %s" % (client.name, error_msg))
#     client.disconnect()
#     exit(0)
