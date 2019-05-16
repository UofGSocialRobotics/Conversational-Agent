# Conversational Agent - Server Side

## Set up

Python 3.7

To install python packages, run:
```shell
pip install paho-mqtt
```

## Start server

```shell
python main.py
```

__IMPORTANT__: If running the server from University of Glasgow, you need an ethernet connection.
The server will fail to connect to the broker via wifi.

## [Developer] Logging module

We log the server's activity using a python logging module.

If you want to add specific logs, use 
```python 
from ca_logging import log
``` 
Then `log` has 5 methods: `debug(message)`, `info(message)`, `warning(message)`, `error(message)` and `critical(message)`. Chose the appropriate one. When using `debug(message)`, the log will be visible only in the console and not written in the log file. 
