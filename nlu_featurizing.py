import nlu_functions
import argparse
import spacy
import dataparser
import csv
import math
import random

'''
features
f1 - Actor/director in sentence
f2 - voc_greetings in sentence
f3 - "already" in sentence
f4 - voc_request_more in sentence
f5 - voc_bye in sentence
f6 - voc_genres in sentence
f7 - verb is first word
f8 - what is 1st word
f9 - ["genre", "type", "kind"] in sentence
f10 - WDT / WP is first word tag
f11 - in / on in sentence
f12 - "actor", "act", "star", "cast" in sentence
f13 - by in sentence
f14 - "director", "direct" in sentence
f15 - "happen", "plot", "summary", "plot" in sentence
f16 - tag 1st word is WP
f17 - len(sentence) >3
f18 - voc_yes in sentece
f19 - voc_no in sentence

formulas:
1 askActor
2 askDirector
3 askGenre
4 askPlot
5 yes
6 no
7 greetings
8 goodbye
9 inform_cast
10 inform_genre
11 request_more
12 alreadyWatched
13 IDK
'''

SIZE_TESTSET = 0.2

def get_formula_code(formula):

    v = -1
    if "askActor" in formula:
        v = 1
    elif "askDirector" in formula:
        v = 2
    elif "askGenre" in formula:
        v = 3
    elif "askPlot" in formula:
        v = 4
    elif "greet" in formula:
        v = 7
    elif "goodbye" in formula or "bye" in formula:
        v = 8
    elif "inform" in formula:
        if "director" in formula or "actor" in formula or "cast" in formula.lower():
            v = 9
        elif "genre" in formula.lower():
            v = 10
        else:
            print("ERR with formula "+formula)
    elif "more" in formula:
        v = 11
    elif "alreadyWatched" in formula:
        v = 12
    elif "yes" == formula or formula == "affirmative":
        v = 5
    elif "no" == formula or formula == "negative":
        v = 6
    elif "IDK" == formula:
        v = 13
    else:
        print("ERR with formula "+formula)
    return v

def featurize(utterance, formula, voc, spacy_nlp, cast_dicts, verbose=False):

    utterance = nlu_functions.preprocess(utterance)
    document = spacy_nlp(utterance)
    capitalized_document = spacy_nlp(utterance.title())

    cast_list = nlu_functions.get_cast(capitalized_document, cast_dicts)
    f1 = 1 if cast_list and len(cast_list)>0 else 0

    f2 = 1 if nlu_functions.is_greeting(document, voc["greetings"]) else 0

    f3 = 1 if nlu_functions.is_alreadywatched(utterance) else 0

    f4 = 1 if nlu_functions.is_requestmore(document, voc["request_more"]) else 0

    f5 = 1 if nlu_functions.is_goodbye(document, utterance, voc["bye"]) else 0

    f7 = 1 if nlu_functions.is_verb(document[0]) else 0

    f8 = 1 if document[0].text == "what" else 0

    f10 = 1 if document[0].tag_ == "WDT" else 0

    f16 = 1 if document[0].tag_ == "WP" else 0

    f17 = 1 if len(document) > 3 else 0

    yes_no = nlu_functions.is_yes_no(document, utterance, voc["yes"], voc["no"])
    f18 = 1 if yes_no == "yes" else 0
    f19 = 1 if yes_no == "no" else 0

    f6, f9, f11, f12, f13, f14, f15 = 0, 0, 0, 0, 0, 0, 0
    for token in document:
        if token.lemma_ in voc["genres"]:
            f6 = 1
        elif token.lemma_ in ["genre", "type", "kind"]:
            f9 = 1
        elif token.dep == "prep":
            if token.text in ["in", "on"]:
                f11 = 1
            elif token.text == "by":
                f13 = 1
        elif token.lemma_ in ["actor", "act", "star", "cast"]:
            f12 = 1
        elif token.lemma_ in ["director", "direct"]:
            f14 = 1
        elif token.lemma_ in ["happen", "plot", "summary", "plot"]:
            f15 = 1

    rule_based_pred_text = nlu_functions.rule_based_nlu(utterance, spacy_nlp, voc, cast_dicts)
    rule_based_pred = get_formula_code(rule_based_pred_text)

    label = get_formula_code(formula)


    if verbose:
        print(label, rule_based_pred)
        print("1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9")
        print(f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11, f12, f13, f14, f15, f16, f17, f18, f19)
        print(formula)
        print(utterance, formula)

    return [label, rule_based_pred, f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11, f12, f13, f14, f15, f16, f17, f18, f19, utterance, formula]



def create_csv(dataset):

    spacy_nlp = spacy.load("en_core_web_sm")
    voc = dataparser.parse_voc()
    cast_dicts = dataparser.get_all_cast()

    rows_with_label = dict()
    l, i = len(dataset), 0

    for utterance, formula in dataset:
        i += 1
        print("Featurizing in progress: %d \r" % ((float(i)/l)*100), end='')
        row = featurize(utterance, formula, voc, spacy_nlp, cast_dicts)
        label = row[0]
        if label in rows_with_label.keys():
            rows_with_label[label].append(row)
        else:
            rows_with_label[label] = [row]

    first_row = ["label", "rule-based prediction", "\"actor\"/\"director\" in u", "voc greetings in u", "\"already\" in u", "vor request_more in u",
             "voc bye in u", "voc genres in u", "1st word is a verb", "\"what\" is 1st word", "\"genre\", \"type\", \"kind\" in u",
             "1st word POS tag is WDT", "\"in\" or \"on\" in u", "\"cast\", \"actor\", \"act\", \"star\" in u",
             "\"by\" in u", "\"director\", \"direct\" i u", "\"happen\", \"plot\", \"summary\" in u", "1st word POS tag is WP",
             "len(u)>3", "voc yes in u", "voc no in u", "utterance", "formula"]

    train_set, test_set = list(), list()
    train_set.append(first_row)
    test_set.append(first_row)

    for label, rows in rows_with_label.items():
        n_rows = len(rows)
        n_test_set = math.ceil(n_rows * 0.2)
        random.shuffle(rows)
        train_rows, test_rows = list(rows[:-n_test_set]), list(rows[-n_test_set:])
        # print(label, len(train_rows), len(test_rows), len(rows))
        for r in train_rows:
            train_set.append(r)
        for r in test_rows:
            test_set.append(r)

    fname_train = 'resources/nlu/nlu_chatito_dataset_train.csv'
    fname_test = 'resources/nlu/nlu_chatito_dataset_test.csv'

    with open(fname_train, 'w') as writeFile:
        writer = csv.writer(writeFile)
        writer.writerows(train_set)

    with open(fname_test, 'w') as writeFile:
        writer = csv.writer(writeFile)
        writer.writerows(test_set)

    print("Wrote train set in %s - %d examples" % (fname_train, (len(train_set)-1)))
    print("Wrote test set in %s - %d examples" % (fname_test, (len(test_set)-1)))


def test_featurizing():
    q= False
    spacy_nlp = spacy.load("en_core_web_sm")
    voc = dataparser.parse_voc()
    cast_dicts = dataparser.get_all_cast()
    while(not q):
        utterance = input("Enter text (q to quit): ")
        if utterance == 'q':
            q = True
        else:
            featurize(utterance, "", voc, spacy_nlp, cast_dicts, True)

if __name__ == "__main__":

    argp = argparse.ArgumentParser()
    # argp.add_argument("--eval", help="To evaluate the performance of NLU on the labeled dataset", action="store_true")
    argp.add_argument("--test", help="To test nlu featurizing", action="store_true")
    argp.add_argument("--featurize", help="To create a featurized dataset in csv to train ML NLU.", action="store_true")
    # argp.add_argument("--debug", help="Sentence to debug", action="store")

    args = argp.parse_args()

    if args.test:
        test_featurizing()
    elif args.featurize:
        dataset = dataparser.load_chatito_dataset()
        create_csv(dataset)
