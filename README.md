# Marionette
Twitch extension for controlling robots remotely

### Warning: This code only supports one streamer with one robot per server

# Installation

```
$ git clone https://github.com/strangeparts/marionette
$ cd marionette/server
$ virtualenv virtualenv
```
On linux do: `$ source virtualenv/bin/activate`
```
(virtualenv)$ pip3 install -r requirements.txt
```

# Run development server

On linux do: `$ source virtualenv/bin/activate`
```
(virtualenv)$ QUART_DEBUG=1 QUART_APP=quartapp.py quart run --host 0.0.0.0 --port 8000
```