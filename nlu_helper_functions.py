import string
import re
import nltk
from fuzzywuzzy import fuzz
####################################################################################################
##                                          Preprocesss                                           ##
####################################################################################################


def preprocess(sentence):
    s = sentence.lower()
    s = s.replace(" don t ", " don't ")
    # s = s.replace("'s", " 's")
    return s


def flatten_sentence(sentence):
    '''
    :param sentence:
    :return: sentence with no CAPS and no punctuation
    '''
    s = sentence.translate(str.maketrans('', '', string.punctuation))
    s = re.sub(' +', ' ', s)
    return s.lower()


####################################################################################################
##                                      Helper functions                                          ##
####################################################################################################


def is_verb(token):
    '''
    Returns True if token is a verb or aux
    :param token: spacy document-->token
    :return: bool
    '''
    if "VB" in token.tag_ or token.tag_ == "MD":
        return True
    else:
        return False


def is_negation(token, voc_no):
    return (token.lemma_ in voc_no or (token.tag_ == "RB" and token.dep_ == "neg"))


def find_key_in_dict_with_fuzzy_matching(k,d):
    '''
    Uses fuzzy mathcing to find a key in a dictionary
    :param k: key to find
    :param d: dictionay in which to loo for k
    :return: d[k] if k in d or False
    '''
    best_score = 85
    best_id = False
    if k != 'no thanks' and k!= "thanks":
        for key, id in d.items():
            if key == k:
                return id
            else:
                score = fuzz.token_sort_ratio(key, k)
                if score > best_score:
                    best_score = score
                    best_id = id
    # print(best_id,best_score)
    return best_id



def get_NE_Person(capitalized_doc):
    '''
    Using Spacy NER to get Persons from document
    :param capitalized_doc: Takes a document created from a capitalized sentence (i.e. all words have their 1st letter CAP) because spcay NER fails with lowercases.
    :return: list or persons
    '''
    # [print(x) for x in capitalized_doc]
    verbs = [x.text for x in capitalized_doc if is_verb(x)]
    if capitalized_doc.ents and len(capitalized_doc.ents) > 0:
        persons = [X.text for X in capitalized_doc.ents if X.label_ == "PERSON"]
        persons_cleaned = list()
        if len(verbs)>0:
            for p in persons:
                words = p.split()
                # print(words)
                p_cleaned = " ".join([w for w in words if w not in verbs])
                # actor_cleaned = actor_cleaned.replace("'s", "")
                persons_cleaned.append(p_cleaned)
        else:
            persons_cleaned = persons
        # print(actors_cleaned)
        persons_cleaned = [a.lower() for a in persons_cleaned]
        persons_cleaned = [a.replace("'s", '') for a in persons_cleaned]
        return persons_cleaned


def get_NNs(document):
    '''
    Used to get NNs --> try to extract Persons if NER fails.
    If several words in a row are NNs, create just one entiry out of them
    :param document: spacy document
    :return: list of nouns
    '''
    NNs = list()
    i, max = 0, len(document)
    while i < max:
        token = document[i]
        if "NN" in token.tag_:
            j = i + 1
            nn = token.text.lower()
            while j < max:
                next = document[j]
                if "NN" in next.tag_:
                    nn += " " + next.text.lower()
                    j += 1
                else :
                    j += 1
                    break
            NNs.append(nn)
            i = j
        else:
            i += 1
    return NNs

####################################################################################################
##                                          Get intents                                           ##
####################################################################################################

## ---------------------------------------- Bool functions -------------------------------------- ##

def is_greeting(document, voc_greetings):
    '''
    Determines if intent is greeting
    :param document: spacy document
    :param voc_greetings: list of greeting words
    :return: bool
    '''
    for token in document:
        if token.text in voc_greetings:
            return ("greeting", None, None, None)


def is_goodbye(document, sentence, voc_bye):
    '''
    Determines if intent is goodbye
    :param document: spacy document
    :param sentence: string
    :param voc_bye: dictionary of words used to say bye (see resources/nlu/voc.json)
    :return: bool
    '''
    goodbye = ("bye", None, None, None)
    for token in document:
        if token.text in voc_bye["bye_1word"]:
            return goodbye
    if len(sentence) > 1:
        bigrams = nltk.bigrams(sentence.split())
        for bg in bigrams:
            bg_text = ' '.join(bg)
            if bg_text in voc_bye["bye_2words"]:
                return goodbye
    if len(sentence) > 3:
        fourgrams = nltk.ngrams(sentence.split(), 4)
        for fg in fourgrams:
            fg_text = ' '.join(fg)
            if fg_text in voc_bye["bye_4words"]:
                return goodbye
    return False


## ---------------------------------------- Non-bool functions ---------------------------------------- ##

def is_yes_no(document, sentence, voc_yes, voc_no):
    res = {"yes": ("yes", None, None, None), "no": ("no", None, None, None)}
    """
    Determines if intent is yes/no
    :param document: spacy document
    :param sentence: string
    :param voc_yes: dictionary of yes words (see resources/nlu/voc.json)
    :param voc_no: dictionary of no words (see resources/nlu/voc.json)
    :return: yes/no/false
    """
    sentence = flatten_sentence(sentence)
    first_word = document[0]
    if sentence in voc_yes["all_yes_words"]:
        return res["yes"]
    if sentence in voc_no["all_no_words"]:
        return res["no"]
    if first_word.text in voc_no["no_1word"]:
        return res["no"]
    if len(document)>1 and document[1].text in voc_no["no_1word"]:
        return res["no"]
    if len(sentence) > 2:
        bigrams = nltk.bigrams(sentence.split())
        for bg in bigrams:
            bg_text = ' '.join(bg)
            if bg_text in voc_no["no_2words"]:
                return res["no"]
            elif bg_text in voc_yes["yes_words"]["yes_2words"]:
                return res["yes"]
    if len(sentence) > 3:
        trigrams = nltk.trigrams(sentence)
        for tg in trigrams:
            tg_text = ' '.join(tg)
            if tg_text in voc_no["no_3words"]:
                return res["no"]
    is_positive = None
    for token in document:
        if (token.text in voc_yes["all_yes_words"] or token.text in voc_yes["yes_vb"]) and is_positive == None:
            is_positive = True
        elif is_negation(token, voc_no=voc_no["all_no_words"]):
            return res["no"]
    if is_positive == True:
        return res["yes"]


def format_formula(formula):
    intent, entity, entitytype, polarity = "", "", "", ""
    if "ask" in formula or formula in ["greet", "yes", "no", "goodbye", "request_more", "alreadyWatched", "IDK"]:
        intent = formula
    elif "inform" in formula:
        if "cast" in formula:
            intent = "inform"
            entitytype = "cast"
            entity = ' '.join(formula.split()[2:])[:-1]
            polarity = "+"
        elif "genre" in formula:
            intent = "inform"
            entitytype = "genre"
            entity = formula.split()[2][:-1]
            polarity = "+"

    return intent, entity, entitytype, polarity
