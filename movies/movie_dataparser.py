import re
import json
import helper_functions as helper

def parse_dataset(fname):
    '''
    parses .datasets files
    :param fname: file name of dataset
    :return: dataset = list of tuples(utterance, target_formula)
    '''
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


def load_chatito_dataset(fname="resources/nlu/chatito_dataset.json"):
    dataset = list()
    with open(fname) as f:
        content = json.load(f)
    for formula in content.keys():
        elt_list = content[formula]
        for i, elt in enumerate(elt_list):
            utterance = elt[0]["value"]
            # if i <10:
            #     print(utterance)
            dataset.append([utterance, formula])

    return dataset




def load_dataset():

    # Ask genre, director, actor
    dataset = parse_dataset("resources/datasets/scenario1.dataset")
    # inform actor
    dataset += parse_dataset("resources/datasets/scenario2.dataset")
    dataset += parse_dataset("resources/datasets/scenario6.dataset")
    # greet / yes / no
    dataset += parse_dataset("resources/datasets/scenario3.dataset")
    # goodbye
    dataset += parse_dataset("resources/datasets/scenario4.dataset")
    # request more
    dataset += parse_dataset("resources/datasets/scenario5.dataset")
    # inform genre
    dataset += parse_dataset("resources/datasets/scenario7.dataset")
    # inform director
    dataset += parse_dataset("resources/datasets/scenario8.dataset")
    # yes/no
    dataset += parse_dataset("resources/datasets/scenario9.dataset")
    # Ask plot
    dataset += parse_dataset("resources/datasets/scenario10.dataset")
    # already watched
    dataset += parse_dataset("resources/datasets/scenario12.dataset")

    return dataset


def get_all_actors(actorfile="./movies/resources/nlu/actor2id.lexicon"):
    return get_all_cast(actorfile)



def get_all_directors(directorfile="./movies/resources/nlu/director2id.lexicon"):
    return get_all_cast(directorfile)


def get_all_cast(file):
    '''
    Parses files of cast members (actors and directors) --> builds a DB of actors and directors
    :param actorfile: actor2id.lexicon file
    :param directorfile: director2id.lexicon file
    :return: dictionnaires of actors / directors, where the keys are either "firstname lastname", "lastname firstname" of "lastname"
    '''
    with open(file) as f:
        content = f.readlines()

    firstnamelastname2id = dict()
    lastname2id = dict()
    lastnamefirstname2id = dict()

    for l in content:
        l_splited_dash = l.split("-")
        l_splited_underscore = l.split("_")
        firstnamelastname = l_splited_dash[0]
        lastname = l_splited_underscore[-1][:-1]
        x = firstnamelastname.split(" ")
        lastnamefirstname = " ".join(reversed(x))
        # id = l_splited_dash[-1][:-1]
        id = l_splited_dash[0]
        if len(firstnamelastname) > 3 and id != "meagan_good":
            firstnamelastname2id[firstnamelastname] = id
            lastname2id[lastname] = id
            lastnamefirstname2id[lastnamefirstname] = id

    cast_dicts = dict()
    cast_dicts["lastnamefirstname2id"] = lastnamefirstname2id
    cast_dicts["firstnamelastname2id"] = firstnamelastname2id
    cast_dicts["lastname2id"] =lastname2id

    return cast_dicts


if __name__ == "__main__":
    # parse_dataset("resources/datasets/scenario1.dataset")
    # get_all_cast("resources/nlu/actor2id.lexicon","resources/nlu/director2id.lexicon")
    parse_chatito_dataset()

