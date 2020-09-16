import csv
import json
import operator
import pandas as pd

from termcolor import colored

import helper_functions as helper
from food.resources.data_collection.json_to_csv import parse_datetime
from food.resources.recipes_DB.allrecipes.nodejs_scrapper import consts

with open(consts.json_xUsers_Xrecipes_path, 'r') as fDB:
    recipes_data = json.load(fDB)['recipes_data']

TO_REMOE = ['A2M45YGLOWMO4N', '5a89661caa46dd00016bc1bb', '5c71054a5444f60001ec032c', '5d595adfe1e7440001133597', '593a5560cc988600017935be', '5d7c060606189b0017ba79c9',
            '5baf6705848bbd0001d6fc8a', 'popo', '5df5143f58a5c738d0e197af-00', '5e2174afcf46ff459df4e238', "5b222aff59f9620001c109cb", "5aa67d76f053610001726e65",
            "5d767ab1abbb3200160bf2d6", "5d36e5a972282e0019605fa0", "5b9f7f9eaa0e0e0001573bd2", "5c65ed60d9c5be00017428bf", "5c39ed7a688b59000102a145",
            "5c337ffaca23620001b278e0", '5de3bc33cdff8e3beabfc96a', "5c4254f4d77d7c000189ac0f", "5b2a14d40ec82d0001d2721f", "5bafd12a70f8df0001be84a7",
            "5c4ef5379a3f430001757afe"]

REMOVE_BUT_PUT_BACK = ["fakeID", "5c322f84508b7a0001fcb70d"]

WRONG_IDS = {
    "1114022477": "5bdc4ebb1d6f32000183476a",
    "5b94fc0fc168f800011048": "5b94fc0fc168f80001104860",
    "5f58dd7050e39f080150a3f9": "5ecd1abd0c7d0703501a618f"
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
fnames = ["datacol_comp3_noexp2.json", "datacol_comp3_exp2.json", 'datacol_nocomp_noexp.json', 'datacol_nocomp_noexp2.json', 'datacol_comp2_noexp2.json', 'datacol_comp2_exp.json', "datacol_nocomp_exp.json",
          "datacol_comp3_exp3.json", "datacol_comp3_noexp3.json", "datacol_comp2_noexp3.json", "datacol_comp2_exp2.json", "datacol_nocom_noexp3.json",
          "datacol_nocomp_exp2.json"]
# fnames = []

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
    "datacol_comp2_exp.json": "explanations",
    "datacol_nocomp_exp.json": "explanations",
    "datacol_comp3_exp3.json": "explanations",
    "datacol_comp3_noexp3.json": "no explanations",
    "datacol_comp2_noexp3.json": "no explanations",
    "datacol_comp2_exp2.json": "explanations",
    "datacol_nocom_noexp3.json": "no explanations",
    "datacol_nocomp_exp2.json": "explanations"
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
    "datacol_comp2_exp.json": "2 recipes",
    "datacol_nocomp_exp.json": "1 recipe",
    "datacol_comp3_exp3.json": "3 recipes",
    "datacol_comp3_noexp3.json": "3 recipes",
    "datacol_comp2_noexp3.json": "2 recipes",
    "datacol_comp2_exp2.json": "2 recipes",
    "datacol_nocom_noexp3.json": "1 recipe",
    "datacol_nocomp_exp2.json": "1 recipe"
}

csv_all_rows = list()
first_row = ['prolific ID', 'file name', 'Explanation mode', 'Comparison mode', 'liked recipes', 'liked recipes healthscore', 'diet', 'time', 'ingredients',]
first_row += ['r1 title', 'r1 healthscore', 'r1 utility', 'r1 CF score', 'r2 title', 'r2 healthscore', 'r2 utility', 'r2 CF score', 'r3 title', 'r3 healthscore', 'r3 utility', 'r3 CF score', 'chosen']
first_row += ["chosen r healthy", "small-talk", "self disclosures", "feedback", "usefulness", "transparency", "ease of use", "authority", "liking", "trust", "satisfaction", "intention to cook", "intention of use", "recommendation accuracy"]
first_row += ["wants to eat healthy (1-5)", "likes coocking (1-5)", "cooking frequency", "healthy eating frequency", "CA familiarity"]
first_row += ['Age', 'Country of Birth', 'Current Country of Residence', 'Employment Status', 'First Language', 'Nationality', 'Sex', 'Student Status']

csv_all_rows.append(first_row)

def get_prolific_demographics(userid):
    row = df_prolific.loc[list(df_prolific['participant_id'] == userid)]
    # print(row.iloc[0]['Country of Birth'])
    return row.iloc[0]['age'], row.iloc[0]['Country of Birth'], row.iloc[0]['Current Country of Residence'], row.iloc[0]['Employment Status'], row.iloc[0]['First Language'], row.iloc[0]['Nationality'], row.iloc[0]['Sex'], row.iloc[0]['Student Status']

df_prolific = pd.read_csv(path+"prolific_export.csv")
print(get_prolific_demographics("5c6c8f79cf8909000144e8d4"))

def parse_json():

    for fname in fnames:
        with open(path+fname, 'r') as f:
            content = json.load(f)
            print(colored(fname, "green"))

            for key_user, data in content["Sessions"].items():

                if key_user!="false" and isinstance(data, dict) and "data_collection" in data.keys() and isinstance(data["data_collection"]['amt_id'], dict)\
                        and isinstance(data["data_collection"]['questionnaire_answers_q1'], dict):


                    new_row = list()
                    data_collection = data["data_collection"]
                    amtid = data_collection['amt_id']['value']
                    start_time = parse_datetime(data_collection['amt_id']['datetime'])

                    if amtid in WRONG_IDS.keys():
                        amtid = WRONG_IDS[amtid]
                    print(amtid)
                    # print("+"+amtid.strip()+"+")

                    if "lucile" in amtid or amtid.strip() in TO_REMOE or amtid in REMOVE_BUT_PUT_BACK:
                        pass

                    else:

                        age, c_birth, c_residence, employment, language, nationality, sex, student = get_prolific_demographics(amtid)


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
                                new_row.append(dialog_unit['utilities'][0])
                                new_row.append(dialog_unit['cf_scores'][0])
                                t1 = dialog_unit['titles'][0]
                                t2 = None
                                t3 = None
                                if len(rids) > 1:
                                    new_row.append(rids[1])
                                    new_row.append(get_healthScore(rids[1]))
                                    new_row.append(dialog_unit['utilities'][1])
                                    new_row.append(dialog_unit['cf_scores'][1])
                                    t2 = dialog_unit['titles'][1]
                                else:
                                    new_row += [None, None, None, None]
                                    # new_row += [None, None, None]
                                    new_row[3] = "1 recipe"
                                if len(rids) > 2:
                                    new_row.append(rids[2])
                                    new_row.append(get_healthScore(rids[2]))
                                    new_row.append(dialog_unit['utilities'][2])
                                    new_row.append(dialog_unit['cf_scores'][2])
                                    t3 = dialog_unit['titles'][2]
                                else:
                                    new_row += [None, None, None, None]
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


                        to_append = [age, c_birth, c_residence, employment, language, nationality, sex, student]
                        new_row += to_append

                # except KeyError:
                #     print(data['data_collection'])

    outFile = "res.csv"
    with open(path+outFile, 'w') as fcsv:
        csv_writer = csv.writer(fcsv)
        for row in csv_all_rows:
            csv_writer.writerow(row)


def match_ids():
    prolific_ids = list()

    participant_id_to_file_dict = dict()

    with open(path+"prolific_export.csv", 'r') as fcsv:
        csv_reader = csv.reader(fcsv, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count > 0 and row[2] != "RETURNED" and row[2] != "TIMEDOUT":
                prolific_ids.append(row[1])
            line_count += 1


    collected_ids = list()

    for fname in fnames:
        with open(path+fname, 'r') as f:
            content = json.load(f)

            for key_user, data in content["Sessions"].items():

                if key_user!="false" and isinstance(data, dict) and "data_collection" in data.keys() and isinstance(data["data_collection"]['amt_id'], dict)\
                        and isinstance(data["data_collection"]['questionnaire_answers_q1'], dict):
                    data_collection = data["data_collection"]
                    amtid = data_collection['amt_id']['value']
                    start_time = parse_datetime(data_collection['amt_id']['datetime'])
                    if amtid in WRONG_IDS.keys():
                        amtid = WRONG_IDS[amtid]
                    if "lucile" in amtid or amtid.strip() in TO_REMOE or amtid in REMOVE_BUT_PUT_BACK:
                        pass
                    else:
                        collected_ids.append(amtid)
                        participant_id_to_file_dict[amtid] = fname


    print("Particpants according to Prolific but we don't have their IDs...")
    diff1 = helper.diff_list(prolific_ids, collected_ids)
    diff1 = helper.diff_list(diff1, TO_REMOE)
    print(diff1)

    print("Our participants that we can't find in Prolific")
    diff2 = helper.diff_list(collected_ids, prolific_ids)
    print(diff2)
    for uid in diff2:
        print(participant_id_to_file_dict[uid])



if __name__ == "__main__":
    # match_ids()
    parse_json()
