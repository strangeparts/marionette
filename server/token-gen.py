# python token-gen.py --id=robotid --name=robotname --chat=chatchanelname --streamkey=twitch_stream_key servername

import time
from cryptography.fernet import Fernet
import jwt
import getopt
import json
import sys
from configparser import ConfigParser, NoSectionError, NoOptionError

argv = sys.argv[1:]
opts, args = getopt.getopt(argv, shortopts='', longopts=['id=', 'name=', 'chat=', 'streamkey='])
robot = {}
robots = {}


def key_gen():
  return Fernet.generate_key()


def token_gen(secret, payload):
  payload["iat"] = int(time.time())
  # print("payload: " + str(payload))
  return jwt.encode(payload, secret, algorithm='HS256')


for option in opts:
  robot[option[0][2:]] = option[1]

robot["host"] = args[0]

try:
  with open('robots.json', 'r') as filepointer:
    robots = json.load(filepointer)
    filepointer.close()
except(IOError, FileNotFoundError):
  try:
    with open('robots.json', 'w') as filepointer:
      json.dump(robots, filepointer, indent=4)
      filepointer.close()
  except(IOError, FileNotFoundError):
    print("Unable to write robots.json, check that you have permission to write in the directory.")
    sys.exit()

config = ConfigParser()
try:
  with open('config.conf', 'r') as filepointer:
    config.read_file(filepointer)
  filepointer.close()
except(IOError, FileNotFoundError):
  print("Unable to read config.conf, check that it exists and that the program has permission to read it.")
  sys.exit()

try:
  key = config.get('server', 'secret_key')

except(NoSectionError, NoOptionError):
  print("Error in config.conf:", sys.exc_info()[1])
  sys.exit()

if (len(key) != 44) or (key[-1:] != "="):
  key = str(key_gen())[2:46]

print("Key: " + key)
token = token_gen(key, robot)
print("Token: " + token)

try:
  t = robot['streamkey']
except KeyError:
  robot['streamkey'] = "Twitch stream Key not set"

print("Robot data: " + str(robot))
if robots == {}:
  robots[args[0]] = {}
elif robots == "":
  robots = {args[0]: {}}

robots[args[0]][robot["id"]] = \
  {
    "token": token,
    "info": {
      "name": robot["name"],
      "chat": robot["chat"],
      "stream_key": robot['streamkey']
    }
  }

try:
  with open('robots.json', 'w') as filepointer:
    json.dump(robots, filepointer, indent=4)
    filepointer.close()
except(IOError, FileNotFoundError):
  print("Unable to write robots.json, check that you have permission to write in the directory.")
  sys.exit()

print("robots.json updated")
