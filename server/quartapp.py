import asyncio
import base64
from functools import wraps
import json
import os

import jwt
from quart import websocket, Quart, request, Response
from quart_cors import cors

app = Quart(__name__)
app = cors(app)

connected_websockets = set()

secret = os.getenv("TWITCH_SECRET_KEY", None)
if secret is None:
  secret_file_path = os.path.join(os.getcwd(), "secret.key")
  secret = base64.b64decode(open(secret_file_path).read().strip())


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

async def receiving(queue):
  while True:
    data = await websocket.receive()
    await process_message(websocket, data)

async def broadcast(message):
  for queue in connected_websockets:
    await queue.put(message)

@app.websocket('/')
@collect_websocket
async def ws(queue):
  producer = asyncio.create_task(sending(queue))
  consumer = asyncio.create_task(receiving(queue))
  await asyncio.gather(producer, consumer)

@app.route('/broadcast')
async def bcast():
  await broadcast(request.args.get('message'))
  return 'OK'

@app.route('/command')
async def command():
  c = request.args.get('command')

  auth = request.headers.get('Authorization').replace('Bearer ', '')

  r = jwt.decode(auth, secret, algorithms=['HS256'])

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
  await broadcast(j)
  response = Response('OK')
  response.headers['Access-Control-Allow-Origin'] = '*'
  return response

async def process_message(websocket, message):
  m = json.loads(message)
  if m.get('e', '') == 'AUTHENTICATE_ROBOT':
    j = json.dumps({
      'e': 'ROBOT_VALIDATED',
      'd': {
        'host': '192.168.0.136:8000',
      },
    })
    await websocket.send(j)

if __name__ == "__main__":
  app.run(host='0.0.0.0')
