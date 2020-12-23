# import rdt
# check_sum = 0x0006+rdt.get_sum(b'hello')
# print(hex(check_sum))
# hex_chk_sum = hex(check_sum)[2:]
# overflow = 0
# if len(hex_chk_sum) > 4:
#     overflow = int(hex_chk_sum[:len(hex_chk_sum) - 4], 16)
# check_sum += overflow
# print(hex(check_sum)[-4:])

# a = bytes.fromhex('12345678')
# for i in range(len(a)):
#     print(hex(a[i]))

# import rdt
# data = b'hello'
# packet = rdt.RDTPacket(False,False,False,1,0,len(data),data)
# encoded = packet.encode()
# c = rdt.decode(encoded)
# print(c.payload)
import time

import rdt


if __name__ == '__main__':
    socket = rdt.RDTSocket()
    socket.bind(('127.0.0.1', 7000))
    socket.setblocking(False)
    while True:
        try:
            conn, addr = socket.accept()
            data = conn.recv(10000000)
            print(data.decode())
            print('waiting')
        except:
            pass
