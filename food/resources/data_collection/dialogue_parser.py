import os
import csv
folder = './food/resources/dialogues/aamas'
csvFile = open('csvfile.csv', 'w')
writer = csv.writer(csvFile)
for filename in os.listdir(folder):
	if filename.startswith("5"):
		with open(folder + "/" + filename) as f:
			content = f.readlines()
			content = [line.replace("\n","") for line in content]
			content = [line.replace("\r","") for line in content]
			if content:
				writer.writerow(content)
csvFile.close()