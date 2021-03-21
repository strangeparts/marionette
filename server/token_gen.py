from cryptography.fernet import Fernet
def token_gen():
  print (str(Fernet.generate_key())[2:46])
token_gen()
