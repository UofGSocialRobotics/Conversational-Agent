import re


def parse_dataset(fname):
    dataset = list()
    with open(fname) as f:
        content = f.readlines()
    # you may also want to remove whitespace characters like `\n` at the end of each line
    content = [x.strip() for x in content]

    x = 0
    for line in content:
        if x % 4 == 1:
            utterance = re.findall('"([^"]*)"', line)[0]
            # print(utterance)
        if x % 4 == 2:
            s = line.strip()[1:-1]
            s = s.split(' ', 1)[1]
            formula = s[1:-1]
            # print(formula)
            # formula = formula.replace("_iii_", "_")
            # formula = formula.replace("_ii_", "_")
            # formula = formula.replace("_i_", "_")
            # formula = formula.replace("_v_", "_")
            formula = formula.replace('"', "")
            formula = formula.replace("inform (actor", "inform (cast")
            formula = formula.replace("inform (director", "inform (cast")
            dataset.append([utterance, formula])
        x += 1

    return dataset


def get_lastnames2ids(fname):
    names2ids = dict()
    with open(fname) as f:
        content = f.readlines()
    for l in content:
        l_splited_underscore = l.split("_")
        l_splited_dash = l.split("-")
        last_name = l_splited_underscore[-1][:-1]
        id = l_splited_dash[-1][:-1]
        if len(last_name) > 3 and id != "meagan_good":
            names2ids[last_name] = id
    # print(names2ids)
    return names2ids

def get_firstnamelastname2ids(fname):
    names2ids = dict()
    with open(fname) as f:
        content = f.readlines()
    for l in content:
        # l_splited_underscore = l.split("_")
        l_splited_dash = l.split("-")
        firstnamelastname = l_splited_dash[0]
        id = l_splited_dash[-1][:-1]
        if len(firstnamelastname) > 3 and id != "meagan_good":
            # print(firstnamelastname, id)
            names2ids[firstnamelastname] = id
    # print(names2ids)
    return names2ids

def get_lastnamefirstname2ids(fname):
    names2ids = dict()
    with open(fname) as f:
        content = f.readlines()
    for l in content:
        # l_splited_underscore = l.split("_")
        l_splited_dash = l.split("-")
        firstnamelastname = l_splited_dash[0]
        x = firstnamelastname.split(" ")
        lastnamefirstname = " ".join(reversed(x))
        id = l_splited_dash[-1][:-1]
        if len(lastnamefirstname) > 3 and id != "meagan_good":
            names2ids[lastnamefirstname] = id
    return names2ids

def get_all_cast():
    cast_dicts = dict()
    cast_dicts["lastnamefirstname2id"] = dict(get_lastnamefirstname2ids("resources/nlu/actor2id.lexicon"), **get_lastnamefirstname2ids("resources/nlu/director2id.lexicon"))
    cast_dicts["firstnamelastname2id"] = dict(get_firstnamelastname2ids("resources/nlu/actor2id.lexicon"), **get_firstnamelastname2ids("resources/nlu/director2id.lexicon"))
    cast_dicts["lastname2id"] = dict(get_lastnames2ids("resources/nlu/actor2id.lexicon"), **get_lastnames2ids("resources/nlu/director2id.lexicon"))
    return cast_dicts


if __name__ == "__main__":
    # parse_dataset("resources/datasets/scenario1.dataset")
    get_all_cast()
