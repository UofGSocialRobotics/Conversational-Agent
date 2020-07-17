import csv
import json
import operator
import statistics
import pandas as pd
import numpy as np
from termcolor import colored
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.stats import ttest_ind

import food.resources.recipes_DB.allrecipes.nodejs_scrapper.consts as consts
import helper_functions as helper
from food.resources.data_collection.json_to_csv import parse_datetime, to_seconds

json_path = "food/resources/data_collection/healthRecSys/pilot_pref.json"
csv_path = "food/resources/data_collection/healthRecSys/pilot_pref.csv"
# json_path = "pilot_hybrid_wtags.json"
# csv_path = "pilot_hybrid_wtags.csv"

DEMOGRAPHICS = True
STARS_EVAL = False
ANONYMIZED = False

BLOCKED_WORKERS = ['A16KAOOWIMYBF6', 'A3R6Z6HDL5JGM6']

# files_list = ['pilot_pref', 'pilot_health', 'pilot_hybrid2',  'pilot_pref_wtags', 'pilot_health_wtags', 'pilot_hybrid_wtags2', 'test']
files_list = ['pilot_pref', 'pilot_pref2', 'pilot_health', 'health', 'pilot_hybrid_coef31', 'hybrid_coef31',  'pilot_pref_wtags', 'pref_wtags', 'pilot_health_wtags', 'health_wtags', 'pilot_hybrid_wtags31', 'hybrid31_wtags']
if not DEMOGRAPHICS:
    files_list = ['pilot_pref', 'pilot_pref2', 'pilot_health', 'pilot_hybrid', 'pilot_hybrid_coef21', 'pilot_hybrid_coef31', 'pilot_hybrid_coef31_notrandom_292', 'pilot_hybrid_coef31_notrandom_75', 'pilot_pref_wtags', 'pilot_health_wtags', 'pilot_hybrid_wtags', 'pilot_hybrid_wtags31']
if STARS_EVAL:
    files_list = ['s_pilot_pref', 's_pilot_health', 's_pilot_hybrid', 's_pilot_hybrid_wtags', 's_pilot_health_wtags', 's_pilot_pref_wtags']

dir = "food/resources/data_collection/healthRecSys/"

healthy_food_num_dict = {"no": 0, "occasionnaly":1, "most_times":2, "always":3}
employment_num_dict = {"unemployed":0, "student":1, "part-time":2, "full-time":3}
gender_num = {"male":0, "female":1, 'other':2}
education_num_dict = {"secondary": 0, "college": 1, "udergrad":2, "graduate":3, "PhD":4}
freq_cook_num_dict = {"never": 0, "occasionnaly":1, "once_w":2, "several_t_w":3, "once_day": 4}


with open(consts.json_xUsers_Xrecipes_path, 'r') as fDB:
    recipes_data = json.load(fDB)['recipes_data']


def get_healthScore(rid):
    return recipes_data[rid]['FSAscore']

def get_avg_healthScore(rids_list):
    sum = 0
    for rid in rids_list:
        sum += get_healthScore(rid)
    return float(sum/len(rids_list))



def json_to_csv():
    csv_all_rows = list()

    rs_eval_header = ['AUC', "FN", 'FP', 'N', 'N_predict', 'P', "P_predict", 'TN', 'TP', 'accuracy', 'cond', 'f1', 'final_score_others', 'final_score_reco', 'precision', 'pref_score_others', 'pref_scores_reco', 'recall', 'reco', 'reco health score', 'total_recommended_recipes']
    rs_eval_header.sort()

    if ANONYMIZED:
        first_row = []
    else:
        first_row = ["amtid"]

    if not STARS_EVAL:
        first_row += ['cond', 'file']
        first_row += rs_eval_header
    else:
        first_row += ['file']

    first_row += [
         'recipes learn pref', 'health score learn pref', "normed health score learn pref", '# rightClicks learn pref', 'right-clicked recipes learn pref']

    if not STARS_EVAL:
        first_row += [
                 'recipes eval', 'health score eval', "normed health score eval", '# rightClicks eval', 'right-clicked recipes eval',
                 'satisfaction', 'easiness', 'influence_most', 'rs_satisfaction_comments']
    else:
        first_row += ['ratings', "ratings avg", 'ratings std']

    if DEMOGRAPHICS:
        first_row += [
                 'whats_important', 'free_comment',
                 'healthiness habits', 'normed healthiness habits', 'fillingness habits', 'normed fillingness habits',
                 'age', 'gender', 'gender_num', 'from', 'where', 'education', 'education_num', 'employment', 'employment_num', 'freq_cook', 'freq_cook_num', 'healthy_food', "healthy_food_num",
                 'duration', "duration_sec", 'duration_AMT_sec'
                 ]

    keys_to_check_for = ['final_score_others', 'final_score_reco', 'pref_score_others', 'pref_score_reco']

    csv_all_rows.append(first_row)

    amtid_to_duration = dict()
    amtid_to_creation_time = dict()
    with open(dir+"HealthRecSys_batch_all.csv") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            amtid_to_duration[row[15]] = row[23]
            amtid_to_creation_time[row[15]] = row[6]


    for file_name in files_list:

        path = dir+file_name+'.json'
        with open(path, 'r') as fjson:
            print(path)

            with_tag = ""

            if "wtags" in file_name:
                with_tag = "_with_tags"

            content = json.load(fjson)

            for key_user, data in content["Sessions"].items():

                if not STARS_EVAL:
                    cond = isinstance(data, dict) and 'rs_eval_data' in data.keys() and isinstance(data["data_collection"]['rs_satisfaction'], dict)
                else:
                    cond = isinstance(data, dict) and "data_collection" in data.keys() and ('recipe_ratings' in data["data_collection"].keys())

                if cond:

                    last_cond = isinstance(data["data_collection"]['demographics'], dict)
                    if not DEMOGRAPHICS:
                        last_cond = True

                    if last_cond:

                        # try:
                        csv_row = list()
                        data_collection = data["data_collection"]
                        amtid = data_collection['amt_id']['value']
                        start_time = parse_datetime(data_collection['amt_id']['datetime'])

                        # print(amtid)
                        if "lucile" in amtid or amtid in BLOCKED_WORKERS:
                            pass
                        else:
                            if not ANONYMIZED:
                                csv_row.append(amtid)

                            if not STARS_EVAL:

                                rs_eval_data = data['rs_eval_data']

                                csv_row.append(rs_eval_data['cond']+with_tag)

                            csv_row.append(file_name.replace("pilot_", "p_"))

                            if not STARS_EVAL:
                                for k_to_check in keys_to_check_for:
                                    if k_to_check not in rs_eval_data.keys():
                                        rs_eval_data[k_to_check] = -1

                                tmp_list = list()
                                for key, val in rs_eval_data.items():
                                    tmp_list.append([key, val])
                                tmp_list = sorted(tmp_list, key=operator.itemgetter(0))
                                # print(tmp_list)

                                for key, val in tmp_list:
                                    csv_row.append(val)
                                    if key == 'reco':
                                        csv_row.append(get_avg_healthScore(val))


                            for dialog_unit in data["dialog"].values():
                                # print(dialog_unit)
                                if isinstance(dialog_unit, dict) and "liked_recipes" in dialog_unit.keys() and isinstance(dialog_unit['liked_recipes'], list):
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

                            if STARS_EVAL:
                                recipe_ratings = data_collection['recipe_ratings']
                                csv_row.append(recipe_ratings)
                                ratings = [y for [x, y] in recipe_ratings]
                                avg_ratings = statistics.mean(ratings)
                                std_ratings = statistics.stdev(ratings)
                                csv_row.append(avg_ratings)
                                csv_row.append(std_ratings)


                            if DEMOGRAPHICS:
                                rs_post_study_anwers = data_collection['rs_post_study_answers']
                                whats_important = rs_post_study_anwers['whats_important']
                                free_comment = rs_post_study_anwers['free_comment']

                            if not STARS_EVAL:
                                rs_satisfaction = data_collection['rs_satisfaction']
                                satisfaction = rs_satisfaction['satisfaction']
                                easiness = rs_satisfaction['easiness']
                                influence = rs_satisfaction['influence']
                                rs_satisfaction_comments = rs_satisfaction['comments']
                                csv_row.append(satisfaction)
                                csv_row.append(easiness)
                                csv_row.append(influence)
                                csv_row.append(rs_satisfaction_comments)

                            if DEMOGRAPHICS:
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
                                stop_time = parse_datetime(demographics['datetime'])
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
                                csv_row.append(gender_num[gender])
                                csv_row.append(isfrom)
                                csv_row.append(where)
                                csv_row.append(education)
                                csv_row.append(education_num_dict[education])
                                csv_row.append(employment)
                                csv_row.append(employment_num_dict[employment[0]])
                                csv_row.append(freq_cook)
                                csv_row.append(freq_cook_num_dict[freq_cook])
                                csv_row.append(healthy_food)

                                csv_row.append(healthy_food_num_dict[healthy_food])

                                total_time = stop_time-start_time
                                csv_row.append(total_time)
                                csv_row.append(to_seconds(total_time))
                                try:
                                    csv_row.append(amtid_to_duration[amtid])
                                    print(amtid_to_creation_time[amtid])
                                except KeyError:
                                    print(colored("Did not find %s in batch" % amtid,"blue"))
                                    csv_row.append("")



                            if len(csv_row) == len(first_row):
                                csv_all_rows.append(csv_row)
                            else:
                                print("Discarding AMT %s (firebase sessions' key: %s \\\\ %d %d)" % (amtid, key_user, len(csv_row), len(first_row)))

                    # except:
                    #     pass


    if ANONYMIZED:
        anon_str = "_anonymized"
    else:
        anon_str = ""

    if STARS_EVAL:
        outFile = dir+"starEval_all"+anon_str+".csv"
    else:
        outFile = dir+"all"+anon_str+".csv"
    with open(outFile, 'w') as fcsv:
        csv_writer = csv.writer(fcsv)
        for row in csv_all_rows:
            csv_writer.writerow(row)


def json_to_csv_health_scores_reco():
    csv_all_rows = list()

    first_row = ["amtid", 'cond', 'file', 'reco health score']

    csv_all_rows.append(first_row)

    for file_name in files_list:

        path = dir+file_name+'.json'
        with open(path, 'r') as fjson:
            print(path)

            with_tag = ""

            if "wtags" in file_name:
                with_tag = "_with_tags"

            content = json.load(fjson)

            for key_user, data in content["Sessions"].items():
                if isinstance(data, dict) and 'rs_eval_data' in data.keys() and isinstance(data["data_collection"]['rs_satisfaction'], dict):

                    last_cond = isinstance(data["data_collection"]['demographics'], dict)
                    if not DEMOGRAPHICS:
                        last_cond = True

                    if last_cond:

                        data_collection = data["data_collection"]
                        amtid = data_collection['amt_id']['value']


                        if "lucile" in amtid:
                            pass
                        else:

                            rs_eval_data = data['rs_eval_data']
                            reco = rs_eval_data['reco']
                            cond = rs_eval_data['cond']+with_tag
                            file_str = file_name.replace("pilot_", "p_")
                            for rid in reco:
                                new_row = list()
                                new_row.append(amtid)
                                new_row.append(cond)
                                new_row.append(file_str)
                                new_row.append(get_healthScore(rid))
                                csv_all_rows.append(new_row)


    with open(dir+"reco_health_scores.csv", 'w') as fcsv:
        csv_writer = csv.writer(fcsv)
        for row in csv_all_rows:
            csv_writer.writerow(row)


def count_reasons_for_choice():
    reasons_dict = dict()
    total_user = 0

    for file_name in files_list:

        path = dir+file_name+'.json'
        with open(path, 'r') as fjson:
            print(path)

            content = json.load(fjson)

            for key_user, data in content["Sessions"].items():
                if isinstance(data, dict) and 'rs_eval_data' in data.keys() and isinstance(data["data_collection"]['rs_satisfaction'], dict) and isinstance(data["data_collection"]['demographics'], dict):

                    data_collection = data["data_collection"]
                    amtid = data_collection['amt_id']['value']
                    if "lucile" in amtid:
                        pass
                    else:
                        total_user += 1
                        data_collection = data["data_collection"]
                        rs_post_study_anwers = data_collection['rs_post_study_answers']
                        whats_important = rs_post_study_anwers['whats_important']
                        free_comment = rs_post_study_anwers['free_comment']
                        if free_comment and free_comment.lower() != "no" and free_comment.lower() != "nothing" and free_comment.lower() != "good" and free_comment.lower() != "none":
                            print(free_comment)
                        for elt in whats_important:
                            if elt not in reasons_dict.keys():
                                reasons_dict[elt] = 0
                            reasons_dict[elt] += 1

    print(total_user)
    l = list()
    for k, v in reasons_dict.items():
        l.append((k,v))

    l = sorted(l, key=operator.itemgetter(1), reverse=True)
    for elt in l:
        print(elt[0], elt[1])


def compute_similarities_reco_vs_selected_recipes():
    with open(dir+'all.csv') as csvfile:

        csv_reader = csv.reader(csvfile, delimiter=',')
        row_count = 0
        sim_scores_reco = list()
        sim_scores_selected = list()
        for row in csv_reader:
            if row_count > 0:
                reco_list = row[21].replace('[',"").replace(']',')').replace("'","").split(",")
                selected_list = row[29].replace('[',"").replace(']',')').replace("'","").split(",")
                reco_list = [x.split('/')[1].replace('-', ' ') for x in reco_list]
                selected_list = [x.split('/')[1].replace('-', ' ') for x in selected_list]
                # print(reco_list, selected_list)

                count_vectorizer = CountVectorizer(stop_words='english')
                count_vectorizer = CountVectorizer()
                sparse_matrix_reco = count_vectorizer.fit_transform(reco_list)
                doc_term_matrix_reco = sparse_matrix_reco.todense()
                df_reco = pd.DataFrame(doc_term_matrix_reco, columns=count_vectorizer.get_feature_names())
                cosine_matrix_reco = cosine_similarity(df_reco, df_reco)

                sparse_matrix_selected = count_vectorizer.fit_transform(selected_list)
                doc_term_matrix_selected = sparse_matrix_selected.todense()
                df_selected = pd.DataFrame(doc_term_matrix_selected, columns=count_vectorizer.get_feature_names())
                cosine_matrix_selected = cosine_similarity(df_selected, df_selected)

                sim_scores_reco.append(np.mean(cosine_matrix_reco))
                sim_scores_selected.append(np.mean(cosine_matrix_selected))

                # print(np.mean(cosine_matrix_reco), np.mean(cosine_matrix_selected))


            row_count += 1

        print("Avg sim selected:", statistics.mean(sim_scores_selected), statistics.stdev(sim_scores_selected))
        print("Avg sim reco:", statistics.mean(sim_scores_reco), statistics.stdev((sim_scores_reco)))

        t, p = ttest_ind(sim_scores_selected, sim_scores_reco, equal_var=False)
        print(t, p)


if __name__ == "__main__":
    # json_to_csv()
    # json_to_csv_health_scores_reco()
    # count_reasons_for_choice()
    compute_similarities_reco_vs_selected_recipes()
