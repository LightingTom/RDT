import time

import rdt

with open('alice.txt', 'rb') as f:
    DATA = f.read()

c = rdt.RDTSocket()
c.bind(('127.0.0.1', 8081))
c.connect(('127.0.0.1',8080))
c.send(DATA)
# c.send(b'hello, world. This is Toms.sdsad dasdasdasdasdasd\nWelcome to CSEsadasdasdasdasdsadasdasdfsdaf')
