import time

import rdt

with open('h_alice.txt', 'rb') as f:
    DATA = f.read()

begin_time = time.time()

c = rdt.RDTSocket()
c.bind(('127.0.0.1', 8050))
c.connect(('127.0.0.1',6000))
c.send(DATA)

c.close()
# c.send(b'hello, world. This is Toms.sdsad dasdasdasdasdasd\nWelcome to CSEsadasdasdasdasdsadasdasdfsdaf')
# time.sleep(4)
print("time cost: ", time.time() - begin_time)
