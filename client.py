import time

import rdt


c = rdt.RDTSocket()
c.bind(('127.0.0.1', 8081))
c.connect(('127.0.0.1',8080))
time.sleep(1)
c.send(b'hello')
print(c.recv(10000))