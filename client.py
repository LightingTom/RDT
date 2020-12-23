import time

import rdt

with open('alice.txt', 'rb') as f:
    DATA = f.read()

begin_time = time.time()

c = rdt.RDTSocket()
c.bind(('127.0.0.1', 7050))
c.connect(('127.0.0.1',7000))
c.send(DATA)

c.close()
# c.send(b'hello, world. This is Toms.sdsad dasdasdasdasdasd\nWelcome to CSEsadasdasdasdasdsadasdasdfsdaf')
# time.sleep(4)
print("time cost: ", time.time() - begin_time)
