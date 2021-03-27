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


app = Quart(__name__)
app = cors(app)

connected_websockets = set()
# robots_con = {}
robots_config = {}

# config start
config = ConfigParser()
try:
  with open('config.conf', 'r') as filepointer:
    config.read_file(filepointer)
  filepointer.close()
except(IOError, FileNotFoundError):
  print("Unable to read config.conf, check that it exists and that the program has permission to read it.")
  sys.exit()

try:
  with open('robots.json', 'r') as filepointer:
    robots_config = json.load(filepointer)
  filepointer.close()
except(IOError, FileNotFoundError):
  print("Unable to read robots.json, check that it exists and that the program has permission to read it.")
  sys.exit()

try:
  # To read values from config:
  # value = config.get('section', 'key')

  twitch_ext_secret = os.getenv("TWITCH_SECRET_KEY", None)
  if twitch_ext_secret is None:
    twitch_ext_secret = base64.b64decode(config.get('twitch', 'ext_secret'))
    # twitch_ext_secret = base64.b64decode(open(os.path.join(os.getcwd(), "secret.key")).read().strip())

  secret_key = config.get('server', 'secret_key')

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
    await websocket.send(data)


async def receiving():
  while True:
    data = await websocket.receive()
    await process_message(data)


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


@app.route('/api/dev/channels/list/<host>')
async def channels_list(host):
  chanlist = []
  try:
    for rid in robots_config[host]:
      chanlist.append({
        "name": robots_config[host][rid]["info"]["name"],
        "id": rid,
        "chat": robots_config[host][rid]['info']['chat']
      })
  except KeyError:
    response = Response('')
    response.status_code = 404
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response
  return {"channels": chanlist}


@app.route('/command')
async def command():
  c = request.args.get('command')

  auth = request.headers.get('Authorization', '').replace('Bearer ', '')

  try:
    t_jwt = jwt.decode(auth, twitch_ext_secret, algorithms=['HS256'],
                       options={"require": ["channel_id", "opaque_user_id", "role"]})
  except(InvalidSignatureError, ExpiredSignatureError, InvalidTokenError, MissingRequiredClaimError):
    response = Response('')
    response.status_code = 403
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

  if t_jwt:
    if t_jwt.get('opaque_user_id', '')[0] == 'U':
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
    else:
      app.logger.debug("JWT: " + str(t_jwt))
      response = Response('')
      response.status_code = 403
      response.headers['Access-Control-Allow-Origin'] = '*'
      return response
  else:
    app.logger.debug("JWT: " + str(t_jwt))
    response = Response('')
    response.status_code = 403
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

  await broadcast(j)  # after the websockets context issue is solved change this to send message only to target robot
  response = Response('OK')
  response.headers['Access-Control-Allow-Origin'] = '*'
  return response


async def process_message(message):
  app.logger.debug(message)
  m = json.loads(message)
  if m.get('e', '') == 'AUTHENTICATE_ROBOT':
    try:
      r_jwt = jwt.decode(m['d']['token'], secret_key, algorithms=['HS256'])
    except(InvalidSignatureError, ExpiredSignatureError, InvalidTokenError):
      e = json.dumps({
        'e': 'INVALID_TOKEN',
        'd': "token did not validate, check that it's correct",
      })

      await websocket.send(e)
      # await websocket.close(1000)  not available on a quart release yet
      return None

    j = json.dumps({
      'e': 'ROBOT_VALIDATED',
      'd': {
        'host': r_jwt["host"],
        'stream_key': robots_config[r_jwt["host"]][r_jwt["id"]]["info"]["stream_key"],
      },
    })

    await websocket.send(j)
    return None

  # future code to copy websockets context for use to send websockets messages
  # if m.get('e', '') == 'JOIN_CHANNEL':
  #   robots_con[m.get('d', '')] = webaocket_context_copy
  #   app.logger.debug(robots)

  if m.get('e', '') == 'ERROR':
    j = json.dumps({
      'e': 'ERROR',
      'd': m.get('d', '')
    })

    await websocket.send(j)
    # await websocket.close(1000)  not available on a quart release yet
    return None


# @app.cli.command('run')
# def run():
#   app.run(host='0.0.0.0', port=8000)  # , certfile='cert.pem', keyfile='key.pem'


if __name__ == "__main__":
  app.run(host='0.0.0.0', port=8000)  # , certfile='cert.pem', keyfile='key.pem'
