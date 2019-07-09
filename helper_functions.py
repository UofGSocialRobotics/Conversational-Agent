from ca_logging import log
import json
import random
import os

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


def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z


def identical(l1, l2):
    if len(l1) == len(l2):
        for i in range(len(l1)):
            if l1[i] != l2[i]:
                return False
        return True
    return False

