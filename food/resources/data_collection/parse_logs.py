import random
import csv
import argparse
import json


def parse_data_reco_no_list(line, list_to_parse, list_to_append):
    for elt in list_to_parse:
        list_to_append.append(elt)
        data = line.split("'"+elt+"': ")[1].split(",")[0]
        list_to_append.append(data)
        list_to_append.append("")


def parse_data_reco_lists_or_dicts(line, list_to_parse, list_to_append):
    for elt in list_to_parse:
        splited = line.split("'"+elt+"': ")[1]
        if splited[0] == '[':
            data = splited.split("]")[0] + "]"
        else:
            data = splited.split("}")[0] + "}"
        if elt == "queries":
            queries_splited = data.split("',")
            for i, query in enumerate(queries_splited):
                query = query.replace("'","")
                query = query.replace("]","")
                query = query.replace("[","")
                list_to_append.append("query_"+i.__str__())
                list_to_append.append(query)
                list_to_append.append("")
        else:
            list_to_append.append(elt)
            list_to_append.append(data)
            list_to_append.append("")


def logs_to_csv(client_id_wanted="", data_reco_wanted=False):

    filepath = 'server_logs.log'
    NLU_intents_by_clients = dict()
    with open(filepath) as fp:
        line = fp.readline()
        while line:
            if client_id_wanted and client_id_wanted in line:
                to_get_NLU_intents = ("DM" in line and "received" in line and "NLU/" in line)
                if ("NLU" in line and "received" in line and "Server_in" in line) or to_get_NLU_intents:
                    msg = line.strip().split("CONTENT = ")[1]
                    if to_get_NLU_intents:
                        client_id = line.split("NLU/")[1].split(" ")[0]
                    else:
                        client_id = line.split("NLU")[1].split(":")[0]
                    # print(client_id, msg)
                    if client_id not in NLU_intents_by_clients.keys():
                        NLU_intents_by_clients[client_id] = [""]
                    NLU_intents_by_clients[client_id].append(msg)
                    # print(msg)
                # get current sate
                if ("NLG" in line and "received" in line and "DM/" in line):
                    msg = line.strip().split("CONTENT = ")[1]
                    current_state = msg.split(":")[1].split(",")[0].replace("'","").strip()
                    client_id = line.split("NLG")[1].split(":")[0]
                    # print(current_state)
                    NLU_intents_by_clients[client_id].append(current_state)
                # get data_reco
                if data_reco_wanted and ("DataCollector_in" in line and "received" in line and "data_recommendation" in line):
                    to_get_from_data_reco_no_list = ['n_queries', 'n_seed_ingredients', 'n_reco', 'n_accepted_reco']
                    to_get_from_data_reco_lists_dicts = ["queries", "seed_ingredients", "food_values", "food_val_state"]
                    parse_data_reco_no_list(line, to_get_from_data_reco_no_list, NLU_intents_by_clients[client_id])
                    parse_data_reco_lists_or_dicts(line, to_get_from_data_reco_lists_dicts, NLU_intents_by_clients[client_id])


            line = fp.readline()

    # print(NLU_intents_by_clients)

    clients_list = list(NLU_intents_by_clients.keys())
    random.shuffle(clients_list)

    dict_for_csv = dict()
    for client in clients_list:
        client_list_csv = list()
        dict_for_csv[client] = []
        for i, elt in enumerate(NLU_intents_by_clients[client]):
            if i % 3 == 0:
                client_list_csv = list()
            client_list_csv.append(elt)
            if i % 3 == 2:
                dict_for_csv[client].append(client_list_csv)



    with open("NLU_data"+client_id_wanted+".csv", 'w') as fcsv:
        csv_writer = csv.writer(fcsv)
        for client_id, client_data in dict_for_csv.items():
            for line in client_data:
                # print(line)
                csv_writer.writerow(line)


    print("Wrote data for %d conversations" % len(dict_for_csv.keys()))


def get_sigir_clients_ids(csv_file_all_data):
    clients_ids_list = list()
    with open(csv_file_all_data, 'r') as f:
        csv_lines = csv.reader(f)
        for line in csv_lines:
            # print(line)
            clients_ids_list.append(line[0])
    return clients_ids_list

def extract_answers_for_question(clients_ids_list, question):
    if question == "ingredients":
        q_text = "food you'd like to use?"
    elif question == "time":
        q_text = "spend cooking tonight?"
    filepath = 'server_logs.log'
    for client_id in clients_ids_list:
        # print(client_id)
        ingredients_line = False
        with open(filepath) as fp:
            line = fp.readline()
            while line:
                if client_id in line:
                    # print(line)
                    if ingredients_line:
                        user_utterance = line.split("text': '")
                        if len(user_utterance) > 1 :
                            user_utterance = user_utterance[1].split('}')[0]
                        print(user_utterance)
                    if q_text in line:
                        # print("TRUE")
                        ingredients_line = True
                    else:
                        ingredients_line = False
                line = fp.readline()


def print_logs_for_client(client_id):

    filepath = 'server_logs.log'
    with open(filepath) as fp:
        line = fp.readline()
        while line:
            if client_id in line:
                print(line)
            line = fp.readline()

def print_json_for_client_from_file(client_id, file_name):
    with open(file_name, 'r') as f:
        content = json.load(f)
        sessions = content["Sessions"]
        for id, data in sessions.items():
            # print(id)
            if client_id in id:
                print(data)
                return True
    return False

def print_json_for_client(client_id):
    found_bool = False
    found_bool = print_json_for_client_from_file(client_id, "food/resources/aamas/data.json")
    # if not found_bool:
    #     found_bool = print_json_for_client_from_file(client_id, "food/resources/aamas/subset/data.json")
    if not found_bool:
        found_bool = print_json_for_client_from_file(client_id, "food/resources/pilot1/data.json")
    if not found_bool:
        found_bool = print_json_for_client_from_file(client_id, "food/resources/pilot2/data.json")
    if not found_bool:
        found_bool = print_json_for_client_from_file(client_id, "food/resources/pilot3/data.json")
    if not found_bool:
        found_bool = print_json_for_client_from_file(client_id, "food/resources/pilot4/data.json")
    if not found_bool:
        found_bool = print_json_for_client_from_file(client_id, "food/resources/no_rapport/data.json")
    if not found_bool:
        found_bool = print_json_for_client_from_file(client_id, "food/resources/no_rapport2/data.json")
    if not found_bool:
        print("Cannot find client " + args.c)

if __name__ == "__main__":

    argp = argparse.ArgumentParser()
    argp.add_argument('-c', metavar='client_id', type=str, help='Client ID.')
    argp.add_argument("--logs", help="Print logs", action="store_true")
    argp.add_argument("--json", help="Print json data", action="store_true")
    argp.add_argument("--to_csv", help="To csv", action="store_true")
    argp.add_argument("--data_reco", help="Do you want data about recommendation as well?", action="store_true")
    argp.add_argument('--ingredients', help="Print users' inputs for ingredients", action="store_true")

    args = argp.parse_args()

    if args.c and not args.to_csv:
        if args.logs:
            print_logs_for_client(args.c)
        elif args.json:
            print_json_for_client(args.c)
        else:
            print("What do you want for client " + args.c + "?")
            argp.print_help()
    elif args.ingredients:
        csv_path = "food/resources/data_collection/sigir/data_all_prolific.csv"
        clients_ids_list = get_sigir_clients_ids(csv_path)
        print(clients_ids_list)
        extract_answers_for_question(clients_ids_list, "time")
    else:
        logs_to_csv(args.c, args.data_reco)
