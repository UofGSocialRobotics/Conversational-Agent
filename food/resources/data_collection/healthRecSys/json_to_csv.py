import csv
import json

# json_path = "food/resources/data_collection/healthRecSys/pilot_pref.json"
# csv_path = "food/resources/data_collection/healthRecSys/pilot_pref.csv"
json_path = "pilot_pref.json"
csv_path = "pilot_pref.csv"

with open(json_path, 'r') as fjson:
    content = json.load(fjson)
    csv_all_rows = list()

    first_row = ["amtid",
                 'AUC', "FN", 'FP', 'N', 'N_predict', 'P', "P_predict", 'TN', 'TP', 'accuracy', 'cond', 'f1', 'precision', 'recall', 'reco', 'total_recommended_recipes',
                 'age', 'gender', 'from', 'where', 'education', 'employment', 'freq_cook', 'healthy_food',
                 'satisfaction', 'easiness', 'influence_most', 'rs_satisfaction_comments', 'whats_important', 'free_comment']

    csv_all_rows.append(first_row)

    for key, data in content["Sessions"].items():
        if isinstance(data, dict) and 'rs_eval_data' in data.keys() and isinstance(data["data_collection"]['demographics'], dict):
            # try:
            csv_row = list()
            data_collection = data["data_collection"]
            amtid = data_collection['amt_id']['value']
            demographics = data_collection['demographics']
            age = demographics['age']
            gender = demographics['gender']
            isfrom = demographics['from']
            where = demographics['where']
            education = demographics['education']
            freq_cook = demographics['freq_cook']
            healthy_food = demographics['healthy_food']
            employment = demographics['employment']
            rs_post_study_anwers = data_collection['rs_post_study_answers']
            whats_important = rs_post_study_anwers['whats_important']
            free_comment = rs_post_study_anwers['free_comment']
            rs_satisfaction = data_collection['rs_satisfaction']
            satisfaction = rs_satisfaction['satisfaction']
            easiness = rs_satisfaction['easiness']
            influence = rs_satisfaction['influence']
            rs_satisfaction_comments = rs_satisfaction['comments']
            csv_row.append(amtid)

            rs_eval_data = data['rs_eval_data']
            for val in rs_eval_data.values():
                csv_row.append(val)

            csv_row.append(age)
            csv_row.append(gender)
            csv_row.append(isfrom)
            csv_row.append(where)
            csv_row.append(education)
            csv_row.append(employment)
            csv_row.append(freq_cook)
            csv_row.append(healthy_food)
            csv_row.append(satisfaction)
            csv_row.append(easiness)
            csv_row.append(influence)
            csv_row.append(rs_satisfaction_comments)
            csv_row.append(whats_important)
            csv_row.append(free_comment)

            csv_all_rows.append(csv_row)

            # except:
            #     pass


    with open(csv_path, 'w') as fcsv:
        csv_writer = csv.writer(fcsv)
        for row in csv_all_rows:
            csv_writer.writerow(row)
