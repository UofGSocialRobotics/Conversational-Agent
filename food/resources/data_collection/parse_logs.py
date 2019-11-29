import random
import csv
import argparse
import json

def logs_to_csv():

    filepath = 'server_logs.log'
    NLU_intents_by_clients = dict()
    with open(filepath) as fp:
        line = fp.readline()
        while line:
            if ("NLU" in line and "received" in line and "Server_in" in line) or ("NLU" in line and "publishing" in line):
                msg = line.strip().split("CONTENT = ")[1]
                client_id = line.split("NLU")[1].split(":")[0]
                # print(client_id, msg)
                if client_id not in NLU_intents_by_clients.keys():
                    NLU_intents_by_clients[client_id] = [""]
                NLU_intents_by_clients[client_id].append(msg)
            if ("NLG" in line and "received" in line and "DM/" in line):
                msg = line.strip().split("CONTENT = ")[1]
                intent = msg.split(":")[1].split(",")[0].replace("'","").strip()
                client_id = line.split("NLG")[1].split(":")[0]
                # print(client_id, intent)
                NLU_intents_by_clients[client_id].append(intent)
            line = fp.readline()

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

    # lines_by_client_old_csv = dict()
    # with open("food/resources/data_collection/NLU_for_analysis_analyzed.csv", 'r') as fcsv_r:
    #     content_csv = csv.reader(fcsv_r)
    #     for line_input in content_csv:
    #         if "client_id: " in line_input[0]:
    #             client_id = line_input[0].split()[1]
    #             # print(client_id)
    #             lines_by_client_old_csv[client_id] = list()
    #         else:
    #             lines_by_client_old_csv[client_id].append(line_input)

    # final_csv = dict()
    # for client_id, client_data in lines_by_client_old_csv.items():
    #     if client_id not in dict_for_csv.keys():
    #         print("Can't find client %s" % client_id)
    #     elif len(client_data) != len(dict_for_csv[client_id]):
    #         print("Data does not correspond for client %s" % client_id)
    #         print(len(client_data), len(dict_for_csv[client_id]))
    #         for l1 in client_data:
    #             print(l1)
    #         for l2 in dict_for_csv[client_id]:
    #             print(l2)
    #     else:
    #         final_csv[client_id] = [["client_id: "+client_id]]
    #         for i, l1 in enumerate(client_data):
    #             l2 = dict_for_csv[client_id][i]
    #             # print(l1, l2)
    #             final_csv[client_id].append([l2[0]] + l1)


    with open("NLU_for_analysis2.csv", 'w') as fcsv:
        csv_writer = csv.writer(fcsv)
        for client_id, client_data in dict_for_csv.items():
            for line in client_data:
                csv_writer.writerow(line)




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

    args = argp.parse_args()

    if args.c:
        if args.logs:
            print_logs_for_client(args.c)
        elif args.json:
            print_json_for_client(args.c)
        else:
            print("What do you want for client " + args.c + "?")
            argp.print_help()
    else:
        logs_to_csv()
