import csv
import json
import datetime

path = "food/resources/data.json"
csv_path = "food/resources/data.csv"

def format_date_splited_at_separator(date_val, separator):
    date_splited_at_slash = date_val.split(separator)
    if len(date_splited_at_slash[0]) == 1:
        date_splited_at_slash[0] = '0' + date_splited_at_slash[0]
    if len(date_splited_at_slash[1]) == 1:
        date_splited_at_slash[1] = '0' + date_splited_at_slash[1]
    return date_splited_at_slash

def parse_datetime(value):
    # print(value)
    # print("new datetime", len(value))
    if 'à' in value:
        splited_at_comma = value.split("à")
    elif ',' in value:
        splited_at_comma = value.split(",")
    else:
        splited_at_comma = value.split(" ")
    value = ','.join(splited_at_comma)
    # print(value.split(' '))
    value = ''.join(value.split(' '))
    value = ''.join(value.split('\u200e'))
    # print(value)
    splited_at_comma = value.split(",")
    if 'μ.μ.' in value:
        value = value.replace('μ.μ.', 'PM')
    elif 'π.μ.' in value:
        value = value.replace('π.μ.', "AM")
    if "/" in value:
        date_splited_at_slash = format_date_splited_at_separator(splited_at_comma[0], '/')
    elif "-" in value:
        date_splited_at_slash = format_date_splited_at_separator(splited_at_comma[0], '-')
    else:
        date_splited_at_slash = format_date_splited_at_separator(splited_at_comma[0], '.')
    time_splited_at_semicolumn = splited_at_comma[1].split(':')
    if len(time_splited_at_semicolumn[0]) == 1:
        time_splited_at_semicolumn[0] = '0' + time_splited_at_semicolumn[0].strip()
    if len(time_splited_at_semicolumn[1]) == 1:
        time_splited_at_semicolumn[1] = '0' + time_splited_at_semicolumn[1].strip()
    new_value = ("/".join(date_splited_at_slash)).strip() + "," + ":".join(time_splited_at_semicolumn)
    if len(new_value) == len("09/11/2019,14:45:33"):
        return datetime.datetime.strptime(new_value, '%d/%m/%Y,%H:%M:%S')
    else:
        if len(new_value) == len("11/09/2019,10:12:06AM") or len(new_value) == len("11/9/2019,4:14:04PM"):
            return datetime.datetime.strptime(new_value, '%m/%d/%Y,%H:%M:%S%p')
        else:
            print('error', new_value)
            print(len("09/11/2019,14:45:33"), len("11/9/2019,10:12:06AM"), len(new_value))
            raise "error"

with open(path, 'r') as f:
    with open(csv_path, 'w') as fcsv:
        csv_writer = csv.writer(fcsv)

        content = json.load(f)
        sessions = content["Sessions"]
        first_line = list()
        first_line_bool = True
        for id, data in sessions.items():
            # print(data)
            # print("\n-----\n")
            if first_line_bool:
                first_line.append("id")
            # try:
                # print(data)
            if data["data_collection"] and "amt_id" in data["data_collection"].keys() and data["data_collection"]["amt_id"]:
                prolific_id = data["data_collection"]["amt_id"]["value"]
                if first_line_bool:
                    first_line.append("prolific_id")
            start_time = False
            stop_time = False
            data_participant = list()
            data_participant.append(data["xp_condition"])
            diaglog = list()
            if data["data_collection"]["amt_id"]:
                for key, value in data["data_collection"]["amt_id"].items():
                    if key != "client_id" and key != "datetime":
                        data_participant.append(value)
                        if first_line_bool:
                            first_line.append(key)
                    if key == "datetime" and not start_time:
                        start_time = parse_datetime(value)
            if data["data_collection"]["demographics"]:
                for key, value in data["data_collection"]["demographics"].items():
                    if key != "client_id" and key != "datetime" and not any(w in key for w in ["feet", "pounds", "stones", 'height', "weight"]):
                        data_participant.append(value)
                        if first_line_bool:
                            first_line.append(key)
            if data["data_collection"]["food_diagnosis_answers"]:
                for key, value in data["data_collection"]["food_diagnosis_answers"].items():
                    if key != "client_id" and key != "datetime":
                        data_participant.append(value)
                        if first_line_bool:
                            first_line.append(key)
            if data["data_collection"]["questionnaire_answers_q1"]:
                for key, value in data["data_collection"]["questionnaire_answers_q1"].items():
                    if key != "client_id" and key != "datetime":
                        data_participant.append(value)
                        if first_line_bool:
                            first_line.append(key)
            if data["data_collection"]["questionnaire_answers_q2"]:
                for key, value in data["data_collection"]["questionnaire_answers_q2"].items():
                    if key != "client_id" and key != "datetime":
                        data_participant.append(value)
                        if first_line_bool:
                            first_line.append(key)
            if "data_recommendation" in data.keys():
                for key, value in data["data_recommendation"].items():
                    if key != "client_id" and key != "datetime":
                        data_participant.append(value)
                        if first_line_bool:
                            first_line.append(key)
            if data["data_collection"]["free_comments"]:
                for key, value in data["data_collection"]["free_comments"].items():
                    if key != "client_id" and key != "datetime":
                        data_participant.append(value)
                        if first_line_bool:
                            first_line.append(key)
                    if key == "datetime" and not stop_time:
                        if first_line_bool:
                            first_line.append("duration")
                        stop_time = parse_datetime(value)
                        if start_time and stop_time:
                            data_participant.append(stop_time - start_time)

            if data["dialog"]:
                # print(data["dialog"],"\n\n")
                for data_dialog in data["dialog"].values():
                    if data_dialog:
                        if "text" in data_dialog.keys():
                            utterance = data_dialog['text']
                        elif "sentence" in data_dialog.keys():
                            utterance = data_dialog['sentence']
                        diaglog.append(utterance)

            # except Error:
            #     print(data)

            if first_line_bool:
                csv_writer.writerow(first_line)
                first_line_bool = False
            participant_data = [id[1:]] + data_participant
            csv_writer.writerow(participant_data)

            with open('food/resources/pilot2/'+prolific_id+".txt", 'w+') as dialog_file:
                for line in diaglog:
                    dialog_file.write(line+'\n')










