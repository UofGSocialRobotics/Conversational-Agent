import csv
import json

path = "food/resources/data.json"
csv_path = "food/resources/data.csv"

with open(path, 'r') as f:
    with open(csv_path, 'w') as fcsv:
        csv_writer = csv.writer(fcsv)

        content = json.load(f)
        sessions = content["Sessions"]
        first_line = list()
        first_line_bool = True
        for id, data in sessions.items():
            if first_line_bool:
                first_line.append("id")
            try:
                # print(data)
                prolific_id = data["data_collection"]["amt_id"]["value"]
                data_demo = list()
                # for data_demo_key, data_demo_val in data["data_collection"]["demographics"].items():
                #     if data_demo_key != "client_id" and data_demo_key != "datetime":
                #         data_demo.append(data_demo_val)
                #     if "feet_in" not in data["data_collection"]["demographics"].keys():
                #         data_demo.append()
                data_food_q = list()
                for data_food_key, data_food_val in data["data_collection"]["food_diagnosis_answers"].items():
                    if data_food_key != "client_id" and data_food_key != "datetime":
                        data_food_q.append(data_food_val)
                        if first_line_bool:
                            first_line.append(data_food_key)
                data_questionnaire_1 = list()
                for key, value in data["data_collection"]["questionnaire_answers_q1"].items():
                    if key != "client_id" and key != "datetime":
                        data_questionnaire_1.append(value)
                        if first_line_bool:
                            first_line.append(key)
                for key, value in data["data_collection"]["questionnaire_answers_q2"].items():
                    if key != "client_id" and key != "datetime":
                        data_questionnaire_1.append(value)
                        if first_line_bool:
                            first_line.append(key)
                for key, value in data["data_recommendation"].items():
                    if key != "client_id" and key != "datetime":
                        data_questionnaire_1.append(value)
                        if first_line_bool:
                            first_line.append(key)

                data_questionnaire_1.append(data["xp_condition"])

            except :
                print(data)

            if first_line_bool:
                csv_writer.writerow(first_line)
                first_line_bool = False
            participant_data = [id] + data_demo + data_food_q + data_questionnaire_1

            csv_writer.writerow(participant_data)










