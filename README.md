# Conversational Agent - Server Side

This is the server side of the CORA (COnversational Rapport-building Agent) project. 

Cora is a virtual agent that interacts with people 

## Set up

Python 3.7

To install python packages, run:
```shell
pip install paho-mqtt
pip install nltk
pip install simple-websocket-server #  https://pypi.org/project/SimpleWebSocketServerFork/0.1.1/
pip install stanfordnlp
pip install spacy
pip install textblob
python -m spacy download en
# pip install fuzzywuzzy
pip install pandas
# pip install google-cloud-language
```

Run in your python environment:
```python
import nltk
nltk.download('vader_lexicon')
nltk.download('punkt')
import stanfordnlp
stanfordnlp.download('en')
```

## Server options

You can run everything on your local machine and use websockest to connect the web client with the python server.
If accessing the server from a client hosted on the Internet, you'll need the python server that uses an external broker.

__IMPORTANT__: If running the distant-broker-server from University of Glasgow, you need an ethernet connection.
The server will fail to connect to the broker via wifi.

To choose between a server using a distant broker or websockets, you just need to comment appropriately in `config.py`:
```python
# USING = BROKER
USING = WEBSOCKETS
```

## Start server

```shell
python main.py
```

## Debug

If you get the following error message:
```shell
Traceback (most recent call last):
  File "dum_NLU.py", line 6, in <module>
    import stanfordnlp
  File "/Users/lucileca/Desktop/Conversational_Agent/server_side/venv/lib/python3.7/site-packages/stanfordnlp/__init__.py", line 1, in <module>
    from stanfordnlp.pipeline.core import Pipeline
  File "/Users/lucileca/Desktop/Conversational_Agent/server_side/venv/lib/python3.7/site-packages/stanfordnlp/pipeline/core.py", line 7, in <module>
    import torch
  File "/Users/lucileca/Desktop/Conversational_Agent/server_side/venv/lib/python3.7/site-packages/torch/__init__.py", line 79, in <module>
    from torch._C import *
ImportError: dlopen(/Users/lucileca/Desktop/Conversational_Agent/server_side/venv/lib/python3.7/site-packages/torch/_C.cpython-37m-darwin.so, 9): Library not loaded: /usr/local/opt/libomp/lib/libomp.dylib
  Referenced from: /Users/lucileca/Desktop/Conversational_Agent/server_side/venv/lib/python3.7/site-packages/torch/lib/libshm.dylib
  Reason: image not found
```
you can try:
```shell
pip uninstall torch -y
pip uninstall pytorch -y
pip uninstall torchvision -y
pip install torch==1.0.1 -f https://download.pytorch.org/whl/cpu/stable # CPU-only build
```
__NOTE__: Check which build you have on you machin (CUDAXX or CPU only), see https://pytorch.org/get-started/previous-versions/

## [Developer] Logging module

We log the server's activity using a python logging module.

If you want to add specific logs, use 
```python 
from ca_logging import log
``` 
Then `log` has 5 methods: `debug(message)`, `info(message)`, `warning(message)`, `error(message)` and `critical(message)`. Chose the appropriate one. When using `debug(message)`, the log will be visible only in the console and not written in the log file. 


