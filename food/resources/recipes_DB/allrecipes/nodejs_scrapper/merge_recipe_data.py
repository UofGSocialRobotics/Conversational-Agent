import json
import collections
reviews_path = 'reviews_all_recipes.json'
mainpage_path = 'recipes_mainpage.json'
nutriinfo_path = 'recipes_nutritionInfo.json'

full_DB = 'fullDB.json'

with open(reviews_path, 'r') as freviews:
    reviews_content = json.load(freviews)
reviews_rids = set(reviews_content.keys())

# for k, v in reviews_content.items():
#     print(k, v)
#     break

with open(mainpage_path, 'r') as fmainpage:
    mainpage_content = json.load(fmainpage)
mainpage_rids = set(mainpage_content.keys())

with open(nutriinfo_path, 'r') as fnutri:
    nutri_content = json.load(fnutri)
nutri_rids = set(nutri_content.keys())

l1 = list(reviews_rids) + list(mainpage_rids) + list(nutri_rids)

rids_fulldata = [item for item, count in collections.Counter(l1).items() if count == 3]

rdata = dict()
udata = dict()
n_ratings = 0

for rid in rids_fulldata:
    rdata[rid] = dict()
    rdata[rid]['recipe_info'] = mainpage_content[rid]
    rdata[rid]['recipe_info']['nutrition'] = nutri_content[rid]
    rdata[rid]['reviews'] = reviews_content[rid]

    for rdict in reviews_content[rid]['reviews']:
        # print(rdict)
        uid = rdict['id']
        if uid not in udata.keys():
            udata[uid] = dict()
            udata[uid]['n_comments'] = 0
            udata[uid]['recipes_commented'] = list()
        udata[uid]['n_comments'] += 1
        udata[uid]['recipes_commented'].append(rid)
        n_ratings += 1

print("Total recipes:", len(rdata.keys()))
print("Total users:", len(udata.keys()))
print("Total ratings:", n_ratings)

# data = dict()
# data['recipes_data'] = rdata
# data['users_data'] = rdata
#
# with open(full_DB, 'w') as fout:
#     json.dump(data, fout, indent=True)



