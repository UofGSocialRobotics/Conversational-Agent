import spacy
import dataparser
import food.NLU as food_NLU
import nlu_helper_functions as nlu_helper
import food.food_dataparser as food_dataparser
import movies.movies_nlu_functions as movies_NLU
import movies.movie_dataparser as movies_dataparser
import argparse
import helper_functions as helper

def test_nlu(domain):
    q= False
    spacy_nlp = spacy.load("en_core_web_sm")
    if domain == "movies":
        voc = dataparser.parse_voc(f_domain_voc="movies/resources/nlu/movies_voc.json")
        directors_dicts = movies_dataparser.get_all_directors()
        actors_dicts = movies_dataparser.get_all_actors()
    elif domain == "food":
        voc = dataparser.parse_voc(f_domain_voc="food/resources/nlu/food_voc.json")
        food_list = food_dataparser.get_food_names()
    while(not q):
        utterance = input("Enter text (q to quit): ")
        if utterance == 'q':
            q = True
        else:
            if domain == "movies":
                formula = movies_NLU.rule_based_nlu(utterance, spacy_nlp, voc=voc, directors_dicts=directors_dicts, actors_dicts=actors_dicts)
            elif domain == "food":
                formula = food_NLU.rule_based_nlu(utterance, spacy_nlp, voc, food_list)
            print(formula)
            # intent, entity, entitytype, polarity = nlu_helper.format_formula(formula)
            # print(intent, entity, entitytype, polarity)


def evaluate(domain, to_print="wrong"):
    spacy_nlp = spacy.load("en_core_web_sm")
    if domain == "movies":
        voc = dataparser.parse_voc(f_domain_voc="movies/resources/nlu/movies_voc.json")
        directors_dicts = movies_dataparser.get_all_directors()
        actors_dicts = movies_dataparser.get_all_actors()
        log.ERROR("ERROR: no dataset")
        exit(0)
    elif domain == "food":
        voc = dataparser.parse_voc(f_domain_voc="food/resources/nlu/food_voc.json")
        food_list = food_dataparser.get_food_names()
        dataset = food_dataparser.get_dataset()
    got_right = 0
    for utterance, formula in dataset:
        if domain == "movies":
            f = movies_NLU.rule_based_nlu(utterance, spacy_nlp, voc=voc, directors_dicts=directors_dicts, actors_dicts=actors_dicts)
        elif domain == "food":
            f = food_NLU.rule_based_nlu(utterance, spacy_nlp, voc, food_list)
        identical = helper.identical(f, formula)
        if identical:
            got_right += 1
        if to_print == 'all' or (not identical and to_print == "wrong"):
            print(utterance)
            print(formula)
            print(f)
            print()
    print("ACCURACY SCORE: %.2f (%d/%d)" % (got_right / float(len(dataset)), got_right, len(dataset)))
    if to_print == 'wrong':
        print("Printed only utterances for which we got it wrong")



if __name__ == "__main__":

    argp = argparse.ArgumentParser()
    argp.add_argument('domain', metavar='domain', type=str, help='Domain to test (e.g. movies? food?)')
    argp.add_argument("--eval", help="To evaluate the performance of NLU on the labeled dataset", action="store_true")
    argp.add_argument("--test", help="To test the NLU module yourself", action="store_true")

    args = argp.parse_args()

    if(args.domain in ["movies", "food"]):
        if (args.test):
            test_nlu(args.domain)
        elif (args.eval):
            evaluate(args.domain)
