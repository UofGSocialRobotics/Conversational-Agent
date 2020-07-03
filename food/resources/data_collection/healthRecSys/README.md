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
* `pilot_hybrid_error.json`: error in bias formula: biasing towards UNhealthier options.
* `pilot_hybrid.json`: same as `pilot_hybrid.json` but with _healthiness_ tags on the eval page.
* `pilot_hybrid_wtags31.json`: same as `pilot_hybrid_coef31.json` but pref-score if coef 3 and health score is coef 1.
* `pilot_hybrid_wtags31_notrandom.json`: same, but the not-recommended recipes (eval page) are not selected at random. We first select the 292 (one fourth of the DB) least recommended recipes, and then we select randomly from that sample.
* `pilot_hybrid_wtags_error.json`: as `pilot_hybrid_error.json` but with _healthiness_ tags on the eval page.
