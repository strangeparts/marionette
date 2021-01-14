import sys
import json
import websocket

def on_message(ws, message):
  print(message)
  j = json.loads(message)
  if j.get('e') == 'ROBOT_VALIDATED':
    print()
    print('Connection ok.')
    sys.exit()

def on_error(ws, error):
  print(error)

def on_close(ws):
  print("### closed ###")

def on_open(ws):
  auth_req = { 'e': 'AUTHENTICATE_ROBOT' }
  ws.send(json.dumps(auth_req))


if __name__ == "__main__":
  ws = websocket.WebSocketApp(sys.argv[1],
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
  ws.on_open = on_open
  ws.run_forever()
