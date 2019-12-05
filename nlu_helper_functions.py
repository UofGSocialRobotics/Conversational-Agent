import string
import re
import nltk
from fuzzywuzzy import fuzz
from ca_logging import log
import helper_functions as helper
####################################################################################################
##                                          Preprocesss                                           ##
####################################################################################################


def preprocess(sentence):
    s = sentence.lower()
    s = s.replace(" don t ", " don't ")
    s = s.replace(" dont ", " don't ")

    if "1/2" in s:
        s_splited = s.split("1/2")
        s = " 1/2 ".join([re.sub(r"([0-9]+(\.[0-9]+)?)",r" \1 ", sub_s).strip() for sub_s in s_splited])
    elif "1/4" in s:
        s_splited = s.split("1/4")
        s = " 1/4 ".join([re.sub(r"([0-9]+(\.[0-9]+)?)",r" \1 ", sub_s).strip() for sub_s in s_splited])
    else:
        s = re.sub(r"([0-9]+(\.[0-9]+)?)",r" \1 ", s).strip()
    # s = s.replace("'s", " 's")
    s = ' '.join(s.split())

    return s

def remove_punctuation(sentence):

    exclude = set(string.punctuation)
    s = ''.join(ch for ch in sentence if ch not in exclude)
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

def NLU_token_in_list_fuzz(token, my_list):
    s1, w = NLU_string_in_list_fuzz(token.text, my_list)
    if s1:
        return s1, w
    s2, w = NLU_string_in_list_fuzz(token.lemma_, my_list)
    if s2:
        return s2, w
    return NLU_string_in_list_fuzz(helper.remove_duplicate_consecutive_char_from_string(token.text), my_list)

def NLU_token_in_list_bool(token, my_list):
    s, _ = NLU_token_in_list_fuzz(token, my_list)
    if s:
        return True
    return False

def NLU_string_in_list_fuzz(s, my_list, threshold=80):
    found, word = False, None
    for w in my_list:
        score = fuzz.token_sort_ratio(s, w)
        if score >= threshold:
            threshold = score
            word = w
            found = True
    if found:
        return threshold, word
    return False, False

def NLU_string_in_sentence_fuzz(s, sentence):
    my_list = sentence.split()
    return NLU_string_in_list_fuzz(s, my_list)

def NLU_string_in_sentence_bool(s, sentence):
    s, _ = NLU_string_in_sentence_fuzz(s, sentence)
    if s:
        return True

def NLU_string_in_list_bool(s, my_list, threshold=80):
    score, _ = NLU_string_in_list_fuzz(s, my_list, threshold)
    if score:
        return True
    return False


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
    return NLU_token_in_list_bool(token, voc_no) or (token.tag_ == "RB" and token.dep_ == "neg")


def is_dont_know(document, voc_no):
    know, negation = False, False
    for token in document:
        if NLU_token_in_list_bool(token, ["know"]):
            know = True
        elif is_negation(token, voc_no):
            negation = True
    if know and negation:
        return True
    return False

def is_dont_care(document, voc_no):
    care, negation = False, False
    for token in document:
        if NLU_token_in_list_bool(token, ["care"]):
            care = True
        elif is_negation(token, voc_no):
            negation = True
    if care and negation:
        return True
    return False

def is_doesnt_matter(document, voc_no):
    matter, negation = False, False
    for token in document:
        if NLU_token_in_list_bool(token, ["matter"]):
            matter = True
        elif is_negation(token, voc_no):
            negation = True
    if matter and negation:
        return True
    return False


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

def user_feels_good(document, sentence, voc_feel_good, voc_feel_bad, voc_feel_tired, voc_no):
    res = {"yes": ("yes", None, None, None), "no": ("no", None, None, None)}
    feel_good, feel_bad, negation = False, False, False
    # print(voc_feel_tired)
    if "under the weather" in sentence:
        return res["no"]
    for token in document:
        # if token.lemma_ in voc_feel_good or token.text in voc_feel_good:
        if NLU_token_in_list_bool(token, voc_feel_good):
            feel_good = True
        # elif token.lemma_ in voc_feel_bad + voc_feel_tired or token.text in voc_feel_bad+voc_feel_tired:
        elif NLU_token_in_list_bool(token, voc_feel_bad+voc_feel_tired):
            feel_bad = True
        elif is_negation(token, voc_no):
            negation = True
    # print(feel_good, feel_bad, negation)
    if feel_bad:
        if negation:
            return res["yes"]
        else:
            return res["no"]
    elif feel_good:
        if not negation:
            return res['yes']
        else:
            return res["no"]
    else:
        return None

def is_requestmore(document, voc_request_more):
    '''
    Determines if intent is request more
    :param document: spacy document
    :param voc_request_more: list of request-more key words
    :return: bool
    '''
    for token in document:
        if token.text in voc_request_more:
            return ("request", "more", None, None)
    return False


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
    # log.debug("in is_yes_no")
    # log.debug((voc_no["no_1word"]))
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
        # if (token.text in voc_yes["all_yes_words"] or token.text in voc_yes["yes_vb"]) and is_positive == None:
        if (NLU_token_in_list_bool(token, voc_yes["all_yes_words"]) or NLU_token_in_list_bool(token,voc_yes["yes_vb"])) and is_positive == None:
            is_positive = True
        elif is_negation(token, voc_no=voc_no["all_no_words"]):
            return res["no"]
    if is_positive == True:
        return res["yes"]

def iamgood_means_no(document, voc_yes):
    for token in document:
        if NLU_token_in_list_bool(token, voc_yes["yes_words"]["yes_adj"]):
            return ("no", None, None, None)
    return False


def is_number(s, voc_numbers):
    for key in reversed(list(voc_numbers.keys())):
        value = voc_numbers[key]
        if s in value:
            return key
    return False


def is_duration_unit(s, voc_units):
    for key in reversed(list(voc_units.keys())):
        value = voc_units[key]
        if s in value:
            return key
    return False

def find_unit_immediately_after_number(n_idx, units, units_idx):
    for i, u in enumerate(units):
        u_idx = units_idx[i]
        if u_idx >= n_idx:
            return u, u_idx
    return False, False

def is_duration(document, sentence, voc_numbers, voc_duration, voc_fractions):
    units, units_idx = list(), list()
    numbers, numbers_idx = list(), list()
    fraction, index_fraction = False, -1

    w_few, w_to, w_to_idx, duration_2 = False, False, False, 0

    # find fractions and "few"
    for i, token in enumerate(document):
        if token.text == "few":
            w_few = True
        if token.text == "to":
            w_to, w_to_idx = True, i
        if token.text in voc_fractions['half'] or token.lemma_ in voc_fractions['half']:
            fraction, index_fraction = 30, i
        elif token.text in voc_fractions['quarter'] or token.lemma_ in voc_fractions['quarter']:
            fraction, index_fraction = 15, i
    if not fraction:
        for i, word in enumerate(sentence.split()):
            if word in voc_fractions['half']:
                fraction, index_fraction = 30, i
            elif word in voc_fractions['quarter']:
                fraction, index_fraction = 15, i

    # find numbers in bigrams (e.g. forty five)
    if len(sentence) > 2:
        bigrams = nltk.bigrams(sentence.split())

        for i_bg, bg in enumerate(bigrams):
            bg_str = " ".join(bg)
            n = is_number(bg_str, voc_numbers)
            if n:
                numbers.append(int(n))
                numbers_idx.append(i_bg)
                numbers_idx.append(i_bg + 1)

    # find other numbers
    for i, token in enumerate(document):
        if i not in numbers_idx:
            n = is_number(token.text, voc_numbers)
            if n:
                numbers.append(int(n))
                numbers_idx.append(i)
        u = is_duration_unit(token.text, voc_duration)
        if not u:
            u = is_duration_unit(token.lemma_, voc_duration)
        if u:
            units.append(u)
            units_idx.append(i)

    if w_few:
        if units:
            if units[0] == "h":
                return "inform", "duration", 120, None
            elif units[0] == "m":
                return "inform", "duration", 20, None

    if fraction:
        if not numbers or numbers[0] == 1:
            if list(set(voc_duration["h"]) & set(sentence.split()[index_fraction:])):
                return "inform", "duration", fraction, None
            elif list(set(voc_duration["h"]) & set(sentence.split()[:index_fraction])):
                return "inform", "duration", 60+fraction, None
        else:
            if units:
                if numbers_idx[0] < index_fraction and units[0] == "h":
                    return "inform", "duration", 60*numbers[0] + fraction
        return False


    duration = 0

    if numbers:
        if not units:
            # log.debug("No units!")
            return False
        else:
            # parse stuff like 30, 40 min
            if len(numbers) == 2 and len(units) == 1 and units_idx[0] > numbers_idx[1]:
                max_n = max(numbers)
                duration = max_n * 60 if units[0] == 'h' else max_n
            else:
                # parse stuff like 1h30
                found_h_unit = False
                for i, n in enumerate(numbers):
                    n_idx = numbers_idx[i]
                    d, found_h_unit = calculate_duration(found_h_unit, n, n_idx, units, units_idx)
                    if d == False and found_h_unit == False:
                        return False
                    if w_to and w_to_idx < n_idx and duration > 0:
                        duration_2 += d
                    else:
                        duration += d

        if duration_2 > 0:
            return "inform", "duration", duration_2, None

        return "inform", "duration", duration, None


def calculate_duration(found_h_unit, n, n_idx, units, units_idx):
    u_just_after, u_just_after_idx = find_unit_immediately_after_number(n_idx, units, units_idx)
    duration = 0
    if u_just_after == "h":
        found_h_unit = True
    if not u_just_after and not found_h_unit:
        log.debug("Can't find proper units")
        return False, False
    elif u_just_after:
        if u_just_after == "m":
            duration = n
        elif u_just_after == "h":
            duration = n * 60
    elif not u_just_after and found_h_unit:
        duration = n
    return duration, found_h_unit


def name_in_one_word_sentence(document):
    if len(document) == 1 and not NLU_token_in_list_bool(document[0], ["hello", "hi", "yes", "no"]):
        return ("inform", "user_name", document[0].text.title(), None)
    return False


def name_in_my_name_is_sentence(document):
    # for token in document:
    #     print(token.text, token.lemma_, token.tag_)
    # print(document)
    if document[0].text == "my" and document[1].text == "name" and (document[2].text == "is" or document[2].tag_ == "VBZ" or document[2].tag_ == "POS"):
        return ("inform", "user_name", document[3].text.title(), None)
    if len(document) == 3:
        if document[0].tag_ == "PRP" and document[1].tag_ == "VBP" and document[1].lemma_ == "be":
            return ("inform", "user_name", document[2].text.title(), None)
        # else:
        #     for token in document:
        #         print(token.tag_)
    return False


def question_in_sentence(document, sentence):
    if "?" in sentence:
        return ("question", None, None, None)
    return False


def get_quantifiers(document, sentence, voc_quantifiers):
    list_quantifiers = list()
    score = 0
    bigrams = nltk.bigrams(sentence.split())
    for i_bg, bg in enumerate(bigrams):
        bg_str = " ".join(bg)
        for quantifier, words in voc_quantifiers.items():
            for w in words:
                if len(w.split()) == 2 and bg_str == w:
                    list_quantifiers.append(quantifier)
                    score = 100
    for token in document:
        for quantifier, words in voc_quantifiers.items():
            s = NLU_token_in_list_bool(token, words)
            if s:
                if s == score:
                    list_quantifiers.append(quantifier)
                elif s > score:
                    list_quantifiers = [quantifier]
                    score = s
    return list_quantifiers

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
