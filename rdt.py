from collections import deque

from USocket import UnreliableSocket
from socket import timeout as TimeoutException
from threading import Timer
import time


WINDOW_SIZE = 4
TIME_OUT = 2
MAX_RETRY = 5
RCV_BUFF_SIZE = 4
MAX_SEND_SIZE = 5


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
        self.buffer_size = 25
        self.debug = debug
        self.timer_list = []
        self.send_win = deque(maxlen=WINDOW_SIZE)
        #############################################################################
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
        # print("accept addr",addr)
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
        #############################################################################                                                    #
        #############################################################################
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################


    def connect(self, address:(str, int)):
        """
        Connect to a remote socket at address.
        Corresponds to the process of establishing a connection on the client side.
        """
        #############################################################################                                                    #
        #############################################################################
        pkt = RDTPacket(True, False, False, 0, 0, 0, b'')
        self.sendto(pkt.encode(),address)
        data, addr = self.recvfrom(self.buffer_size)
        # print("connect", addr)
        if decode(data).syn and decode(data).ack:
            pkt2 = RDTPacket(False, False, True, 0, 0, 0, b'')
            self.sendto(pkt2.encode(), address)
            self.set_send_to(get_send_to(self.sendto, addr))
            self.set_recv_from(self.recvfrom)
            print("connection succeed with", address)
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def get_pos(self, seq_num, cur_win):
        for i in range(len(cur_win)):
            if seq_num == cur_win[i].seq:
                return i
        return -1

    def handle_timeout(self, pkt):
        print("Time out")
        print("Resend pkt #", pkt.seq)
        timer = Timer(TIME_OUT, self.handle_timeout, args=(pkt,))
        # print("pos:",self.get_pos(pkt.seq, self.send_win))
        self.timer_list[self.get_pos(pkt.seq, self.send_win)] = timer
        self._send_to(pkt.encode())
        timer.start()

    def recv(self, bufsize:int)->bytes:
        """
        Receive data from the socket. 
        The return value is a bytes object representing the data received. 
        The maximum amount of data to be received at once is specified by bufsize. 
        
        Note that ONLY data send by the peer should be accepted.
        In other words, if someone else sends data to you from another address,
        it MUST NOT affect the data returned by this function.
        """
        # Used to test send(), just send ack when receive packet
        # self.settimeout(1)
        # result = b''
        # cnt = 0
        # while True:
        #     try:
        #         data = self._recv_from(1000)
        #         p = decode(data[0])
        #         ack = RDTPacket(False, False, False, 0, p.seq, 0, b'')
        #         print("rev #", p.seq)
        #         if cnt == 0 and p.seq == 2:
        #             cnt += 1
        #             print("skip")
        #             continue
        #         self._send_to(ack.encode())
        #     except TimeoutException:
        #         print("Resend")
        buffer = deque(maxlen=RCV_BUFF_SIZE)
        result = b''

        need = 0
        ack = -1
        # cnt = 0
        # cnt1 = 0
        while True:
            try:
                data = self._recv_from(bufsize)
                pkt_rcv = decode(data[0])
                # End with four-way handshake
                if pkt_rcv.fin:
                    ack_pkt = RDTPacket(False, False, True, 0, 0, 0, b'')
                    self._send_to(ack_pkt.encode())
                    fin_pkt = RDTPacket(False, True, False, 0, 0, 0, b'')
                    self._send_to(fin_pkt.encode())
                    f_ack = self._recv_from(bufsize)
                    if decode(f_ack[0]).ack:
                        break

                # Receive the packet
                seq_ack = pkt_rcv.seq
                ack = seq_ack
                # You can simulate packet loss here
                # if cnt == 0 and ack == 2:
                #     cnt += 1
                #     continue
                # if cnt1 == 0 and ack == 6:
                #     cnt1 += 1
                #     continue
                print("ack #", ack)
                # print("buffer length:", len(buffer))
                self._send_to(RDTPacket(False, False, False, 0, ack, 0, b'').encode())
                if ack == need:
                    need += 1
                    # if len(buffer) != 0:
                    #     print("buffer[0]:", buffer[0].seq)
                    # print("need:", need)
                    result += pkt_rcv.payload
                    # clean the buffer
                    while len(buffer) != 0 and buffer[0].seq == need:
                        p = buffer.popleft()
                        result += p.payload
                        need += 1
                elif ack > need:
                    # If not full, add to the buffer
                    if len(buffer) == RCV_BUFF_SIZE:
                        continue
                    else:
                        inserted = False
                        for i in range(len(buffer)):
                            if pkt_rcv.seq < buffer[i].seq:
                                buffer.insert(i, pkt_rcv)
                                inserted = True
                                break
                        if not inserted:
                            buffer.append(pkt_rcv)
                else:
                    pass
            except TimeoutException:
                self._send_to(RDTPacket(False, False, False, 0, ack, 0, b'').encode())
            except ValueError:
                pass
        print(result)
        #############################################################################                                                     #
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
        # TODO: Add max retry
        pkt_list = []
        # TODO: Change 5 to self.buffer_size
        # Split the data and get the whole packet list
        seq = 0
        while len(bytes) > self.buffer_size - 16:
            data = bytes[:self.buffer_size - 16]
            pkt = RDTPacket(False, False, False, seq, 0, self.buffer_size - 16, data)
            pkt_list.append(pkt)
            bytes = bytes[self.buffer_size - 16:]
            seq += 1
        if len(bytes) != 0:
            pkt_list.append(RDTPacket(False, False, False, seq, 0, len(bytes), bytes))
        acked = [False for _ in range(len(pkt_list))]
        # print(data_list)
        # Add packets to the window
        added = -1
        if len(pkt_list) > WINDOW_SIZE:
            for i in range(WINDOW_SIZE):
                self.send_win.append(pkt_list[i])
                added = i
        else:
            for i in pkt_list:
                self.send_win.append(i)

        # Send all packet in the window now
        window_base = 0
        for pkt in self.send_win:
            print("Send pkt #", pkt.seq)
            timer = Timer(TIME_OUT, self.handle_timeout, args=(pkt,))
            self.timer_list.append(timer)
            self._send_to(pkt.encode())
            timer.start()
        # Wait for acks
        retry = 0
        cnt1 = 0
        while True:
            try:
                # print("loop:", cnt1)
                # print("win_length", len(self.send_win))
                # print("window_base", window_base)
                cnt1+=1
                data_rcv = self._recv_from(1000)
                p = decode(data_rcv[0])
                acked[p.seq_ack] = True
                win_pos = p.seq_ack - window_base
                print("Recv ack #", p.seq_ack)
                self.timer_list[win_pos].cancel()

                retry = 0
                # record the ack and move the window
                window_base = get_base(acked)
                while len(self.send_win) != 0 and window_base > self.send_win[0].seq:
                    # print("win[0] =", self.send_win[0].seq)
                    # print("window_base", window_base)
                    self.send_win.popleft()
                    self.timer_list.pop(0)

                if len(self.send_win) == WINDOW_SIZE:
                    continue
                add_num = 0
                if len(self.send_win) != 0:
                    add_num = WINDOW_SIZE - (self.send_win[-1].seq - window_base + 1)
                for i in range(add_num):
                    to_add = added + 1 + i
                    if to_add < len(pkt_list):
                        timer = Timer(TIME_OUT, self.handle_timeout, args=(pkt_list[to_add],))
                        self.timer_list.append(timer)
                        self._send_to(pkt_list[to_add].encode())
                        timer.start()
                        print("Send pkt #", pkt_list[to_add].seq)
                        self.send_win.append(pkt_list[to_add])
                        added = to_add
                    else:
                        break

                if len(self.send_win) == 0:
                    if added == len(pkt_list) - 1:
                        break
                    else:
                        p_to_send = pkt_list[added + 1]
                        timer = Timer(TIME_OUT, self.handle_timeout, args=(p_to_send,))
                        self.timer_list.append(timer)
                        self.send_win.append(p_to_send)
                        self._send_to(p_to_send.encode())
                        timer.start()
                        added = added + 1

            except TimeoutException:
                # Retransmit the timeout packet
                retry += 1
                if retry >= MAX_RETRY:
                    print("connection failed")
                    break
            except ValueError:
                # ignore the packet if the packet corrupt
                pass
            except IndexError:
                print("Index Error")
                print("loop", cnt1)
                print("window base", window_base)

        # End with four-way handshake
        fin_pkt = RDTPacket(False,True,False,0,0,0,b'')
        self._send_to(fin_pkt.encode())
        retry = 0
        while True:
            try:
                data_rcv = self._recv_from(1000)
                if decode(data_rcv[0]).ack:
                    break
            except TimeoutException:
                retry += 1
                if retry >= MAX_RETRY:
                    print("connection break")
                self._send_to(fin_pkt.encode())

        fin_rcv = self._recv_from(1000)
        if decode(fin_rcv[0]).fin:
            self._send_to(RDTPacket(False, False, True, 0, 0, 0, b'').encode())


        #############################################################################                                               #
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
        if self.check != 0:
            check_sum = hex(self.check)[2:]
        else:
            self.check = int(check_sum,16)
        hex_str = check_sum
        if len(hex_str) == 3:
            hex_str = '0'+hex_str
        elif len(hex_str) == 2:
            hex_str = '00' + hex_str
        elif len(hex_str) == 1:
            hex_str = '000' + hex_str
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
    # print(packet)
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
    second = hex(packet[15])[2:]
    if len(second) == 1:
        second = '0'+second
    check_sum = hex(packet[14])[2:] + second
    payload = packet[16:]
    result = RDTPacket(syn,fin,ack,seq,seq_ack,length,payload,check=int(check_sum,16))
    try:
        r, chk = result.calculate()
        assert chk == '0'
        return result
    except AssertionError as e:
        print("check_sum", check_sum)
        print("calculated:", chk)
        print("Corrupted packet")
        raise ValueError from e
