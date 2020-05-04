# https://www.ethanrosenthal.com/2016/10/19/implicit-mf-part-1/
# https://towardsdatascience.com/building-a-collaborative-filtering-recommender-system-with-clickstream-data-dffc86c8c65

import pandas as pd
import numpy as np
import scipy.sparse as sparse
import implicit

import food.resources.recipes_DB.allrecipes.nodejs_scrapper.consts as consts


df = pd.read_csv(consts.csv_xUsers_Xrecipes_binary_path)
print(df.head())

# df['title'] = df['title'].astype("category")
df['user'] = df['user'].astype("category")
df['item'] = df['item'].astype("category")
df['uid'] = df['user'].cat.codes
df['rid'] = df['item'].cat.codes

sparse_content_person = sparse.csr_matrix((df['strength'].astype(float), (df['rid'], df['uid'])))
sparse_person_content = sparse.csr_matrix((df['strength'].astype(float), (df['uid'], df['rid'])))

model = implicit.als.AlternatingLeastSquares(factors=20, regularization=0.1, iterations=50)

alpha = 15
data = (sparse_content_person * alpha).astype('double')
model.fit(data)

rid_list = [3, 689, 2956, 6542, 80, 643]

# rid = 450
for rid in rid_list:
    print("\n----", df.item.loc[df.rid == rid].iloc[0])
    n_similar = 10

    person_vecs = model.user_factors
    content_vecs = model.item_factors

    content_norms = np.sqrt((content_vecs * content_vecs).sum(axis=1))

    scores = content_vecs.dot(content_vecs[rid]) / content_norms
    top_idx = np.argpartition(scores, -n_similar)[-n_similar:]
    similar = sorted(zip(top_idx, scores[top_idx] / content_norms[rid]), key=lambda x: -x[1])

    for content in similar:
        idx, score = content
        print(df.item.loc[df.rid == idx].iloc[0])
