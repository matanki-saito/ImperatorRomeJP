import sys
import getpass
import my_aes
import os

password = os.environ.get("CREDENTIALS_PASSWORD")
dec = my_aes.decrypt(sys.stdin.buffer.read(), password)
sys.stdout.buffer.write(dec)