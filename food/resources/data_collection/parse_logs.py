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
           # if "NLU" in line:
               # print(line)
           if ("NLU" in line and "received" in line and "Server_in" in line) or ("NLU" in line and "publishing" in line):
               msg = line.strip().split("CONTENT = ")[1]
               client_id = line.split("NLU")[1].split(":")[0]
               # print(client_id, msg)
               if client_id not in NLU_intents_by_clients.keys():
                   NLU_intents_by_clients[client_id] = list()
               NLU_intents_by_clients[client_id].append(msg)
           # if "NLU" in line and "publishing" in line:
           #     msg = line.strip().split("CONTENT = ")[1]
           #     client_id = line.split("NLU")[1].split(":")[0]
           #     print(client_id, msg)
           line = fp.readline()

    clients_list = list(NLU_intents_by_clients.keys())
    random.shuffle(clients_list)

    with open("NLU_for_analysis.csv", 'w') as fcsv:
        csv_writer = csv.writer(fcsv)
        # for i in range(20):
        for client in clients_list:
            client_list_csv = list()
            # client = random.choice(clients_list)
            csv_writer.writerow(["client_id: "+client])
            print("\n", client)
            for i, elt in enumerate(NLU_intents_by_clients[client]):
                print(elt)
                if i % 2 == 0:
                    client_list_csv = [elt]
                else:
                    client_list_csv.append(elt)
                    csv_writer.writerow(client_list_csv)


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
