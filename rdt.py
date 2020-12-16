from USocket import UnreliableSocket
import threading
import time


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
            conn.set_recv_from(conn.recvfrom)
            conn.set_send_to(conn.sendto)
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
            print("connection succeed")
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
        data = None
        assert self._recv_from, "Connection not established yet. Use recvfrom instead."
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        return data

    def send(self, bytes:bytes):
        """
        Send data to the socket. 
        The socket must be connected to a remote socket, i.e. self._send_to must not be none.
        """
        assert self._send_to, "Connection not established yet. Use sendto instead."
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        raise NotImplementedError()
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


def decode(packet):
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
        raise ValueError from e


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
        result += bytes.fromhex(check_sum)
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





