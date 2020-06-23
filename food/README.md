# Recommendation system

## Cora vs. RS standalone

Cora is not used to evaluate the RS as a standalone, only the RS module is used (see `config_modules.py`).

To switch from Cora to RS-standalone, first set `DOMAIN = DOMAIN_RS_EVAL` in `config.py`, then start the server using:
```shell
python main.py --rseval
```

To switch back to Cora, set `DOMAIN = DOMAIN_CORA` and then start the server using on of the two commands:
```shell
python main.py --food
python main.py --movies
```

## Recommendation evaluation

We consider three kinds of recommender systems: preference-based, healthiness-based and hybrid.

To switch between those three modes, just set `rs_eval_cond` in `config.py` to the approriate value, e.g.:
```python
cond_pref = "cond_pref"
cond_health = "cond_health"
cond_hybrid = "cond_hybrid"
rs_eval_cond = cond_hybrid
``` 
