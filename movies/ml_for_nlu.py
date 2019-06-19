import csv
import argparse
import numpy as np
import math
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, f1_score,recall_score, precision_score


def read_dataset(dataset):
	M = list()
	rule_based_labels = list()
	with open(dataset,'r') as f:
		csv_reader = csv.reader(f)
		for i, row in enumerate(csv_reader):
			# ignore headers
			if i > 0:
				new_row = list()
				for j, elt in enumerate(row):
					if j < len(row) - 2 :
						new_row.append(float(elt))
				M.append(new_row)
	matrix_of_examples = np.matrix(M)
	return matrix_of_examples #, rule_based_labels


def get_X_Y(dataset):
	matrix_of_examples = read_dataset(dataset)
	Y = matrix_of_examples[1:,0].getA1()
	Y_rule_based = matrix_of_examples[1:,1].getA1()
	X = matrix_of_examples[1:,2:]
	return X, Y, Y_rule_based


def logistic_regression(X_train, Y_train, X_test, Y_test):

	lr_classifier = LogisticRegression()
	lr_classifier.fit(X_train,Y_train)
	# print(X,Y)
	err = error(X_train,Y_train,lr_classifier.predict)
	print('Error on train set:%.6f'%err)
	err = error(X_test,Y_test,lr_classifier.predict)
	print('Error on test set:%.6f'%err)


def rule_based_classification(Y_train, Y_test, Y_train_rule_based, Y_test_rule_based):
	print('Error on train set:%.6f' % (1 - float(np.sum(Y_train == Y_train_rule_based))/float(len(X_train))))
	print('Error on test set:%.6f' % (1 - float(np.sum(Y_test == Y_test_rule_based))/float(len(X_test))))

def decision_tree(X_train, Y_train, X_test, Y_test):
	## get best max depth using cross-validation
	n_row, n_col = X_train.shape
	err_list = list()
	for depth in range(1, n_col):
		n_folds = 10
		k = math.floor(n_row / n_folds)
		err_list_cv = list()
		j = 0
		for i in range(n_folds):
			if j == 0:
				## first fold
				X_train_cv, Y_train_cv = X_train[j+k:,:], Y_train[j+k:]
				X_cv, Y_cv = X_train[j:j+k,:], Y_train[j:j+k]
			if (j+k) >n_row:
				## last fold
				X_train_cv, Y_train_cv = X_train[0:j,:], Y_train[0:j]
				X_cv, Y_cv = X_train[j:,:], Y_train[j:]
			else:
				X_train_cv, Y_train_cv = np.concatenate((X_train[0:j,:],X_train[j+k:,:])), np.concatenate((Y_train[0:j],Y_train[j+k:]))
				X_cv, Y_cv = X_train[j:j+k], Y_train[j:j+k]

			dt_classifier = DecisionTreeClassifier(criterion='entropy', max_depth=depth)
			dt_classifier.fit(X_train_cv,Y_train_cv)
			err = error(X_cv,Y_cv,dt_classifier.predict)
			err_list_cv.append(err)
			j += k
		err_list.append(np.average(np.array(err_list_cv)))

	# print(err_list)
	# print(best_depth)

	best_depth = err_list.index(min(err_list)) + 1

	## retrain on all train set and get error
	dt_classifier = DecisionTreeClassifier(criterion='entropy', max_depth=best_depth)
	dt_classifier.fit(X_train,Y_train)
	err = error(X_train,Y_train,dt_classifier.predict)
	print('Error on train set:%.6f'%err)
	err = error(X_test,Y_test,dt_classifier.predict)
	print('Error on test set:%.6f'%err)


def KNN(X_train,Y_train,X_test,Y_test):
	n_row, n_col = X_train.shape
	err_list = list()
	for neighbors in range(1,math.ceil(n_row/2)):
		n_folds = 10
		k = math.floor(n_row / n_folds)
		err_list_cv = list()
		j = 0
		for i in range(n_folds):
			if j == 0:
				## first fold
				X_train_cv, Y_train_cv = X_train[j+k:,:], Y_train[j+k:]
				X_cv, Y_cv = X_train[j:j+k,:], Y_train[j:j+k]
			if (j+k) >n_row:
				## last fold
				X_train_cv, Y_train_cv = X_train[0:j,:], Y_train[0:j]
				X_cv, Y_cv = X_train[j:,:], Y_train[j:]
			else:
				X_train_cv, Y_train_cv = np.concatenate((X_train[0:j,:],X_train[j+k:,:])), np.concatenate((Y_train[0:j],Y_train[j+k:]))
				X_cv, Y_cv = X_train[j:j+k], Y_train[j:j+k]

			knn_classifier = KNeighborsClassifier(n_neighbors=neighbors)
			knn_classifier.fit(X_train_cv,Y_train_cv)
			err = error(X_cv,Y_cv,knn_classifier.predict)
			err_list_cv.append(err)
			j += k
		err_list.append(np.average(np.array(err_list_cv)))

	best_n_neighbors = err_list.index(min(err_list)) + 1

	knn_classifier = KNeighborsClassifier(n_neighbors=best_n_neighbors)
	knn_classifier.fit(X_train, Y_train)
	err = error(X_train, Y_train, knn_classifier.predict)
	print('Error on train set:%.6f'%err)
	err = error(X_test, Y_test, knn_classifier.predict)
	print('Error on test set:%.6f' % err)


def error(X,Y,prediction_function):
	n_row, n_col = X.shape
	n_ex_OK = 0
	for i in range(n_row):
		ex = X[i]
		prediction = prediction_function(ex)
		if prediction == Y[i]:
			n_ex_OK += 1
	err = float(n_row - n_ex_OK) / n_row
	return err


if __name__ == '__main__':

	parser = argparse.ArgumentParser(description='Predicts the type of table.')
	parser.add_argument('train_set', metavar='train_set', type=str, help='Path to the CSV of the train set.')
	parser.add_argument('test_set', metavar='test_set', type=str, help='Path to the CSV of the test set.')

	args = parser.parse_args()

	X_train, Y_train, Y_train_rule_based = get_X_Y(args.train_set)
	X_test, Y_test, Y_test_rule_based = get_X_Y(args.test_set)
	# print(X_test)
	# print(Y_test)

	print('Logistic regression:')
	logistic_regression(X_train, Y_train, X_test, Y_test)

	print('\nRule-based classification:')
	rule_based_classification(Y_train, Y_test, Y_train_rule_based, Y_test_rule_based)

	print('\nDecision tree classification:')
	decision_tree(X_train, Y_train, X_test, Y_test)

	print('\nKNN classification:')
	KNN(X_train, Y_train, X_test, Y_test)
