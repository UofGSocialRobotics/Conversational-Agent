import json
import helper_functions as helper

def parse_voc(f_voc_shared = "./shared_resources/nlu/voc.json", f_domain_voc = None):
    with open(f_voc_shared) as json_file:
        data1 = json.load(json_file)
    if f_domain_voc:
        with open(f_domain_voc) as json_file:
            data2 = json.load(json_file)
        data = helper.merge_two_dicts(data1, data2)
    else:
        data = data1
    all_yes_words = list()
    # get all yes words in a single list
    for values in data["yes"]["yes_words"].values():
        all_yes_words += values
    data["yes"]["all_yes_words"] = all_yes_words
    # get all no words in a single list
    all_no_words = list()
    for values in data["no"].values():
        all_no_words.append(values)
    data["no"]["all_no_words"] = all_no_words
    all_bye_words = list()
    for values in data["bye"].values():
        all_bye_words.append(values)
    data["bye"]["all_bye_words"] = all_bye_words
    # print(data)
    return data
