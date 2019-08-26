# Conversational Agent - Server Side

This is the server side of the CORA (COnversational Rapport-building Agent) project. 

## Set up

The server was developped using Python 3.7.

To install python packages, run:
```shell
pip install spacy
python -m spacy download en
import nltk
pip install fuzzywuzzy
# pip install pandas
pip install pyrebase #https://github.com/thisbejim/Pyrebase
pip install cryptography
```

Run in your python environment:
```python
import nltk
nltk.download('vader_lexicon')
nltk.download('punkt')
``` 

## Start server

You need the encryption key. Ask Lucile.

For the movie domain:
```shell
python main.py --movies
```
For the food domain:
```shell
python main.py --food
```


## [Developer] Logging module

We log the server's activity using a python logging module.

If you want to add specific logs, use 
```python 
from ca_logging import log
``` 
Then `log` has 5 methods: `debug(message)`, `info(message)`, `warning(message)`, `error(message)` and `critical(message)`. Chose the appropriate one. When using `debug(message)`, the log will be visible only in the console and not written in the log file. 

**Debug**: please use `log.debug("debug message")` instead of `print("debug message")`!
