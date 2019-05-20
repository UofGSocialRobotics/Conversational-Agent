from ca_logging import log

def print_message(name,action,msg_txt,topic):
    log.info("%s: %-10s message: TOPIC = %-20s | CONTENT = %s"%(name,action,topic,msg_txt))

def append_c_to_elts(my_list,c):
    return [elt + c for elt in my_list]
