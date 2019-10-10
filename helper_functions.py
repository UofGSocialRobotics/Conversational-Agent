from ca_logging import log
import json
import random
import os
import copy

def write_json(file_name,dictionary):
    with open(file_name, 'w') as fp:
        json.dump(dictionary, fp, indent=4)
    log.debug('Wrote in '+file_name)


def print_message(name,action,msg_txt,topic):
    msg_to_print = copy.deepcopy(msg_txt)
    # print(type(msg_txt))
    if isinstance(msg_txt,dict) and "intent" in msg_txt.keys():
        if "user_model" in msg_txt.keys():
            msg_to_print['user_model']['liked_recipe'] = get_new_recipe_list_with_main_info_only(msg_txt['user_model']['liked_recipe'])
            msg_to_print['user_model']['disliked_recipe'] = get_new_recipe_list_with_main_info_only(msg_txt['user_model']['disliked_recipe'])
        if "recipe" in msg_txt.keys() and msg_to_print["recipe"]:
            # print(msg_txt["recipe"])
            msg_to_print["recipe"] = just_get_recipe_main_info(msg_txt["recipe"])

    log.info("%s: %-10s message: TOPIC = %-20s | CONTENT = %s" % (name,action,topic,msg_to_print))

def get_new_recipe_list_with_main_info_only(recipe_list):
    new_list = list()
    for recipe in recipe_list:
        new_list.append(just_get_recipe_main_info(recipe))
    return new_list

def just_get_recipe_main_info(recipe_dict):
    new_dict = dict()
    # print(recipe_dict)
    new_dict["title"] = recipe_dict['title']
    new_dict['vegan'] = recipe_dict['vegan']
    new_dict['spoonacularSourceUrl'] = recipe_dict['spoonacularSourceUrl']
    new_dict["..."] = "..."
    return new_dict


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

def string_contain_common_word(string1, string2):
    d = {}
    for word in string1.split():
      d[word] = True
    for word in string2.split():
      if word in d.keys():
        return True
    return False
