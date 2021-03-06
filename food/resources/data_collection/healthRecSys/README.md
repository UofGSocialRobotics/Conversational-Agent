# List of files

`.json` files are the data collected from firebase. Those files are parsed to generate a `.csv` file containing all the results we are interested in.


For the pilot, we collected:

* `pilot_health.json`: recommending healthy recipes only, not taking into account the user's preferences.
* `pilot_healthy_wtags.json`: same but on the eval page, the recipes have a _healthiness_ tag (FSA trafic light system) 
* `pilot_pref.json`: pref-based recommendation.
* `pilot_pref2.json`: second batch of pref-based recommendation.
* `pilot_pref_wtags.json`: pref-based recommendation with _healthiness_ tags on eval page.
* `pilot_hybrid.json`: biasing pref-based recommendation towards healthier recipes. Coefficients for pref score and health scores are both 1.
* `pilot_hybrid_coef21.json`: same, but pref-score if coef 2 and health score is coef 1.
* `pilot_hybrid_coef31.json`: same, but pref-score if coef 3 and health score is coef 1.
* `pilot_hybrid_coef31_notrandom_292.json`: same, but controlled the not-recommended recipes: randomly chose 25 from the 292 (quater of DB) that are ranked the lowest by the hybrid reco.
* `pilot_hybrid_cpef31_notrandom_error.json`: wanted to control recipes that were not recommended but ended up selecting more "good" recipes for the user.
* `pilot_hybrid_coef31_notrandom_75_error.json`: same.
* `pilot_hybrid_error.json`: error in bias formula: biasing towards UNhealthier options.
* `pilot_hybrid.json`: same as `pilot_hybrid.json` but with _healthiness_ tags on the eval page.
* `pilot_hybrid_coef31.json`: same as `pilot_hybrid_coef31.json` but pref-score if coef 3 and health score is coef 1.
* `pilot_hybrid_wtags_error.json`: as `pilot_hybrid_error.json` but with _healthiness_ tags on the eval page.

For the data collection, we setled on a 2x3 design with `Tag-Mode` and `Recommender-Mode` as the two dependent variables:
* `Tag-Mode` values are _tags_ and _no-tags_.
* `Recommender-Mode` values are _preference-based_, _health-based_ and _hybrid_. In the hybrid system, the weights are 3 for preference-score and 1 for health-score.

Pilot data corresponding to those conditions are integrated to the overall data collection.

The files with the remaining of the data are:
* `hybrid_coef31.json`: hybrid system with coef 3 1, not-recommended recipes randomly selected.
* `health.json`: healthy recommender system, not-recommended recipes randomly selected.
* `health_wtags.json`: healthy recommender system, not-recommended recipes randomly selected, with tags on eval page.

**For all the pilot files + `hybrid_coef31.json` the _final scores_ and _pref scores_ are switched.**

## Subjective evaluation

Subjective evaluation has the same design, but users rate the 5 recommended recipes (as opposed to choosing 5 recipes out of 30).

The files with the data of this evaluation are `s_pilot_pref.json`, `s_pilot_health.json`, `s_pilot_hybrid.json`. The hybrid system is the Hybrid-31 (pref-score if coef 3 and health score is coef 1).  
