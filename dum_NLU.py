import whiteboard_client as wbc
import helper_functions as helper
import json
from ca_logging import log
import nltk
import stanfordnlp
# stanfordnlp.download('en')
from textblob import TextBlob
import spacy
import parse_dataset
import string
import re

GENRES = ["action", "adventre", "comedy", "crime", "drama", "fantasy", "historical", "fiction", "horror", "mystery", "polotical",
"romance", "saga", "satire", "animation", "western", "musical", "superhero", "bibliography", "documentary", "family", "romantic comedy", "war"]
GENRE_SCIFI = ["sci-fi", "scifi", "fiction"]

YES_1 = ["yes", "yep", "yup", "ok", "okay", "yeah", "okeydokey", "yea", "affirmative", "ja", "ya", "aye", "yea", "okey-dokey", "yea", "righto",]
#  you bet
YES_2 = ["great", "cool", "good", "right", "all right", "correct", "sure", "agreed", "fine", "alright", "well", "granted", "true", "likely"]
YES_3 = ["definitely", "absolutely", "certainly", "naturally", "totally", "exactly", "precisely", "gladly", "probably", "indeed"]
YES_4 = ["no problem", "why not"]
YES_5 = ["amazing", "awesome", "booyah", "excellent", "fab", "fabulous", "fantastic", "great", "hooray", "incredible", "splendid", "super", "terrific", "tremendous", "whoopee", "wonderful"]
YES = YES_1 + YES_2 + YES_3 + YES_4 + YES_5
YES_VB = ["guess", "think", "like", "love", "agree", "will", "would"]

NO_1 = ["no", "nope", "nop", "nah", "neh", "nay", "never", "not", "nix", "uh-uh", "nixy", "nixey", "negative", "none", "nothing", "noway", "noways", "hardly", "enough", "disagree", "wrong"]
NO_2 = ["uh uh", "no way"]
NO_3 = ["by no means", "on no account", "not at all"]
NO = NO_1 + NO_2

GREETINGS_1 = ["hi", "hey", 'hello', "morning", "afternoon", "evening", "howdy", "d'day", "yo", "greeting", "hiya", "welcome", "hi-ya", "salutation", "hola"]
# GREETINGS_2 = ["good morning", "good afternoon", 'good evening']

BYE_1 = ["bye", "ciao", "adieu", "farewell", "stop", "end", "adios", "goodbye", "cheerio", "goodby", "good-by", "cheers"]
BYE_2 = ["see you", "au revoir", "see ya"]
BYE_3 = ["have a nice day"]

REQUEST_MORE_1 = ["more", "another", "other", "else"]

def preprocess(sentence):
    s = sentence.lower()
    s = s.replace(" don t ", " don't ")
    # s = s.replace("'s", " 's")
    return s

def is_verb(token):
    if "VB" in token.tag_ or token.tag_ == "MD":
        return True
    else:
        return False

def get_NNs(document):
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

def get_NE_Person(capitalized_doc):
    # [print(x) for x in capitalized_doc]
    verbs = [x.text for x in capitalized_doc if is_verb(x)]
    if capitalized_doc.ents and len(capitalized_doc.ents) > 0:
        actors = [X.text for X in capitalized_doc.ents if X.label_ == "PERSON"]
        actors_cleaned = list()
        if len(verbs)>0:
            for actor in actors:
                words = actor.split()
                # print(words)
                actor_cleaned = " ".join([w for w in words if w not in verbs])
                # actor_cleaned = actor_cleaned.replace("'s", "")
                actors_cleaned.append(actor_cleaned)
        else:
            actors_cleaned = actors
        # print(actors_cleaned)
        actors_cleaned = [a.lower() for a in actors_cleaned]
        actors_cleaned = [a.replace("'s", '') for a in actors_cleaned]
        return actors_cleaned
        # return actors_cleaned


def find_key_in_dict_with_fuzzy_matching(k,d):
    for key, id in d.items():
        if key == k:
            return id
    return False


def get_actor_id(actor_name,cast_dicts):
    '''
    Finds the DB id of an actor those name is actor_name.
    :param actor_name: name of the actor or director we're looking for in the DB
    :param cast_dicts: dictonaries of cast ids. 3 dictionaires mapping (lastname) / (firtname lastname) / (lastname firstname) to the actor id
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
    '''
    Get the ids of cast members mentioned in a document
    :param capitalized_doc: A spacy NLP document built from a capitalized sentece
    :return: the list of actors / directors in capitalized_doc as ids (that will match ids in lexicon files)
    '''
    names = get_NE_Person(capitalized_doc)
    # names2ids = parse_dataset.get_all_cast()
    if not names or len(names) == 0:
        names = get_NNs(capitalized_doc)
        # print("got names from NNs")
    if len(names)>0:
        actor_ids = list()
        for x in names:
            id = get_actor_id(x, cast_dicts)
            actor_ids.append(id)
        # print(actor_ids)
        return [x for x in actor_ids if x is not False]


def flatten_sentence(sentence):
    s = sentence.translate(str.maketrans('','',string.punctuation))
    s = re.sub(' +', ' ', s)
    return s.lower()

def is_greeting(document):
    for token in document:
        if token.text in GREETINGS_1:
            return True

def is_alreadywatched(sentence):
    return ("already" in sentence)

def is_requestmore(document):
    for token in document:
        if token.text in REQUEST_MORE_1:
            return True

def is_goodbye(document, sentence):
    for token in document:
        if token.text in BYE_1:
            return True
    if len(sentence) > 1:
        bigrams = nltk.bigrams(sentence.split())
        for bg in bigrams:
            bg_text = ' '.join(bg)
            if bg_text in BYE_2:
                return True
    if len(sentence) > 3:
        fourgrams = nltk.ngrams(sentence.split(), 4)
        for fg in fourgrams:
            fg_text = ' '.join(fg)
            if fg_text in BYE_3:
                return True
    return False

def is_yes_no(document, sentence):
    sentence = flatten_sentence(sentence)
    first_word = document[0]
    if sentence in YES:
        return "yes"
    if sentence in NO:
        return "no"
    if first_word.text in NO_1:
        return "no"
    if len(document)>1 and document[1].text in NO_1:
        return "no"
    if len(sentence) > 2:
        bigrams = nltk.bigrams(sentence.split())
        for bg in bigrams:
            bg_text = ' '.join(bg)
            if bg_text in NO_2:
                return "no"
            elif bg_text in YES_4:
                return "yes"
    if len(sentence) > 3:
        trigrams = nltk.trigrams(sentence)
        for tg in trigrams:
            tg_text = ' '.join(tg)
            if tg_text in NO_3:
                return "no"
    is_positive = None
    for token in document:
        if (token.text in YES or token.text in YES_VB) and is_positive == None:
            is_positive = True
        elif token.text in NO_1 or (token.tag_ == "RB" and token.dep_ == "neg"):
            return "no"
    if is_positive == True:
        return "yes"

def is_inform_genre(document):
    for token in document:
        # print(token.lemma_)
        if token.lemma_ in GENRES:
            if token.lemma_ in GENRE_SCIFI:
                return ("inform (genre sci-fi)")
            return ("inform (genre %s)" % token.lemma_)


def is_inform_actor(capitalized_doc, cast_dicts):
    actors = get_cast(capitalized_doc, cast_dicts)
    if actors and actors[0]:
        return "inform (cast %s)" % actors[0]


def is_askGenre(document):
    '''Given that it is not askActor'''
    first_word = document[0]
    # print(first_word.tag_)
    if first_word.text == "what" or is_verb(first_word):
        for token in document:
            # print(token.lemma_)
            if token.lemma_ == "genre" or token.lemma_ == "type" or token.lemma_ == "kind" or token.lemma_ in GENRES:
                # type kind
                return True
    return False

def is_askPerson(document, prep, key_words):
    first_word = document[0]
    # print(first_word.tag_)
    if first_word.tag_ == "WDT" or first_word.tag_ == "WP" or is_verb(first_word):
        for token in document:
            if token.text in prep and token.dep_ == "prep" :
                return True
            if token.lemma_ in key_words:
                return True
    return False

def is_askActor(document):
    return is_askPerson(document, ["in", "on"], ["actor", "act", "star"])

def is_askDirector(document):
    return is_askPerson(document, ["by"], ["director", "direct"])

def is_askPlot(document):
    '''Given that it is not askActor/Director/Genre'''
    first_word = document[0]
    if (first_word.tag_ == "WP" or is_verb(first_word)) and len(document) > 2:
        return True
    for token in document:
        if token.lemma_ == "happen" or token.lemma_ == "plot" or token.lemma_ == "summary":
            return True
    return False

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

    cast_dicts = parse_dataset.get_all_cast()

    spacy_nlp = spacy.load("en")
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


def rule_based_nlu(utterance,spacy_nlp):
    utterance = preprocess(utterance)
    document = spacy_nlp(utterance)
    capitalized_document = spacy_nlp(utterance.title())
    cast_dicts = parse_dataset.get_all_cast()
    # f = "IDK"
    f = is_inform_actor(capitalized_document, cast_dicts)
    if f:
        return f
    else:
        if is_alreadywatched( utterance):
            f = "alreadyWatched"
        elif is_goodbye(document, utterance):
            f = "goodbye"
        elif is_requestmore(document):
            f = "request_more"
        elif is_askActor(document):
            f = "askActor"
        elif is_askDirector(document):
            f = "askDirector"
        elif is_askGenre(document):
            f = "askGenre"
        elif is_askPlot(document):
            f = "askPlot"
        else :
            f = is_inform_genre(document)
        if f == None:
            f = is_yes_no(document, utterance)
        if f == None and is_greeting(document):
            f = "greet"
        # if f == None and is_requestmore(document):
        #     f = "request_more"
        if f == None:
            f = "IDK"
        return f


    # print(is_askActor(sentence))
def evaluate(dataset,to_print='all'):
    spacy_nlp = spacy.load("en")
    got_right = 0
    for utterance, formula in dataset:
        f = rule_based_nlu(utterance,spacy_nlp)
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


def test_nlu():
    q= False
    spacy_nlp = spacy.load("en")
    while(not q):
        utterance = input("Enter text (q to quit): ")
        if utterance == 'q':
            q = True
        else:
            print(rule_based_nlu(utterance,spacy_nlp))
            # print("tedt")

class NLU(wbc.WhiteBoardClient):
    def __init__(self, subscribes, publishes, clientid):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, name="NLU"+clientid, subscribes=subscribes, publishes=publishes)

    def treat_message(self, msg, topic):
        msg_lower = msg.lower()

        user_intention = 'yes'
        user_entity = ''
        entity_type = ''
        entity_polarity = ''

        if "western" in msg_lower or "love" in msg_lower:
            user_intention = 'inform'
            user_entity = 'western'
            entity_type = 'genre'
            entity_polarity = "+"
        if "tom cruise" in msg_lower or "love" in msg_lower:
            user_intention = 'inform'
            user_entity = 'tom cruise'
            entity_type = 'cast'
            entity_polarity = "+"
        elif "yes" in msg_lower:
            user_intention = 'yes'
        elif "no" in msg_lower:
            user_intention = 'no'
        elif "more" in msg_lower:
            user_intention = 'request_more'
        elif "plot" in msg_lower:
            user_intention = 'askPlot'
        elif "actor" in msg_lower:
            user_intention = 'askActor'
        elif "genre" in msg_lower:
            user_intention = 'askGenre'
        new_msg = self.msg_to_json(user_intention, user_entity, entity_type, entity_polarity)
        self.publish(new_msg)

    def msg_to_json(self, intent, entity, entity_type, polarity):
        frame = {'intent': intent, 'entity': entity, 'entity_type': entity_type, 'polarity': polarity}
        json_msg = json.dumps(frame)
        return json_msg


if __name__ == "__main__":

    # Ask plot
    dataset += parse_dataset.parse_dataset("resources/datasets/scenario1.dataset")
    # inform actor
    dataset += parse_dataset.parse_dataset("resources/datasets/scenario2.dataset")
    dataset += parse_dataset.parse_dataset("resources/datasets/scenario6.dataset")
    # greet / yes / no
    dataset += parse_dataset.parse_dataset("resources/datasets/scenario3.dataset")
    # goodbye
    dataset += parse_dataset.parse_dataset("resources/datasets/scenario4.dataset")
    # request more
    dataset += parse_dataset.parse_dataset("resources/datasets/scenario5.dataset")
    # inform genre
    dataset += parse_dataset.parse_dataset("resources/datasets/scenario7.dataset")
    # inform director
    dataset += parse_dataset.parse_dataset("resources/datasets/scenario8.dataset")
    # yes/no
    dataset += parse_dataset.parse_dataset("resources/datasets/scenario9.dataset")
    # Ask genre, director, actor
    dataset = parse_dataset.parse_dataset("resources/datasets/scenario10.dataset")
    # already watched
    dataset += parse_dataset.parse_dataset("resources/datasets/scenario12.dataset")


    evaluate(dataset, "wrong")

    # test_nlu()

    # sentence = "I'm doing good"
    # compare_syntax_analysis(preprocess(sentence))

    # # n't/RB <--neg-- dream/VB
    # # print(is_askGenre(sentence))
    # compare_sentiment_analysis("I think so")
    # compare_sentiment_analysis("I don't think so")
