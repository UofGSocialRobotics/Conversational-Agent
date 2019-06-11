from ca_logging import log
import whiteboard_client as wbc
import helper_functions as helper
import nltk
import stanfordnlp
# stanfordnlp.download('en')
from textblob import TextBlob
import spacy
import json
import dataparser
import string
import re
import argparse
import helper_functions as helper


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
    s = sentence.translate(str.maketrans('','',string.punctuation))
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


def find_key_in_dict_with_fuzzy_matching(k,d):
    '''
    Uses fuzzy mathcing (TODO) to find a key in a dictionary
    :param k: key to find
    :param d: dictionay in which to loo for k
    :return: d[k] if k in d or False
    '''
    for key, id in d.items():
        if key == k:
            return id
    return False


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


def get_cast_id(actor_name, cast_dicts):
    '''
    Finds the DB id of an actor those name is actor_name.
    :param actor_name: name of the actor or director we're looking for in the DB
    :param cast_dicts: dictionaries of cast ids. 3 dictionaires mapping (lastname) / (firtname lastname) / (lastname firstname) to the actor id
    :return: the id of the actor if found in the DB
    '''
    # print(actor_name)
    actor_name_splited = actor_name.split()
    if len(actor_name_splited) == 1:
        # print("get_actor_id: was given only one string")
        # print(actor_name)
        # look in dictionary that has only last names as keys
        return find_key_in_dict_with_fuzzy_matching(actor_name, cast_dicts['lastname2id'])
    elif len(actor_name_splited) == 2:
        # print("get_actor_id: was given 2 elements")
        # print(actor_name_splited)
        x1, x2 = ' '.join(actor_name_splited), ' '.join(reversed(actor_name_splited))
        id = find_key_in_dict_with_fuzzy_matching(x1, cast_dicts['firstnamelastname2id'])
        if id:
            return id
        else:
            return find_key_in_dict_with_fuzzy_matching(x2, cast_dicts['lastnamefirstname2id'])
    return False


def get_cast(capitalized_doc, cast_dicts):
    """
    Get the ids of cast members mentioned in a document.
    First tries to find names using spacy's NER then manually using POS tagging
    :param capitalized_doc: A spacy NLP document built from a capitalized sentece
    :param cast_dicts: dictionaries of cast ids. 3 dictionaires mapping (lastname) / (firtname lastname) / (lastname firstname) to the actor id
    :return: the list of actors / directors in capitalized_doc as ids (that will match ids in lexicon files)
    """
    names = get_NE_Person(capitalized_doc)
    # names2ids = parse_dataset.get_all_cast()
    if not names or len(names) == 0:
        names = get_NNs(capitalized_doc)
        # print("got names from NNs")
    if len(names)>0:
        actor_ids = list()
        for x in names:
            id = get_cast_id(x, cast_dicts)
            actor_ids.append(id)
        # print(actor_ids)
        return [x for x in actor_ids if x is not False]


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
            return True


def is_alreadywatched(sentence):
    '''
    determines if intent is alreadywatched
    :param sentence: string
    :return: bool
    '''
    return ("already" in sentence)


def is_requestmore(document, voc_request_more):
    '''
    Determines if intent is request more
    :param document: spacy document
    :param voc_request_more: list of request-more key words
    :return: bool
    '''
    for token in document:
        if token.text in voc_request_more:
            return True


def is_goodbye(document, sentence, voc_bye):
    '''
    Determines if intent is goodbye
    :param document: spacy document
    :param sentence: string
    :param voc_bye: dictionary of words used to say bye (see resources/nlu/voc.json)
    :return: bool
    '''
    for token in document:
        if token.text in voc_bye["bye_1word"]:
            return True
    if len(sentence) > 1:
        bigrams = nltk.bigrams(sentence.split())
        for bg in bigrams:
            bg_text = ' '.join(bg)
            if bg_text in voc_bye["bye_2words"]:
                return True
    if len(sentence) > 3:
        fourgrams = nltk.ngrams(sentence.split(), 4)
        for fg in fourgrams:
            fg_text = ' '.join(fg)
            if fg_text in voc_bye["bye_4words"]:
                return True
    return False


def is_askGenre(document, voc_genres):
    """
    Determines if intent is ask_genre
    /!\ will work only given that it is not askActor
    :param document: spacy document
    :param voc_genres: list of genres
    :return: bool
    """
    first_word = document[0]
    if first_word.text == "what" or is_verb(first_word):
        for token in document:
            if token.lemma_ in ["genre", "type", "kind"] or token.lemma_ in voc_genres:
                return True
    return False

def is_askPerson(document, prep, key_words):
    """
    Determines if intent is askPerson
    :param document: spacy document
    :param prep: perpositions to look for
    :param key_words: key words to look for
    :return: bool
    """
    first_word = document[0]
    # print(first_word.tag_)
    if first_word.tag_ == "WDT" or first_word.tag_ == "WP" or is_verb(first_word):
        for token in document:
            if token.text in prep and token.dep_ == "prep":
                return True
            if token.lemma_ in key_words:
                return True
    return False


def is_askActor(document):
    """
    Determines if intent is askActor
    :param document: spacy document
    :return: bool
    """
    return is_askPerson(document, ["in", "on"], ["actor", "act", "star", "cast"])


def is_askDirector(document):
    """
    Determines if intent is askDirector
    :param document: spacy document
    :return: bool
    """
    return is_askPerson(document, ["by"], ["director", "direct"])


def is_askPlot(document):
    """
    Determines if intent is askPlot
    /!\ Will work only given that it is not askActor/Director/Genre
    :param document: spacy document
    :return: bool
    """
    first_word = document[0]
    if (first_word.tag_ == "WP" or is_verb(first_word)) and len(document) > 2:
        return True
    for token in document:
        if token.lemma_ in ["happen", "plot", "summary", "plot"]:
            return True
    return False

## ---------------------------------------- Non-bool functions ---------------------------------------- ##

def is_yes_no(document, sentence, voc_yes, voc_no):
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
        return "yes"
    if sentence in voc_no["all_no_words"]:
        return "no"
    if first_word.text in voc_no["no_1word"]:
        return "no"
    if len(document)>1 and document[1].text in voc_no["no_1word"]:
        return "no"
    if len(sentence) > 2:
        bigrams = nltk.bigrams(sentence.split())
        for bg in bigrams:
            bg_text = ' '.join(bg)
            if bg_text in voc_no["no_2words"]:
                return "no"
            elif bg_text in voc_yes["yes_words"]["yes_2words"]:
                return "yes"
    if len(sentence) > 3:
        trigrams = nltk.trigrams(sentence)
        for tg in trigrams:
            tg_text = ' '.join(tg)
            if tg_text in voc_no["no_3words"]:
                return "no"
    is_positive = None
    for token in document:
        if (token.text in voc_yes["all_yes_words"] or token.text in voc_yes["yes_vb"]) and is_positive == None:
            is_positive = True
        elif token.text in voc_no["no_1word"] or (token.tag_ == "RB" and token.dep_ == "neg"):
            return "no"
    if is_positive == True:
        return "yes"

def is_inform_genre(document, voc_genres, voc_scifi):
    """
    Determines if intent is inform genre
    :param document: spacy document
    :param voc_genres: list of genres
    :param voc_scifi: list of sci-fi words
    :return: intent string
    """
    for token in document:
        # print(token.lemma_)
        if token.lemma_ in voc_genres:
            if token.lemma_ in voc_scifi:
                return ("inform (genre sci-fi)")
            return ("inform (genre %s)" % token.lemma_)


def is_inform_cast(capitalized_doc, cast_dicts):
    """
    Detremines if intent is inform cast
    :param capitalized_doc: spacy document generated from a capitalized sentence
    :param cast_dicts: dictionaries of cast ids. 3 dictionaires mapping (lastname) / (firtname lastname) / (lastname firstname) to the actor id
    :return: intent string
    """
    actors = get_cast(capitalized_doc, cast_dicts)
    if actors and actors[0]:
        return "inform (cast %s)" % actors[0]


####################################################################################################
##                                          Debug functions                                       ##
####################################################################################################


def compare_syntax_analysis(sentence):
    # tokens = nltk.word_tokenize(sentence)
    # nlp = stanfordnlp.Pipeline()
    # doc = nlp(sentence)
    # print("With stanford CoreNLP")
    # doc.sentences[0].print_dependencies()
    #
    # blob = TextBlob(sentence)
    # print("With textblob")
    # print(blob.tags)
    # print(blob.noun_phrases)
    # print("No dependency parser with textblob")
    #

    cast_dicts = dataparser.get_all_cast()

    spacy_nlp = spacy.load("en_core_web_sm")
    document = spacy_nlp(sentence)
    print("With spacy")
    for token in document:
        print("{0}/{1} <--{2}-- {3}/{4}".format(token.text, token.tag_, token.dep_, token.head.text, token.head.tag_))
        # spacy.displacy.serve(doc, style='dep')

    print("\nNER with Spacy:")
    if document.ents and len(document.ents) >0:
        print([(X.text, X.label_) for X in document.ents])
    print(sentence.title())
    capitalized_document = spacy_nlp(sentence.title())
    print("Actors:")
    print(capitalized_document.ents)
    print(get_NNs)
    print(get_NNs(capitalized_document))
    print(get_cast(capitalized_document, cast_dicts=cast_dicts))

def compare_sentiment_analysis(sentence):

    blob = TextBlob(sentence)
    print("With textblob")
    for sentence in blob.sentences:
        print(sentence.sentiment.polarity)


####################################################################################################
##                                Main rule-based NLU function                                    ##
####################################################################################################

def rule_based_nlu(utterance, spacy_nlp, voc, cast_dicts):

    utterance = preprocess(utterance)
    document = spacy_nlp(utterance)
    capitalized_document = spacy_nlp(utterance.title())
    f = is_inform_cast(capitalized_document, cast_dicts)
    if f:
        return f
    else:
        if is_alreadywatched(utterance):
            f = "alreadyWatched"
        elif is_goodbye(document, utterance, voc_bye=voc["bye"]):
            f = "goodbye"
        elif is_requestmore(document, voc_request_more=voc["request_more"]):
            f = "request_more"
        elif is_askActor(document):
            f = "askActor"
        elif is_askDirector(document):
            f = "askDirector"
        elif is_askGenre(document, voc_genres=["genres"]):
            f = "askGenre"
        elif is_askPlot(document):
            f = "askPlot"
        else :
            f = is_inform_genre(document, voc_genres=voc["genres"], voc_scifi=voc["genre_scifi"])
        if f == None:
            f = is_yes_no(document, utterance, voc_yes=voc["yes"], voc_no=voc["no"])
        if f == None and is_greeting(document, voc_greetings=voc["greetings"]):
            f = "greet"
        if f == None:
            f = "IDK"
        return f


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

####################################################################################################
##                                      Evaluate NLU performance                                  ##
####################################################################################################

def evaluate(dataset, to_print='all'):
    spacy_nlp = spacy.load("en_core_web_sm")
    voc = dataparser.parse_voc()
    cast_dicts = dataparser.get_all_cast()
    got_right = 0
    for utterance, formula in dataset:
        f = rule_based_nlu(utterance, spacy_nlp, voc=voc, cast_dicts=cast_dicts)
        if f == formula:
            got_right += 1
        if to_print == 'all' or (f != formula and to_print == "wrong"):
            print(utterance)
            print(formula)
            print(f)
            print()
    print("ACCURACY SCORE: %.2f (%d/%d)" % (got_right / float(len(dataset)), got_right, len(dataset)))
    if to_print == 'wrong':
        print("Printed only utterances for which we got it wrong")



####################################################################################################
##                                            Test NLU                                            ##
####################################################################################################

def test_nlu():
    q= False
    spacy_nlp = spacy.load("en_core_web_sm")
    voc = dataparser.parse_voc()
    cast_dicts = dataparser.get_all_cast()
    while(not q):
        utterance = input("Enter text (q to quit): ")
        if utterance == 'q':
            q = True
        else:
            formula = rule_based_nlu(utterance, spacy_nlp, voc, cast_dicts)
            print(formula)
            intent, entity, entitytype, polarity = format_formula(formula)
            print(intent, entity, entitytype, polarity)


####################################################################################################
##                                     rule-based NLU Module                                      ##
####################################################################################################

class RuleBasedNLU(wbc.WhiteBoardClient):
    def __init__(self, subscribes, publishes, clientid):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, name="NLU"+clientid, subscribes=subscribes, publishes=publishes)
        self.voc = dataparser.parse_voc()
        self.spacy_nlp = spacy.load("en_core_web_sm")
        self.cast_dicts = dataparser.get_all_cast()

    def treat_message(self, msg, topic):
        msg_lower = msg.lower()

        formula = rule_based_nlu(utterance=msg_lower, spacy_nlp=self.spacy_nlp, voc=self.voc, cast_dicts=self.cast_dicts)
        intent, entity, entitytype, polarity = format_formula(formula=formula)

        new_msg = self.msg_to_json(intent, entity, entitytype, polarity)
        self.publish(new_msg)

    def msg_to_json(self, intent, entity, entity_type, polarity):
        frame = {'intent': intent, 'entity': entity, 'entity_type': entity_type, 'polarity': polarity}
        json_msg = json.dumps(frame)
        return json_msg

####################################################################################################
##                                     Run as stand-alone                                         ##
####################################################################################################

if __name__ == "__main__":

    argp = argparse.ArgumentParser()
    argp.add_argument("--eval", help="To evaluate the performance of NLU on the labeled dataset", action="store_true")
    argp.add_argument("--test", help="To test the NLU module yourself", action="store_true")
    argp.add_argument("--debug", help="Sentence to debug", action="store")

    args = argp.parse_args()

    if args.eval:

        # Ask plot
        dataset = dataparser.parse_dataset("resources/datasets/scenario1.dataset")
        # inform actor
        dataset += dataparser.parse_dataset("resources/datasets/scenario2.dataset")
        dataset += dataparser.parse_dataset("resources/datasets/scenario6.dataset")
        # greet / yes / no
        dataset += dataparser.parse_dataset("resources/datasets/scenario3.dataset")
        # goodbye
        dataset += dataparser.parse_dataset("resources/datasets/scenario4.dataset")
        # request more
        dataset += dataparser.parse_dataset("resources/datasets/scenario5.dataset")
        # inform genre
        dataset += dataparser.parse_dataset("resources/datasets/scenario7.dataset")
        # inform director
        dataset += dataparser.parse_dataset("resources/datasets/scenario8.dataset")
        # yes/no
        dataset += dataparser.parse_dataset("resources/datasets/scenario9.dataset")
        # Ask genre, director, actor
        dataset += dataparser.parse_dataset("resources/datasets/scenario10.dataset")
        # already watched
        dataset += dataparser.parse_dataset("resources/datasets/scenario12.dataset")


        evaluate(dataset, "wrong")

    elif args.test:

        test_nlu()

    elif args.debug:
        print(args.debug)
        compare_syntax_analysis(preprocess(args.debug))

    # # n't/RB <--neg-- dream/VB
    # # print(is_askGenre(sentence))
    # compare_sentiment_analysis("I think so")
    # compare_sentiment_analysis("I don't think so")
