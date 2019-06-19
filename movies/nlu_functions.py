import string
import re
import nltk
import spacy
import dataparser
from movies import movie_dataparser
import nlu_helper_functions as nlu_helper



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
        return nlu_helper.find_key_in_dict_with_fuzzy_matching(actor_name, cast_dicts['lastname2id'])
    elif len(actor_name_splited) == 2:
        # print("get_actor_id: was given 2 elements")
        # print(actor_name_splited)
        x1, x2 = ' '.join(actor_name_splited), ' '.join(reversed(actor_name_splited))
        id = nlu_helper.find_key_in_dict_with_fuzzy_matching(x1, cast_dicts['firstnamelastname2id'])
        if id:
            return id
        else:
            return nlu_helper.find_key_in_dict_with_fuzzy_matching(x2, cast_dicts['lastnamefirstname2id'])
    return False


def get_cast(capitalized_doc, cast_dicts):
    """
    Get the ids of cast members mentioned in a document.
    First tries to find names using spacy's NER then manually using POS tagging
    :param capitalized_doc: A spacy NLP document built from a capitalized sentece
    :param cast_dicts: dictionaries of cast ids. 3 dictionaires mapping (lastname) / (firtname lastname) / (lastname firstname) to the actor id
    :return: the list of actors / directors in capitalized_doc as ids (that will match ids in lexicon files)
    """
    names = nlu_helper.get_NE_Person(capitalized_doc)
    # names2ids = parse_dataset.get_all_cast()
    if not names or len(names) == 0:
        names = nlu_helper.get_NNs(capitalized_doc)
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


def is_askGenre(document, voc_genres):
    """
    Determines if intent is ask_genre
    /!\ will work only given that it is not askActor
    :param document: spacy document
    :param voc_genres: list of genres
    :return: bool
    """
    first_word = document[0]
    if first_word.text == "what" or nlu_helper.is_verb(first_word):
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
    if first_word.tag_ == "WDT" or first_word.tag_ == "WP" or nlu_helper.is_verb(first_word):
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
    if (first_word.tag_ == "WP" or nlu_helper.is_verb(first_word)) and len(document) > 2:
        return True
    for token in document:
        if token.lemma_ in ["happen", "plot", "summary", "plot"]:
            return True
    return False

## ---------------------------------------- Non-bool functions ---------------------------------------- ##



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

    cast_dicts = movie_dataparser.get_all_cast()

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
    print(nlu_helper.get_NNs)
    print(nlu_helper.get_NNs(capitalized_document))
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

    utterance = nlu_helper.preprocess(utterance)
    document = spacy_nlp(utterance)
    capitalized_document = spacy_nlp(utterance.title())
    f = is_inform_cast(capitalized_document, cast_dicts)
    if f:
        return f
    else:
        if is_alreadywatched(utterance):
            f = "alreadyWatched"
        elif nlu_helper.is_goodbye(document, utterance, voc_bye=voc["bye"]):
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
            f = nlu_helper.is_yes_no(document, utterance, voc_yes=voc["yes"], voc_no=voc["no"])
        if f == None and nlu_helper.is_greeting(document, voc_greetings=voc["greetings"]):
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
    voc = dataparser.parse_voc(f_domain_voc="./movies/resources/nlu/voc.json")
    cast_dicts = movie_dataparser.get_all_cast()
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
    voc = dataparser.parse_voc(f_domain_voc="./movies/resources/nlu/voc.json")
    cast_dicts = movie_dataparser.get_all_cast()
    while(not q):
        utterance = input("Enter text (q to quit): ")
        if utterance == 'q':
            q = True
        else:
            formula = rule_based_nlu(utterance, spacy_nlp, voc, cast_dicts)
            print(formula)
            intent, entity, entitytype, polarity = format_formula(formula)
            print(intent, entity, entitytype, polarity)
