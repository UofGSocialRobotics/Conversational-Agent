import spacy
import nlu_helper_functions as nlu_helper
from ca_logging import log
import nltk

def get_cast_id(actor_name, cast_dicts):
    '''
    Finds the DB id of an actor those name is actor_name.
    :param actor_name: name of the actor or director we're looking for in the DB
    :param cast_dicts: dictionaries of cast ids. 3 dictionaires mapping (lastname) / (firtname lastname) / (lastname firstname) to the actor id
    :return: the id of the actor if found in the DB
    '''
    actor_name_splited = actor_name.split()
    if len(actor_name_splited) == 1:
        # look in dictionary that has only last names as keys
        return nlu_helper.find_key_in_dict_with_fuzzy_matching(actor_name, cast_dicts['lastname2id'])
    elif len(actor_name_splited) == 2:
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
    if not names or len(names) == 0:
        names = nlu_helper.get_NNs(capitalized_doc)
    if len(names)>0:
        actor_ids = list()
        for x in names:
            id = get_cast_id(x, cast_dicts)
            actor_ids.append(id)
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
    if ("already" in sentence):
        return ("inform", "watched", True, None)
    return False


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
                return ("request", "genre", None, None)
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
    if is_askPerson(document, ["in", "on"], ["actor", "act", "star", "cast"]):
        return ("request", "actor", None, None)
    return False


def is_askDirector(document):
    """
    Determines if intent is askDirector
    :param document: spacy document
    :return: bool
    """
    if is_askPerson(document, ["by"], ["director", "direct"]):
        return ("request", "director", None, None)
    return False


def is_askPlot(document):
    """
    Determines if intent is askPlot
    /!\ Will work only given that it is not askActor/Director/Genre
    :param document: spacy document
    :return: bool
    """
    askPlot = ("request", "plot", None, None)
    first_word = document[0]
    if (first_word.tag_ == "WP" or nlu_helper.is_verb(first_word)) and len(document) > 2:
        return askPlot
    for token in document:
        if token.lemma_ in ["happen", "plot", "summary", "plot"]:
            return askPlot
    return False

## ---------------------------------------- Non-bool functions ---------------------------------------- ##



def is_inform_genre(sentence, document, voc_genres, voc_scifi):
    """
    Determines if intent is inform genre
    :param document: spacy document
    :param voc_genres: list of genres
    :param voc_scifi: list of sci-fi words
    :return: intent string
    """
    if "sci-fi" in sentence or "science-fiction" in sentence:
        return ("inform", "genre", "sci-fi", "+")

    if len(sentence) > 1:
        bigrams = nltk.bigrams(sentence.split())
        for bg in bigrams:
            bg_text = ' '.join(bg)
            if bg_text in voc_scifi:
                return ("inform", "genre", "sci-fi", "+")

    for token in document:
        print(token.text)
        if token.text in voc_scifi:
            return ("inform", "genre", "sci-fi", "+")
        if token.text in voc_genres:
            return ("inform", "genre", token.lemma_, "+")
    return False

def is_inform_cast(capitalized_doc, cast_dicts, director_or_actor):
    """
    Detremines if intent is inform cast
    :param capitalized_doc: spacy document generated from a capitalized sentence
    :param cast_dicts: dictionaries of cast ids. 3 dictionaires mapping (lastname) / (firtname lastname) / (lastname firstname) to the actor id
    :return: intent string
    """
    cast_list = get_cast(capitalized_doc, cast_dicts)
    if cast_list and cast_list[0]:
        # return "inform (cast %s)" % actors[0]
        return ("inform", director_or_actor, cast_list[0], "+")


####################################################################################################
##                                Main rule-based NLU function                                    ##
####################################################################################################

def rule_based_nlu(utterance, spacy_nlp, voc, directors_dicts, actors_dicts):

    utterance = nlu_helper.preprocess(utterance)
    document = spacy_nlp(utterance)
    capitalized_document = spacy_nlp(utterance.title())
    f = is_inform_cast(capitalized_document, directors_dicts, director_or_actor="crew")
    if not f:
        f = is_inform_cast(capitalized_document, actors_dicts, director_or_actor="cast")
        if not f:
            f = is_alreadywatched(utterance)
            if not f:
                f = nlu_helper.is_goodbye(document, utterance, voc_bye=voc["bye"])
                if not f:
                    f = is_requestmore(document, voc_request_more=voc["request_more"])
                    if not f:
                        f = is_askActor(document)
                        if not f:
                            f = is_askDirector(document)
                            if not f:
                                f = is_askGenre(document, voc_genres=["genres"])
                                if not f:
                                    f = is_askPlot(document)
                                    if not f:
                                        f = is_inform_genre(utterance, document, voc_genres=voc["genres"], voc_scifi=voc["genre_scifi"])
                                        if not f:
                                            f = nlu_helper.is_yes_no(document, utterance, voc_yes=voc["yes"], voc_no=voc["no"])
                                            if not f:
                                                f = nlu_helper.is_greeting(document, voc_greetings=voc["greetings"])
                                                if f == None:
                                                    f = ("IDK", None, None, None)
    return f


####################################################################################################
##                                          Debug functions                                       ##
####################################################################################################


def compare_syntax_analysis(sentence):

    spacy_nlp = spacy.load("en_core_web_sm")
    document = spacy_nlp(sentence)
    print("With spacy")
    for token in document:
        print("{0}/{1} <--{2}-- {3}/{4}".format(token.text, token.tag_, token.dep_, token.head.text, token.head.tag_))

    print("\nNER with Spacy:")
    if document.ents and len(document.ents) >0:
        print([(X.text, X.label_) for X in document.ents])
    print(sentence.title())
    capitalized_document = spacy_nlp(sentence.title())
    print("Actors:")
    print(capitalized_document.ents)


####################################################################################################
##                                     Run as stand-alone                                         ##
####################################################################################################

if __name__ == "__main__":

    log.error("Use testNLU.py")
