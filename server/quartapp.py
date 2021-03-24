import asyncio
import base64
from functools import wraps
import json
import os

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError, InvalidTokenError, MissingRequiredClaimError

from quart import websocket, Quart, request, Response
from quart_cors import cors

import sys
from configparser import ConfigParser, NoSectionError, NoOptionError

from cryptography.fernet import Fernet, InvalidToken


app = Quart(__name__)
app = cors(app)

connected_websockets = set()
# config start
config = ConfigParser()
try:
  with open('config.conf', 'r') as filepointer:
    config.read_file(filepointer)
except IOError:
  print("Unable to read config.conf, check that it exists and that the program has permission to read it.")
  sys.exit()
except:
  print("Error in config.conf:", sys.exc_info()[0])
  sys.exit()


try:
  # To read values from config:
  # value = config.get('section', 'key')

  encryption = config.get('crypto', 'encryption')
  if encryption == 'force_both' or encryption == 'force_in' or encryption == 'force_out':
    try:
      secure = Fernet(config.get('crypto', 'token'))
    except ValueError:
      print("Error: Invalid token,", sys.exc_info()[1])
      sys.exit()

  server_address = config.get('server', 'address')

  secret = os.getenv("TWITCH_SECRET_KEY", None)
  if secret is None:
    secret_code = config.get('twitch', 'ext_secret')
#    secret_code = open(os.path.join(os.getcwd(), "secret.key")).read().strip()
    secret = base64.b64decode(secret_code)

  if encryption == 'force_both' or encryption == 'force_out':
    stream_key = config.get('twitch', 'stream_key')
  else:
    stream_key = "set encryption as force_out or force_both to get stream_key"

except(NoSectionError, NoOptionError):
  print("Error in config.conf:", sys.exc_info()[1])
  sys.exit()
# config end


def collect_websocket(func):
  @wraps(func)
  async def wrapper(*args, **kwargs):
    global connected_websockets
    queue = asyncio.Queue()
    connected_websockets.add(queue)
    try:
      return await func(queue, *args, **kwargs)
    finally:
      connected_websockets.remove(queue)
  return wrapper


async def sending(queue):
  while True:
    data = await queue.get()
    await websocket_send(data)


async def receiving():
  while True:
    data = await websocket.receive()
    if encryption == 'force_both' or encryption == 'force_in':
      if data.find("b'") == 0:
        try:
          data = secure.decrypt(bytes(data[2:(len(data)-1)], 'utf-8'))
        except InvalidToken:
          data = json.dumps({
            'e': 'ERROR',
            'd': {
              'error_message': 'message encrypted with the wrong token',
            },
          })
      else:
        data = json.dumps({
          'e': 'ERROR',
          'd': {
            'error_message': 'message not encrypted by robot',
          },
        })
    await process_message(data)


async def websocket_send(message):
  if encryption == 'force_both' or encryption == 'force_out':
    message = str(secure.encrypt(bytes(message, 'utf-8')))
  await websocket.send(message)


async def broadcast(message):
  for queue in connected_websockets:
    await queue.put(message)


@app.websocket('/')
@collect_websocket
async def ws(queue):
  producer = asyncio.create_task(sending(queue))
  consumer = asyncio.create_task(receiving())
  await asyncio.gather(producer, consumer)


@app.route('/')
async def root():
  return 'OK'


@app.route('/command')
async def command():
  c = request.args.get('command')

  auth = request.headers.get('Authorization', '').replace('Bearer ', '')

  try:
    t_jwt = jwt.decode(auth, secret, algorithms=['HS256'],
                       options={"require": ["channel_id", "opaque_user_id", "role"]})
  except(InvalidSignatureError, ExpiredSignatureError, InvalidTokenError, MissingRequiredClaimError):
    response = Response('')
    response.status_code = 403
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

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
  await websocket_send(j)
  response = Response('OK')
  response.headers['Access-Control-Allow-Origin'] = '*'
  return response


async def process_message(message):
  m = json.loads(message)
  if m.get('e', '') == 'AUTHENTICATE_ROBOT':
    j = json.dumps({
      'e': 'ROBOT_VALIDATED',
      'd': {
        'host': server_address,
        'stream_key': stream_key,
      },
    })

    await websocket_send(j)
    return None

  if m.get('e', '') == 'ERROR':
    j = json.dumps({
      'e': 'ERROR',
      'd': m.get('d', '')
    })

    await websocket_send(j)
    return None

if __name__ == "__main__":
  app.run(host='0.0.0.0', port=8000)
