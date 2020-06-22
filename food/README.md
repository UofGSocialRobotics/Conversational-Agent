# Recommendation system

## Cora vs. RS standalone

Cora is not used to evaluation the RS as a standalone, only the RS module is used (see `config_modules.py`).

To switch from Cora to RS-standalone, first set `DOMAIN = DOMAIN_RS_EVAL` in `config.py`, then start the server using:
```shell
python main.py --rseval
```

To switch back to Cora, set `DOMAIN = DOMAIN_RS_EVAL` and then start the server using on of the two commands:
```shell
python main.py --food
python main.py --movies
```

## Recommendation evaluation

We consider three kinds of recommender systems: preference-based, healthiness-based and hybrid:
* To use the preference-based system, set `healthy_bias = False` in `config.py`.
* To use the healthiness-based system,  

