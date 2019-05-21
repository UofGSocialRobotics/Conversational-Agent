from ca_logging import log
import paho.mqtt.client as paho

def print_message(name,action,msg_txt,topic):
    log.info("%s: %-10s message: TOPIC = %-20s | CONTENT = %s" % (name,action,topic,msg_txt))

def append_c_to_elts(my_list,c):
    return [elt + c for elt in my_list]

def raise_error(client,error_msg,level):
    if level == paho.MQTT_LOG_WARNING:
        print_error_fct = log.warning
    elif level == paho.MQTT_LOG_ERR:
        print_error_fct = log.error
    else :
        return
    print_error_fct("%s: %s" % (client.name, error_msg))
    client.disconnect()
    exit(0)
