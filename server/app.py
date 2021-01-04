import json
import logging
import queue
import sys

from flask import Flask, request
from flask_sockets import Sockets
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
sockets = Sockets(app)

# TODO convert this to pub/sub
command_queue = queue.Queue()

open_sockets = []

@sockets.route('/print')
def print_socket(ws):
  while not ws.closed:
    message = ws.receive()
    print("Message: " + message)

@sockets.route('/')
def robot(ws):
  open_sockets.append(ws)
  print("Added socket")
  while not ws.closed:
    message = ws.receive()
    print("Message: " + message)
    if message:
      r = process_message(message)
      if r:
        ws.send(r + '\n')

#    if not command_queue.empty():
#      c = command_queue.get(block=False)
#      print("Command: " + c)
#      j = json.dumps({
#        'e': 'BUTTON_COMMAND',
#        'd': {
#          'button': {
#            'command': c,
#          },
#          'user': {
#            'username': 'NONEUSER',
#          },
#        },
#      })
#      ws.send(j + "\n")

def send_message(c):
  print("Open sockets: %r" % open_sockets)
  for ws in open_sockets:
    if ws.closed:
      print("Removed closed socket")
      open_sockets.remove(ws)
      continue
    print("Command: " + c)
    j = json.dumps({
      'e': 'BUTTON_COMMAND',
      'd': {
        'button': {
          'command': c,
        },
        'user': {
          'username': 'NONEUSER',
        },
      },
    })
    ws.send(j + "\n")

def process_message(message):
  m = json.loads(message)
  if m.get('e', '') == 'AUTHENTICATE_ROBOT':
    return json.dumps({
      'e': 'ROBOT_VALIDATED',
      'd': {
        'host': '192.168.0.136:8000',
      },
    })

@app.route('/')
def hello():
  return 'Hello World!'

@app.route('/command')
def command():
  c = request.args.get('command')
  print("Received command: " + c)
  #command_queue.put(c)
  send_message(c)
  return 'OK'

if __name__ == "__main__":
  from gevent import pywsgi
  from geventwebsocket.handler import WebSocketHandler

  app.logger.debug('this is a DEBUG message')
  
  server = pywsgi.WSGIServer(('', 8000), app, handler_class=WebSocketHandler)
  server.serve_forever()
