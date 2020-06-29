import csv
import json
import food.resources.recipes_DB.allrecipes.nodejs_scrapper.consts as consts
import helper_functions as helper

json_path = "food/resources/data_collection/healthRecSys/pilot_pref.json"
csv_path = "food/resources/data_collection/healthRecSys/pilot_pref.csv"
# json_path = "pilot_hybrid_wtags.json"
# csv_path = "pilot_hybrid_wtags.csv"

files_list = ['pilot_pref', 'pilot_health', 'pilot_hybrid', 'pilot_health_wtags', 'pilot_hybrid_wtags']
dir = "food/resources/data_collection/healthRecSys/"


with open(consts.json_xUsers_Xrecipes_path, 'r') as fDB:
    recipes_data = json.load(fDB)['recipes_data']


def get_healthScore(rid):
    return recipes_data[rid]['FSAscore']

def get_avg_healthScore(rids_list):
    sum = 0
    for rid in rids_list:
        sum += get_healthScore(rid)
    return float(sum/len(rids_list))


csv_all_rows = list()

first_row = ["amtid", 'cond',
             'AUC', "FN", 'FP', 'N', 'N_predict', 'P', "P_predict", 'TN', 'TP', 'accuracy', 'cond', 'f1', 'precision', 'recall', 'reco', 'total_recommended_recipes',
             'recipes learn pref', 'health score learn pref', "normed health score learn pref", '# rightClicks learn pref', 'right-clicked recipes learn pref',
             'recipes eval', 'health score eval', "normed health score eval", '# rightClicks eval', 'right-clicked recipes eval',
             'satisfaction', 'easiness', 'influence_most', 'rs_satisfaction_comments', 'whats_important', 'free_comment',
             'healthiness habits', 'normed healthiness habits', 'fillingness habits', 'normed fillingness habits',
             'age', 'gender', 'from', 'where', 'education', 'employment', 'freq_cook', 'healthy_food',
             ]

csv_all_rows.append(first_row)

for file_name in files_list:

    with open(dir+file_name+'.json', 'r') as fjson:

        with_tag = ""

        if "wtags" in file_name:
            with_tag = "_with_tags"

        content = json.load(fjson)

        for key, data in content["Sessions"].items():
            if isinstance(data, dict) and 'rs_eval_data' in data.keys() and isinstance(data["data_collection"]['demographics'], dict):
                # try:
                csv_row = list()
                data_collection = data["data_collection"]
                amtid = data_collection['amt_id']['value']
                if "lucile" in amtid:
                    pass
                else:
                    csv_row.append(amtid)

                    rs_eval_data = data['rs_eval_data']

                    csv_row.append(rs_eval_data['cond']+with_tag)

                    for val in rs_eval_data.values():
                        csv_row.append(val)

                    for dialog_unit in data["dialog"].values():
                        # print(dialog_unit)
                        if isinstance(dialog_unit, dict) and "liked_recipes" in dialog_unit.keys() and isinstance(dialog_unit['liked_recipes'], list):
                            liked_recipes = list()
                            right_clicked_recipes = list()
                            liked_recipes = dialog_unit['liked_recipes']
                            avg_healthScore = get_avg_healthScore(liked_recipes)
                            if "right_clicked_recipes" in dialog_unit.keys():
                                right_clicked_recipes = dialog_unit["right_clicked_recipes"]
                                # print("Found right clicks!")

                            n_right_clicks = len(right_clicked_recipes)

                            csv_row.append(liked_recipes)
                            csv_row.append(avg_healthScore)
                            csv_row.append(helper.norm_value_between_zero_and_one(avg_healthScore, 4, 12))
                            csv_row.append(n_right_clicks)
                            csv_row.append(right_clicked_recipes)


                    rs_post_study_anwers = data_collection['rs_post_study_answers']
                    whats_important = rs_post_study_anwers['whats_important']
                    free_comment = rs_post_study_anwers['free_comment']
                    rs_satisfaction = data_collection['rs_satisfaction']
                    satisfaction = rs_satisfaction['satisfaction']
                    easiness = rs_satisfaction['easiness']
                    influence = rs_satisfaction['influence']
                    rs_satisfaction_comments = rs_satisfaction['comments']
                    csv_row.append(satisfaction)
                    csv_row.append(easiness)
                    csv_row.append(influence)
                    csv_row.append(rs_satisfaction_comments)
                    csv_row.append(whats_important)
                    csv_row.append(free_comment)


                    food_diagnosis_answers = data_collection['food_diagnosis_answers']
                    answers_dict = dict()
                    h, f = 0, 0
                    for key, value in food_diagnosis_answers.items():
                        if "question" in key:
                            answers_dict[int(key[len("question"):])] = int(value)
                    for key, value in answers_dict.items():
                        if key == 1: # broccoli
                            h += value
                        elif key == 2: # Chips
                            h -= value
                        elif key == 3: # carrots
                            h += value
                        elif key == 4: # pizza
                            h -= value
                            f += value
                        elif key == 5: # tomatoes
                            f -= value
                        elif key == 6: # pasta
                            f += value
                        elif key == 7: # lettuce
                            f -= value

                    h, f = float(h) / 24, float(f) / 24
                    csv_row.append(h)
                    csv_row.append(helper.norm_value_between_zero_and_one(h, -1, 1))
                    csv_row.append(f)
                    csv_row.append(helper.norm_value_between_zero_and_one(f, -1, 1))

                    demographics = data_collection['demographics']
                    age = demographics['age']
                    gender = demographics['gender']
                    isfrom = demographics['from']
                    where = demographics['where']
                    education = demographics['education']
                    freq_cook = demographics['freq_cook']
                    healthy_food = demographics['healthy_food']
                    employment = demographics['employment']
                    csv_row.append(age)
                    csv_row.append(gender)
                    csv_row.append(isfrom)
                    csv_row.append(where)
                    csv_row.append(education)
                    csv_row.append(employment)
                    csv_row.append(freq_cook)
                    csv_row.append(healthy_food)



                    if len(csv_row) == len(first_row):
                        csv_all_rows.append(csv_row)
                    else:
                        print("Discarding AMT %s (firebase sessions' key: %s)" % (amtid, key))

                # except:
                #     pass


with open(dir+"all.csv", 'w') as fcsv:
    csv_writer = csv.writer(fcsv)
    for row in csv_all_rows:
        csv_writer.writerow(row)
