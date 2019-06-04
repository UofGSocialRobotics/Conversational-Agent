# Conversational Agent - Server Side

## Set up

Python 3.7

To install python packages, run:
```shell
pip install paho-mqtt
pip install nltk
pip install simple-websocket-server
# pip install google-cloud-language
```

Run in your python environment:
```python
import nltk
nltk.download('vader_lexicon')
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

## [Developer] Logging module

We log the server's activity using a python logging module.

If you want to add specific logs, use 
```python 
from ca_logging import log
``` 
Then `log` has 5 methods: `debug(message)`, `info(message)`, `warning(message)`, `error(message)` and `critical(message)`. Chose the appropriate one. When using `debug(message)`, the log will be visible only in the console and not written in the log file. 
