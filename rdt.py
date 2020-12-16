from collections import deque

from USocket import UnreliableSocket
from socket import timeout as TimeoutException
import threading
import time


WINDOW_SIZE = 4
TIME_OUT = 1
MAX_RETRY = 5


def get_send_to(sendto,addr):
    def result(data):
        sendto(data,addr)
    return result


def get_base(bool_arr):
    cnt = 0
    for i in bool_arr:
        if not i:
            break
        cnt += 1
    return cnt


class RDTSocket(UnreliableSocket):
    """
    The functions with which you are to build your RDT.
    -   recvfrom(bufsize)->bytes, addr
    -   sendto(bytes, address)
    -   bind(address)

    You can set the mode of the socket.
    -   settimeout(timeout)
    -   setblocking(flag)
    By default, a socket is created in the blocking mode. 
    https://docs.python.org/3/library/socket.html#socket-timeouts

    """
    def __init__(self, rate=None, debug=True):
        super().__init__(rate=rate)
        self._rate = rate
        self._send_to = None
        self._recv_from = None
        self.target_addr = None
        self.buffer_size = 100000
        self.debug = debug
        #############################################################################
        # TODO: ADD YOUR NECESSARY ATTRIBUTES HERE
        #############################################################################
        
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def bind(self, address:(str, int)):
        super(RDTSocket, self).bind(address)

    def accept(self):
        """
        Accept a connection. The socket must be bound to an address and listening for 
        connections. The return value is a pair (conn, address) where conn is a new 
        socket object usable to send and receive data on the connection, and address 
        is the address bound to the socket on the other end of the connection.

        This function should be blocking. 
        """
        conn, addr = RDTSocket(self._rate), None
        data, addr = self.recvfrom(self.buffer_size)
        self.setblocking(True)
        pkt = decode(data)
        if pkt.syn:
            reply = RDTPacket(True, False, True, 0, 0, 0, b'')
            self.sendto(reply.encode(),addr)
        data, addr = self.recvfrom(self.buffer_size)
        if decode(data).ack:
            conn.set_recv_from(self.recvfrom)
            conn.set_send_to(get_send_to(conn.sendto,addr))
            return conn, addr
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################


    def connect(self, address:(str, int)):
        """
        Connect to a remote socket at address.
        Corresponds to the process of establishing a connection on the client side.
        """
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        pkt = RDTPacket(True, False, False, 0, 0, 0, b'')
        self.sendto(pkt.encode(),address)
        data, addr = self.recvfrom(self.buffer_size)
        if decode(data).syn and decode(data).ack:
            pkt2 = RDTPacket(False, False, True, 0, 0, 0, b'')
            self.sendto(pkt2.encode(), address)
            self.set_send_to(get_send_to(self.sendto, addr))
            self.set_recv_from(self.recvfrom)
            print("connection succeed with", address)
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def recv(self, bufsize:int)->bytes:
        """
        Receive data from the socket. 
        The return value is a bytes object representing the data received. 
        The maximum amount of data to be received at once is specified by bufsize. 
        
        Note that ONLY data send by the peer should be accepted.
        In other words, if someone else sends data to you from another address,
        it MUST NOT affect the data returned by this function.
        """
        self.settimeout(1)
        result = b''
        data = self._recv_from(bufsize)
        while not decode(data[0]).fin:
            result += decode(data[0]).payload
            ack_pkt = RDTPacket(False, False, False, 0, decode(data[0]).seq,0,b'')
            self.sendto(ack_pkt.encode(),('127.0.0.1',8081))
            data = self._recv_from(bufsize)
        print(result)
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        return result

    def send(self, bytes:bytes):
        """
        Send data to the socket. 
        The socket must be connected to a remote socket, i.e. self._send_to must not be none.
        """
        self.settimeout(TIME_OUT)
        pkt_list = []
        # TODO: Change 5 to self.buffer_size
        seq = 0
        while len(bytes) > 5:
            data = bytes[:5]
            pkt = RDTPacket(False, False, False, seq, 0, 5, data)
            pkt_list.append(pkt)
            bytes = bytes[5:]
            seq += 1
        if len(bytes) != 0:
            pkt_list.append(RDTPacket(False, False, False, seq, 0, len(bytes), bytes))
        acked = [False for _ in range(len(pkt_list))]
        # print(data_list)
        added = -1
        win = deque(maxlen=WINDOW_SIZE)
        if len(pkt_list) > WINDOW_SIZE:
            for i in range(WINDOW_SIZE):
                win.append(pkt_list[i])
                added = i
        else:
            for i in pkt_list:
                win.append(i)

        window_base = 0
        for pkt in win:
            self._send_to(pkt.encode())

        retry = 0
        while True:
            try:
                data_rcv = self._recv_from(1000)
                p = decode(data_rcv[0])
                acked[p.seq_ack] = True
                retry = 0

                window_base = get_base(acked)
                while True and len(win) != 0:
                    front = win.popleft().seq
                    if front == window_base - 1:
                        break

                if len(win) != 0:
                    add_num = WINDOW_SIZE - (win[-1].seq - window_base + 1)
                for i in range(add_num):
                    to_add = added + 1 + i
                    if to_add < len(pkt_list):
                        self._send_to(pkt_list[to_add].encode())
                        win.append(pkt_list[to_add])
                        added = to_add
                    else:
                        break

                if len(win) == 0:
                    break
            except TimeoutException:
                retry += 1
                if retry >= MAX_RETRY:
                    print("connection failed")
                    break
                self._send_to(pkt_list[window_base].encode())

        fin_pkt = RDTPacket(False,True,False,0,0,0,b'')
        self._send_to(fin_pkt.encode())


        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def close(self):
        """
        Finish the connection and release resources. For simplicity, assume that
        after a socket is closed, neither futher sends nor receives are allowed.
        """
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        super().close()
        
    def set_send_to(self, send_to):
        self._send_to = send_to
    
    def set_recv_from(self, recv_from):
        self._recv_from = recv_from

"""
You can define additional functions and classes to do thing such as packing/unpacking packets, or threading.

"""

def get_separate(num):
    left = num >> 16
    return left, num - (left << 16)


def get_sum(data):
    result = 0
    if len(data) % 2 != 0:
        data = data + b'\x00'

    while len(data) != 0:
        cur = data[0:2]
        result += int.from_bytes(cur,'big')
        data = data[2:]
    return result


class RDTPacket:
    """
    Form(in byte):
    1, 2: syn + fin + ack +00000
    3, 4, 5, 6: sequence number
    7, 8, 9, 10: sequence ack
    11, 12, 13, 14: length of payload
    15, 16: checksum
    17- : data
    """
    def __init__(self, syn:bool, fin:bool, ack:bool, seq:int, seq_ack:int, length:int, payload:bytes, check = 0):
        self.syn = syn
        self.fin = fin
        self.ack = ack
        self.seq = seq
        self.seq_ack = seq_ack
        self.length = length
        self.payload = payload
        self.check = check

    def encode(self):
        result, check_sum = self.calculate()
        print(check_sum)
        self.check = int(check_sum,16)
        hex_str = check_sum
        if len(hex_str) == 3:
            hex_str = '0'+hex_str
        result += bytes.fromhex(hex_str)
        result += self.payload
        return result

    def calculate(self):
        head = 0x0000
        if self.syn:
            head |= 0x8000
        if self.fin:
            head |= 0x4000
        if self.ack:
            head |= 0x2000
        result = head.to_bytes(2, byteorder="big")
        seq1, seq2 = get_separate(self.seq)
        result += (seq1.to_bytes(2, "big") + seq2.to_bytes(2, "big"))
        seq_ack1, seq_ack2 = get_separate(self.seq_ack)
        result += (seq_ack1.to_bytes(2, "big") + seq_ack2.to_bytes(2, "big"))
        len1, len2 = get_separate(self.length)
        result += (len1.to_bytes(2, "big") + len2.to_bytes(2, "big"))
        check_sum = head + seq1 + seq2 + seq_ack1 + seq_ack2 + len1 + len2 + get_sum(self.payload)
        check_sum += self.check
        hex_chk_sum = hex(check_sum)[2:]
        overflow = 0
        if len(hex_chk_sum) > 4:
            overflow = int(hex_chk_sum[:len(hex_chk_sum) - 4], 16)
        check_sum += overflow
        if overflow == 0:
            check_sum = hex(check_sum)[2:]
        else:
            check_sum = hex(check_sum)[-4:]
        return result, hex(~int(check_sum,16) & 0xFFFF)[2:]


def decode(packet) -> RDTPacket:
    info = packet[0:1]
    flag = bin(info[0]>>5)[2:]
    syn, fin, ack = False, False, False
    if len(flag) == 1:
        flag = '00' + flag
    if len(flag) == 2:
        flag = '0' + flag
    if flag[0] == '1':
        syn = True
    if flag[1] == '1':
        fin = True
    if flag[2] == '1':
        ack = True
    seq = int.from_bytes(packet[2:6], 'big')
    seq_ack = int.from_bytes(packet[6:10], 'big')
    length = int.from_bytes(packet[10:14], 'big')
    check_sum = hex(packet[14])[2:] + hex(packet[15])[2:]
    payload = packet[16:]
    result = RDTPacket(syn,fin,ack,seq,seq_ack,length,payload,check=int(check_sum,16))
    try:
        r, chk = result.calculate()
        assert chk == '0'
        return result
    except AssertionError as e:
        print("Corrupted packet")
        raise ValueError from e
