import time

import rdt


c = rdt.RDTSocket()
c.bind(('127.0.0.1', 8081))
c.connect(('127.0.0.1',8080))
c.send(b'hello, world. This is Toms.sdsad dasdasdasdasdasd\nWelcome to CSEsadasdasdasdasdsadasdasdfsdaf')
