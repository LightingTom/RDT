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
import threading

def udp_recv_1():
    socket = rdt.RDTSocket()
    socket.bind(('127.0.0.1', 8000))
    while True:
        conn, addr = socket.accept()
        data = conn.recv(10000000)
        print(data.decode())
        print('waiting')

def udp_recv_2():
    socket = rdt.RDTSocket()
    socket.bind(('127.0.0.1', 8080))
    while True:
        conn, addr = socket.accept()
        data = conn.recv(10000000)
        print(data.decode())
        print('waiting')

# while True:
#     conn, addr = s.accept()
#     data = conn.recv(1000000000)
#     print(data.decode())
#     print('waiting')


# def deal_client(socket, addr):
#     while True:
#         data = socket.recv(1024)
#         if data:
#             print("%s %s" % (str(addr), data))
#         else:
#             print("client [%s] exit" % str(addr))
#             newSocket.close()
#             break

if __name__ == '__main__':
    socket = rdt.RDTSocket()
    socket.bind(('127.0.0.1', 8000))
    socket.setblocking(True)
    while True:
        conn, addr = socket.accept()
        data = conn.recv(10000000)
        print(data.decode())
        print('waiting')
    # t1 = threading.Thread(target=udp_recv_1)
    # t2 = threading.Thread(target=udp_recv_2)
    # t1.start()
    # t2.start()
    # while True:
    #     newSocket, addr = socket.accept()
    #     print("client [%s] is connected!" % str(addr))
    #     client = threading.Thread(target=deal_client, args=(newSocket, addr))
    #     client.start()