import pandas

csv_in_path = "food/resources/pilot3/data.csv"

df = pandas.read_csv(csv_in_path)
# print(df)

prolific_id, cond_str = "prolific_id", "XP_condition"
esthers_q = ("question17", "question18", "question19", "question20", "question21")
rapport_q = ("question1", "question2", "question3", "question4", "question5", "question6", "question7", "question8_reversed")
task_perf_q = ("question9", "question10", "question11", "question12", "question13", "question14", "question15", "question16")
questions_list = [esthers_q, rapport_q, task_perf_q]
files_names = {esthers_q: "intiont_to_cook", rapport_q: "rapport", task_perf_q: "task performance"}
conditions = ["NONE", "robot", "human"]

for _q in questions_list:
    cols = [prolific_id, cond_str] + list(_q)
    # print(cols)
    df_q_all = df[cols]

    n_participants_per_cond = dict()
    df_by_cond = dict()
    max_participants = 0

    for cond in conditions:
        df_by_cond[cond] = df_q_all.query("XP_condition == '" + cond + "'")
        tmp_list = df_by_cond[cond][_q[0]].to_list()
        tmp_series = pandas.Series(tmp_list)
        tmp_series = tmp_series[~tmp_series.isnull()]
        n_participants_per_cond[cond] = len(tmp_series.to_list())
        if n_participants_per_cond[cond] > max_participants:
            max_participants = n_participants_per_cond[cond]
    # print("paticipants", cond, n_participants_per_cond[cond])


    new_df = pandas.DataFrame(None, columns=['prolific_id'] + conditions)
    _scores_per_cond = dict()
    for cond in conditions:
        # df_q_by_cond = df_q_all.query("XP_condition == '" + cond + "'")
        _scores = list()
        prolific_ids = list()
        for num_q, question in enumerate(_q):
            if num_q == 0:
                tmp_average = df_by_cond[cond].sum(axis=1, skipna=False).to_list()
                # print(tmp_average)
            prolific_ids += df_by_cond[cond][prolific_id].to_list()
            tmp_list = df_by_cond[cond][question].to_list()
            tmp_series = pandas.Series(tmp_list)
            # tmp_series = tmp_series[~tmp_series.isnull()]
            # tmp_list = tmp_series.to_list()
            for i, elt in enumerate(tmp_series):
                if not pandas.isnull(elt):
                    p_id = prolific_ids[i]
                    if num_q == 0:
                        average = tmp_average[i] / len(_q)
                    else:
                        average = ""

                    _scores.append([p_id, question, elt, average])
        while (len(_scores) < max_participants * len(_q)):
            _scores.append(["", "", "", ""])

        _scores_per_cond[cond] = _scores
        # print()

    # print(_scores_per_cond)
    new_df_list = list()
    columns_list = list()

    first_cond_bool = True
    for cond, scores in _scores_per_cond.items():
        columns_list += [c + "_" + cond for c in [prolific_id, "question", "score", "average_over_questions"]]
        for i, s in enumerate(scores):
            if first_cond_bool:
                new_df_list.append(s)
            else:
                new_df_list[i] += s
        first_cond_bool = False

    print(len(new_df_list))
    new_df = pandas.DataFrame(new_df_list, columns=columns_list)
    # print(new_df)

    ordered_cols = list()
    for i in [prolific_id, "question", "score", "average_over_questions"]:
        for j in ["_" + c for c in conditions]:
            ordered_cols.append(i + j)
    print("ordered_cols", ordered_cols)

    # print(new_df)
    new_df = new_df[ordered_cols]
    # new_df = pandas.DataFrame(_scores, columns=[prolific_id, "question", "score", "average_over_questions"])
    new_df.to_csv("food/resources/pilot3/"+files_names[_q]+".csv")

    # print(new_df)
