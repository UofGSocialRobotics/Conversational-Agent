from ca_logging import log
import json
import random
import re
import copy
import inflect

def write_json(file_name,dictionary):
    with open(file_name, 'w') as fp:
        json.dump(dictionary, fp, indent=4)
    log.debug('Wrote in '+file_name)

def int_to_word(n):
    return inflect.engine().number_to_words(n)

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
    if isinstance(msg_txt, list):
        if len(msg_txt) > 0:
            if "vegetarian" in msg_txt[0].keys():
                msg_to_print = list()
                for recipe in msg_txt:
                    msg_to_print.append(just_get_recipe_main_info(recipe))
        else:
            msg_to_print = ""

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
    if 'seed_ingredient' in new_dict.keys():
        new_dict['seed_ingredient'] = recipe_dict['seed_ingredient']
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
    # print(l1, l2)
    if len(l1) == len(l2):
        for i in range(len(l1)):
            if isinstance(l1[i], list) and isinstance(l2[i], list):
                if not identical_no_order(l1[i], l2[i]):
                    return False
            elif l1[i] != l2[i]:
                # if isinstance(l1[i], str) and isinstance(l2[i], str):
                #     return is_plural(l1[i], l2[i])
                return False
        return True
    return False

def is_plural(w1, w2):
    # print("checking for plurals")
    l1, l2 = len(w1), len(w2)
    if l1 > l2:
        tmp = w2
        w2 = w1
        w1 = tmp
        l1, l2 = len(w1), len(w2)
    # l1 <= l2
    print("pl, sing", w2, w1)
    if l1 + 1 == l2:
        if w2[-1] == "s" and w1 == w2[:-1]:
            return True
    return False

def identical_no_order(l1, l2):
    if len(l1) == len(l2):
        for i in range(len(l1)):
            if l1[i] not in l2:
                # print("can't find %s" % l1[i])
                # if word is plural, look for sing
                if l1[i][-1] == "s":
                    if l1[i][:-1] not in l2:
                        return False
                else:
                # if word is sing, look for pl
                    if l1[i]+"s" not in l2:
                        return False

    return True

def string_contain_common_word(string1, string2):
    d = {}
    for word in string1.split():
      d[word] = True
    for word in string2.split():
      if word in d.keys():
        return True
    return False

def capitalize_after_punctuation(text):
    punc_filter = re.compile('([.!?]\s*)')
    split_with_punctuation = punc_filter.split(text)
    final = ''.join([capitalize_first_word_in_str(i) for i in split_with_punctuation])
    return final

def capitalize_first_word_in_str(str):
    str_splited = str.split(" ")
    if len(str_splited) == 1:
        return str_splited[0].capitalize()
    else:
        return str_splited[0].capitalize() + " " + " ".join([w for w in str_splited[1:]])

def norm_pandas_matrix(matrix):
    mins_per_column = dict()
    maxs_per_column = dict()
    normed_matrix = copy.deepcopy(matrix)
    print(matrix.shape)
    lines, columns = matrix.shape
    for j in range(4, columns):
        mins_per_column[j] = 10
        maxs_per_column[j] = -10
    for i, row in matrix.iterrows():
        for j, elt in enumerate(row):
            # print(i, j)
            if j > 3:
                if elt < mins_per_column[j]:
                    mins_per_column[j] = elt
                if elt > maxs_per_column[j]:
                    maxs_per_column[j] = elt
    # matrix = copy.deepcopy(normed_matrix)
    i_init = None
    for i, row in matrix.iterrows():
        if not i_init:
            i_init = i
        for j, elt in enumerate(row):
            if j > 3:
                v = 2 * ((elt - mins_per_column[j]) / (maxs_per_column[j] - mins_per_column[j])) - 1
                normed_matrix.iat[i - i_init, j] = v

    return normed_matrix

def remove_duplicate_consecutive_char_from_string(s):
    new_s = " "
    for c in s:
        if new_s[-1] != c:
            new_s += c
    new_s = new_s.strip()
    return new_s
