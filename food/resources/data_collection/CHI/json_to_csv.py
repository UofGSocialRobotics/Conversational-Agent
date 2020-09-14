import csv
import json
import operator

from termcolor import colored

from food.resources.data_collection.json_to_csv import parse_datetime
from food.resources.recipes_DB.allrecipes.nodejs_scrapper import consts

with open(consts.json_xUsers_Xrecipes_path, 'r') as fDB:
    recipes_data = json.load(fDB)['recipes_data']

TO_REMOE = ['A2M45YGLOWMO4N', '5a89661caa46dd00016bc1bb', '5c71054a5444f60001ec032c', '5d595adfe1e7440001133597', '593a5560cc988600017935be', '5d7c060606189b0017ba79c9',
            '5baf6705848bbd0001d6fc8a', 'popo', '5df5143f58a5c738d0e197af-00', '5e2174afcf46ff459df4e238', "5b222aff59f9620001c109cb"]

WRONG_IDS = {
    "1114022477": "5bdc4ebb1d6f32000183476a"
}

def get_healthScore(rid):
    return recipes_data[rid]['FSAscore']

def get_avg_healthScore(rids_list):
    sum = 0
    for rid in rids_list:
        sum += get_healthScore(rid)
    return float(sum/len(rids_list))

path = 'food/resources/data_collection/CHI/'
# fnames = ["pilot_comp2_explanations.json", "pilot_comp2_noexplanations.json"]
# fnames = ["pilot2_comp2_explanations.json", "pilot2_comp2_noexplanations.json", "pilot2_comp3_explanations.json", "pilot2_comp3_no_explanations.json"]
# fnames = ["pilot2_comp3_explanations.json", "pilot2_comp3_no_explanations.json", "pilot3_comp3_no_explanations.json"]
fnames = ["datacol_comp3_noexp2.json", "datacol_comp3_exp2.json", 'datacol_nocomp_noexp.json', 'datacol_nocomp_noexp2.json', 'datacol_comp2_noexp2.json', 'datacol_comp2_exp.json']

fname_to_explanation_mode = {
    "pilot_comp2_explanations.json": "explanations",
    "pilot_comp2_noexplanations.json": "no explanation",
    "pilot2_comp2_explanations.json": "explanations",
    "pilot2_comp2_noexplanations.json": "no explanations",
    'pilot2_comp3_explanations.json': "explanations",
    "pilot2_comp3_no_explanations.json": "no explanations",
    "pilot3_comp3_no_explanations.json": "no explanations",
    "datacol_comp3_noexp.json": "no explanations",
    "datacol_comp3_noexp2.json": "no explanations",
    "datacol_comp3_exp2.json": "explanations",
    "datacol_nocomp_noexp.json": "no explanations",
    "datacol_nocomp_noexp2.json": "no explanations",
    "datacol_comp2_noexp.json": "no explanations",
    "datacol_comp2_noexp2.json": "no explanations",
    "datacol_comp2_exp.json": "explanations"
}

fname_to_comparison_mode = {
    "pilot_comp2_explanations.json": "2 recipes",
    "pilot_comp2_noexplanations.json": "2 recipes",
    "pilot2_comp2_explanations.json": "2 recipes",
    "pilot2_comp2_noexplanations.json": "2 recipes",
    "pilot2_comp3_explanations.json": "3 recipes",
    "pilot2_comp3_no_explanations.json": "3 recipes",
    "pilot3_comp3_no_explanations.json": "3 recipes",
    "datacol_comp3_noexp.json": "3 recipes",
    "datacol_comp3_noexp2.json": "3 recipes",
    "datacol_comp3_exp2.json": "3 recipes",
    "datacol_nocomp_noexp.json": "1 recipe",
    "datacol_nocomp_noexp2.json": "1 recipe",
    "datacol_comp2_noexp.json": "2 recipes",
    "datacol_comp2_noexp2.json": "2 recipes",
    "datacol_comp2_exp.json": "2 recipes"
}

csv_all_rows = list()
first_row = ['prolific ID', 'file name', 'Explanation mode', 'Comparison mode', 'liked recipes', 'liked recipes healthscore', 'diet', 'time', 'ingredients', 'r1 title', 'r1 healthscore', 'r2 title', 'r2 healthscore', 'r3 title', 'r3 healthscore', 'chosen']
first_row += ["chosen r healthy", "small-talk", "self disclosures", "feedback", "usefulness", "transparency", "ease of use", "authority", "liking", "trust", "satisfaction", "intention to cook", "intention of use", "recommendation accuracy"]
first_row += ["wants to eat healthy (1-5)", "likes coocking (1-5)", "cooking frequency", "healthy eating frequency", "CA familiarity"]
csv_all_rows.append(first_row)


for fname in fnames:
    with open(path+fname, 'r') as f:
        content = json.load(f)
        print(colored(fname,"green"))

        for key_user, data in content["Sessions"].items():

            if isinstance(data, dict) and "data_collection" in data.keys() and isinstance(data["data_collection"]['amt_id'], dict)\
                    and isinstance(data["data_collection"]['questionnaire_answers_q1'], dict):

                new_row = list()
                data_collection = data["data_collection"]
                amtid = data_collection['amt_id']['value']
                start_time = parse_datetime(data_collection['amt_id']['datetime'])

                print(amtid)
                # print("+"+amtid.strip()+"+")

                if "lucile" in amtid or amtid.strip() in TO_REMOE:
                    pass

                else:

                    new_row.append(amtid)
                    new_row.append(fname)
                    new_row.append(fname_to_explanation_mode[fname])
                    new_row.append(fname_to_comparison_mode[fname])

                    liked_recipes_cf = data['rs_data']['liked_recipes']
                    new_row.append(liked_recipes_cf)
                    new_row.append(get_avg_healthScore(liked_recipes_cf))

                    resp_like_recipe = False

                    parse_diet, parse_time, parse_ingredients = False, False, False

                    t1, t2 = None, None
                    for dialog_unit in data["dialog"].values():

                        if parse_diet:
                            answer = dialog_unit['text']
                            if answer == "None":
                                new_row.append(answer)
                            else:
                                new_row.append(answer[len("I have a "):-len(" diet")])
                            parse_diet = False
                        elif parse_time:
                            answer = dialog_unit['text'].replace("\n"," ").strip()
                            new_row.append(answer)
                            parse_time = False
                        elif parse_ingredients:
                            answer = dialog_unit['text'].replace("\n"," ").strip()
                            if len(answer) > 4:
                                answer = answer[len("I would like "):]
                            new_row.append(answer)
                            parse_ingredients = False

                        if resp_like_recipe:
                            # print(dialog_unit)
                            answer = dialog_unit['text']
                            if answer.lower().strip() == "No, I don't like the recipe".lower().strip() \
                                    or answer.lower().strip() == "I don't like either of the recipes".lower().strip() \
                                    or answer.lower().strip() == "I don't like any of the recipes".lower().strip():
                                new_row.append("none")
                            elif answer.lower().strip().replace("\n", " ") == "Yes, I like it!".lower().strip():
                                if t2:
                                    raise ValueError("We have 2 recipes but answer is I like it!!")
                                new_row.append("r1")
                            elif t1 in answer:
                                new_row.append("r1")
                            elif t2 and t2 in answer:
                                new_row.append("r2")
                            elif t3 and t3 in answer:
                                new_row.append("r3")
                            else:
                                raise ValueError(answer)

                            resp_like_recipe = False
                            csv_all_rows.append(new_row)

                        if isinstance(dialog_unit, dict) and "rids" in dialog_unit.keys():
                            rids = dialog_unit['rids']
                            new_row.append(rids[0])
                            new_row.append(get_healthScore(rids[0]))
                            t1 = dialog_unit['titles'][0]
                            t2 = None
                            t3 = None
                            if len(rids) > 1:
                                new_row.append(rids[1])
                                new_row.append(get_healthScore(rids[1]))
                                t2 = dialog_unit['titles'][1]
                            else:
                                new_row.append(None)
                                new_row.append(None)
                                new_row[3] = "1 recipe"
                            if len(rids) > 2:
                                new_row.append(rids[2])
                                new_row.append(get_healthScore(rids[2]))
                                t3 = dialog_unit['titles'][2]
                            else:
                                new_row.append(None)
                                new_row.append(None)
                                # new_row[3] = "1 recipe"

                            resp_like_recipe = True


                        if isinstance(dialog_unit, dict) and "source" in dialog_unit.keys() and dialog_unit['source'] == "agent":
                            if "Any specific diet or intolerance I should be aware of?" in dialog_unit['sentence']:
                                parse_diet = True
                            elif "How much time do you want to spend cooking?" in dialog_unit['sentence']:
                                parse_time = True
                            elif "Is there any food you'd like to use? Something already in your kitchen or that you could buy?" in dialog_unit['sentence']:
                                parse_ingredients = True


                    questionnaire_answers_list = list()
                    for qid, v in data_collection['questionnaire_answers_q1'].items():
                        if "question" in qid:
                            qid_n = int(qid.replace("question", ""))
                            questionnaire_answers_list.append((qid_n, int(v)))
                    if len(questionnaire_answers_list) == 13:
                        questionnaire_answers_list.append((0, None))
                    questionnaire_answers_list = [v for (_, v) in sorted(questionnaire_answers_list, key=operator.itemgetter(0), reverse=False)]
                    new_row += questionnaire_answers_list

                    demographics = data_collection['demographics']
                    # first_row += ["wants to eat healthy (1-5)", "likes coocking (1-5)", "cooking frequency", "healthy eating frequency", "CA familiarity"]
                    new_row.append(int(demographics['want_to_eat_healthy']))
                    new_row.append(int(demographics['like_cooking']))
                    new_row.append(demographics['freq_cook'])
                    new_row.append(demographics['healthy_food'])
                    new_row.append(demographics['CA_familiarity'])






outFile = "res.csv"
with open(path+outFile, 'w') as fcsv:
    csv_writer = csv.writer(fcsv)
    for row in csv_all_rows:
        csv_writer.writerow(row)

