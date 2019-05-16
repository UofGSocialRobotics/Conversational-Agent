from ca_logging import log

def print_message(name,action,msg_txt,topic):
    log.info("%s: %-10s message: TOPIC = %-20s | CONTENT = %s"%(name,action,topic,msg_txt))
