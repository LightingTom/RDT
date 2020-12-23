import time

import rdt

with open('alice.txt', 'rb') as f:
    DATA = f.read()

begin_time = time.time()

c = rdt.RDTSocket()
c.bind(('127.0.0.1', 8050))
c.connect(('127.0.0.1',7000))
c.send(DATA)
c.close()
# print("-------------------------------------------end-1-----------------------------------")
# c.send(DATA)
# c.close()
# print("--------------------------------------------end-----------------------------")
# c.send(DATA)
# c.send(b'hello, world. This is Toms.sdsad dasdasdasdasdasd\nWelcome to CSEsadasdasdasdasdsadasdasdfsdaf')

end_time = time.time()
print("time cost: ", end_time - begin_time)
