import spacy
import dataparser
import food.NLU as food_NLU
import nlu_helper_functions as nlu_helper
import food.food_dataparser as food_dataparser
import movies.movies_nlu_functions as movies_NLU
import movies.movie_dataparser as movies_dataparser
import argparse
import helper_functions as helper
from ca_logging import log
import csv

def test_nlu(domain):
    q= False
    spacy_nlp = spacy.load("en_core_web_sm")
    if domain == "movies":
        voc = dataparser.parse_voc(f_domain_voc="movies/resources/nlu/movies_voc.json")
        directors_dicts = movies_dataparser.get_all_directors()
        actors_dicts = movies_dataparser.get_all_actors()
    elif domain == "food":
        voc = dataparser.parse_voc(f_domain_voc="food/resources/nlu/food_voc.json")
        food_list = food_dataparser.extensive_food_DBs.all_foods_list
    while(not q):
        utterance = input("Enter conversation_stage // utterance (q to quit): ")
        if utterance == 'q':
            q = True
        else:
            if domain == "movies":
                formula = movies_NLU.rule_based_nlu(utterance, spacy_nlp, voc=voc, directors_dicts=directors_dicts, actors_dicts=actors_dicts)
            elif domain == "food":
                if "//" in utterance:
                    conversation_stage, utterance = utterance.split('//')
                else:
                    conversation_stage = "default"
                formula = food_NLU.rule_based_nlu(utterance.strip(), spacy_nlp, voc, food_list, conversation_stage.strip())
            print(formula)
            # intent, entity, entitytype, polarity = nlu_helper.format_formula(formula)
            # print(intent, entity, entitytype, polarity)


def evaluate(domain, intent=None, out_file=None, get_missing_foods=False, to_print="wrong"):
    spacy_nlp = spacy.load("en_core_web_sm")
    if domain == "movies":
        voc = dataparser.parse_voc(f_domain_voc="movies/resources/nlu/movies_voc.json")
        directors_dicts = movies_dataparser.get_all_directors()
        actors_dicts = movies_dataparser.get_all_actors()
        log.ERROR("ERROR: no dataset")
        exit(0)
    elif domain == "food":
        voc = dataparser.parse_voc(f_domain_voc="food/resources/nlu/food_voc.json")
        food_list = food_dataparser.extensive_food_DBs.all_foods_list
        dataset = food_dataparser.get_dataset()
    got_right = 0
    with_intent = 0
    missing_foods = list()
    csv_lines = list()
    for elt in dataset:
        utterance, formula, conv_stage, id = elt["utterance"], elt["user_intent"], elt["conv_stage"], elt['id']
        if not intent or (intent == conv_stage):
            formula = list(formula.values())
            if domain == "movies":
                # f = movies_NLU.rule_based_nlu(utterance, spacy_nlp, voc=voc, directors_dicts=directors_dicts, actors_dicts=actors_dicts)
                log.critical("Changed stuff here, will not work")
                exit(-1)
            elif domain == "food":
                f = food_NLU.rule_based_nlu(utterance, spacy_nlp, voc, food_list, conv_stage)
            identical = helper.identical(f, formula)
            if identical:
                got_right += 1
            if to_print == 'all' or (not identical and to_print == "wrong"):
                if not identical:
                    if get_missing_foods:
                        # print(formula, f)
                        if f[1] and formula[1] and isinstance(f[1], list) and isinstance(formula[1], list):
                            missing_list = list(set(formula[1]) - set(f[1]))
                        elif formula[1] and isinstance(formula[1], list):
                            missing_list = formula[1]
                        else:
                            missing_list = list()
                        if missing_list:
                            for food in missing_list:
                                if food not in missing_foods:
                                    missing_foods.append(food)
                csv_lines.append([id, conv_stage, utterance,f , formula])
                print(id, conv_stage, utterance)
                print("Expected:", formula)
                print("Got:", f)
                print()
            with_intent += 1
    if get_missing_foods:
        print("Missing foods:")
        print(", ".join(missing_foods))
    total = float(with_intent) if intent else float(len(dataset))
    print("ACCURACY SCORE: %.2f (%d/%d)" % (got_right / total, got_right, total))
    if to_print == 'wrong':
        print("Printed only utterances for which we got it wrong")
    if out_file:
        with open(out_file, 'w') as fcsv:
            csv_writer = csv.writer(fcsv)
            for line in csv_lines:
                csv_writer.writerow(line)



if __name__ == "__main__":

    argp = argparse.ArgumentParser()
    argp.add_argument('domain', metavar='domain', type=str, help='Domain to test (e.g. movies? food?)')
    argp.add_argument("--eval", help="To evaluate the performance of NLU on the labeled dataset", action="store_true")
    argp.add_argument("--test", help="To test the NLU module yourself", action="store_true")
    argp.add_argument("--missing_foods", help="Do you want to print foods that NLU did not parse correctly?", action="store_true")
    argp.add_argument('-intent', metavar='intent', type=str, help='Intent you want to work on')
    argp.add_argument('-out_file', metavar='out_file', type=str, help='CSV file to write NLU errors.')

    args = argp.parse_args()

    if(args.domain in ["movies", "food"]):
        if (args.test):
            test_nlu(args.domain)
        elif (args.eval):
            evaluate(args.domain, args.intent, args.out_file, args.missing_foods)
