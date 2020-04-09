import random
import string

DEBUG = True
SECRET_KEY = "".join([random.choice(string.printable) for _ in range(24)])
