import math

# http://sdsawtelle.github.io/blog/output/mean-average-precision-MAP-for-recommender-systems.html
# https://towardsdatascience.com/evaluation-metrics-for-recommender-systems-df56c6611093
# https://link.springer.com/content/pdf/10.1007%2F978-0-387-85820-3.pdf
def MAPatK(y_pred_list, y_test_list, k=5):
    n_predictions = len(y_pred_list)
    sum_AP_at_k = 0
    for c, y_pred in enumerate(y_pred_list):
        # print(y_pred)
        # print(len(y_pred))
        y_test = y_test_list[c]
        prev_pred_correct = 0
        p_at_k_vect = list()
        correct_vect = list()
        for i in range(0, k):
            v_pred, v_test = y_pred[i], y_test[i]
            correct_pred = 1 if v_pred == v_test else 0
            correct_vect.append(correct_pred)
            correct_pred_cum = correct_pred + prev_pred_correct
            if correct_pred:
                prev_pred_correct += 1
            p_at_k = correct_pred_cum / float(i + 1)
            p_at_k_vect.append(p_at_k)
            # print(correct_pred_cum, p_at_k)
        s = 0
        # print(correct_vect, p_at_k_vect)
        for i in range(0, len(p_at_k_vect)):
            s += p_at_k_vect[i] * correct_vect[i]
        averaged_precision = s/float(len(p_at_k_vect))
        # print(averaged_precision)
        sum_AP_at_k += averaged_precision
    return float(sum_AP_at_k) / n_predictions

def nDCGatK(y_test_ordered_by_pred_list, k=5):
    sum_nDCG = 0
    n_passed = 0
    for y_test in y_test_ordered_by_pred_list:
        y_test_ideal = list(reversed(sorted(y_test)))
        # print(y_test, y_test_ideal)
        DCG, iDCG = 0, 0
        if len(y_test) < k:
            n_passed += 1
        else:
            for i in range(0, k):
                relevance = y_test[i]
                relevance_ideal = y_test_ideal[i]
                d = math.log2((i + 1) + 1)
                DCG += relevance / d
                iDCG += relevance_ideal / d
            if DCG == iDCG:
                nDCG = 1
            elif iDCG == 0:
                n_passed += 1
            else:
                nDCG = float(DCG) / iDCG
            sum_nDCG += nDCG
    # print(len(y_test_ordered_by_pred_list) - n_passed)
    return (float(sum_nDCG) / (len(y_test_ordered_by_pred_list) - n_passed))
