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
                data_participant = list()
                data_participant.append(data["xp_condition"])
                for key, value in data["data_collection"]["amt_id"].items():
                    if key != "client_id" and key != "datetime":
                        data_participant.append(value)
                        if first_line_bool:
                            first_line.append(key)
                for key, value in data["data_collection"]["demographics"].items():
                    if key != "client_id" and key != "datetime" and not any(w in key for w in ["feet", "pounds", "stones"]):
                        data_participant.append(value)
                        if first_line_bool:
                            first_line.append(key)
                for key, value in data["data_collection"]["food_diagnosis_answers"].items():
                    if key != "client_id" and key != "datetime":
                        data_participant.append(value)
                        if first_line_bool:
                            first_line.append(key)
                for key, value in data["data_collection"]["questionnaire_answers_q1"].items():
                    if key != "client_id" and key != "datetime":
                        data_participant.append(value)
                        if first_line_bool:
                            first_line.append(key)
                for key, value in data["data_collection"]["questionnaire_answers_q2"].items():
                    if key != "client_id" and key != "datetime":
                        data_participant.append(value)
                        if first_line_bool:
                            first_line.append(key)
                for key, value in data["data_recommendation"].items():
                    if key != "client_id" and key != "datetime":
                        data_participant.append(value)
                        if first_line_bool:
                            first_line.append(key)


            except :
                print(data)

            if first_line_bool:
                csv_writer.writerow(first_line)
                first_line_bool = False
            participant_data = [id[1:]] + data_participant
            csv_writer.writerow(participant_data)










