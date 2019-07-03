import os
import csv


with open('employee_file.csv', mode='w') as csv_file:
    dataset = csv.writer(csv_file, delimiter=',')
    dataset.writerow(['group'],['id'],['t1'],['t2'],['t3'],['t4'],['t5'],['t6'],['t7'],['t8'],['t9'],['t10'],['t11'],['t12'],['t13'],['t14'],['t15'],['t16'],['t17'],['t18'])

    tmp_row = []
    feature = []

    for root, dirs, files in os.walk("./"):
        for name in files:
            i = 2
            if name.endswith(".csv"):
                with open(name, mode='rt') as csv_file:
                    interaction = csv.reader(csv_file, delimiter=',')
                    for row in interaction:
                        if i == 2:
                            tmp_row.append(row[1])
                            feature.append(row[9])
                        else:
                            feature.append(row[4])
                            feature.append(row[6])
                            tmp_row.append(feature)
                            feature = []
                            feature.append(row[9])
                        i += 1
            dataset.writerow(tmp_row)
            tmp_row = []
            feature = []
